from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence

from analysis_configs import AnalysisConfig, LUMIS_PB, SUPPORTED_ANALYSES, ShapeChannel

try:
    import ROOT  # type: ignore
except Exception as exc:  # pragma: no cover
    raise RuntimeError("These scripts require a CMSSW/ROOT environment.") from exc


@dataclass
class Point:
    chain_index: int
    niteration: int

    @property
    def key(self) -> str:
        return f"{self.chain_index}_{self.niteration}"


@dataclass
class MaterializedCard:
    analysis: str
    label: str
    card_path: Path
    signal_sum: float


class RootHandleCache:
    def __init__(self) -> None:
        self._files: Dict[Path, object] = {}
        self._trees: Dict[tuple[Path, str], object] = {}

    def tfile(self, path: Path):
        path = path.resolve()
        if path not in self._files:
            tf = ROOT.TFile.Open(str(path))
            if not tf or tf.IsZombie():
                raise OSError(f"Could not open ROOT file: {path}")
            self._files[path] = tf
        return self._files[path]

    def ttree(self, path: Path, tree_name: str):
        key = (path.resolve(), tree_name)
        if key not in self._trees:
            tree = self.tfile(path).Get(tree_name)
            if tree is None:
                raise KeyError(f"Could not find tree '{tree_name}' in {path}")
            self._trees[key] = tree
        return self._trees[key]

    def close(self) -> None:
        for tf in self._files.values():
            try:
                tf.Close()
            except Exception:
                pass
        self._files.clear()
        self._trees.clear()


def find_existing(base_dir: Path, candidates: Sequence[str]) -> Path:
    for candidate in candidates:
        path = base_dir / candidate
        if path.exists():
            return path
    raise FileNotFoundError(f"None of the candidate paths exists: {list(candidates)}")


class PipelineContext:
    def __init__(self, base_dir: Path, pmssm_tree_path: Path, pmssm_tree_name: str = "mcmc") -> None:
        self.base_dir = base_dir.resolve()
        self.pmssm_tree_path = pmssm_tree_path.resolve()
        self.pmssm_tree_name = pmssm_tree_name
        self.cache = RootHandleCache()
        self.pmssm_tree = self.cache.ttree(self.pmssm_tree_path, self.pmssm_tree_name)
        self.pmssm_tree.BuildIndex("chain_index", "Niteration")
        self._counts_trees: Dict[str, object] = {}

    def counts_tree(self, config: AnalysisConfig):
        if config.name not in self._counts_trees:
            counts_path = find_existing(self.base_dir, config.counts_root_candidates)
            tree = self.cache.ttree(counts_path, config.counts_tree_name)
            if hasattr(tree, "BuildIndex"):
                try:
                    tree.BuildIndex("chain_index", "Niteration")
                except Exception:
                    pass
            self._counts_trees[config.name] = tree
            print(f"[open] counts tree: {counts_path}::{config.counts_tree_name}")
        return self._counts_trees[config.name]

    def load_point(self, point: Point) -> bool:
        return self.pmssm_tree.GetEntryWithIndex(point.chain_index, point.niteration) >= 0

    def close(self) -> None:
        self.cache.close()


