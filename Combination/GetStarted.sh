#need to set up combine, I did this on 
cmsrel CMSSW_10_2_13

cd CMSSW_10_2_13/src
cmsenv
#set up 

cd ../../Combination
#one time per analysis to include, for example
mkdir -p datacards/derived/CMS_SUS_18_004/{2016,2017,2018,Run2}

#kind of a unit test:
cd <...>CMSSW_10_2_13/src
python tools/getSingleAnalysisLhdCombine.py

#produce many cards
cd ../../CMSSW_12_2_4/src/
cmsenv
cd -
nohup python3 tools/deriveRootAndCards_SUS_18_004.py sos_2los_sr_high  > out_sos_2los_sr_high.txt &
nohup python3 tools/deriveRootAndCards_SUS_18_004.py sos_2los_sr_low   > out_sos_2los_sr_low.txt &
nohup python3 tools/deriveRootAndCards_SUS_18_004.py sos_2los_sr_med   > out_sos_2los_sr_med.txt &
nohup python3 tools/deriveRootAndCards_SUS_18_004.py sos_2los_sr_ultra > out_sos_2los_sr_ultra.txt &
nohup python3 tools/deriveRootAndCards_SUS_18_004.py sos_3l_sr_low     > out_sos_3l_sr_low.txt &
nohup python3 tools/deriveRootAndCards_SUS_18_004.py sos_3l_sr_med     > out_sos_3l_sr_med.txt & 
nohup python tools/deriveRootAndCards_SUS_18_004.py Run2 > out_run2_sos.txt &

#after the above finishes, create file lists of input files
find  datacards/derived/CMS_SUS_18_004/2018/sos_2los_sr_high/ | grep txt > textfiles/sos_2los_sr_high.txt &
find  datacards/derived/CMS_SUS_18_004/2018/sos_2los_sr_low/ | grep txt > textfiles/sos_2los_sr_low.txt &
find  datacards/derived/CMS_SUS_18_004/2018/sos_2los_sr_med/ | grep txt > textfiles/tsos_2los_sr_med.txt &
find  datacards/derived/CMS_SUS_18_004/2018/sos_2los_sr_ultra/ | grep txt > textfiles/sos_2los_sr_ultra.txt &
find  datacards/derived/CMS_SUS_18_004/2018/sos_3l_sr_low/ | grep txt > textfiles/sos_3l_sr_low.txt &
find  datacards/derived/CMS_SUS_18_004/2018/sos_3l_sr_med/ | grep txt > textfiles/sos_3l_sr_med.txt &
find  datacards/derived/CMS_SUS_18_004/Run2/ | grep txt > textfiles/Run2.txt

#run combine over these cards
nohup python tools/runCombineOverCards.py  textfiles/sos_2los_sr_high.txt &
nohup python tools/runCombineOverCards.py  textfiles/sos_2los_sr_low.txt &
nohup python tools/runCombineOverCards.py  textfiles/tsos_2los_sr_med.txt &
nohup python tools/runCombineOverCards.py  textfiles/sos_2los_sr_ultra.txt &
nohup python tools/runCombineOverCards.py  textfiles/sos_3l_sr_low.txt &
nohup python tools/runCombineOverCards.py  textfiles/sos_3l_sr_med.txt &
nohup python tools/runCombineOverCards.py  textfiles/Run2.txt &

#harvest the above results into a main tree:
cd ../../CMSSW_12_2_3/src/
csmenv
cd -
nohup python3 tools/llhdHarvestor.py 

