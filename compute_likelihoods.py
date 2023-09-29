import argparse
import os,sys
from ROOT import *
import importlib
#from utils import *
from tqdm import tqdm
import numpy as np
import math
"""
The purpose of this script is to calculate simplified likelihoods from a root tree containing the signal counts in each signal region, as well as derived quantities like the Bayes factor and Z significance. It also needs a file defining the output branches, by default called "output_branches_likelihood.py", as well as a file containing the signal region observed counts, background predictions and uncertainties.
"""
def setup_tree(outtree,_output_branches):
    """
    Creates the output branches in the output tree
    @param outtree: Output tree in which to create the branches
    @param _output_branches: dictionary from which to create the tree branches. Each dictionary value corresponds to an output branch and is itself a dictionary with the following entries:
    "name": name of the output branch
    "container": numpy container created using np.zeros(1,dtype=datatype), where datatype corresponds to the desired datatype of the output branch. For example, use np.zeros(1,dtype=float) for branches containing floating point values
    "dtype": datatype of the output branch ('D' for float, 'I' for int, ...)
    The dictionary can optionally contain entries for 2017 and 2018 seperately.
    """

    #now for the function that sets up the tree
    #first parameter of TTree.Branch() is the name of the branch in the output, second parameter is the variable that is queried for the value to fill the tree with, each time tree.Fill() is called. The third parameter is used here to tell root to convert the value of the container to "dtype". See dictionary above.
    for key,outbranch in _output_branches.items():
        outtree.Branch(outbranch["name"],outbranch["container"],outbranch["name"]+"/"+outbranch["dtype"])


def reset_containers(_output_branches):
    """
    Resets all the branch containers in @param _output_branches to a default value (0 by default)
    @param _output_branches: dictionary for the output branches. Assumes same format as in function setup_tree()
    """

    #for safety, reset all containers to zero after each time tree.Fill() is called
    for outbranch in _output_branches.values():
        for key,value in outbranch.items():
            if "container" in key:
                value[0] = 0

def get_signal_strength(branchnamestring):
    """
    Parses a branch name for its designated signal strength modifier, assuming a format "_muXpYs" or "_muXpYf", where XpY -> mu=X.Y. Returns False if no signal strength can be identified in the branch name.
    @param branchnamestring: string of the branchname to parse for the signal strength modifier.
    """
    #the signal strength string should have the format "_muXpYs" or "_muXpYf", where XpY -> mu=X.Y
    if not "_mu" in branchnamestring:
        return False
    stringelems = branchnamestring.split("_")
    for elem in stringelems:
        if "mu" in elem:
            return float(elem[elem.find("mu")+len("mu"):-1].replace("p","."))#The signal strength string should always have "s" (simplified) or "f" (full) at the end.
    return False
def get_sr_from_branchname(branchname):
    """
    Helper function specifically for this analysis implementation. Parses a branchname for the signal region bin it corresponds to
    @param branchname: string of the branchname to parse for its signal region bin
    """
    #Example: cms_sus_19_006_sr_174_2017 -> SR174
    return "".join(branchname.split("_")[-3:-1]).upper()
