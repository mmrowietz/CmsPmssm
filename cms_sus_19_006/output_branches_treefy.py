import numpy as np
# First define the output tree structure. This can be put in a separate file and imported, which allows this script to be more generally useful.
output_branches_treefy = {} #each entry needs a name for the output branch, as well as a numpty container and branch datatype

#each pMSSM points is identified by a unique pair of integer values indices: chain_index and Niteration
#np.zeros makes python floats and integers compatible with root trees
output_branches_treefy["Niteration"] = {"name":"Niteration","container":np.zeros(1,dtype = int),"dtype":"I"}
output_branches_treefy["chain_index"] = {"name":"chain_index","container":np.zeros(1,dtype = int),"dtype":"I"}
#carry over the total production cross section and gen-filter efficiency
output_branches_treefy["xsec"] = {"name":"xsec_pb","container":np.zeros(1,dtype = float),"dtype":"D"}
output_branches_treefy["filtereff"] = {"name":"filtereff","container":np.zeros(1,dtype = float),"dtype":"D"}

#now map the THnSparse signal region bin index to the tree output branch

for i in range(1,175): #CAUTION: THnSparses start indexing bins at 1, even if the histogram is set up to start at 0! If it was set up to start at zero, the bins are shifted by 1! This can have nasty consequences! I highly suggest to tell analyzers to set up the THnSparses to explicitly start all axes at 1.
    #2017 and 2018 data count should be treated separately
    output_branches_treefy[i] = {"name_2017":"cms_sus_19_006_sr_"+str(i)+"_2017","container_2017":np.zeros(1,dtype = float),"dtype":"D","name_2018":"cms_sus_19_006_sr_"+str(i)+"_2018","container_2018":np.zeros(1,dtype = float),"dtype":"D"}
#ATTENTION: In case of additional signal region dimensions, the dictionary keys should be tuples of (srbin_dim1,srbin_dim2,...) in order to work with treefy.py

    
#we also need to include the total of events encountered by the analysis in the output tree in order to compute the weights
#This analysis provides a separate THnSparse for the signal region counts and the event totals. I use a string of the bin index here to separate the dictionary entries  
output_branches_treefy["1"] = {"name_2017":"cms_sus_19_006_nTotal_2017","container_2017":np.zeros(1,dtype = int),"dtype":"I","name_2018":"cms_sus_19_006_nTotal_2018","container_2018":np.zeros(1,dtype = int),"dtype":"I"}


