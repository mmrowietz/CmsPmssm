from ROOT import *
import os, sys
from time import time

#This script is really only good for running combinations of things - otherwise it's very confusing

'''
nohup python tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/Run2 & sleep 1
nohup python tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004_CMS_SUS_21_006/Run2 & sleep 1


cd ../../CMSSW_12_2_3/src/
cmsenv
cd -
nohup python3 tools/combineCardsAndStuff.py > ccsSos.txt &

#notes from Philip:
#saveFitResult, saveWorkspace  -->snapshotMultiDimFit, combineHarvestor ->counts and shapes
#then, maybe there's something to dropping:
#--X-rtd REMOVE_CONSTANT_ZERO_POINT=1

#messed up baselines:
root [15] mcmc->Scan("Niteration:chain_index","llhdcms_sus_18_004_mu0p0f>10")
************************************
*    Row   * Niteratio * chain_ind *
************************************
*     4131 *    112581 *        48 *
*     8832 *    122391 *       440 *
*    15788 *     76975 *       202 *
*    55049 *     68871 *        15 *
*    55645 *     49233 *       451 *
*    87931 *     74181 *       414 *
*   113198 *     14183 *       217 *
*   124708 *     10384 *       142 *
*   128097 *     21822 *       499 *
*   148580 *     98838 *       201 *
*   166876 *    135377 *        81 *
*   169524 *     33806 *       385 *
*   182435 *     93420 *       483 *
*   183779 *      7284 *        34 *
*   184035 *     19883 *        34 *
*   188941 *     54008 *        77 *
*   192658 *     87920 *       590 *
*   200309 *     25367 *       523 *
*   219471 *     77550 *       534 *
*   255318 *     98209 *       506 *
*   279243 *     71749 *       160 *
*   292618 *     60056 *       467 *
*   303118 *     87940 *       573 *
*   312708 *     59571 *       156 *
*   321111 *     61270 *       218 *
*   323965 *     75381 *       307 *
*   333481 *    116840 *       262 *
*   348172 *     48758 *        17 *
*   400422 *    109410 *       171 *
*   430116 *    101099 *       316 *
*   433891 *     24613 *       535 *
*   442298 *    122103 *       256 *
*   450330 *     71306 *       361 *
*   457263 *     32198 *       338 *
*   471365 *     81369 *       162 *
*   491160 *     19920 *       447 *
************************************
'''

istest = False
useBatch = True 
doSmallNumber = False
runCombine = True

#cmd_template1 = 'text2workspace.py  INPUT --out OUTPUT --mass 125.0\n'
cmd_template2 = '''attempts=0
while [ $attempts -lt $max_attempts ]; do
    # Attempt the command
    combine --method MultiDimFit INPUT --mass 125.0 --algo grid --redefineSignalPOIs r --setParameterRanges r=0.0,1.5 --points 16 --alignEdges 1 --saveNLL --cminDefaultMinimizerType Minuit2 --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 --cminFallbackAlgo Minuit2,0:0.2 --name ROOTOUT > /dev/null 2>&1
    # Check the exit status
    if [ $(root -l -b -q -e "TFile* file = TFile::Open(\\"COMBOUT\\"); TTree* tree = (TTree*)file->Get(\\"limit\\"); float nentries = tree->GetEntries(); std::cout << nentries << std::endl;")>0 ]; then 
        # Success
        break
    else
        attempts=$((attempts+1))
        echo "Command failed. Attempt $attempts of $max_attempts."
        sleep 5
    fi
done
'''

analyses2combine = ['CMS_SUS_18_004','CMS_SUS_21_006']
#analyses2combine = ['CMS_SUS_21_006']#I don't think this one works!
analyses2combine = ['CMS_SUS_18_004']
channels = {}
channels['CMS_SUS_18_004'] = ['sos_2los_sr_high','sos_2los_sr_med','sos_2los_sr_ultra','sos_2los_sr_low' ,'sos_3l_sr_low','sos_3l_sr_med']
channels['CMS_SUS_21_006'] = ['']#no specific channel
eras = {}
eras['CMS_SUS_18_004'] = ['2016','2017','2018']
eras['CMS_SUS_21_006'] = ['Run2']

cwd = os.getcwd()
shtemplate = '''#!/bin/zsh
source /etc/profile.d/modules.sh
source /afs/desy.de/user/b/beinsam/.bash_profile
module use -a /afs/desy.de/group/cms/modulefiles/
module load cmssw
echo "$QUEUE $JOB $HOST"
source /afs/desy.de/user/b/beinsam/.bash_profile
cd CWD
cmsenv
export timestamp=$(date +%Y%m%d_%H%M%S%N)
echo will use folder $timestamp
cd jobsubmit/
mkdir $timestamp
cd $timestamp
max_attempts=5
'''