class CardBuilder:
    def __init__(self, context: PipelineContext):
        self.ctx = context

    def _analysis_active(self, config: AnalysisConfig) -> bool:
        if not config.zero_acceptance_branches:
            return True
        for branch in config.zero_acceptance_branches:
            try:
                value = float(getattr(self.ctx.pmssm_tree, branch))
                return value != 0.0
            except AttributeError:
                continue
        return True

    def _analysis_tokens(self, config: AnalysisConfig) -> list[str]:
        tokens = {config.name, config.name.lower()}
        for alias in config.directory_aliases:
            tokens.add(alias)
            tokens.add(alias.lower())
        return sorted(tokens, key=len, reverse=True)

    def _replace_placeholder_token(self, text: str, token: str, value: float) -> str:
        numeric = f"{value:.6g}"
        patterns = [
            rf"(?<!\S){re.escape(token)}(?=\s)",
            rf"(?<!\S){re.escape(token)}(?!\S)",
        ]
        updated = text
        for pattern in patterns:
            updated, nsub = re.subn(pattern, numeric, updated)
            if nsub > 0:
                return updated
        return text

    def materialize_cards(self, point: Point, analyses: Sequence[str], workdir: Path) -> List[MaterializedCard]:
        cards: List[MaterializedCard] = []
        for analysis_name in analyses:
            config = SUPPORTED_ANALYSES[analysis_name]
            if config.mode == "shape_histogram":
                cards.extend(self._build_shape_cards(config, point, workdir))
            elif config.mode == "template_replace":
                cards.append(self._build_template_card(config, point, workdir))
            else:
                raise ValueError(f"Unsupported mode '{config.mode}' for {analysis_name}")
        return cards

    def _point_xsec(self) -> float:
        return float(getattr(self.ctx.pmssm_tree, "xsec_tot_pb"))

    def _point_filter_eff(self) -> float:
        return float(getattr(self.ctx.pmssm_tree, "filter_eff", 1.0))

    def _signal_name(self, point: Point, analysis: str, suffix: str = "") -> str:
        stem = f"Signal_{analysis}_{point.key}"
        return stem if not suffix else f"{stem}_{suffix}"

    def _build_shape_cards(self, config: AnalysisConfig, point: Point, workdir: Path) -> List[MaterializedCard]:
        cards: List[MaterializedCard] = []
        counts_tree = self.ctx.counts_tree(config)
        active = self._analysis_active(config)
        if active:
            counts_tree.GetEntryWithIndex(point.chain_index, point.niteration)
        point_filter_eff = self._point_filter_eff()
        point_xsec_pb = self._point_xsec()

        for channel in config.shape_channels:
            analysis_dir = config.resolve_analysis_dir(self.ctx.base_dir, "datacards/provided")
            txt_path = analysis_dir / channel.era / f"{channel.region}.txt"
            root_path = analysis_dir / channel.era / f"{channel.region}.root"
            if not txt_path.exists() or not root_path.exists():
                raise FileNotFoundError(f"Missing provided inputs for {config.name} {channel.era} {channel.region}")

            out_root_path = workdir / f"{config.name}_{channel.era}_{channel.region}_{point.key}.root"
            signal_name = self._signal_name(point, config.name, f"{channel.era}_{channel.region}")
            signal_sum = self._write_shape_root(
                root_path=root_path,
                region=channel.region,
                out_root_path=out_root_path,
                signal_name=signal_name,
                config=config,
                channel=channel,
                active=active,
                point_filter_eff=point_filter_eff,
                point_xsec_pb=point_xsec_pb,
                counts_tree=counts_tree,
            )

            card_text = txt_path.read_text()
            card_text = card_text.replace("Signal          ", f"{signal_name:<16}")
            card_text = card_text.replace("nsig     ", f"{signal_sum:<9.6g}")
            card_text = card_text.replace(f"{channel.region}.root", out_root_path.name)

            card_path = workdir / f"card_{config.name}_{channel.era}_{channel.region}_{point.key}.txt"
            card_path.write_text(card_text)
            print(f"[new root created] {out_root_path}")
            print(f"[new card created] {card_path}")
            cards.append(
                MaterializedCard(
                    analysis=config.name,
                    label=f"{config.name}_{channel.era}_{channel.region}",
                    card_path=card_path,
                    signal_sum=signal_sum,
                )
            )
        return cards

    def _write_shape_root(
        self,
        *,
        root_path: Path,
        region: str,
        out_root_path: Path,
        signal_name: str,
        config: AnalysisConfig,
        channel: ShapeChannel,
        active: bool,
        point_filter_eff: float,
        point_xsec_pb: float,
        counts_tree,
    ) -> float:
        source = self.ctx.cache.tfile(root_path)
        region_dir = source.Get(region)
        if region_dir is None:
            raise KeyError(f"Directory '{region}' not found in {root_path}")
        target = ROOT.TFile(str(out_root_path), "RECREATE")
        target.mkdir(region)
        target.cd(region)

        keys = region_dir.GetListOfKeys()
        for key in keys:
            name = key.GetName()
            obj = source.Get(f"{region}/{name}")
            obj.Write(name)

        htemplate = source.Get(f"{region}/data_obs").Clone("htemplate")
        htemplate.Reset()
        hsignal = htemplate.Clone(signal_name)

        signal_sum = 0.0
        if active:
            lumi_pb = LUMIS_PB[channel.era]
            for ibin, bin_name in enumerate(channel.bin_names, start=1):
                branch_name = f"{channel.branch_prefix}_{bin_name}_{channel.era}"
                nproc_name = f"{config.name}_nProcessed_{channel.era}"
                try:
                    signal_count = float(getattr(counts_tree, branch_name))
                    nprocessed = float(getattr(counts_tree, nproc_name))
                except AttributeError:
                    signal_count = 0.0
                    nprocessed = 0.0
                value = 0.0
                if nprocessed > 0.0:
                    value = point_filter_eff * lumi_pb * point_xsec_pb * (signal_count / nprocessed)
                hsignal.SetBinContent(ibin, value)
                signal_sum += value

        target.cd(region)
        hsignal.Write(signal_name)
        target.Close()
        return signal_sum

    def _build_template_card(self, config: AnalysisConfig, point: Point, workdir: Path) -> MaterializedCard:
        if config.special_handler == "sus_24_003_phase1proxy":
            return self._build_sus_24_003_card(config, point, workdir)
            
        if config.special_handler == "sus_20_001_phase1proxy":
            return self._build_sus_20_001_card(config, point, workdir)  
            
        if config.special_handler == "sus_21_001_run2":
            return self._build_sus_21_001_card(config, point, workdir)                      

        counts_tree = self.ctx.counts_tree(config)
        active = self._analysis_active(config)
        found = counts_tree.GetEntryWithIndex(point.chain_index, point.niteration) >= 0
        template_path = find_existing(self.ctx.base_dir, config.template_candidates)
        card_text = template_path.read_text()
        print(f"[open] template card: {template_path}")

        branch_names = [br.GetName() for br in counts_tree.GetListOfBranches()]
        signal_sum = 0.0
        analysis_tokens = self._analysis_tokens(config)
        for branch_name in branch_names:
            if branch_name in {"chain_index", "Niteration"}:
                continue
            lowered = branch_name.lower()
            if not any(token.lower() in lowered for token in analysis_tokens):
                continue
            value = 0.0
            if active and found:
                try:
                    value = float(getattr(counts_tree, branch_name))
                except Exception:
                    value = 0.0
            signal_sum += max(0.0, value)

            suffixes = {branch_name}
            for token in analysis_tokens:
                suffixes.add(branch_name.replace(token, ""))
                suffixes.add(branch_name.replace(token.lower(), ""))

            for suffix in sorted({s for s in suffixes if s}, key=len, reverse=True):
                before = card_text
                card_text = self._replace_placeholder_token(card_text, suffix, value)
                if card_text != before:
                    break

        if not any(line.lstrip().startswith("shapes ") for line in card_text.splitlines()):
            lines = card_text.splitlines()
            insert_at = 0
            if lines and lines[0].startswith("imax"):
                insert_at = 1
            lines.insert(insert_at, "shapes * * FAKE")
            card_text = "\n".join(lines) + ("\n" if card_text.endswith("\n") else "")

        card_path = workdir / f"card_{config.name}_Run2_{point.key}.txt"
        card_path.write_text(card_text)
        print(f"[new card created] {card_path}")
        return MaterializedCard(
            analysis=config.name,
            label=f"{config.name}_Run2",
            card_path=card_path,
            signal_sum=signal_sum,
        )

    def _build_sus_24_003_card(self, config: AnalysisConfig, point: Point, workdir: Path) -> MaterializedCard:
        counts_tree = self.ctx.counts_tree(config)
        template_path = find_existing(self.ctx.base_dir, config.template_candidates)
        card_text = template_path.read_text()
        print(f"[open] template card: {template_path}")

        found = counts_tree.GetEntryWithIndex(point.chain_index, point.niteration) >= 0
        if not found:
            raise RuntimeError(
                f"SUS_24_003 point not found in tree for chain_index={point.chain_index}, "
                f"Niteration={point.niteration}"
            )

        xsec_pb = float(getattr(counts_tree, "xsec_pb"))
        filtereff = float(getattr(counts_tree, "filtereff", 1.0))

        def safe_yield(sr_idx: int, year: str) -> float:
            sr_branch = f"cms_sus_24_003_sr_{sr_idx}_{year}"
            ntot_branch = f"cms_sus_24_003_nTotal_{year}"

            n_total = float(getattr(counts_tree, ntot_branch, 0.0))
            if n_total <= 0.0:
                return 0.0

            passed = float(getattr(counts_tree, sr_branch, 0.0))
            lumi_pb = float(LUMIS_PB[year])
            return lumi_pb * xsec_pb * filtereff * passed / n_total

        phase1_yields: List[float] = []
        for sr in range(1, 7):
            y17 = safe_yield(sr, "2017")
            y18 = safe_yield(sr, "2018")
            phase1_yields.append(y17 + y18)

        lumi16 = float(LUMIS_PB["2016"])
        lumi17 = float(LUMIS_PB["2017"])
        lumi18 = float(LUMIS_PB["2018"])
        proxy_scale = lumi16 / (lumi17 + lumi18)

        phase0_yields = [y * proxy_scale for y in phase1_yields]

        replacements: Dict[str, float] = {}
        for i, y in enumerate(phase0_yields, start=1):
            replacements[f"_SR_{i}"] = y
        for i, y in enumerate(phase1_yields, start=7):
            replacements[f"_SR_{i}"] = y

        signal_sum = 0.0
        for token, value in replacements.items():
            card_text = self._replace_placeholder_token(card_text, token, value)
            signal_sum += max(0.0, value)

        if not any(line.lstrip().startswith("shapes ") for line in card_text.splitlines()):
            lines = card_text.splitlines()
            insert_at = 0
            if lines and lines[0].startswith("imax"):
                insert_at = 1
            lines.insert(insert_at, "shapes * * FAKE")
            card_text = "\n".join(lines) + ("\n" if card_text.endswith("\n") else "")

        out_card = workdir / f"card_{config.name}_Run2_{point.key}.txt"
        out_card.write_text(card_text)
        print(f"[new card created] {out_card}")

        return MaterializedCard(
            analysis=config.name,
            label=f"{config.name}_Run2",
            card_path=out_card,
            signal_sum=signal_sum,
        )
    def _build_sus_20_001_card(self, config: AnalysisConfig, point: Point, workdir: Path) -> MaterializedCard:
        counts_tree = self.ctx.counts_tree(config)
        template_path = find_existing(self.ctx.base_dir, config.template_candidates)
        card_text = template_path.read_text()
        print(f"[open] template card: {template_path}")
    
        found = counts_tree.GetEntryWithIndex(point.chain_index, point.niteration) >= 0
        if not found:
            raise RuntimeError(
                f"SUS_20_001 point not found in tree for chain_index={point.chain_index}, "
                f"Niteration={point.niteration}"
            )
    
        xsec_pb = float(getattr(counts_tree, "xsec_pb"))
        filtereff = float(getattr(counts_tree, "filtereff", 1.0))
    
        def safe_yield(sr_idx: int, year: str) -> float:
            sr_branch = f"cms_sus_20_001_sr_{sr_idx}_{year}"
            ntot_branch = f"cms_sus_20_001_nTotal_{year}"
    
            n_total = float(getattr(counts_tree, ntot_branch, 0.0))
            if n_total <= 0.0:
                return 0.0
    
            passed = float(getattr(counts_tree, sr_branch, 0.0))
            lumi_pb = float(LUMIS_PB[year])
            return lumi_pb * xsec_pb * filtereff * passed / n_total
    
        yields_2017 = [safe_yield(sr, "2017") for sr in range(1, 29)]
        yields_2018 = [safe_yield(sr, "2018") for sr in range(1, 29)]
        phase1 = [a + b for a, b in zip(yields_2017, yields_2018)]
    
        proxy_scale = float(LUMIS_PB["2016"]) / (float(LUMIS_PB["2017"]) + float(LUMIS_PB["2018"]))
        proxy_2016 = [y * proxy_scale for y in phase1]
    
        # final Run2 signal yield per SR = proxy2016 + 2017 + 2018
        run2_yields = [y16 + y17 + y18 for y16, y17, y18 in zip(proxy_2016, yields_2017, yields_2018)]
    
        signal_sum = 0.0
        for i, value in enumerate(run2_yields, start=1):
            card_text = self._replace_placeholder_token(card_text, f"_SR_{i}", value)
            signal_sum += max(0.0, value)
    
        if not any(line.lstrip().startswith("shapes ") for line in card_text.splitlines()):
            lines = card_text.splitlines()
            insert_at = 0
            if lines and lines[0].startswith("imax"):
                insert_at = 1
            lines.insert(insert_at, "shapes * * FAKE")
            card_text = "\n".join(lines) + ("\n" if card_text.endswith("\n") else "")
    
        out_card = workdir / f"card_{config.name}_Run2_{point.key}.txt"
        out_card.write_text(card_text)
        print(f"[new card created] {out_card}")
    
        return MaterializedCard(
            analysis=config.name,
            label=f"{config.name}_Run2",
            card_path=out_card,
            signal_sum=signal_sum,
        )        





    def _build_sus_21_001_card(self, config: AnalysisConfig, point: Point, workdir: Path) -> MaterializedCard:
        counts_tree = self.ctx.counts_tree(config)
        template_path = find_existing(self.ctx.base_dir, config.template_candidates)
        card_text = template_path.read_text()
        print(f"[open] template card: {template_path}")
    
        found = counts_tree.GetEntryWithIndex(point.chain_index, point.niteration) >= 0
        if not found:
            raise RuntimeError(
                f"SUS_21_001 point not found in tree for chain_index={point.chain_index}, "
                f"Niteration={point.niteration}"
            )
    
        xsec_pb = float(getattr(counts_tree, "xsec_pb"))
        filtereff = float(getattr(counts_tree, "filtereff", 1.0))
    
        def year_yield(sr_idx: int, year: str) -> float:
            sr_branch = f"cms_sus_21_001_sr_{sr_idx}_{year}"
            ntot_branch = f"cms_sus_21_001_nTotal_{year}"
    
            passed = float(getattr(counts_tree, sr_branch, 0.0))
            n_total = float(getattr(counts_tree, ntot_branch, 0.0))
    
            if n_total <= 0.0:
                raise RuntimeError(
                    f"SUS_21_001 has non-positive {ntot_branch} for "
                    f"point {point.chain_index}_{point.niteration}"
                )
    
            lumi_pb = float(LUMIS_PB[year])
            return lumi_pb * xsec_pb * filtereff * passed / n_total
    
        run2_yields = []
        for sr in range(1, 32):
            y16 = year_yield(sr, "2016")
            y17 = year_yield(sr, "2017")
            y18 = year_yield(sr, "2018")
            run2_yields.append(y16 + y17 + y18)
    
        signal_sum = 0.0
        for i, value in enumerate(run2_yields, start=1):
            card_text = self._replace_placeholder_token(card_text, f"_SR_{i}", value)
            signal_sum += max(0.0, value)
    
        out_card = workdir / f"card_{config.name}_Run2_{point.key}.txt"
        out_card.write_text(card_text)
        print(f"[new card created] {out_card}")
    
        return MaterializedCard(
            analysis=config.name,
            label=f"{config.name}_Run2",
            card_path=out_card,
            signal_sum=signal_sum,
        )        


