from ROOT import *
import os,sys
from tqdm import tqdm
import argparse


def check_parallel(_baseTree,_friendTree):
    #first discover if trees are not parallel
    parallel = True
    for iEntry in tqdm(range(_baseTree.GetEntries())):
        _baseTree.GetEntry(iEntry)
        id1_base = _baseTree.chain_index
        id2_base = _baseTree.Niteration
        _friendTree.GetEntry(iEntry)
        id1_friend = _friendTree.chain_index
        id2_friend = _friendTree.Niteration
        if (id1_base,id2_base) != (id1_friend,id2_friend):
            parallel=False
            break
    return parallel
def run(args):
    outdir = args.outdir
    if outdir[-1]!="/":
        outdir+="/"
    if not os.path.exists(outdir):
        os.system("mkdir -p "+outdir)
    
    baseFile = TFile(args.infile1)
    baseTree = baseFile.Get(args.treename1)
    friendFile = TFile(args.infile2)
    friendTree = friendFile.Get(args.treename2)
    if not check_parallel(baseTree,friendTree):
        print("Trees are not parallel, creating parallelized copy of friend tree.")
        outFile = TFile(outdir+args.outname,"recreate")
        outTree = friendTree.CloneTree(0)
        for iEntry in tqdm(range(baseTree.GetEntries())):
            baseTree.GetEntry(iEntry)
            id1_base = int(baseTree.chain_index)
            id2_base = int(baseTree.Niteration)
            friendTree.GetEntryWithIndex(id1_base,id2_base)
            outTree.Fill()
        outTree.BuildIndex("chain_index","Niteration")
        outTree.Write()
        outFile.Close()
    else:
        print("Trees are parallel, exiting.")
            
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i1","--infile1",help="Specify the full pMSSM tree to which the friend tree should be parallel.",required = True)
    parser.add_argument("-i2","--infile2",help="Specify the friend tree that should be parallel to the full pMSSM tree.",required = True)
    parser.add_argument("-o","--outdir",help="Specify the output directory",required=True)
    parser.add_argument("-t1","--treename1",help="Specify the tree name in infile1",required = True)
    parser.add_argument("-t2","--treename2",help="Specify the tree name in infile2",required = True)
    parser.add_argument("-n","--outname",help="give a name for the output file",required = True)
    args=parser.parse_args()

    #

    run(args)

    
    
