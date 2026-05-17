from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Sequence


LUMIS_PB = {
    "2016": 36330.0,
    "2017": 41530.0,
    "2018": 59740.0,
    "Run2": 137600.0,
}


@dataclass(frozen=True)
class ShapeChannel:
    era: str
    region: str
    bin_names: Sequence[str]
    branch_prefix: str


@dataclass(frozen=True)
class AnalysisConfig:
    name: str
    mode: str  # "shape_histogram" or "template_replace"
    directory_aliases: Sequence[str]
    counts_root_candidates: Sequence[str]
    counts_tree_name: str = "Counts"
    zero_acceptance_branches: Sequence[str] = field(default_factory=tuple)
    template_candidates: Sequence[str] = field(default_factory=list)
    shape_root_candidates: Sequence[str] = field(default_factory=list)
    shape_channels: Sequence[ShapeChannel] = field(default_factory=list)
    use_combine_alias: bool = True
    special_handler: str = ""

    def resolve_existing_path(self, relative_candidates: Sequence[str], base_dir: Path) -> Path:
        for rel in relative_candidates:
            path = base_dir / rel
            if path.exists():
                return path
        raise FileNotFoundError(
            f"Could not resolve any of: {list(relative_candidates)} relative to {base_dir}"
        )

    def resolve_analysis_dir(self, base_dir: Path, subdir: str) -> Path:
        for alias in self.directory_aliases:
            candidate = base_dir / subdir / alias
            if candidate.exists():
                return candidate
        raise FileNotFoundError(
            f"Could not resolve {subdir} directory for {self.name}. Tried aliases: {list(self.directory_aliases)}"
        )


SUS_18_004 = AnalysisConfig(
    name="SUS_18_004",
    mode="shape_histogram",
    directory_aliases=["SUS_18_004", "CMS_SUS_18_004"],
    counts_root_candidates=[
        "THnSparses/SUS_18_004/sus_18_004.root",
        "THnSparses/SUS_18_004/cms_sus_18_004.root",
        "THnSparses/CMS_SUS_18_004/cms_sus_18_004.root",
    ],
    counts_tree_name="Counts",
    zero_acceptance_branches=("Zsig_sus_18_004", "Zsig_cms_sus_18_004"),
    shape_channels=[
        ShapeChannel("2017", "sos_2los_sr_high", ["Mll_1_4", "Mll_4_10", "Mll_10_20", "Mll_20_30", "Mll_30_50"], "SUS_18_004_2l_highMET"),
        ShapeChannel("2017", "sos_2los_sr_low", ["Mll_4_10", "Mll_10_20", "Mll_20_30", "Mll_30_50"], "SUS_18_004_2l_lowMET"),
        ShapeChannel("2017", "sos_2los_sr_med", ["Mll_1_4", "Mll_4_10", "Mll_10_20", "Mll_20_30", "Mll_30_50"], "SUS_18_004_2l_medMET"),
        ShapeChannel("2017", "sos_2los_sr_ultra", ["Mll_1_4", "Mll_4_10", "Mll_10_20", "Mll_20_30", "Mll_30_50"], "SUS_18_004_2l_ultraMET"),
        ShapeChannel("2017", "sos_3l_sr_low", ["Mll_4_10", "Mll_10_20", "Mll_20_30", "Mll_30_50"], "SUS_18_004_3l_lowMET"),
        ShapeChannel("2017", "sos_3l_sr_med", ["Mll_1_4", "Mll_4_10", "Mll_10_20", "Mll_20_30", "Mll_30_50"], "SUS_18_004_3l_medMET"),
        ShapeChannel("2018", "sos_2los_sr_high", ["Mll_1_4", "Mll_4_10", "Mll_10_20", "Mll_20_30", "Mll_30_50"], "SUS_18_004_2l_highMET"),
        ShapeChannel("2018", "sos_2los_sr_low", ["Mll_4_10", "Mll_10_20", "Mll_20_30", "Mll_30_50"], "SUS_18_004_2l_lowMET"),
        ShapeChannel("2018", "sos_2los_sr_med", ["Mll_1_4", "Mll_4_10", "Mll_10_20", "Mll_20_30", "Mll_30_50"], "SUS_18_004_2l_medMET"),
        ShapeChannel("2018", "sos_2los_sr_ultra", ["Mll_1_4", "Mll_4_10", "Mll_10_20", "Mll_20_30", "Mll_30_50"], "SUS_18_004_2l_ultraMET"),
        ShapeChannel("2018", "sos_3l_sr_low", ["Mll_4_10", "Mll_10_20", "Mll_20_30", "Mll_30_50"], "SUS_18_004_3l_lowMET"),
        ShapeChannel("2018", "sos_3l_sr_med", ["Mll_1_4", "Mll_4_10", "Mll_10_20", "Mll_20_30", "Mll_30_50"], "SUS_18_004_3l_medMET"),
    ],
    use_combine_alias=True,
)