#tpmssmfile = TFile('rootfiles/full.root')
tpmssmfile = TFile('rootfiles/TheNewestAndMostExcitingFullTree.root')#TheNewAndExcitingFullTree.root')
tpmssm = tpmssmfile.Get('mcmc')
nentries = tpmssm.GetEntries()
print ('going to process', nentries)

cmdlist = []
t0 = time()
commandsPerJob = 1
outdir = 'datacards/derived/'+'_'.join(analyses2combine)+'/Run2'
if not os.path.exists(outdir): os.system('mkdir -p '+outdir)
combineoutdir = outdir.replace('datacards/derived','combineroots')
os.system('mkdir -p '+combineoutdir)

icom = 0
ijob = 0

go = True # to start at a given model, set to False
for ientry in range(nentries):  
    tpmssm.GetEntry(ientry)  
    chain_index, Niteration = str(int(tpmssm.chain_index)), str(int(tpmssm.Niteration))
    keypiece = '_%s_%s'%(chain_index, Niteration)
    if '364_8348' in keypiece: 
        go=True
    if not go:
        continue
    newfname = '%s/%s/card%s.txt' % (cwd,outdir,keypiece)
    if runCombine:
       predname = cwd+'/%s/higgsCombine_%s_%s.MultiDimFit.mH125.root' % (combineoutdir,chain_index,Niteration)
       if os.path.exists(predname):
           print ('already got', predname)
           continue 
    else:
       if os.path.exists(newfname):
           print ('already got', newfname)
           continue                   
    cmdlist.append('combineCards.py ')
    for analysis in analyses2combine:
        for era in eras[analysis]:
            for channel in channels[analysis]:
                cardname = '%s/datacards/derived/%s/%s/%s/card_%s_%s.txt' % (cwd,analysis,era,channel,chain_index, Niteration)
                if os.path.exists(cardname): 
                    cmdlist.append(cardname)
                if cardname==newfname:
                    print('it really doesnt seem like youre wanting to combine different channels here')
                    exit(0)
    cmdlist.append('> %s\n' % newfname)
    if runCombine:
        combout = 'higgsCombine%s.MultiDimFit.mH125.root' % keypiece
        #cmdlist.append(cmd_template1.replace('INPUT',newfname).replace('OUTPUT','werkstatt%s_%s.root'%(chain_index, Niteration)))
        cmdlist.append(cmd_template2.replace('INPUT',newfname).replace('ROOTOUT',keypiece).replace('COMBOUT',combout))
        cmdlist.append('mv %s %s/%s && ' % (combout, cwd,combineoutdir)+'echo nice work\n')
    if useBatch:
        if icom%commandsPerJob==0:
            t1 = time()
            print('d_time: ', t1-t0, t1, t0)
            t0 = t1                        
            os.chdir('jobsubmit/')
            jobfile = open('_'.join(newfname.split('/')[-2:]).replace('.txt','_.sh').replace('.sh','_'.join(analyses2combine))+'.sh','w')
        if icom%commandsPerJob==commandsPerJob-1:
            cmd = ' '.join(cmdlist)
            cmdlist = []
            jobfile.write(shtemplate.replace('CWD',cwd))
            jobfile.write(cmd+'\n')
            ccommand = 'condor_qsub '+jobfile.name
            jobfile.close()
            print (ccommand)
            if not istest: os.system(ccommand)
            os.chdir('../')
            ijob+=1
    else:
        ijob+=1   
        cmd = ' '.join(cmdlist)
        print (cmd)
        os.system(cmd)
    icom+=1
    if ijob>0 and doSmallNumber: 
        print('we reached the premature exit')
        break
if len(cmdlist)>0:       
    if useBatch:
            cmd = ' '.join(cmdlist)
            jobfile.write(shtemplate.replace('CWD',cwd))
            jobfile.write(cmd+'\n')
            ccommand = 'condor_qsub '+jobfile.name
            jobfile.close()
            print ('doing last one', ccommand)
            if not istest: os.system(ccommand)
            os.chdir('../')
            ijob+=1
    else:
        ijob+=1   
        cmd = ''.join(cmdlist)     
        print (cmd)
        os.system(cmd)            
    print('we reached the exit')    
    
    
    
    