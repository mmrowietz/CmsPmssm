from ROOT import *
import os, sys

'''
cd /nfs/dust/cms/user/beinsam/pMSSM13TeV/Scan2/Combination/CMSSW_10_2_13/src
python tools/getSingleAnalysisLhdCombine.py

text2workspace.py  datacards/derived/CMS_SUS_21_006/220903/card_594_45955.txt --out testCard_workspace.root --mass 125.0
combine --method MultiDimFit WORKSPACE --verbose 1 --mass 125.0 --algo grid --redefineSignalPOIs r --setParameterRanges r=-10.0,10.0: --gridPoints 21 --firstPoint 11 --lastPoint 11 --alignEdges 1 --saveNLL --cminDefaultMinimizerType Minuit2 --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 --cminFallbackAlgo Minuit2,0:0.2 --cminFallbackAlgo Minuit2,0:0.4 --X-rtd REMOVE_CONSTANT_ZERO_POINT=1

'''

analysis = 'CMS_SUS_21_006'

card_template = open('datacards/provided/'+analysis+'/template_card.txt').read()
countstreefile = 'THnSparses/CMS_SUS_21_006/cms_sus_21_006.root'#probably the thing you want to clone with new branch
countstree = 'Counts'#probably the thing you want to clone with new branch
carddir = 'datacards/derived/'+analysis+'/'
os.system('mkdir -p '+carddir)

cmd_template1 = 'text2workspace.py  INPUT --out testCard_workspace.root --mass 125.0'
cmd_template2 = 'combine --method MultiDimFit testCard_workspace.root --verbose 1 --mass 125.0 --algo grid --redefineSignalPOIs r --setParameterRanges r=-10.0,10.0: --gridPoints 21 --firstPoint 11 --lastPoint 11 --alignEdges 1 --saveNLL --cminDefaultMinimizerType Minuit2 --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 --cminFallbackAlgo Minuit2,0:0.2 --cminFallbackAlgo Minuit2,0:0.4 --X-rtd REMOVE_CONSTANT_ZERO_POINT=1  --name ROOTOUT'

fcountstree = TFile(countstreefile)#probably the thing you want to clone with new branch
tcounts = fcountstree.Get(countstree)#probably the thing you want to clone with new branch

tcounts.Show(0)
branchnames = []
for branch in tcounts.GetListOfBranches():
    branchnames.append(branch.GetName())
    
for ientry in range(tcounts.GetEntries()):
    print ('processing', ientry)
    tcounts.GetEntry(ientry)
    chain_index, Niteration = str(tcounts.chain_index), str(tcounts.Niteration)
    newcardfilename = carddir+'/card_%s_%s.txt'%(chain_index, Niteration)
    print('creating', newcardfilename)
    newcard = open(newcardfilename,'w')
    cardtext = card_template
    for branchname in branchnames: 
        if not analysis in branchname: continue
        thing1 = branchname.replace(analysis,'')+' '
        if len(thing1)==6: thing2 = ' %-4s'%str(round(getattr(tcounts, branchname),2))+' '
        else: thing2 = ' %-5s'%str(round(getattr(tcounts, branchname),2))+' '
        cardtext = cardtext.replace(thing1,thing2)
    newcard.write(cardtext)
    newcard.close()
    cmd1 = cmd_template1.replace('INPUT','datacards/derived/'+analysis+'/'+date+'/card_'+str(chain_index)+'_'+Niteration+'.txt')
    os.system(cmd1)
    combinerootout = '_'+str(chain_index)+'_'+Niteration
    cmd2 = cmd_template2.replace('WORKSPACE','datacards/derived/'+analysis+'/'+date+'/workspace_'+str(chain_index)+'_'+Niteration+'.root').replace('ROOTOUT',combinerootout)
    print ('doing command')
    print(cmd2)
    os.system(cmd2)
    '''
    fcombine = TFile('higgsCombine'+combinerootout+'.MultiDimFit.mH125.root')
    limit = fcombine.Get('limit')
    limit.GetEntry(1)
    t = 2*limit.deltaNLL
    fcombine.Close()    
    L = TMath.Exp(-t/2)/TMath.Sqrt(TMath.Pi()*t)
    print(chain_index, Niteration, t, L)
    '''
    if ientry>5: exit(0)
   