SUS_21_006 = AnalysisConfig(
    name="SUS_21_006",
    mode="template_replace",
    directory_aliases=["SUS_21_006", "CMS_SUS_21_006"],
    counts_root_candidates=[
        "THnSparses/SUS_21_006/sus_21_006.root",
        "THnSparses/SUS_21_006/cms_sus_21_006.root",
        "THnSparses/SUS_21_006/sus_21_006_likelihood.root",
        "THnSparses/SUS_21_006/cms_sus_21_006_likelihood.root",
        "THnSparses/CMS_SUS_21_006/cms_sus_21_006.root",
        "THnSparses/CMS_SUS_21_006/cms_sus_21_006_likelihood.root",
    ],
    counts_tree_name="Counts",
    zero_acceptance_branches=("Zsig_sus_21_006", "Zsig_cms_sus_21_006"),
    template_candidates=[
        "datacards/provided/SUS_21_006/template_card.txt",
        "datacards/provided/CMS_SUS_21_006/template_card.txt",
        "datacards/rawprovided/SUS_21_006/template_card.txt",
        "datacards/rawprovided/CMS_SUS_21_006/template_card.txt",
    ],
    use_combine_alias=False,
)

SUS_24_003 = AnalysisConfig(
    name="SUS_24_003",
    mode="template_replace",
    directory_aliases=["SUS_24_003", "CMS_SUS_24_003"],
    counts_root_candidates=[
        "THnSparses/SUS_24_003/sus_24_003_likelihood_phase1.root",
    ],
    counts_tree_name="cms_sus_24_003",
    zero_acceptance_branches=("Zsig_sus_24_003", "Zsig_cms_sus_24_003"),
    template_candidates=[
        "datacards/provided/SUS_24_003/sus-24-003_TemplateRun2.txt",
        "datacards/provided/SUS_24_003/Run2_card.txt",
        "datacards/provided/CMS_SUS_24_003/sus-24-003_TemplateRun2.txt",
        "datacards/provided/CMS_SUS_24_003/Run2_card.txt",
    ],
    use_combine_alias=True,
    special_handler="sus_24_003_phase1proxy",
)

SUS_20_001 = AnalysisConfig(
    name="SUS_20_001",
    mode="template_replace",
    directory_aliases=["SUS_20_001", "CMS_SUS_20_001"],
    counts_root_candidates=[
        "THnSparses/SUS_20_001/sus_20_001_likelihood.root",
    ],
    counts_tree_name="cms_sus_20_001",
    zero_acceptance_branches=("Zsig_sus_20_001", "Zsig_cms_sus_20_001"),
    template_candidates=[
        "datacards/provided/SUS_20_001/template_card.txt",
    ],
    use_combine_alias=True,
    special_handler="sus_20_001_phase1proxy",
)


SUS_21_001 = AnalysisConfig(
    name="SUS_21_001",
    mode="template_replace",
    directory_aliases=["SUS_21_001", "CMS_SUS_21_001"],
    counts_root_candidates=[
        "THnSparses/SUS_21_001/sus_21_001_likelihood.root",
        "THnSparses/SUS_21_001/cms_sus_21_001.root",
        "THnSparses/CMS_SUS_21_001/sus_21_001_likelihood.root",
        "THnSparses/CMS_SUS_21_001/cms_sus_21_001.root",
    ],
    counts_tree_name="cms_sus_21_001",
    zero_acceptance_branches=("Zsig_sus_21_001", "Zsig_cms_sus_21_001"),
    template_candidates=[
        "datacards/provided/SUS_21_001/template_card.txt",
    ],
    use_combine_alias=True,
    special_handler="sus_21_001_run2",
)


SUPPORTED_ANALYSES: Dict[str, AnalysisConfig] = {
    SUS_18_004.name: SUS_18_004,
    SUS_20_001.name: SUS_20_001,
    SUS_21_001.name: SUS_21_001,
    SUS_21_006.name: SUS_21_006,
    SUS_24_003.name: SUS_24_003,
}