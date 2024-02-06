import numpy as np
# First define the output tree structure. This can be put in a separate file and imported, which allows this script to be more generally useful.
output_branches_likelihood = {} #each entry needs a name for the output branch, as well as a numpty container and branch datatype


#Branches for the likelihood, one branch per assumed signal strength modifier
# I suggest the name convention that contains the analysis name in the branch, the signal strength of the form muXpY for a signal strength of X.Y, and the suffix "s" for simplified, and "f" for full likelihood
output_branches_likelihood["llhd_mu0p0"] = {"name":"llhd_cms_sus_19_006_mu0p0s","container":np.zeros(1,dtype = float),"dtype":"D"}
output_branches_likelihood["llhd_mu1p0"] = {"name":"llhd_cms_sus_19_006_mu1p0s","container":np.zeros(1,dtype = float),"dtype":"D"}
output_branches_likelihood["llhd_mu0p5"] = {"name":"llhd_cms_sus_19_006_mu0p5s","container":np.zeros(1,dtype = float),"dtype":"D"}
output_branches_likelihood["llhd_mu1p5"] = {"name":"llhd_cms_sus_19_006_mu1p5s","container":np.zeros(1,dtype = float),"dtype":"D"}
#For convenience, it also makes sense to save the Bayes factor
output_branches_likelihood["bf_mu1p0"] = {"name":"bf_cms_sus_19_006_mu1p0s","container":np.zeros(1,dtype = float),"dtype":"D"}
output_branches_likelihood["bf_mu0p5"] = {"name":"bf_cms_sus_19_006_mu0p5s","container":np.zeros(1,dtype = float),"dtype":"D"}
output_branches_likelihood["bf_mu1p5"] = {"name":"bf_cms_sus_19_006_mu1p5s","container":np.zeros(1,dtype = float),"dtype":"D"}
#And the signed Z significance
output_branches_likelihood["Zsig_mu1p0"] = {"name":"Zsig_cms_sus_19_006_mu1p0s","container":np.zeros(1,dtype = float),"dtype":"D"}
output_branches_likelihood["Zsig_mu0p5"] = {"name":"Zsig_cms_sus_19_006_mu0p5s","container":np.zeros(1,dtype = float),"dtype":"D"}
output_branches_likelihood["Zsig_mu1p5"] = {"name":"Zsig_cms_sus_19_006_mu1p5s","container":np.zeros(1,dtype = float),"dtype":"D"}

