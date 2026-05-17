#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Tuple

try:
    import ROOT  # type: ignore
except Exception as exc:
    raise RuntimeError("Run inside CMSSW with ROOT available.") from exc


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Prepare condor shards and submit files for pMSSM combine scans."
    )
    p.add_argument("--base-dir", default=".")
    p.add_argument("--analyses", nargs="+", required=True)
    p.add_argument("--pmssm-tree", default="rootfiles/TheNewestAndMostExcitingFullTree.root")
    p.add_argument("--pmssm-tree-name", default="mcmc")
    p.add_argument("--points-per-job", type=int, default=120)
    p.add_argument("--start-index", type=int, default=0)
    p.add_argument("--max-points", type=int)
    p.add_argument(
        "--output-dir",
        help="Final combine output directory. Defaults to combinerootsLLM/<combo>/Run2",
    )
    p.add_argument("--work-tag", help="Optional condor working tag. Defaults to combo name.")
    p.add_argument("--combine-binary", default="combine")
    p.add_argument("--request-cpus", type=int, default=1)
    p.add_argument("--request-memory", default="2GB")
    p.add_argument("--request-disk", default="2GB")
    p.add_argument("--job-flavour", default="tomorrow")
    return p.parse_args()


def load_points(
    tree_path: Path,
    tree_name: str,
    start_index: int,
    max_points: int | None,
) -> List[Tuple[int, int]]:
    tf = ROOT.TFile.Open(str(tree_path))
    if not tf or tf.IsZombie():
        raise OSError(f"Could not open {tree_path}")

    tree = tf.Get(tree_name)
    if tree is None:
        tf.Close()
        raise KeyError(f"No tree {tree_name} in {tree_path}")

    points: List[Tuple[int, int]] = []
    nentries = int(tree.GetEntries())
    stop = nentries if max_points is None else min(nentries, start_index + max_points)

    for i in range(start_index, stop):
        tree.GetEntry(i)
        points.append((int(tree.chain_index), int(tree.Niteration)))

    tf.Close()
    return points


def chunked(points: List[Tuple[int, int]], size: int) -> List[List[Tuple[int, int]]]:
    if size <= 0:
        raise ValueError(f"points-per-job must be positive, got {size}")
    return [points[i:i + size] for i in range(0, len(points), size)]


def main() -> int:
    args = parse_args()

    base_dir = Path(args.base_dir).resolve()
    combo = "__".join(args.analyses)
    work_tag = args.work_tag or combo

    condor_root = base_dir / "condorLLM" / work_tag
    shards_dir = condor_root / "shards"
    logs_dir = condor_root / "logs"
    scripts_dir = condor_root / "scripts"

    for d in (shards_dir, logs_dir, scripts_dir):
        d.mkdir(parents=True, exist_ok=True)

    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else (base_dir / "combinerootsLLM" / combo / "Run2")
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    points = load_points(
        base_dir / args.pmssm_tree,
        args.pmssm_tree_name,
        args.start_index,
        args.max_points,
    )
    if not points:
        raise RuntimeError("No points selected. Check --start-index / --max-points / input tree.")

    shards = chunked(points, args.points_per_job)

    for idx, shard in enumerate(shards):
        shard_path = shards_dir / f"points_{idx:05d}.txt"
        with shard_path.open("w") as handle:
            for chain_index, niteration in shard:
                handle.write(f"{chain_index} {niteration}\n")

    runner = scripts_dir / "run_one_shard.sh"
    runner.write_text(
        f"""#!/bin/bash
set -euo pipefail
BASE_DIR="{base_dir}"
source /cvmfs/cms.cern.ch/cmsset_default.sh
cd "$BASE_DIR/CMSSW_14_1_0_pre4/src"
eval "$(scramv1 runtime -sh)"
cd "$BASE_DIR"
python3 toolsLLM/run_pmssm_combination.py \\
  --base-dir "$BASE_DIR" \\
  --analyses {' '.join(args.analyses)} \\
  --points-file "$1" \\
  --output-dir "{output_dir}" \\
  --combine-binary "{args.combine_binary}"
"""
    )
    runner.chmod(0o755)

    submit = condor_root / "submit.sub"
    submit.write_text(
        f"""universe = vanilla
executable = {runner}
arguments = $(shard)
output = {logs_dir}/$(ClusterId).$(ProcId).out
error = {logs_dir}/$(ClusterId).$(ProcId).err
log = {logs_dir}/$(ClusterId).log
request_cpus = {args.request_cpus}
request_memory = {args.request_memory}
request_disk = {args.request_disk}
+RequestRuntime     = 86400
+JobFlavour = "{args.job_flavour}"
should_transfer_files = NO
queue shard matching files {shards_dir}/*.txt
"""
    )

    print(f"[prepared] {len(points)} points in {len(shards)} shards")
    print(f"[submit file] {submit}")
    print(f"[run wrapper] {runner}")
    print(f"[output dir] {output_dir}")
    print(f"[submit] condor_submit {submit}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())