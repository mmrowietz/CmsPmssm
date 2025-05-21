# CmsPmssm
Basic scripts for the CMS pMSSM Run 2 team - best would be to go ahead and fork the repo before cloning:


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

# For running Combine for the combination

## Step 0: Set up combine
If it's the first time, set up the Higgs combine tool just outside of the git repo
https://cms-analysis.github.io/HiggsAnalysis-CombinedLimit/latest/#combine-v10-recommended-version

Whether it's your first or future time, source the environment there.

Then, come back to the repo and go here:

```
cd CmsPmssm/Combination
```

The cards are organized in folders like:
```
>ls datacards/*/SUS_24_003/
datacards/rawprovided/SUS_24_003/:
Run2_card.txt  sus-24-003_TemplatePhase0.txt  sus-24-003_TemplatePhase1.txt  sus-24-003_TemplateRun2.txt
datacards/provided/SUS_24_003/:
datacards/derived/SUS_24_003/:
```
these three directories contain a template card directly provided by the analysis team, our processed versions of this card, and all cards populated with counts, respectively.


## Step 1: test run over raw Combine card
the raw combine card(s) are the ones provided by the analysis directly - you can run over them by doing something like:
```
combine --method MultiDimFit datacards/rawprovided/SUS_24_003/sus-24-003_TemplatePhase0.txt --verbose 1 --mass 125.0 --algo grid --redefineSignalPOIs r  --setParameterRanges r=-10.0,10.0 --gridPoints 21 --firstPoint 11 --lastPoint 11 --alignEdges 1 --saveNLL --cminDefaultMinimizerType Minuit2 --cminDefaultMinimizerStrategy 0  --cminDefaultMinimizerTolerance 0.1 --cminFallbackAlgo Minuit2,0:0.2 --cminFallbackAlgo Minuit2,0:0.4 --X-rtd REMOVE_CONSTANT_ZERO_POINT=1 --name ROOTOUT
```
this produces a ROOT file from which you can make sure you extract deltaNLL for mu=1. 

## Step 2: prepare template card

Prepare it for production by replacing the signal counts and uncertainties with replaceable keywords, save this file in datacards/provided/.

## Step 3: Set up script to create cards and run combine 

Prepare the script ```getSingleAnalysisLlhdCombine.py``` to run over the target analysis, modifying keywords, the input ROOT file with a tree provided by Yildiray derived from the THnSparse.

## Step 4: big production

condorize this, and extract the deltaNLLs, compute the BFs and Z significances for mu=0,0.5,1.0,1.5, save to tree. 
