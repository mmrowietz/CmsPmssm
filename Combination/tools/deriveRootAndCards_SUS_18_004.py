from ROOT import *
import os, sys
from time import time

'''
nohup python3 tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/2018/sos_2los_sr_high & sleep 1
nohup python3 tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/2018/sos_2los_sr_low & sleep 1
nohup python3 tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/2018/sos_2los_sr_med & sleep 1
nohup python3 tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/2018/sos_2los_sr_ultra & sleep 1
nohup python3 tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/2018/sos_3l_sr_low & sleep 1
nohup python3 tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/2018/sos_3l_sr_med & sleep 1
nohup python3 tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/Run2 & sleep 1

nohup python3 tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/2017/sos_2los_sr_high & sleep 1
nohup python3 tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/2017/sos_2los_sr_low & sleep 1
nohup python3 tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/2017/sos_2los_sr_med & sleep 1
nohup python3 tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/2017/sos_2los_sr_ultra & sleep 1
nohup python3 tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/2017/sos_3l_sr_low & sleep 1
nohup python3 tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/2017/sos_3l_sr_med & sleep 1

nohup python3 tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/2016/sos_2los_sr_high & sleep 1
nohup python3 tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/2016/sos_2los_sr_low & sleep 1
nohup python3 tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/2016/sos_2los_sr_med & sleep 1
nohup python3 tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/2016/sos_2los_sr_ultra & sleep 1
nohup python3 tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/2016/sos_3l_sr_low & sleep 1
nohup python3 tools/removeReplaceFolder.py datacards/derived/CMS_SUS_18_004/2016/sos_3l_sr_med & sleep 1
'''

'''
cd /nfs/dust/cms/user/beinsam/pMSSM13TeV/Scan2/Combination/CMSSW_10_2_13/src
python tools/getSingleAnalysisLhdCombine.py
cd ../../CMSSW_12_2_4/src/
cmsenv
cd -
nohup python3 tools/deriveRootAndCards_SUS_18_004.py sos_2los_sr_high  > out_sos_2los_sr_high.txt &
nohup python3 tools/deriveRootAndCards_SUS_18_004.py sos_2los_sr_low   > out_sos_2los_sr_low.txt &
nohup python3 tools/deriveRootAndCards_SUS_18_004.py sos_2los_sr_med   > out_sos_2los_sr_med.txt &
nohup python3 tools/deriveRootAndCards_SUS_18_004.py sos_2los_sr_ultra > out_sos_2los_sr_ultra.txt &
nohup python3 tools/deriveRootAndCards_SUS_18_004.py sos_3l_sr_low     > out_sos_3l_sr_low.txt &
nohup python3 tools/deriveRootAndCards_SUS_18_004.py sos_3l_sr_med     > out_sos_3l_sr_med.txt & 
cmsenv
nohup python tools/deriveRootAndCards_SUS_18_004.py Run2 > out_run2_sos.txt &

nohup python tools/removeReplaceFolder.py combineroots/CMS_SUS_18_004/Run2 &
nohup python tools/removeReplaceFolder.py combineroots/CMS_SUS_21_006/Run2 &
'''

istest = True #found it false after desert
useBatch = False#found it true after desert #only applies to Run2s
doSmallNumber = True# found it False after desert

analysis = 'CMS_SUS_18_004'

lumis = {'Run2':137000, 2018:59740, 2017:41530, 2016:36330}
lumi16, lumi17, lumi18, lumirun2 = 36330, 41530, 59740, 137600

try: 
    region = sys.argv[1]
    #regions = ['sos_2los_sr_high', 'sos_2los_sr_low','sos_2los_sr_med','sos_2los_sr_ultra','sos_3l_sr_low','sos_3l_sr_med']
except:
    region = 'sos_2los_sr_high'
    region = 'sos_2los_sr_med'
    region = 'sos_2los_sr_ultra'
    region = 'sos_2los_sr_low'    
    region = 'sos_3l_sr_low'
    region = 'sos_3l_sr_med'
