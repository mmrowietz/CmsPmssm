# CmsPmssm
Basic scripts for the CMS pMSSM Run 2 team


```
export SCRAM_ARCH=slc7_amd64_gcc900
git clone https://github.com/mmrowietz/CmsPmssm
cmsrel CMSSW_12_2_4
cd CMSSW_12_2_4/src/
cmsenv
cd ../../CmsPmssm
python3 plotmaker.py -i /eos/cms/store/group/phys_susy/pMSSMScan/MasterTrees/pmssmtree_11aug2023.root -o plots
##(or at DESY point to /nfs/dust/cms/user/mrowietm/output_pMSSMscan_new/python/GetLikelihoodForpMSSM/results/full.root)
```
