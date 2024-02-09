from ROOT import *
import os, sys
from time import time
import numpy as np
from glob import glob
'''
cd ../../CMSSW_12_2_3/src/
cmsenv
cd -
nohup python3 tools/statsharvestor.py CMS_SUS_21_006 CMS_SUS_18_004 &
nohup python3 tools/statsharvestor.py CMS_SUS_21_006 &
nohup python3 tools/statsharvestor.py CMS_SUS_18_004  > harvestIt.txt &
python3 tools/statsharvestor.py CMS_SUS_18_004_CMS_SUS_21_006
'''

try: analyses = sys.argv[1:]
except: analyses = ['CMS_SUS_21_006','CMS_SUS_18_004']

#analyses = ['CMS_SUS_21_006','CMS_SUS_18_004']
#analyses = ['CMS_SUS_18_004']
#analyses = ['CMS_SUS_21_006']
#infile = TFile('tin/scan.root')

#infilename = 'rootfiles/full.root'
infilename = 'rootfiles/TheNewAndExcitingFullTree.root'
infilename = 'rootfiles/TheNewestAndMostExcitingFullTree.root'
twois1 = False
twois1 = True
if twois1: two = 1
else: two = 2

print('analyses', analyses)


for analysis in analyses:
    if len(analysis.split('_'))>4: bigcombo = True
    else: bigcombo = False
    print('gonna tackle analysis:', analysis)
    infile = TFile(infilename) #from /nfs/dust/cms/user/mrowietm/output_pMSSMscan_new/python/GetLikelihoodForpMSSM/results/full.root
    tin = infile.Get('mcmc')
    tin.Show(0)
    nentries = tin.GetEntries()
    #nentries = 1000
    outfilename = infilename.replace('.root','-'+analysis+'.root')
    if twois1: outfilename = outfilename.replace('.root','TwoIs1.root')
    outfile = TFile(outfilename,'recreate')
    tout = tin.CloneTree(0)

    #fname_bkgonly = glob('combineroots/'+analysis+'/Run2/*ertifiedBkgOnly.root')[0]
    lilanalysis = analysis.lower()
    llhdmu0p0 = np.zeros(1, dtype=float)
    tout.Branch('llhd_'+lilanalysis+'_mu0p0f', llhdmu0p0, 'llhd_'+lilanalysis+'_mu0p0f'+'/D')    
    Zsigmu0p5 = np.zeros(1, dtype=float)
    tout.Branch('Zsig_'+lilanalysis+'_mu0p5f', Zsigmu0p5, 'Zsig_'+lilanalysis+'_mu0p5f'+'/D')
    Zsigmu1p0 = np.zeros(1, dtype=float)
    tout.Branch('Zsig_'+lilanalysis+'_mu1p0f', Zsigmu1p0, 'Zsig_'+lilanalysis+'_mu1p0f'+'/D')
    Zsigmu1p5 = np.zeros(1, dtype=float)
    tout.Branch('Zsig_'+lilanalysis+'_mu1p5f', Zsigmu1p5, 'Zsig_'+lilanalysis+'_mu1p5f'+'/D')
    bfmu0p5 = np.zeros(1, dtype=float)
    tout.Branch('bf_'+lilanalysis+'_mu0p5f',   bfmu0p5,   'bf_'+lilanalysis  +'_mu0p5f'+'/D')
    bfmu1p0 = np.zeros(1, dtype=float)      
    tout.Branch('bf_'+lilanalysis+'_mu1p0f',   bfmu1p0,   'bf_'+lilanalysis  +'_mu1p0f'+'/D')
    bfmu1p5 = np.zeros(1, dtype=float)      
    tout.Branch('bf_'+lilanalysis+'_mu1p5f',   bfmu1p5,   'bf_'+lilanalysis  +'_mu1p5f'+'/D')
            
    print('gonna process', nentries)
    for ientry in range(nentries):
        tin.GetEntry(ientry)
        
        if not bigcombo:
            nprockinda = getattr(tin, 'Zsig_'+analysis.lower())
            if nprockinda==0: 
                filename = 'combineroots/'+analysis+'/Run2/certifiedBkgOnly.root'
                print('processing empty file', ientry, filename)
                for thing in [llhdmu0p0, Zsigmu0p5, Zsigmu1p0, Zsigmu1p5]: thing[0] = 0.0
                for thing in [bfmu0p5, bfmu1p0, bfmu1p5]: thing[0] = 1.0
                tout.Fill()
                continue
            else: filename = 'combineroots/'+analysis+'/Run2/higgsCombine_'+str(int(tin.chain_index))+'_'+str(int(tin.Niteration))+'.MultiDimFit.mH125.root'
        else: filename = 'combineroots/'+analysis+'/Run2/higgsCombine_'+str(int(tin.chain_index))+'_'+str(int(tin.Niteration))+'.MultiDimFit.mH125.root'
        print('really processing file', ientry, filename, getattr(tin, 'Zsig_'+analysis.lower()), 'BK', bigcombo)
        fpoint = TFile.Open(filename)
        tlimit = fpoint.Get('limit')
        tlimit.GetEntry(1)
        #tlimit.deltaNLL+tlimit.nll+tlimit.nll0
        llhdmu0p0[0] = -(two*tlimit.deltaNLL)
        
        #tlimit.GetEntry(6)
        tlimit.GetEntry(6)
        llhdmu0p5 = -(two*tlimit.deltaNLL)#nll
        lbfmu0p5 = llhdmu0p5    
        lbfmu0p5-=llhdmu0p0[0]
        bfmu0p5[0] = TMath.Exp(lbfmu0p5)
        Zsigmu0p5[0] = TMath.Sign(1,lbfmu0p5)* TMath.Sqrt(2*abs(lbfmu0p5))
        
        #tlimit.GetEntry(11)
        tlimit.GetEntry(11)
        llhdmu1p0 = -(two*tlimit.deltaNLL)#nll
        lbfmu1p0 = llhdmu1p0    
        lbfmu1p0-=llhdmu0p0[0]
        bfmu1p0[0] = TMath.Exp(lbfmu1p0)
        Zsigmu1p0[0] = TMath.Sign(1,lbfmu1p0)* TMath.Sqrt(2*abs(lbfmu1p0))
        
        #tlimit.GetEntry(16)
        tlimit.GetEntry(16)
        llhdmu1p5 = -(two*tlimit.deltaNLL)#nll
        lbfmu1p5 = llhdmu1p5    
        lbfmu1p5-=llhdmu0p0[0]
        bfmu1p5[0] = TMath.Exp(lbfmu1p5)
        Zsigmu1p5[0] = TMath.Sign(1,lbfmu1p5)* TMath.Sqrt(2*abs(lbfmu1p5))
            
        tout.Fill()
        fpoint.Close()
        
    
    outfile.cd()
    tout.Write()
    print('just created', outfile.GetName())
    outfile.Close()
    infilename = outfilename
    
print('done')
