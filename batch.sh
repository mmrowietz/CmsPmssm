#!/bin/zsh
source /afs/desy.de/user/m/mrowietm/.zshrc
source /etc/profile.d/modules.sh  
module use -a /afs/desy.de/group/cms/modulefiles/
module load cmssw
SCRAM_ARCH=slc7_amd64_gcc820
export SCRAM_ARCH
export timestamp=$(date +%(PERCENT)sS%(PERCENT)sN)
cd /nfs/dust/cms/user/mrowietm/make_scan/CMSSW_10_5_0/src
cmsenv
cd /tmp
mkdir $timestamp
cd $timestamp
echo python /nfs/dust/cms/user/mrowietm/output_pMSSMscan_new/python/beautiful_scripts/CmsPmssm/compute_likelihoods.py -i %(INPUT)s -o %(OUTDIR)s -a %(ANALYSIS)s -r %(RANGE)s -n %(OUTFILENAME)s
python /nfs/dust/cms/user/mrowietm/output_pMSSMscan_new/python/beautiful_scripts/CmsPmssm/compute_likelihoods.py -i %(INPUT)s -o %(OUTDIR)s -a %(ANALYSIS)s -r %(RANGE)s -n %(OUTFILENAME)s
cd /tmp
echo rm -rf $timestamp
rm -rf $timestamp