def run(args):
    homedir = "/nfs/dust/cms/user/mrowietm/output_pMSSMscan_new/python/beautiful_scripts/CmsPmssm/"
    outdir = args.outdir
    if outdir[-1]!="/":
        outdir+="/"
    if not os.path.exists(outdir):
        os.system("mkdir -p "+outdir)
    infile = TFile(args.infile)
    intree = infile.Get(str(args.analysis))
    outfile = TFile(outdir+args.outname,"recreate")
    outtree = intree.CloneTree(0) # Clone the tree structure from the input tree, but do not copy over entries

    gROOT.ProcessLine(".L "+homedir+"calcLlhdSingleCount.C+") # this contains a c++ function that calculates the simplified likelihood 
    sys.path.append(homedir)

    """
    Import the output tree structure and the signal region counts and background predictions and uncertainties
    output_branches_likelihood.py : file containing a dictionary "output_branches_likelihood" that maps the THnSparse SR bins to the tree branch names in the output for ALL years, as well as a branch for the two pMSSM point indices, and one branch for the processed event totals in EACH year.
    SR_counts.py : containing a dictionary "SR_counts" that provides the observed counts "nobs", the background counts "nb", and the background uncertainty "deltanb" for EACH signal region
    
    By default, these files are assumed to be in a directory corresponding to the analysis (e.g. cms_sus_19_006) downstream from homedir
    """

    outbranches = importlib.import_module(".".join([args.analysis,"output_branches_likelihood"]))
    output_branches = outbranches.output_branches_likelihood
    setup_tree(outtree,output_branches)    
    SRcounts = importlib.import_module(".".join([args.analysis,"SR_counts"]))
    SR_counts = SRcounts.counts
    srdict = SR_counts[args.analysis]
    
    likelihoods = {}#dictionary collecting the likelihoods, Bayes factors, and Z significances for each signal strength modifier   
    for branchname, branchdict in output_branches.items():
        if "name" in branchdict.keys():
            sstrength = get_signal_strength(branchdict["name"]) #this returns the signal strength modifier if the branch specifies one ("_muXpYs") or False if the branch does not specify one
        elif type(branchname)==str:
            sstrength = get_signal_strength(branchname)
        else:
            sstrength=False
        if sstrength and sstrength not in likelihoods:
            likelihoods[sstrength] = {"llhd":0,"BayesFactor":1,"Zsig":0}
        elif sstrength == 0 and type(sstrength)==float:
            likelihoods[sstrength] = {"llhd":0}
    #the part below is to run over sub-sets of the input tree, to make it run in parallel batches
    runrange = args.range
    if runrange[0] == -1:
        run_over = range(nEntries)
    else:
        run_over = range(max(0,runrange[0]-1),runrange[1])

    do_once = True #only need to calculate the SM likelihoods once
    llhd_sm = 0
    for iEntry in tqdm(run_over):
        intree.GetEntry(iEntry)
        reset_containers(output_branches)
        for sstrength in likelihoods:
            likelihoods[sstrength]["llhd"] = 0
            if sstrength>0:
                likelihoods[sstrength]["BayesFactor"] = 1
                likelihoods[sstrength]["Zsig"] = 0

        nev_2017 = getattr(intree,args.analysis+"_nTotal_2017")
        nev_2018 = getattr(intree,args.analysis+"_nTotal_2018")
        nev_tot = nev_2017+nev_2018
        if nev_2017>0 and nev_2018>0:
            weight17 = ((intree.xsec_pb*41486.*intree.filtereff)/nev_2017)
            weight18 = ((intree.xsec_pb*59546.*intree.filtereff)/nev_2018)
            weight = 136847./(41486.+59546.)
        elif nev_tot>0:
            weight17 = False
            weight18 = False
            weight = ((intree.xsec_pb*137000.*intree.filtereff)/nev_tot)
        if nev_tot<=0:
            for bname, branchdict in output_branches.items():
                if "llhd" in bname:
                    branchdict["container"][0] = llhd_sm
                elif "bf_" in bname:
                    branchdict["container"][0] = 1
                elif "Zsig_" in bname:
                    branchdict["container"][0] = 0
    
        else:
            #calculate the simplified likelihood
            for sr in intree.GetListOfBranches():
                if sr.GetName() in ["Niteration","chain_index","xsec_pb","filtereff"]:continue
                if "nTotal" in sr.GetName():continue
                if "_2018" in sr.GetName():continue #each signal region should only be encountered once, not once for each year
                sr17 = "_".join(sr.GetName().split("_")[:-1])+"_2017"
                sr18 = "_".join(sr.GetName().split("_")[:-1])+"_2018"
                if nev_2017>0 and nev_2018>0:
                    s17 = weight17*getattr(intree,sr17)
                    s18 = weight18*getattr(intree,sr18)
                    s = weight*(s17+s18)#in this case, the weight simply scales up the 2017+2018 signals to also cover 2016
                elif nev_2017>0:
                    s = weight*getattr(intree,sr17)
                elif nev_2018>0:
                    s = weight*getattr(intree,sr18)
                srbin = get_sr_from_branchname(sr.GetName())
                obs = srdict[srbin]["nobs"]
                b =srdict[srbin]["nb"]
                db =srdict[srbin]["deltanb"]
                if obs==0 and b==0 and db==0:
                    print("no counts in SR, skipping SR!")
                    continue
                for sstrength in likelihoods:
                    llhd = max(-1E10,llhdAna(obs,max(0,sstrength*s),b,db))
                    likelihoods[sstrength]["llhd"] += llhd
                if do_once:#only do this for first point
                    L0 = llhdAna(obs,0,b,db)
                    if L0 < -1e10:
                        L0=-1e10
                    llhd_sm+=L0
            do_once = False
            #calculate the Bayes factor and Z-significance
            for sstrength in likelihoods:
                if sstrength == 0:continue
                likelihoods[sstrength]["BayesFactor"] = math.exp(likelihoods[sstrength]["llhd"]-llhd_sm)
                if likelihoods[sstrength]["BayesFactor"]==1:
                    likelihoods[sstrength]["Zsig"] = 0
                else:
                    likelihoods[sstrength]["Zsig"] = (likelihoods[sstrength]["llhd"]-llhd_sm)/abs(likelihoods[sstrength]["llhd"]-llhd_sm)*math.sqrt(2*abs(likelihoods[sstrength]["llhd"]-llhd_sm))
                #fill the output branch containers. Set empty signal regions to 0
            for bname, branchdict in output_branches.items():
                if "name" in branchdict.keys():
                    sstrength = get_signal_strength(branchdict["name"]) #this returns the signal strength modifier if the branch specifies one ("_muXpYs") or False if the branch does not specify one
                elif type(sstrength) == str:
                    sstrength = get_signal_strength(bname)
                else:
                    sstrength=False
                if sstrength>0:
                    if "llhd" in branchdict["name"]:
                        branchdict["container"][0] = likelihoods[sstrength]["llhd"]
                    elif "bf" in branchdict["name"]:

                        branchdict["container"][0] = likelihoods[sstrength]["BayesFactor"]
                    elif "Zsig" in branchdict["name"]:
                        branchdict["container"][0] = likelihoods[sstrength]["Zsig"]
                if type(sstrength) == float and sstrength == 0:
                    branchdict["container"][0] = likelihoods[sstrength]["llhd"]
        outtree.Fill()
    outtree.BuildIndex("chain_index","Niteration")# index the tree. The tree index can be used to find individual points in the output tree later, by calling tree.GetEntryWithIndex()
    outtree.Write()
    outfile.Close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i","--infile",help="Specify the input tree from which to calculate the likelihoods",required=True)
    parser.add_argument("-r","--range",help="choose over which range of tree entries to run over.Format = (start,stop). default=all",default=[-1],nargs="+",type=int)
    parser.add_argument("-o","--outdir",help="Specify the output directory",required=True)
    parser.add_argument("-a","--analysis",choices=["cms_sus_19_006"],help="Specify the analysis. A corresponding directory needs to exist from the homepath, which includes the files: __init__.py, output_branches.py, SR_counts.py, ThnSparse_inputs.py",required = True)
    parser.add_argument("-n","--outname",help="give a name for the output file",default = "")
    args=parser.parse_args()

    #

    run(args)
