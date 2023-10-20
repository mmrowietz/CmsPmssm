from ROOT import *
import os,sys
import importlib
import math
import numpy as np
from tqdm import tqdm
import argparse



"""
The purpose of this script is to collect the signal region counts from potentially multiple THnSparses and save them to a tree. Because individual pMSSM models may be distributed across multiple input THnSparses, we first need to collect everything in a dictionary, and then write the tree after the totals for each pMSSM point are known.
"""

def get_thnsparse_dimension(hnsparse):
    """
    Returns the dimensionality of the ThnSparse input
    """
    ndim = hnsparse.GetNdimensions()
    return ndim
def get_ntotal_inputtype(output_dictionary):
    """
    Returns the method of providing the encountered event totals for the analysis
    """
    pass
def setup_tree(outtree,_output_branches):
    """
    Creates the output branches in the output tree
    @param outtree: Output tree in which to create the branches
    @param _output_branches: dictionary from which to create the tree branches. Each dictionary value corresponds to an output branch and is itself a dictionary with the following entries:
    "name": name of the output branch
    "container": numpy container created using np.zeros(1,dtype=datatype), where datatype corresponds to the desired datatype of the output branch. For example, use np.zeros(1,dtype=float) for branches containing floating point values
    "dtype": datatype of the output branch ('D' for float, 'I' for int, ...)
    The dictionary can optionally contain entries for 2017 and 2018 seperately.
    """
    #first parameter of TTree.Branch() is the name of the branch in the output, second parameter is the variable that is queried for the value to fill the tree with, each time tree.Fill() is called. The third parameter is used here to tell root to convert the value of the container to "dtype". See dictionary above.
    for key,outbranch in _output_branches.items():
        if "name_2017" in outbranch or "name_2018" in outbranch:#These are the signal region bins, for which we need to make one branch for each year
            outtree.Branch(outbranch["name_2017"],outbranch["container_2017"],outbranch["name_2017"]+"/"+outbranch["dtype"])
            outtree.Branch(outbranch["name_2018"],outbranch["container_2018"],outbranch["name_2018"]+"/"+outbranch["dtype"])
        else:
            outtree.Branch(outbranch["name"],outbranch["container"],outbranch["name"]+"/"+outbranch["dtype"])



def reset_containers(_output_branches):
    """
    Resets all the branch containers in @param _output_branches to a default value (0 by default)
    @param _output_branches: dictionary for the output branches. Assumes same format as in function setup_tree()
    """
    #for safety, reset all containers to zero after each time tree.Fill() is called
    for outbranch in _output_branches.values():
        for key,value in outbranch.items():
            if "container" in key:
                value[0] = 0