def combine_cards(cards: Sequence[MaterializedCard], output_path: Path) -> None:
    cmd = ["combineCards.py"]
    for card in cards:
        if SUPPORTED_ANALYSES[card.analysis].use_combine_alias:
            arg = f"{card.label}={card.card_path}"
        else:
            arg = str(card.card_path)
        cmd.append(arg)
        print(f"[combine input] {arg}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w") as handle:
        subprocess.run(cmd, check=True, stdout=handle)

    print(f"[combine output card] {output_path}")
    print(f"[new card created] {output_path}")


def run_combine(card_path: Path, output_dir: Path, name: str, combine_binary: str = "combine") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        combine_binary,
        "--method",
        "MultiDimFit",
        str(card_path),
        "--mass",
        "125.0",
        "--algo",
        "grid",
        "--redefineSignalPOIs",
        "r",
        "--setParameterRanges",
        "r=0.0,1.5",
        "--points",
        "16",
        "--alignEdges",
        "1",
        "--saveNLL",
        "--cminDefaultMinimizerType",
        "Minuit2",
        "--cminDefaultMinimizerStrategy",
        "0",
        "--cminDefaultMinimizerTolerance",
        "0.1",
        "--cminFallbackAlgo",
        "Minuit2,0:0.2",
        "--name",
        name,
    ]
    print(f"[run] {' '.join(cmd)}")
    subprocess.run(cmd, cwd=card_path.parent, check=True)

    produced_name = f"higgsCombine{name}.MultiDimFit.mH125.root"
    produced_path = card_path.parent / produced_name
    if not produced_path.exists():
        raise FileNotFoundError(f"Expected combine output not found: {produced_path}")

    final_path = output_dir / produced_name.replace(f"higgsCombine{name}", "higgsCombine" + name)
    if final_path.resolve() != produced_path.resolve():
        produced_path.replace(final_path)
    print(f"[new root created] {final_path}")
    return final_path
    



