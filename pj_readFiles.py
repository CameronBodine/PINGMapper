

from common_funcs import *
from c_sonObj import sonObj
from joblib import delayed
import time

#===========================================
def read_master_func(sonFiles, humFile, projDir, tempC, nchunk, wcp, src, detectDep, smthDep):
    '''
    Main script to read data from Humminbird sonar recordings. Scripts have been
    tested on 9xx, 11xx, Helix, Solix and Onyx models but should work with any
    Humminbird model (updated July 2021).

    ----------
    Parameters
    ----------
    sonFiles : str
        DESCRIPTION - Path to .SON file directory associated w/ .DAT file.
        EXAMPLE -     sonFiles = 'C:/PINGMapper/SonarRecordings/R00001'
    humFile : str
        DESCRIPTION - Path to .DAT file associated w/ .SON directory.
        EXAMPLE -     humFile = 'C:/PINGMapper/SonarRecordings/R00001.DAT'
    projDir : str
        DESCRIPTION - Path to output directory.
        EXAMPLE -     projDir = 'C:/PINGMapper/procData/R00001'
    tempC : float
        DESCRIPTION - Water temperature (Celcius) during survey divided by 10.
        EXAMPLE -     tempC = (20/10)
    nchunk : int
        DESCRIPTION - Number of pings per chunk.  Chunk size dictates size of
                      sonar tiles (sonograms).  Most testing has been on chunk
                      sizes of 500 (recommended).
        EXAMPLE -     nchunk = 500
    wcp : bool
        DESCRIPTION - Flag to export non-rectified sonar tiles w/ water column
                      present (wcp).
                      True = export wcp sonar tiles;
                      False = do not export wcp sonar tiles.
        EXAMPLE -     wcp = True
    src : bool
        DESCRIPTION - Flag to export non-rectified sonar tiles w/ water column
                      removed & slant range corrected (src).
                      True = export src sonar tiles;
                      False = do not export src sonar tiles.
        EXAMPLE -     src = True
    detectDep : int
        DESCRIPTION - Determines if depth will be automatically estimated for
                      water column removal.
                      0 = use Humminbird depth;
                      1 = auto pick using binary thresholding;
                      2 = auto pick using machine learning (not implemented).
        EXAMPLE -     detectDep = 0
    smthDep : bool
        DESCRIPTION - Apply Savitzky-Golay filter to depth data.  May help smooth
                      noisy depth estimations.  Recommended if using Humminbird
                      depth to remove water column (detectDep=0).
                      True = smooth depth estimate;
                      False = do not smooth depth estimate.
        EXAMPLE -     smthDep = False

    -------
    Returns
    -------
    Project directory with following structure and outputs, pending parameter
    selection:

    |--projDir
    |
    |--|ds_highfreq (if B001.SON available) [wcp=True]
    |  |--wcp
    |     |--*.PNG : Down-looking sonar (ds) 200 kHz sonar tiles (non-rectified),
    |     |          w/ water column present
    |
    |--|ds_lowfreq (if B000.SON available) [wcp=True]
    |  |--wcp
    |     |--*.PNG : Down-looking sonar (ds) 83 kHz sonar tiles (non-rectified),
    |     |          w/ water column present
    |
    |--|ds_vhighfreq (if B004.SON available) [wcp=True]
    |  |--wcp
    |     |--*.PNG : Down-looking sonar (ds) 1.2 mHz sonar tiles (non-rectified),
    |     |          w/ water column present
    |
    |--|meta
    |  |--B000_ds_lowfreq_meta.csv : Sonar record metadata for B000.SON (if present)
    |  |--B000_ds_lowfreq_meta.meta : Pickled sonObj instance for B000.SON (if present)
    |  |--B001_ds_highfreq_meta.csv : Sonar record metadata for B001.SON (if present)
    |  |--B001_ds_highfreq_meta.meta : Pickled sonObj instance for B001.SON (if present)
    |  |--B002_ss_port_meta.csv : Sonar record metadata for B002.SON (if present)
    |  |--B002_ss_port_meta.meta : Pickled sonObj instance for B002.SON (if present)
    |  |--B003_ss_star_meta.csv : Sonar record metadata for B003.SON (if present)
    |  |--B003_ss_star_meta.meta : Pickled sonObj instance for B003.SON (if present)
    |  |--B004_ds_vhighfreq.csv : Sonar record metadata for B004.SON (if present)
    |  |--B004_ds_vhighfreq.meta : Pickled sonObj instance for B004.SON (if present)
    |  |--DAT_meta.csv : Sonar recording metadata for *.DAT.
    |
    |--|ss_port (if B002.SON OR B003.SON [tranducer flipped] available)
    |  |--src [src=True]
    |     |--*.PNG : Portside side scan (ss) sonar tiles (non-rectified), w/
    |     |          water column removed & slant range corrected (src)
    |  |--wcp [wcp=True]
    |     |--*.PNG : Portside side scan (ss) sonar tiles (non-rectified), w/
    |     |          water column present (wcp)

    |--|ss_star (if B003.SON OR B002.SON [tranducer flipped] available)
    |  |--src [src=True]
    |     |--*.PNG : Starboard side scan (ss) sonar tiles (non-rectified), w/
    |     |          water column removed & slant range corrected (src)
    |  |--wcp [wcp=True]
    |     |--*.PNG : Starboard side scan (ss) sonar tiles (non-rectified), w/
    |     |          water column present (wcp)
    '''

    ####################################
    # Remove project directory if exists
    if os.path.exists(projDir):
        shutil.rmtree(projDir)
    else:
        pass

    ##############################
    # Create the project directory
    try:
        os.mkdir(projDir)
    except:
        pass

    ############################################################################
    # Decode DAT file (varies by model)                                        #
    ############################################################################

    print("\nGetting DAT Metadata...")
    # Create sonObj to store sonar attributes, access processing functions,
    ## and access sonar data.  We will use the first sonar beam to make an
    ## initial sonar object, then create a copy for each beam.
    son = sonObj(sonFiles[0], humFile, projDir, tempC, nchunk)
    son.datLen = os.path.getsize(son.humFile) #Length (in bytes) of .DAT

    # Determine .DAT (humDat) structure
    son._getHumDatStruct()

    # Read in the humdat data
    if son.isOnix == 0:
        son._getHumdat()
    else:
        son._decodeOnix()

    # Determine epsg code and transformation (if we can, ONIX doesn't have
    ## lat/lon in DAT, so will determine at a later processing step).
    son._getEPSG()

    # Save DAT metadata to file (csv)
    metaDir = os.path.join(projDir, 'meta')
    try:
        os.mkdir(metaDir)
    except:
        pass

    son.metaDir = metaDir #Store metadata directory in sonObj
    outFile = os.path.join(metaDir, 'DAT_meta.csv')
    pd.DataFrame.from_dict(son.humDat, orient='index').T.to_csv(outFile, index=False)
    son.datMetaFile = outFile #Store metadata file path in sonObj
    print("Done!")

    #######################################################
    # Try copying sonObj instance for every sonar channel #
    #######################################################

    # Determine which sonar beams are present (B000,B001,..)
    chanAvail = {}
    for s in sonFiles:
        beam = os.path.split(s)[-1].split('.')[0] #Get beam number (B000,B001,..)
        chanAvail[beam] = s

    # Copy the previously created sonObj instance to make a unique sonObj for
    ## each beam.  Then update certain sonObj attributes specific to each beam.
    sonObjs = []
    for chan, file in chanAvail.items():
        if chan == 'B000':
            B000 = deepcopy(son)
            B000.beamName = 'ds_lowfreq' #Update beam name
            B000.outDir = os.path.join(B000.projDir, B000.beamName) #Update output directory
            B000.beam = chan #Update beam number
            B000.sonFile = file #Update sonar file path
            sonObjs.append(B000) #Store in sonObjs list

        elif chan == 'B001':
            B001 = deepcopy(son)
            B001.beamName = 'ds_highfreq' #Update beam name
            B001.outDir = os.path.join(B001.projDir, B001.beamName) #Update output directory
            B001.beam = chan #Update beam number
            B001.sonFile = file #Update sonar file path
            sonObjs.append(B001) #Store in sonObjs list

        elif chan == 'B002':
            B002 = deepcopy(son)
            B002.beamName = 'ss_port' #Update beam name
            B002.outDir = os.path.join(B002.projDir, B002.beamName) #Update output directory
            B002.beam = chan #Update beam number
            B002.sonFile = file #Update sonar file path
            sonObjs.append(B002) #Store in sonObjs list

        elif chan == 'B003':
            B003 = deepcopy(son)
            B003.beamName = 'ss_star' #Update beam name
            B003.outDir = os.path.join(B003.projDir, B003.beamName) #Update output directory
            B003.beam = chan #Update beam number
            B003.sonFile = file #Update sonar file path
            sonObjs.append(B003) #Store in sonObjs list

        elif chan == 'B004':
            B004 = deepcopy(son)
            B004.beamName = 'ds_vhighfreq' #Update beam name
            B004.outDir = os.path.join(B004.projDir, B004.beamName) #Update output directory
            B004.beam = chan #Update beam number
            B004.sonFile = file #Update sonar file path
            sonObjs.append(B004) #Store in sonObjs list

        else:
            pass

    ############################################################################
    # Determine sonar record header length (varies by model)                   #
    ############################################################################

    print("\nGetting Header Structure...")
    cntSON = len(sonObjs) # Number of sonar files
    gotHeader = False # Flag indicating if length of header is found
    i = 0 # Counter for iterating son files
    while gotHeader is False:
        try:
            son = sonObjs[i]
            headbytes = son._cntHead() # Try counting head bytes
            if headbytes > 0: # See if we determined header length
                print("Header Length: {}".format(headbytes))
                gotHeader = True
            else:
                i+=1
        except:
            sys.exit("\n#####\nERROR: Out of SON files... \n"+
            "Unable to determine header length.")

    # Update sonar objects with header length
    if headbytes > 0:
        for son in sonObjs:
            son.headBytes = headbytes

    ############################################################################
    # Get the SON header structure and attributes                              #
    ############################################################################

    # The number of sonar record header bytes indicates the structure and order
    ## of sonar record attributes.  For known structures, the sonar record
    ## header structure will be stored in the sonObj.
    for son in sonObjs:
        son._getHeadStruct()

    # Let's check and make sure the header structure is correct.
    for son in sonObjs:
        son._checkHeadStruct()

    for son in sonObjs:
        headValid = son.headValid # Flag indicating if sonar header structure is known.
        # Sonar record header structure is known!
        if headValid[0] is True:
            print(son.beamName, ":", "Done!")
        # Header byte length is of a known length, but we found an inconsistency
        ## in the sonar record header structure.  Report byte location where
        ## mis-match occured (for debugging purposes), then try to decode automatically.
        elif headValid[0] is False:
            print("\n#####\nERROR: Wrong Header Structure")
            print("Expected {} at index {}.".format(headValid[1], headValid[2]))
            print("Found {} instead.".format(headValid[3]))
            print("Attempting to decode header structure.....")
            son._decodeHeadStruct() # Try to automatically decode.
        # Header structure is completely unknown.  Try to automatically decode.
        else:
            print("\n#####\nERROR: Wrong Header Structure")
            print("Attempting to decode header structure.....")
            son._decodeHeadStruct() # Try to automatically decode.

    # If we had to decode header structure, let's make sure it decoded correctly.
    ## If we are wrong, then we found a completely new Humminbird file format.
    ## Report byte location where mis-match occured (for dubugging purposes),
    ## and terminate the process.  We can't automatically decode this file.
    ## Report to PING Mapper developers.
    for son in sonObjs:
        if son.headValid[0] is not True:
            son._checkHeadStruct()
            headValid = son.headValid
            if headValid[0] is True:
                print("Succesfully determined header structure!")
            else:
                print("\n#####\nERROR:Unable to decode header structure")
                print("Expected {} at index {}.".format(headValid[1], headValid[2]))
                print("Found {} instead.".format(headValid[3]))
                print("Terminating srcipt.")
                sys.exit()

    ########################################
    # Let's get the metadata for each ping #
    ########################################

    # Now that we know the sonar record header structure, let's read that data
    ## and save it to .CSV in the meta directory.
    print("\nGetting SON file header metadata:")
    # Check to see if metadata is already saved to csv.
    toProcess = []
    for son in sonObjs:
        beam = os.path.split(son.sonFile)[-1].split(".")[0]
        file = os.path.join(son.metaDir, beam+"_meta.csv")
        if os.path.exists(file):
            print("File {0} exists. No need to re-process.".format(file))
            son.sonMetaFile = file
        else:
            toProcess.append(son)

    for son in sonObjs:
        idxFile = son.sonFile.replace(".SON", ".IDX")
        if os.path.exists(idxFile):
            son.sonIdxFile = idxFile
        else:
            son.sonIdxFile = "NA"

    # Get metadata for each beam in parallel.
    if len(toProcess) > 0:
        Parallel(n_jobs= np.min([len(toProcess), cpu_count()]), verbose=10)(delayed(son._getSonMeta)() for son in toProcess)

    metaDir = sonObjs[0].metaDir
    sonMeta = sorted(glob(os.path.join(metaDir,'*B*_meta.csv')))
    for i in range(0,len(sonObjs)):
        sonObjs[i].sonMetaFile = sonMeta[i] # Store meta file path in sonObj

    # Store flag to export un-rectified sonar tiles in each sonObj.
    for son in sonObjs:
        son.wcp = wcp
        son.src = src
        try:
            os.mkdir(son.outDir)
        except:
            pass

    print("Done!")

    ############################################################################
    # Export un-rectified sonar tiles                                          #
    ############################################################################

    if wcp or src:
        print("\nGetting sonar data and exporting tile images:")
        # Export sonar tiles for each beam.
        Parallel(n_jobs= np.min([len(sonObjs), cpu_count()]), verbose=10)(delayed(son._getScansChunk)(detectDep, smthDep) for son in sonObjs)

    ##############################################
    # Let's pickle sonObj so we can reload later #
    ##############################################

    for son in sonObjs:
        outFile = son.sonMetaFile.replace(".csv", ".meta")
        son.sonMetaPickle = outFile
        with open(outFile, 'wb') as sonFile:
            pickle.dump(son, sonFile)

    # for son in sonObjs:
    #     print("\n\n", son)

    # print(round((time.time() - start_time),ndigits=2))