doCombination = bool('Run2' in region) # consider dropping this feature from this script


    
if not 'low' in region: binnames = ['Mll_1_4','Mll_4_10', 'Mll_10_20', 'Mll_20_30','Mll_30_50']
else: binnames = ['Mll_4_10', 'Mll_10_20', 'Mll_20_30','Mll_30_50']

regionv2 = {}
regionv2['sos_2los_sr_high'] = '2l_highMET'
regionv2['sos_2los_sr_low'] = '2l_lowMET'
regionv2['sos_2los_sr_med'] = '2l_medMET'
regionv2['sos_2los_sr_ultra'] = '2l_ultraMET'
regionv2['sos_3l_sr_low'] = '3l_lowMET'
regionv2['sos_3l_sr_med'] = '3l_medMET'
       

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
cd jobsubmit/
mkdir $timestamp
cd $timestamp
'''

cmdlist = []
t0 = time()
if doCombination:
    era = 2018
    commandsPerJob = 100
    FinalStates = ['sos_2los_sr_high','sos_2los_sr_low', 'sos_2los_sr_med','sos_2los_sr_ultra','sos_3l_sr_low','sos_3l_sr_med']
    from glob import glob
    flagdir = 'datacards/derived/'+analysis+'/2018/'+region
    outdir = flagdir.replace('/2018','')
    if not os.path.exists(outdir): os.system('mkdir -p '+outdir)   
    flagshipfilenames = glob(flagdir.replace(region, FinalStates[0]+'/*'))
    thelength = len(flagshipfilenames)
    print ('length', thelength)
    icom = 0
    ijob = 0
    for flagshipfilename in flagshipfilenames:
        #print ('here we aa', icom)
        newfname = cwd+'/'+flagshipfilename.replace(FinalStates[0],region).replace('/2018','')
        if os.path.exists(newfname):
            print ('already got', newfname)
            continue        
        cmdlist.append('combineCards.py '+ cwd+'/' + flagshipfilename+' ')
        cmdlist.append(cwd+'/' + flagshipfilename.replace('/2018','/2017')+' ')
        cmdlist.append(cwd+'/' + flagshipfilename.replace('/2018','/2016')+' ')
        for fstate in FinalStates[1:]:
            cmdlist.append(cwd+'/'+flagshipfilename.replace(FinalStates[0],fstate)+' ')
            cmdlist.append(cwd+'/'+flagshipfilename.replace(FinalStates[0],fstate).replace('/2018','/2017')+' ')
            cmdlist.append(cwd+'/'+flagshipfilename.replace(FinalStates[0],fstate).replace('/2018','/2016')+' ')
        cmdlist.append('> '+ cwd+'/'+flagshipfilename.replace(FinalStates[0],'').replace('/2018','/Run2'))
        cmdlist[-1]+='\n'
        if useBatch:
            if icom%commandsPerJob==0:
                t1 = time()
                print('dt: ', t1-t0, t1, t0)
                t0 = t1                        
                os.chdir('jobsubmit/')
                newfile = open('cc_'+ flagshipfilename.split('/')[-1].replace('.txt','.sh'),'w')
            if icom%commandsPerJob==commandsPerJob-1:
                cmd = ''.join(cmdlist)
                cmdlist = []
                newfile.write(shtemplate.replace('CWD',cwd))
                newfile.write(cmd+'\n')
                ccommand = 'condor_qsub '+newfile.name
                newfile.close()
                print (ccommand)
                if not istest: os.system(ccommand)
                os.chdir('../')
                ijob+=1
        else:
            ijob+=1   
            cmd = ''.join(cmdlist)     
            print (cmd)
            os.system(cmd)
        icom+=1
        if istest: break
        if ijob>0 and doSmallNumber: 
            print('we reached the premature exit')
            newfile.close()
            exit(0)
    if useBatch:
            cmd = ''.join(cmdlist)
            newfile.write(shtemplate.replace('CWD',cwd))
            newfile.write(cmd+'\n')
            ccommand = 'condor_qsub '+newfile.name
            newfile.close()
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
    exit(0)
    
    
#for era in [2016,2017,2018]:
#for era in [2017,2018]:
#for era in [2016]:
for era in [2018]:
    lumi = lumis[era]
    indir = 'datacards/provided/'+analysis+'/'+str(era)+'/'
    outdir = indir.replace('provided', 'derived')+'/'+region+'/'
    if not os.path.exists(outdir): os.system('mkdir -p '+outdir)
    
    rawcard = open(indir+'/'+region+'.txt').read()
    rawroot = TFile(indir+'/'+region+'.root')
    rawroot.cd(region)
    thekeys = rawroot.Get(region).GetListOfKeys()
    names = [key.GetName() for key in thekeys]
    
    tpmssmfile = TFile('rootfiles/TheNewestAndMostExcitingFullTree.root')#full.root')
    tpmssm = tpmssmfile.Get('mcmc')
    nentries = tpmssm.GetEntries()
    print ('going to process', nentries)
    
    countstreefile = 'THnSparses/'+analysis+'/'+analysis.lower()+'.root'
    countstree = 'Counts'
    fcountstree = TFile(countstreefile)
    tcounts = fcountstree.Get(countstree)
    branchnames = []
    for branch in tcounts.GetListOfBranches():
        branchnames.append(branch.GetName())    
    rootname = outdir+'/'+region+'.root'
    print ('rootname', rootname)
    
    newroot = TFile(rootname,'recreate')
    newroot.mkdir(region)
    
    for name in names: 
        obj = rawroot.Get(region+'/'+name)
        newroot.cd(region)
        obj.Write(name)
    
    htemplate = rawroot.Get(region+'/'+'data_obs').Clone('htemplate')
    htemplate.Reset()
    xax = htemplate.GetXaxis()
    
    emptyname = ''
    for ientry in range(nentries):
    
    
    
        ###if not ientry>418500: continue
        
        
        
        #tcounts.GetEntry(ientry)
        if ientry%100==0: print('processing', ientry)
        tpmssm.GetEntry(ientry)
                
        ###if not (tpmssm.chain_index==447 and tpmssm.Niteration == 85245): continue
        
        chain_index, Niteration = str(int(tpmssm.chain_index)), str(int(tpmssm.Niteration))
        
        newcardfilename = outdir+'/card_%s_%s.txt'%(chain_index, Niteration)
        if os.path.exists(newcardfilename) and (not istest):
            print ('continuing past',   newcardfilename)
            print ('actually this would mess up the root file, so you should probably start fresh')
            exit(0)
            
        #tpmssm.Show(ientry)
        signame = 'Signal_%-10s' % (chain_index+'_'+Niteration)
        hsig = htemplate.Clone(signame)
        nprockinda = getattr(tpmssm, 'Zsig_'+analysis.lower())
        if nprockinda==0:
            if emptyname: 
                linkcmd = 'ln -s %s %s' % (emptyname, newcardfilename)
                #print('My linkcmd', linkcmd)
                newroot.cd(region)
                hsig.Write()
                os.system(linkcmd)
                #os.symlink(emptyname, newcardfilename)
                continue
            else: emptyname = cwd+'/'+newcardfilename
        
        itcounts = tcounts.GetEntryWithIndex(int(tpmssm.chain_index), int(tpmssm.Niteration))
        if itcounts==-1:
           entryexists = False
        else: entryexists = True
        
                
        xsecpb = tpmssm.xsec_tot_pb
        if entryexists:
          for ibinm, binname in enumerate(binnames):
            bname17, bname18 = '_'.join([analysis,regionv2[region],binname, '2017']), '_'.join([analysis,regionv2[region],binname, '2018'])
            scount17, scount18 = getattr(tcounts, bname17), getattr(tcounts, bname18)
            nproc17name, nproc18name = analysis+'_nProcessed_2017', analysis+'_nProcessed_2018'
            nproc17, nproc18 = getattr(tcounts, nproc17name), getattr(tcounts, nproc18name)
            
            if nproc17>0 and nproc18>0: hsig.SetBinContent(ibinm+1, tpmssm.filter_eff*lumi*xsecpb*(lumi17*scount17/nproc17+lumi18*scount18/nproc18)/(lumi18+lumi17))
            elif nproc17>0: hsig.SetBinContent(ibinm+1, tpmssm.filter_eff*lumi*xsecpb*(scount17/nproc17))
            elif nproc18>0: hsig.SetBinContent(ibinm+1, tpmssm.filter_eff*lumi*xsecpb*(scount18/nproc18))
            else: hsig.SetBinContent(ibinm+1, 0)

            
            #print(era, 'bname17 bname18: ', bname17, bname18, ibinm, 'content:', hsig.GetBinContent(ibinm), 'rawcounts17and18', scount17, scount18, 'nproc17and18:', nproc17, nproc18)
        if istest: print (signame, hsig.Integral())
        

        newroot.cd(region)
        hsig.Write()
        newcard = open(newcardfilename,'w')    
        newtext = rawcard.replace('Signal          ',signame)
        newtext = newtext.replace('nsig     ','%-9s'%str(hsig.Integral()))
        newcard.write(newtext)
        print(ientry, 'just created', newcard.name)
        if hsig.Integral()>1: print('creating interesting', newcardfilename, 'having processed', hsig.Integral())        
        newcard.close()
        if istest or (doSmallNumber and ientry>20): 
            break
        
    print ('just created root file', newroot.GetName())
    newroot.Close()




'''
echo 2018/sos_2los_sr_high
ls -latr datacards/derived/CMS_SUS_18_004/2018/sos_2los_sr_high | head
echo 2018/sos_2los_sr_low
ls -latr datacards/derived/CMS_SUS_18_004/2018/sos_2los_sr_low | head
echo 2018/sos_2los_sr_med
ls -latr datacards/derived/CMS_SUS_18_004/2018/sos_2los_sr_med | head
echo 2018/sos_2los_sr_ultra
ls -latr datacards/derived/CMS_SUS_18_004/2018/sos_2los_sr_ultra | head
echo 2018/sos_3l_sr_low
ls -latr datacards/derived/CMS_SUS_18_004/2018/sos_3l_sr_low | head
echo 2018/sos_3l_sr_med
ls -latr datacards/derived/CMS_SUS_18_004/2018/sos_3l_sr_med | head
echo 2017/sos_2los_sr_high
ls -latr datacards/derived/CMS_SUS_18_004/2017/sos_2los_sr_high | head
echo 2017/sos_2los_sr_low
ls -latr datacards/derived/CMS_SUS_18_004/2017/sos_2los_sr_low | head
echo 2017/sos_2los_sr_med
ls -latr datacards/derived/CMS_SUS_18_004/2017/sos_2los_sr_med | head
echo 2017/sos_2los_sr_ultra
ls -latr datacards/derived/CMS_SUS_18_004/2017/sos_2los_sr_ultra | head
echo 2017/sos_3l_sr_low
ls -latr datacards/derived/CMS_SUS_18_004/2017/sos_3l_sr_low | head
echo 2017/sos_3l_sr_med
ls -latr datacards/derived/CMS_SUS_18_004/2017/sos_3l_sr_med | head
echo 2016/sos_2los_sr_high
ls -latr datacards/derived/CMS_SUS_18_004/2016/sos_2los_sr_high | head
echo 2016/sos_2los_sr_low
ls -latr datacards/derived/CMS_SUS_18_004/2016/sos_2los_sr_low | head
echo 2016/sos_2los_sr_med
ls -latr datacards/derived/CMS_SUS_18_004/2016/sos_2los_sr_med | head
echo 2016/sos_2los_sr_ultra
ls -latr datacards/derived/CMS_SUS_18_004/2016/sos_2los_sr_ultra | head
echo 2016/sos_3l_sr_low
ls -latr datacards/derived/CMS_SUS_18_004/2016/sos_3l_sr_low | head
echo 2016/sos_3l_sr_med
ls -latr datacards/derived/CMS_SUS_18_004/2016/sos_3l_sr_med | head
echo Run2
ls -latr datacards/derived/CMS_SUS_18_004/Run2 | head

'''