LIMIT_INDEX_MAP = {
    "mu0p0": 1,
    "mu0p5": 6,
    "mu1p0": 11,
    "mu1p5": 16,
}


def read_limit_values(root_file: Path, two_delta_nll_scale: float = 2.0) -> HarvestValues:
    tf = ROOT.TFile.Open(str(root_file))
    if not tf or tf.IsZombie():
        raise OSError(f"Could not open combine output: {root_file}")
    limit = tf.Get("limit")
    if limit is None:
        raise KeyError(f"No 'limit' tree found in {root_file}")

    llhds: Dict[str, float] = {}
    for key, entry in LIMIT_INDEX_MAP.items():
        if limit.GetEntry(entry) <= 0:
            raise RuntimeError(f"Could not read entry {entry} from {root_file}")
        llhds[key] = -(2.0 * float(limit.deltaNLL))

    tf.Close()
    base = llhds["mu0p0"]

    def bf(target: str) -> float:
        return math.exp(llhds[target] - base)

    def z(target: str) -> float:
        delta = llhds[target] - base
        return math.copysign(math.sqrt(2.0 * abs(delta)), delta) if delta != 0.0 else 0.0

    return HarvestValues(
        llhd_mu0p0=llhds["mu0p0"],
        llhd_mu0p5=llhds["mu0p5"],
        llhd_mu1p0=llhds["mu1p0"],
        llhd_mu1p5=llhds["mu1p5"],
        bf_mu0p5=bf("mu0p5"),
        bf_mu1p0=bf("mu1p0"),
        bf_mu1p5=bf("mu1p5"),
        zsig_mu0p5=z("mu0p5"),
        zsig_mu1p0=z("mu1p0"),
        zsig_mu1p5=z("mu1p5"),
    )
