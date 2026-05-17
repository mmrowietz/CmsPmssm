#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
from array import array
from pathlib import Path

try:
    import ROOT  # type: ignore
except Exception as exc:
    raise RuntimeError("Run inside CMSSW with ROOT available.") from exc


TARGET_RS = (0.0, 0.5, 1.0, 1.5)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Harvest combine MultiDimFit outputs back into a cloned pMSSM ROOT tree."
    )
    p.add_argument("--base-dir", default=".")
    p.add_argument("--pmssm-tree", default="rootfiles/TheNewestAndMostExcitingFullTree.root")
    p.add_argument("--pmssm-tree-name", default="mcmc")
    p.add_argument("--combine-dir", required=True,
                   help="Directory containing higgsCombine_<chain>_<iter>.MultiDimFit.mH125.root files")
    p.add_argument("--output", required=True,
                   help="Output ROOT file with cloned tree and harvested branches")
    p.add_argument("--tag", required=True,
                   help="Branch tag, e.g. sus_18_004__sus_20_001__sus_21_006__sus_24_003")
    p.add_argument("--tree-out-name", default=None)
    p.add_argument("--missing", choices=["nan", "zero"], default="nan")
    p.add_argument("--status-branch", action="store_true",
                   help="Add integer status branch: 1 found, 0 missing, -1 unreadable")
    p.add_argument("--start-index", type=int, default=0)
    p.add_argument("--max-points", type=int, default=None)
    return p.parse_args()


def sanitize(tag: str) -> str:
    tag = tag.strip().lower()
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in tag)


def signed_z(delta_llhd: float) -> float:
    if not math.isfinite(delta_llhd):
        return float("nan")
    if delta_llhd == 0.0:
        return 0.0
    return math.copysign(math.sqrt(2.0 * abs(delta_llhd)), delta_llhd)


def read_limit_values(root_path: Path, tol: float = 5e-2):
    tf = ROOT.TFile.Open(str(root_path))
    if not tf or tf.IsZombie():
        raise OSError(f"Could not open combine output: {root_path}")

    tlimit = tf.Get("limit")
    if tlimit is None:
        tf.Close()
        raise KeyError(f"No 'limit' tree in {root_path}")

    best = {}
    for target in TARGET_RS:
        best[target] = {"dist": float("inf"), "deltaNLL": None, "entry": -1, "r": None}

    nentries = int(tlimit.GetEntries())
    for i in range(nentries):
        tlimit.GetEntry(i)
        try:
            r_val = float(tlimit.r)
            dnll = float(tlimit.deltaNLL)
        except Exception:
            continue

        if not math.isfinite(r_val) or not math.isfinite(dnll):
            continue

        for target in TARGET_RS:
            dist = abs(r_val - target)
            if dist < best[target]["dist"]:
                best[target] = {
                    "dist": dist,
                    "deltaNLL": dnll,
                    "entry": i,
                    "r": r_val,
                }

    tf.Close()

    # Require that we actually found nearby grid points
    for target in TARGET_RS:
        if best[target]["deltaNLL"] is None:
            raise RuntimeError(f"Could not find any limit entry near r={target} in {root_path}")
        if best[target]["dist"] > tol:
            raise RuntimeError(
                f"Nearest entry to r={target} in {root_path} is too far away: "
                f"r={best[target]['r']} (dist={best[target]['dist']})"
            )

    llhd_mu0p0 = -2.0 * float(best[0.0]["deltaNLL"])
    llhd_mu0p5 = -2.0 * float(best[0.5]["deltaNLL"])
    llhd_mu1p0 = -2.0 * float(best[1.0]["deltaNLL"])
    llhd_mu1p5 = -2.0 * float(best[1.5]["deltaNLL"])

    d05 = llhd_mu0p5 - llhd_mu0p0
    d10 = llhd_mu1p0 - llhd_mu0p0
    d15 = llhd_mu1p5 - llhd_mu0p0

    bf05 = math.exp(d05)
    bf10 = math.exp(d10)
    bf15 = math.exp(d15)

    z05 = signed_z(d05)
    z10 = signed_z(d10)
    z15 = signed_z(d15)

    return {
        "llhd_mu0p0": llhd_mu0p0,
        "llhd_mu0p5": llhd_mu0p5,
        "llhd_mu1p0": llhd_mu1p0,
        "llhd_mu1p5": llhd_mu1p5,
        "bf_mu0p5": bf05,
        "bf_mu1p0": bf10,
        "bf_mu1p5": bf15,
        "zsig_mu0p5": z05,
        "zsig_mu1p0": z10,
        "zsig_mu1p5": z15,
    }


