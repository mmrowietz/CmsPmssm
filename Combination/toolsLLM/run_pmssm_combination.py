#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import tempfile
from pathlib import Path

from analysis_configs import SUPPORTED_ANALYSES
from pipeline_lib import CardBuilder, PipelineContext, Point, combine_cards, run_combine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize per-point cards on demand and run combine without storing 500k permanent cards. Run this from the Combination area after setting up CMSSW_14_1_0_pre4/src and cmsenv."
    )
    parser.add_argument("--base-dir", default=".", help="Combination working area")
    parser.add_argument(
        "--pmssm-tree",
        default="rootfiles/TheNewestAndMostExcitingFullTree.root",
        help="ROOT file containing the master mcmc tree",
    )
    parser.add_argument("--pmssm-tree-name", default="mcmc")
    parser.add_argument(
        "--analyses",
        nargs="+",
        default=["SUS_18_004", "SUS_21_006"],
        choices=sorted(SUPPORTED_ANALYSES.keys()),
    )
    parser.add_argument("--point", nargs=2, type=int, metavar=("CHAIN_INDEX", "NITERATION"))
    parser.add_argument("--points-file")
    parser.add_argument("--max-points", type=int)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument(
        "--output-dir",
        help="Directory for final combine ROOT outputs; defaults to combinerootsLLM/<combo>/Run2",
    )
    parser.add_argument("--combine-binary", default="combine")
    parser.add_argument("--keep-workdirs", action="store_true")
    return parser.parse_args()


def iter_points_from_file(path: Path):
    with path.open() as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            fields = stripped.replace(",", " ").split()
            if len(fields) < 2:
                raise ValueError(f"Could not parse point line: {line!r}")
            yield Point(int(fields[0]), int(fields[1]))


def iter_points_from_tree(ctx: PipelineContext, start_index: int = 0, max_points: int | None = None):
    tree = ctx.pmssm_tree
    nentries = int(tree.GetEntries())
    yielded = 0
    for ientry in range(start_index, nentries):
        tree.GetEntry(ientry)
        yield Point(int(tree.chain_index), int(tree.Niteration))
        yielded += 1
        if max_points is not None and yielded >= max_points:
            break


def main() -> int:
    args = parse_args()
    base_dir = Path(args.base_dir).resolve()
    ctx = PipelineContext(base_dir, base_dir / args.pmssm_tree, args.pmssm_tree_name)
    builder = CardBuilder(ctx)

    combo_name = "__".join(args.analyses)
    output_dir = Path(args.output_dir).resolve() if args.output_dir else (base_dir / "combinerootsLLM" / combo_name / "Run2")
    output_dir.mkdir(parents=True, exist_ok=True)
    bkg_only_cache = output_dir / "certifiedBkgOnly.root"

    if args.point:
        points = [Point(args.point[0], args.point[1])]
    elif args.points_file:
        points = list(iter_points_from_file(Path(args.points_file)))
    else:
        points = list(iter_points_from_tree(ctx, start_index=args.start_index, max_points=args.max_points))

    work_parent = base_dir / "toolsLLM" if (base_dir / "toolsLLM").exists() else base_dir

    for point in points:
        if not ctx.load_point(point):
            print(f"[warn] point {point.key}: not found in {ctx.pmssm_tree_path}")
            continue

        expected = output_dir / f"higgsCombine_{point.key}.MultiDimFit.mH125.root"
        if expected.exists():
            print(f"[skip] {expected}")
            continue

        workdir = Path(tempfile.mkdtemp(prefix=f"pmssm_{point.key}_", dir=str(work_parent)))
        print(f"[debug] working directory: {workdir}")
        try:
            cards = builder.materialize_cards(point, args.analyses, workdir)
            combo_card = workdir / f"combo_{point.key}.txt"
            combine_cards(cards, combo_card)
            if all(card.signal_sum <= 0.0 for card in cards) and bkg_only_cache.exists():
                os.symlink(bkg_only_cache, expected)
                print(f"[cache] point {point.key} -> {expected}")
                continue

            produced = run_combine(combo_card, output_dir, name=f"_{point.key}", combine_binary=args.combine_binary)
            if all(card.signal_sum <= 0.0 for card in cards) and not bkg_only_cache.exists():
                shutil.copy2(produced, bkg_only_cache)
            print(f"[done] {point.key} -> {produced}")
        finally:
            if args.keep_workdirs:
                print(f"[keep] {workdir}")
            else:
                shutil.rmtree(workdir, ignore_errors=True)

    ctx.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
