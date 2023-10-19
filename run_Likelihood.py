import os,sys
import argparse
import datetime
from ROOT import *
from glob import glob


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i","--input",required=True,help="Specify the tree containing the points for which you want the likelihoods")
    parser.add_argument("-o","--outdir",help="Specify the output directory",required=True)
    parser.add_argument("-a","--analysis",choices=["cms_sus_19_006","atlas_susy_2018_32","atlas_susy_2018_06","cms_sus_21_006","cms_sus_18_004","cms_sus_21_007"],help="Specify the analysis for which the likelihoods should be calculated")
    parser.add_argument("-s","--split",help="choose into how many jobs to split the thing",default = 500,type=int)
    args=parser.parse_args()
    homedir = "/nfs/dust/cms/user/mrowietm/output_pMSSMscan_new/python/beautiful_scripts/CmsPmssm/"
    tempjobcont = open(homedir+"jobtemplate.job").read()
    tempshcont = open(homedir+"batch.sh").read()
    jobdir = homedir+"jobs/"
    timestamp = datetime.datetime.now()
    timestamp = timestamp.strftime("%m_%d_%H_%M_%S") 
    names = {}
    names["TIMESTAMP"] = timestamp
    names["JOBDIR"] = jobdir+timestamp+'/'
    os.system("mkdir "+names["JOBDIR"])
    names["PERCENT"] = '%'
    outpath = args.outdir
    if outpath[-1]!="/":
        outpath+="/"
    outdirfiles = glob(outpath+"*.root")
    infile = TFile(args.input)
    intree = infile.Get(args.analysis)
    ntot = intree.GetEntries()
    nrange = range(ntot)
    thesplit = ntot/args.split
    ranges = [nrange[i * thesplit:(i + 1) * thesplit] for i in range((ntot + thesplit - 1) // thesplit )]
    names["OUTDIR"] = outpath+timestamp
    names["INPUT"] = args.input
    names["ANALYSIS"] = args.analysis

    os.system("mkdir "+names["OUTDIR"])
#    ranges = ranges[:1]
    for rge in ranges:
        names["OUTFILENAME"]="friend_"+str(args.analysis)+"_"+"_".join([str(rge[0]),str(rge[-1])])+".root"
        if outpath+names["OUTFILENAME"] in outdirfiles:
            print "skipping "+ names["OUTFILENAME"]
            continue
        names["RANGE"] = " ".join([str(rge[0]),str(rge[-1])])
        script =  names["JOBDIR"]+"batch_"+str(args.analysis)+"_"+"_".join([str(rge[0]),str(rge[-1])])+".sh"
        names["SETENVNAME"]=script
        shcont = tempshcont % names
        job = names["JOBDIR"]+"job_"+str(args.analysis)+"_"+"_".join([str(rge[0]),str(rge[-1])])+".job"
        jobcont = tempjobcont % names
        open(script,'w').write(shcont)
        os.system('chmod +xX '+script)
        open(job,'w').write(jobcont)
        os.system('chmod +xX '+job)
        os.system("condor_submit "+job)

    