def run(args):
    homedir = "/nfs/dust/cms/user/mrowietm/output_pMSSMscan_new/python/beautiful_scripts/CmsPmssm/"
    outdir = args.outdir
    if outdir[-1]!="/":
        outdir+="/"
    if not os.path.exists(outdir):
        os.system("mkdir -p "+outdir)
    reference_file = TFile(args.scan)
    reference_tree = reference_file.Get("mcmc")

    gROOT.ProcessLine(".L "+homedir+"calcLlhdSingleCount.C+") # this contains a c++ function that calculates the simplified likelihood 
    sys.path.append(homedir)
    """
    The following imports the necessary information from the analysis directory. To implement a new analysis, you need to create a corresponding directory branching of the home directory, which contains the files:
    output_branches_treefy.py : containing a directionary "output_branches_treefy" that maps the THnSparse SR bins to the tree branch names in the output for ALL years, as well as a branch for the two pMSSM point indices, and one branch for the processed event totals in EACH year.
    ThnSparse_inputs.py : containing, for each year, a dictionary of the input ThnSparses with the signal regions, and a dictionary with input THnSparses containing the raw encountered event totals, "thnsparses_sr_YEAR" and "thnsparses_ntot_YEAR". The key and values are the file path and THnSparse name inside the root file, respectively.
    Note that some analyses have previously chosen to provide the event totals in a single designated bin inside the THnSparses that contain the signal region counts. In that case, this code needs to be modified accordingly
    """
    outbranches = importlib.import_module(".".join([args.analysis,"output_branches_treefy"]))
    output_branches = outbranches.output_branches_treefy

    infiles = importlib.import_module(".".join([args.analysis,"ThnSparse_inputs"]))
    #the following are dictionaries mapping the input file names for the respective year for the signal regions "sr" and the event totals "ntot" to the respective thnsparse therein
    infiles_sr_2017 = infiles.thnsparses_sr_2017
    infiles_sr_2018 = infiles.thnsparses_sr_2018
    infiles_ntot_2017 = infiles.thnsparses_ntot_2017
    infiles_ntot_2018 = infiles.thnsparses_ntot_2018
    #create output file
    collect_output = {} #this dictionary collects the output from the various input thnsparses, such that for each pMSSM point there is one dictionary entry with the event counts

    if not os.path.exists(homedir+"pMSSMIds.py"):
        #this is a safety check to see if the provided THnSparse contains invalid pMSSM point IDs, or if there are missing points. The entries of the collect output directionary are later checked against the list of pMSSM Ids created here
        referencecoords = []
        for ix in tqdm(range(reference_tree.GetEntries())):
            reference_tree.GetEntry(ix)
            referencecoords.append((int(reference_tree.chain_index),int(reference_tree.Niteration)))
        with open("pMSSMIds.py","w") as fout:
            fout.write("referencecoords = "+str(referencecoords))
    else:
        from pMSSMIds import referencecoords
    for year, hnsparsedict in {"2017":infiles_sr_2017,"2018":infiles_sr_2018}.items():
        print("running signal regions for year: ",year)
        ix = 1
        for filepath,hnsparsename in hnsparsedict.items():

            print("processing file nr. ",ix, " of ",len(hnsparsedict))
            ix+=1
            hnsparsefile = TFile(filepath)
            hnsparse = getattr(hnsparsefile,hnsparsename)
            thnsparsedim = hnsparse.GetNdimensions()
            break
            for linix in tqdm(range(hnsparse.GetNbins())):#iterate over LINEAR THnSparse indices. All filled bins in a thnsparse are assigned a unique linear index
                coordinates = np.intc([0]*thnsparsedim) # container with 3D coordinates, filled with THnSparse bin bin coordinates by calling thnsparse.GetBinContent()
                #The ThnSparse coordinates are set up such that coordinates is filled with [chain_index,Niteration, SR bin] after GetBinContent is called 
                count = hnsparse.GetBinContent(linix,coordinates) # get the bin content of the bin with linear index linix, fill "coordinates" with 3D bin coordinates
                #Check if the bin corresponds to a valid pMSSM point. Uncomment below if check is desired
                """
                if (int(coordinates[0]),int(coordinates[1])) not in referencecoords:
                    print("coordinates not found in reference tree in SR THnSparse: ",(int(coordinates[0]),int(coordinates[1])))
                """

                if not (int(coordinates[0]),int(coordinates[1])) in collect_output:
                    #It is in principle possible that a pMSSM point appears in more than one thnsparse, but we only want one root tree entry per pMSSM point at the end. Thus we first collect all the information in a python dictionary, before writing to the output root tree in a separate loop at the end
                    collect_output[(int(coordinates[0]),int(coordinates[1]))]={year:{}}#set up new entry if point was not encountered before
                else:
                    if not year in collect_output[(int(coordinates[0]),int(coordinates[1]))]:
                        #it is possible that the pMSSM point was already encountered, but for a different data taking year
                        collect_output[(int(coordinates[0]),int(coordinates[1]))][year]={}

                #This needs to add a layer for every dimension above 2. This will be painful to implement. Assume for now that only 3 or 4 are possible.
                if thnsparsedim == 3:
                    if not output_branches[coordinates[2]]["name_"+year] in collect_output[(int(coordinates[0]),int(coordinates[1]))][year]:# if this is the first time the pMSSM model is encountered, set signal region counts in dictionary.
                        #The following line seems waaaaaaaay too nested to be understandable. I may make sense to simplify this in the future.
                        #for now: the structure of collect_output is: collect_output[(ID1,ID2)][year][outputBranchName]
                        collect_output[(int(coordinates[0]),int(coordinates[1]))][year][output_branches[coordinates[2]]["name_"+year]] = count 
                    else:
                        collect_output[(int(coordinates[0]),int(coordinates[1]))][year][output_branches[coordinates[2]]["name_"+year]] += count# if there already is a signal event count, add the newly encountered events
                elif thnsparsedim > 3:#this case assumes that the dictionary keys in output_branches_treefy.py are tuples of the sr bin coordinates
                    if not output_branches[tuple(coordinates[2-thnsparsedim:])]["name_"+year] in collect_output[(int(coordinates[0]),int(coordinates[1]))][year]:
                        collect_output[(int(coordinates[0]),int(coordinates[1]))][year][tuple(coordinates[2-thnsparsedim:])]["name_"+year] = count
                    else:
                        collect_output[(int(coordinates[0]),int(coordinates[1]))][year][tuple(coordinates[2-thnsparsedim:])]["name_"+year] += count
                            
            hnsparsefile.Close()
    #repeat the thing for the event totals. If the event totals are provided in a signal region bin above, the code above needs to be modified.
    #only do this if the event totals are in a separate THnSparse
    
    for year, hnsparsedict in {"2017":infiles_ntot_2017,"2018":infiles_ntot_2018}.items():
        print("running event totals for year: ",year)
        ix = 1
        for filepath,hnsparsename in hnsparsedict.items():
            print("processing file nr. ",ix, " of ",len(hnsparsedict))
            ix+=1
            hnsparsefile = TFile(filepath)
            hnsparse = getattr(hnsparsefile,hnsparsename)
            thnsparsedim = hnsparse.GetNdimensions()
            #check whether this thnsparse contains only a single bin along the last axis
            if thnsparsedim>2 and hnsparse.GetAxis(thnsparsedim-1).GetNbins()>1:
                print("The presumed axis containing the event totals has more than one bin. It is assumed that the event totals are in the ThnSparse as the signal region event counts, in which case this step of the script has to and is skipped.")
                break
            for linix in tqdm(range(hnsparse.GetNbins())):#iterate over LINEAR THnSparse indices. All filled bins in a thnsparse are assigned a unique linear index
                coordinates = np.intc([0]*thnsparsedim) # container with 3D coordinates, filled with THnSparse bin bin coordinates by calling thnsparse.GetBinContent()
                #The ThnSparse coordinates are set up such that coordinates is filled with [chain_index,Niteration, SR bin] after GetBinContent is called 
                count = hnsparse.GetBinContent(linix,coordinates) # get the bin content of the bin with linear index linix, fill "coordinates" with 3D bin coordinates
                #FIXME: test if the thnsparse binning is correct - which is the min and max coordinate 3?

                #Check if the bin corresponds to a valid pMSSM point. Uncomment below if check is desired
                """
                if (int(coordinates[0]),int(coordinates[1])) not in referencecoords:
                    print("coordinates not found in reference tree in SR THnSparse: ",(int(coordinates[0]),int(coordinates[1])))
                """
                if not (int(coordinates[0]),int(coordinates[1])) in collect_output:
                    collect_output[(int(coordinates[0]),int(coordinates[1]))]={year:{}}#set up new entry if point was not encountered before
                else:
                    if not year in collect_output[(int(coordinates[0]),int(coordinates[1]))]:
                        #it is possible that the pMSSM point was already encountered, but for a different data taking year
                        collect_output[(int(coordinates[0]),int(coordinates[1]))][year]={}
                # for some reason, coordinates[2] is offset by one from the expected. This may need some investigating. In any case, ALWAYS be careful with the THnSparse binning and double-check that it is correct
                if thnsparsedim == 3:
                    if not output_branches[str(coordinates[2]-1)]["name_"+year] in collect_output[(int(coordinates[0]),int(coordinates[1]))][year]:# if this is the first time the pMSSM model is encountered, set signal region counts in dictionary.
                        collect_output[(int(coordinates[0]),int(coordinates[1]))][year][output_branches[str(coordinates[2]-1)]["name_"+year]] = count 
                    else:
                        collect_output[(int(coordinates[0]),int(coordinates[1]))][year][output_branches[str(coordinates[2]-1)]["name_"+year]] += count# if there already is a signal event count, add the newly encountered events
                elif thnsparsedim > 3:#this case assumes that the dictionary keys in output_branches_treefy.py are tuples of the sr bin coordinates
                    if not output_branches[tuple(coordinates[2-thnsparsedim:]-[1]*(2-thnsparsedim))]["name_"+year] in collect_output[(int(coordinates[0]),int(coordinates[1]))][year]:#this might need to be offset by 1, which is problematic with tuples. The part "-[1]*(2-thnsparsedim)" is supposed to substract from the coordinates array before tupleizing
                        collect_output[(int(coordinates[0]),int(coordinates[1]))][year][tuple(coordinates[2-thnsparsedim:]-[1]*(2-thnsparsedim))]["name_"+year] = count
                    else:
                        collect_output[(int(coordinates[0]),int(coordinates[1]))][year][tuple(coordinates[2-thnsparsedim:]-[1]*(2-thnsparsedim))]["name_"+year] += count

    #We now have a dictionary containing the signal region and total event counts for each pMSSM point, identified by its two IDs

    #Uncomment below to check for invalid pMSSM IDs
    """
    #Note that Monte Carlo events for two pMSSM points may exist that are not in the reference tree (pMSSMscan). These points were removed at some point, I don't remember exactly why anymore
    for coordtuple in collect_output.keys():
        if (int(coordtuple[0]),int(coordtuple[1])) in referencecoords:
            referencecoords.remove((int(coordtuple[0]),int(coordtuple[1])))
        else:
            print("Coordinates ",coordtuple, " not found in reference tree. Invalid IDs?")
    """
    #Next we iterate over the reference tree given by the -s argument, calculate a simplified likelihood and fill a tree with the outputs. If a point was not processed, it is assigned a default value in the output
    do_once = True
    #save tree every X entries
    #the three lines below are intended to write out a tree every 50,000 pMSSM points, so as to not lose all progress in case of a crash.
    file_nr = 1#change this value to start the loop below from a different file
    start = (file_nr-1)*50000
    stop = start+50000
    
    outfile = TFile(outdir+args.outname,"recreate")#create the output file
    outtree = TTree(str(args.analysis),str(args.analysis))#create the output tree
    setup_tree(outtree,output_branches)#set up the branches in the output tree

    #    for iEntry in tqdm(range(reference_tree.GetEntries())):#uncomment this if you want to run over the whole tree without saving progress
    for iEntry in tqdm(range(start,reference_tree.GetEntries())):
        if iEntry % 50000 == 0:#this part can be commented if you don't want to save the progress every 50,000 pMSSM points
            outtree.Write()
            outfile.Close()
            outfile = TFile(outdir+args.outname+"_"+str(start)+"_"+str(stop),"recreate")#create the output file
            outtree = TTree(str(args.analysis),str(args.analysis))#create the output tree
            setup_tree(outtree,output_branches)#set up the branches in the output tree
            file_nr+=1
            start=( file_nr-1)*50000
            stop = start+50000
        reference_tree.GetEntry(iEntry)
        id1 = reference_tree.chain_index
        id2 = reference_tree.Niteration
        xsec = reference_tree.xsec_tot_pb #total SUSY cross section in pb
        feff = reference_tree.filter_eff #truth-level filter efficiency
        reset_containers(output_branches)
        #now find the dictionary entry. If it does not exist, fill the OUTPUT TREE with default values
        output_branches["chain_index"]["container"][0] = id1
        output_branches["Niteration"]["container"][0] = id2
        #the two values below are needed to calculate an event weight, which is necessary for any likelihood calculations
        output_branches["xsec"]["container"][0] = xsec
        output_branches["filtereff"]["container"][0] = feff
        if (int(id1),int(id2)) in collect_output.keys():#if point was processed by the analysis, fill the output containers
            for bname, branchdict in output_branches.items():
                if bname in ["Niteration","chain_index"]:continue
                if not "name_2017" in branchdict.keys() and not "name_2018" in branchdict.keys():continue
                if "2017" in collect_output[(int(id1),int(id2))].keys() and branchdict["name_2017"] in collect_output[(int(id1),int(id2))]["2017"].keys():
                    branchdict["container_2017"][0] = max(0,collect_output[(int(id1),int(id2))]["2017"][branchdict["name_2017"]])
                if "2018" in collect_output[(int(id1),int(id2))].keys() and branchdict["name_2018"] in collect_output[(int(id1),int(id2))]["2018"].keys():
                    branchdict["container_2018"][0] = max(0,collect_output[(int(id1),int(id2))]["2018"][branchdict["name_2018"]])
                    
                    
            #fill the output tree
                    
        outtree.Fill()
    outtree.BuildIndex("chain_index","Niteration")# index the tree. The tree index can be used to find individual points in the output tree later, by calling tree.GetEntryWithIndex()
    outtree.Write()
    outfile.Close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s","--scan",default = "/nfs/dust/cms/user/mrowietm/output_pMSSMscan_new/python/GetLikelihoodForpMSSM/pMSSM_points/scan.root",help="Specify the full pMSSM tree to which the output will be a friend tree")
    parser.add_argument("-o","--outdir",help="Specify the output directory",required=True)
    parser.add_argument("-a","--analysis",choices=["cms_sus_19_006"],help="Specify the analysis. A corresponding directory needs to exist from the homepath, which includes the files: __init__.py, output_branches.py, SR_counts.py, ThnSparse_inputs.py",required = True)
    parser.add_argument("-n","--outname",help="give a name for the output file",default = "")
    args=parser.parse_args()

    #

    run(args)
