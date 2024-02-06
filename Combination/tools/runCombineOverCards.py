import os, sys
from random import shuffle
from ROOT import *

'''
find  datacards/derived/CMS_SUS_18_004/2018/sos_2los_sr_high/ | grep txt > textfiles/sos_2los_sr_high.txt &
find  datacards/derived/CMS_SUS_18_004/2018/sos_2los_sr_low/ | grep txt > textfiles/sos_2los_sr_low.txt &
find  datacards/derived/CMS_SUS_18_004/2018/sos_2los_sr_med/ | grep txt > textfiles/tsos_2los_sr_med.txt &
find  datacards/derived/CMS_SUS_18_004/2018/sos_2los_sr_ultra/ | grep txt > textfiles/sos_2los_sr_ultra.txt &
find  datacards/derived/CMS_SUS_18_004/2018/sos_3l_sr_low/ | grep txt > textfiles/sos_3l_sr_low.txt &
find  datacards/derived/CMS_SUS_18_004/2018/sos_3l_sr_med/ | grep txt > textfiles/sos_3l_sr_med.txt &
find  datacards/derived/CMS_SUS_18_004/Run2/ | grep txt > textfiles/Run2.txt
'''

'''
nohup python tools/runCombineOverCards.py  textfiles/sos_2los_sr_high.txt &
nohup python tools/runCombineOverCards.py  textfiles/sos_2los_sr_low.txt &
nohup python tools/runCombineOverCards.py  textfiles/tsos_2los_sr_med.txt &
nohup python tools/runCombineOverCards.py  textfiles/sos_2los_sr_ultra.txt &
nohup python tools/runCombineOverCards.py  textfiles/sos_3l_sr_low.txt &
nohup python tools/runCombineOverCards.py  textfiles/sos_3l_sr_med.txt &
nohup python tools/runCombineOverCards.py  textfiles/Run2.txt &
'''

#notes from Philip:
#saveFitResult, saveWorkspace  -->snapshotMultiDimFit, combineHarvestor ->counts and shapes
#then, maybe there's something to dropping:
#--X-rtd REMOVE_CONSTANT_ZERO_POINT=1

cwd = os.getcwd()
cmd_template2 = '''attempts=0
while [ $attempts -lt $max_attempts ]; do
    # Attempt the command
    combine --method MultiDimFit INPUT  --mass 125.0 --algo grid --redefineSignalPOIs r --setParameterRanges r=0.0,1.5 --points 16 --alignEdges 1 --saveNLL --cminDefaultMinimizerType Minuit2 --cminDefaultMinimizerStrategy 0 --cminDefaultMinimizerTolerance 0.1 --cminFallbackAlgo Minuit2,0:0.2 --name ROOTOUT
    #no more:  --X-rtd REMOVE_CONSTANT_ZERO_POINT=1
    # Check the exit status
    if [ $? -eq 0 ]; then
        # Success
        break
    else
        attempts=$((attempts+1))
        echo "Command failed. Attempt $attempts of $max_attempts."
        sleep 5
    fi
done
'''
istest = False
doafew = False
energysaver = True
commandsPerJob = 1

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
cd jobsubmit/
mkdir $timestamp
echo #timestamp
cd $timestamp
'''

analysis = 'CMS_SUS_18_004'
if energysaver: 
    #tpmssmfile = 'THnSparses/'+analysis+'/'+analysis.lower()+'.root'#probably the thing you want to clone with new branch
    ftpmssm = TFile('rootfiles/TheNewAndExcitingFullTree.root')
    tpmssm = ftpmssm.Get('mcmc')
    tpmssm.SetBranchStatus("*",0)
    tpmssm.SetBranchStatus('Zsig_'+analysis.lower(),1);
    tpmssm.SetBranchStatus('chain_index',1);
    tpmssm.SetBranchStatus('Niteration',1);        
    tpmssm.Show(0)

try: filenamelistfilename = sys.argv[1]
except: filenamelistfilename = 'textfiles/sos_2los_sr_high.txt'


filenamelistfile = open (filenamelistfilename)
filenamelist = filenamelistfile.readlines()
filenamelist.reverse()
#shuffle(filenamelist)
thelength = len(filenamelist)
firstfile = filenamelist[0]

combineoutdir = '/'.join(firstfile.split('/')[:-1]).replace('datacards/derived','combineroots')
os.system('mkdir -p jobsubmit')
os.system('mkdir -p '+combineoutdir)

print('combineoutdir', combineoutdir, firstfile)

ijob, icom, nloaded = 0, 0, 0
emptyname = 0
for txtfile_ in filenamelist:

        txtfile = txtfile_.strip()
        if not '.txt' in txtfile_: continue
                
        lilfile = txtfile.split('/')[-1]        
        chain_index, Niteration = txtfile.replace('.txt','').split('_')[-2:]
        
        predictedoutfile = cwd+'/combineroots/'+analysis+'/Run2/higgsCombine_Run2_'+chain_index+'_'+Niteration+'.MultiDimFit.mH125.root'
        if os.path.exists(predictedoutfile):
            print('already got', predictedoutfile)
            continue
            
        if energysaver: 
            tpmssm.GetEntryWithIndex(int(chain_index),int(Niteration))
            nprockinda = getattr(tpmssm, 'Zsig_'+analysis.lower())
            #print('nprockinda',nprockinda)
            
        if energysaver and nprockinda==0 and emptyname:
            continue #so don't create hundreds of thousands of identical links
        else:
            cmd1 = "echo no longer doing this" #cmd_template1.replace('INPUT', cwd+'/'+txtfile).replace('OUTPUT','werkstatt.root')        
            if energysaver and nprockinda==0: 
                emptyname = predictedoutfile
                cmd1 += ' && ln -s '+emptyname+' '+ '/'.join(emptyname.split('/')[:-1])+'certifiedBkgOnly.root'
            combinerootout = lilfile.replace('.txt','')
            cmd2 = cmd_template2.replace('INPUT',cwd+'/'+txtfile).replace('ROOTOUT',combinerootout)
            cmd3 = 'mv higgsCombine*.root '+cwd+'/combineroots/'+analysis+'/'+'Run2/'
                
        if icom%commandsPerJob==0:
            jobname = 'runcombine_'+lilfile.replace('.txt','.sh')
            print jobname
            os.chdir('jobsubmit/')
            fjob = open(jobname,'w')
            fjob.write(shtemplate.replace('CWD',cwd))
            
            
        fjob.write(cmd1+'\n')
        fjob.write(cmd2+'\n')
        fjob.write(cmd3+'\n')
        nloaded+=1
        
        if icom%commandsPerJob==commandsPerJob-1:
            fjob.write('cd ../\n')
            fjob.write('rm -rf $timestamp \n')            
            ccommand = 'condor_qsub '+fjob.name
            fjob.close()
            print (ccommand)
            if not istest: os.system(ccommand)
            os.chdir('../')
            ijob+=1   
            nloaded = 0      
        icom+=1            
        '''
        limit.GetEntry(1)
        t = 2*limit.deltaNLL
        L = TMath.Exp(-t/2)/TMath.Sqrt(TMath.Pi()*t) #am I forgetting a 2* here?
        print(chain_index, Niteration, t, L)
        '''
        if ijob>2 and (istest or doafew): break
        
if nloaded>0: 
            fjob.write('cd ../\n')
            fjob.write('rm -rf $timestamp \n')  
            ccommand = 'condor_qsub '+fjob.name
            fjob.close()
            print ('last', ccommand)
            if not istest: os.system(ccommand)
os.chdir('../')

    
exit(0)
