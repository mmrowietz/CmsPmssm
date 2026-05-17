#small test of single analysis
python3 toolsLLM/run_pmssm_combination.py --base-dir . --analyses SUS_20_001 --point 233 90317 --keep-workdirs

#small test of combination
python3 toolsLLM/run_pmssm_combination.py --base-dir . --analyses SUS_18_004 SUS_20_001 SUS_21_006 SUS_24_003 --point 233 90317 --keep-workdirs

#main run of combination
python3 toolsLLM/prepare_condor_scan.py --base-dir . --analyses SUS_18_004 SUS_20_001 SUS_21_006 SUS_24_003 --points-per-job 500 --job-flavour tomorrow
condor_submit #that
python3 toolsLLM/harvest_llhd_from_combine.py --base-dir . --combine-dir combinerootsLLM/SUS_18_004__SUS_20_001__SUS_21_006__SUS_24_003/Run2 --output rootfiles/full_with_llhd_SUS_18_004__SUS_20_001__SUS_21_006__SUS_24_003.root --tag sus_18_004__sus_20_001__sus_21_006__sus_24_003 --status-branch


#do individual analyses

nohup python3 toolsLLM/prepare_condor_scan.py --base-dir . --analyses SUS_18_004 --job-flavour longlunch > makinJobsSUS_18_004.txt & #almost done
nohup python3 toolsLLM/prepare_condor_scan.py --base-dir . --analyses SUS_20_001 --job-flavour longlunch > makinJobsSUS_20_001.txt & #too many failed
nohup python3 toolsLLM/prepare_condor_scan.py --base-dir . --analyses SUS_21_006 --job-flavour longlunch > makinJobsSUS_21_006.txt &
nohup python3 toolsLLM/prepare_condor_scan.py --base-dir . --analyses SUS_21_001 --job-flavour longlunch > makinJobsSUS_21_001.txt &
nohup python3 toolsLLM/prepare_condor_scan.py --base-dir . --analyses SUS_24_003 --job-flavour longlunch > makinJobsSUS_24_003.txt & 

python3 toolsLLM/harvest_llhd_from_combine.py --base-dir . --combine-dir combinerootsLLM/SUS_18_004/Run2 --pmssm-tree THnSparses/SUS_18_004/sus_18_004_likelihood_phase1.root --pmssm-tree-name cms_sus_18_004 --output rootfiles/full_with_llhd_SUS_18_004.root --tag sus_18_004 --status-branch
python3 toolsLLM/harvest_llhd_from_combine.py --base-dir . --combine-dir combinerootsLLM/SUS_20_001/Run2 --pmssm-tree THnSparses/SUS_20_001/cms_sus_20_001_xsec.root --pmssm-tree-name Counts --output rootfiles/full_with_llhd_SUS_20_001.root --tag sus_20_001 --status-branch
python3 toolsLLM/harvest_llhd_from_combine.py --base-dir . --combine-dir combinerootsLLM/SUS_21_006/Run2 --pmssm-tree THnSparses/SUS_21_006/cms_sus_21_006_xsec.root --pmssm-tree-name Counts --output rootfiles/full_with_llhd_SUS_21_006.root --tag sus_SUS_21_006 --status-branch
python3 toolsLLM/harvest_llhd_from_combine.py --base-dir . --combine-dir combinerootsLLM/SUS_21_001/Run2 --pmssm-tree THnSparses/SUS_21_001/sus_21_001_likelihood.root --pmssm-tree-name sus_21_001 --output rootfiles/full_with_llhd_SUS_21_001.root --tag sus_21_001 --status-branch
python3 toolsLLM/harvest_llhd_from_combine.py --base-dir . --combine-dir combinerootsLLM/SUS_24_003/Run2 --pmssm-tree THnSparses/SUS_24_003/sus_24_003_likelihood_phase1.root --pmssm-tree-name cms_sus_24_003 --output rootfiles/full_with_llhd_SUS_24_003.root --tag sus_24_003 --status-branch




condor_qedit 2744340 RequestRuntime 172800
condor_qedit 2744340 MaxRuntime 172800
condor_qedit 2744340 RequestMemory 4096
condor_release 2744340