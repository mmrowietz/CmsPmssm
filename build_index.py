from ROOT import *
import argparse


def run(args):
    infile = TFile(args.infile)
    intree = infile.Get(args.treename)
    outfile = TFile(args.infile.replace(".root","_indexed.root"),"recreate")
    outtree = intree.CloneTree(-1)
    outtree.BuildIndex("chain_index","Niteration")
    outtree.Write()
    outfile.Close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i","--infile",help="Specify the input file path.",required = True)
    parser.add_argument("-t","--treename",help="Specify the tree name in the input file.",required = True)
    args=parser.parse_args()

    #

    run(args)