def main() -> int:
    args = parse_args()
    base_dir = Path(args.base_dir).resolve()
    input_path = (base_dir / args.pmssm_tree).resolve()
    combine_dir = Path(args.combine_dir).resolve()
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tf_in = ROOT.TFile.Open(str(input_path))
    if not tf_in or tf_in.IsZombie():
        raise OSError(f"Could not open input tree file: {input_path}")

    tin = tf_in.Get(args.pmssm_tree_name)
    if tin is None:
        tf_in.Close()
        raise KeyError(f"No tree {args.pmssm_tree_name} in {input_path}")

    nentries = int(tin.GetEntries())
    start = max(0, int(args.start_index))
    stop = nentries if args.max_points is None else min(nentries, start + int(args.max_points))

    tf_out = ROOT.TFile(str(output_path), "RECREATE")
    tout_name = args.tree_out_name or args.pmssm_tree_name
    tout = tin.CloneTree(0)
    tout.SetName(tout_name)

    tag = sanitize(args.tag)
    doubles = {
        f"llhd_{tag}_mu0p0f": array("d", [0.0]),
        f"llhd_{tag}_mu0p5f": array("d", [0.0]),
        f"llhd_{tag}_mu1p0f": array("d", [0.0]),
        f"llhd_{tag}_mu1p5f": array("d", [0.0]),
        f"bf_{tag}_mu0p5f": array("d", [0.0]),
        f"bf_{tag}_mu1p0f": array("d", [0.0]),
        f"bf_{tag}_mu1p5f": array("d", [0.0]),
        f"Zsig_{tag}_mu0p5f": array("d", [0.0]),
        f"Zsig_{tag}_mu1p0f": array("d", [0.0]),
        f"Zsig_{tag}_mu1p5f": array("d", [0.0]),
    }
    for name, buf in doubles.items():
        tout.Branch(name, buf, f"{name}/D")

    status_buf = None
    if args.status_branch:
        status_buf = array("i", [0])
        tout.Branch(f"combine_status_{tag}", status_buf, f"combine_status_{tag}/I")

    for i in range(start, stop):
        tin.GetEntry(i)
        if i % 10000 == 0:
            print("now processing pMSSM entry", i)

        chain = int(tin.chain_index)
        niter = int(tin.Niteration)
        root_path = combine_dir / f"higgsCombine_{chain}_{niter}.MultiDimFit.mH125.root"

        if not root_path.exists():
            fill = 0.0 if args.missing == "zero" else float("nan")
            for buf in doubles.values():
                buf[0] = fill
            if status_buf is not None:
                status_buf[0] = 0
            tout.Fill()
            continue

        try:
            hv = read_limit_values(root_path)
            doubles[f"llhd_{tag}_mu0p0f"][0] = hv["llhd_mu0p0"]
            doubles[f"llhd_{tag}_mu0p5f"][0] = hv["llhd_mu0p5"]
            doubles[f"llhd_{tag}_mu1p0f"][0] = hv["llhd_mu1p0"]
            doubles[f"llhd_{tag}_mu1p5f"][0] = hv["llhd_mu1p5"]
            doubles[f"bf_{tag}_mu0p5f"][0] = hv["bf_mu0p5"]
            doubles[f"bf_{tag}_mu1p0f"][0] = hv["bf_mu1p0"]
            doubles[f"bf_{tag}_mu1p5f"][0] = hv["bf_mu1p5"]
            doubles[f"Zsig_{tag}_mu0p5f"][0] = hv["zsig_mu0p5"]
            doubles[f"Zsig_{tag}_mu1p0f"][0] = hv["zsig_mu1p0"]
            doubles[f"Zsig_{tag}_mu1p5f"][0] = hv["zsig_mu1p5"]
            if status_buf is not None:
                status_buf[0] = 1
        except Exception as exc:
            print(f"[warn] failed to read {root_path}: {exc}")
            fill = 0.0 if args.missing == "zero" else float("nan")
            for buf in doubles.values():
                buf[0] = fill
            if status_buf is not None:
                status_buf[0] = -1

        tout.Fill()

    tf_out.cd()
    tout.Write()
    tf_out.Close()
    tf_in.Close()

    print(f"[wrote] {output_path}")
    print(f"[tag] {tag}")
    print(f"[combine dir] {combine_dir}")
    print(f"[range] start={start} stop={stop}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())