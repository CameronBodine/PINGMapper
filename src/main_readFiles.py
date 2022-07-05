# Part of PING-Mapper software
#
# Co-Developed by Cameron S. Bodine and Dr. Daniel Buscombe
#
# Inspired by PyHum: https://github.com/dbuscombe-usgs/PyHum
#
# MIT License
#
# Copyright (c) 2022 Cameron S. Bodine
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from funcs_common import *
from class_sonObj import sonObj
from class_portstarObj import portstarObj

#===========================================
def read_master_func(sonFiles,
                     humFile,
                     projDir,
                     tempC=10,
                     nchunk=500,
                     exportUnknown=False,
                     wcp=False,
                     wcr=False,
                     detectDep=0,
                     smthDep=False,
                     adjDep=0,
                     pltBedPick=False,
                     threadCnt=0):
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
    tempC : float : [Default=10]
        DESCRIPTION - Water temperature (Celcius) during survey.
        EXAMPLE -     tempC = 10
    nchunk : int : [Default=500]
        DESCRIPTION - Number of pings per chunk.  Chunk size dictates size of
                      sonar tiles (sonograms).  Most testing has been on chunk
                      sizes of 500 (recommended).
        EXAMPLE -     nchunk = 500
    exportUnknown : bool [Default=False]
        DESCRIPTION - Flag indicating if unknown attributes in ping
                      should be exported or not.  If a user of PING Mapper
                      determines what an unkown attribute actually is, please
                      report using a github issue.
        EXAMPLE -     exportUnknown = False
    wcp : bool : [Default=False]
        DESCRIPTION - Flag to export non-rectified sonar tiles w/ water column
                      present (wcp).
                      True = export wcp sonar tiles;
                      False = do not export wcp sonar tiles.
        EXAMPLE -     wcp = True
    wcr : bool : [Default=False]
        DESCRIPTION - Flag to export non-rectified sonar tiles w/ water column
                      removed (wcr).
                      True = export wcr sonar tiles;
                      False = do not export wcr sonar tiles.
        EXAMPLE -     wcr = True
    detectDep : int : [Default=0]
        DESCRIPTION - Determines if depth will be automatically estimated for
                      water column removal.
                      0 = use Humminbird depth;
                      1 = auto pick using Zheng et al. 2021;
                      2 = auto pick using binary thresholding.
       EXAMPLE -     detectDep = 0
    smthDep : bool : [Default=False]
        DESCRIPTION - Apply Savitzky-Golay filter to depth data.  May help smooth
                      noisy depth estimations.  Recommended if using Humminbird
                      depth to remove water column (detectDep=0).
                      True = smooth depth estimate;
                      False = do not smooth depth estimate.
        EXAMPLE -     smthDep = False
    adjDep : int : [Default=0]
        DESCRIPTION - Specify additional depth adjustment (in pixels) for water
                      column removal.  Does not affect the depth estimate stored
                      in exported metadata *.CSV files.
                      Integer > 0 = increase depth estimate by x pixels.
                      Integer < 0 = decrease depth estimate by x pixels.
                      0 = use depth estimate with no adjustment.
        EXAMPLE -     adjDep = 5
    pltBedPick : bool : [Default=False]
        DESCRIPTION - Plot bedpick(s) on non-rectified sonogram for visual
                      inspection.
                      True = plot bedpick(s);
                      False = do not plot bedpick(s).
        EXAMPLE -     pltBedPick = True
    threadCnt : int : [Default=0]
        DESCRIPTION - The maximum number of threads to use during multithreaded
                      processing. More threads==faster data export.
                      0 = Use all available threads;
                      <0 = Negative values will be subtracted from total available
                        threads. i.e., -2 -> Total threads (8) - 2 == 6 threads.
                      >0 = Number of threads to use, up to total available threads.
        EXAMPLE -     threadCnt = 0

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
    |  |--B000_ds_lowfreq_meta.csv : ping metadata for B000.SON (if present)
    |  |--B000_ds_lowfreq_meta.meta : Pickled sonObj instance for B000.SON (if present)
    |  |--B001_ds_highfreq_meta.csv : ping metadata for B001.SON (if present)
    |  |--B001_ds_highfreq_meta.meta : Pickled sonObj instance for B001.SON (if present)
    |  |--B002_ss_port_meta.csv : ping metadata for B002.SON (if present)
    |  |--B002_ss_port_meta.meta : Pickled sonObj instance for B002.SON (if present)
    |  |--B003_ss_star_meta.csv : ping metadata for B003.SON (if present)
    |  |--B003_ss_star_meta.meta : Pickled sonObj instance for B003.SON (if present)
    |  |--B004_ds_vhighfreq.csv : ping metadata for B004.SON (if present)
    |  |--B004_ds_vhighfreq.meta : Pickled sonObj instance for B004.SON (if present)
    |  |--DAT_meta.csv : Sonar recording metadata for *.DAT.
    |
    |--|ss_port (if B002.SON OR B003.SON [tranducer flipped] available)
    |  |--wcr [wxr=True]
    |     |--*.PNG : Portside side scan (ss) sonar tiles (non-rectified), w/
    |     |          water column removed (wcr) & slant range corrected
    |  |--wcp [wcp=True]
    |     |--*.PNG : Portside side scan (ss) sonar tiles (non-rectified), w/
    |     |          water column present (wcp)

    |--|ss_star (if B003.SON OR B002.SON [tranducer flipped] available)
    |  |--wcr [wcr=True]
    |     |--*.PNG : Starboard side scan (ss) sonar tiles (non-rectified), w/
    |     |          water column removed (wcr) & slant range corrected
    |  |--wcp [wcp=True]
    |     |--*.PNG : Starboard side scan (ss) sonar tiles (non-rectified), w/
    |     |          water column present (wcp)
    '''
    USE_GPU = False

    # Specify multithreaded processing thread count
    if threadCnt==0: # Use all threads
        threadCnt=cpu_count()
    elif threadCnt<0: # Use all threads except threadCnt; i.e., (cpu_count + (-threadCnt))
        threadCnt=cpu_count()+threadCnt
        if threadCnt<0: # Make sure not negative
            threadCnt=1
    else: # Use specified threadCnt if positive
        pass

    if threadCnt>cpu_count(): # If more than total avail. threads, make cpu_count()
        threadCnt=cpu_count();
        print("\nWARNING: Specified more process threads then available, \nusing {} threads instead.".format(threadCnt))

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

    start_time = time.time()
    print("\nGetting DAT Metadata...")
    # Create sonObj to store sonar attributes, access processing functions,
    ## and access sonar data.  We will use the first sonar beam to make an
    ## initial sonar object, then create a copy for each beam.
    tempC = float(tempC)/10 # Divide temperature by 10
    son = sonObj(sonFiles[0], humFile, projDir, tempC, nchunk) # Initialize sonObj instance from first sonar beam
    son.datLen = os.path.getsize(son.humFile) #Length (in bytes) of .DAT

    # Determine .DAT (humDat) structure
    son._getHumDatStruct()

    # Read in the humdat data
    if son.isOnix == 0:
        son._getHumdat()

        # Determine epsg code and transformation (if we can, ONIX doesn't have
        ## lat/lon in DAT, so will determine at a later processing step).
        son._getEPSG()
    else:
        son._decodeOnix()

    # Create 'meta' directory if it doesn't exist
    metaDir = os.path.join(projDir, 'meta')
    try:
        os.mkdir(metaDir)
    except:
        pass
    son.metaDir = metaDir #Store metadata directory in sonObj

    # Save DAT metadata to file (csv)
    outFile = os.path.join(metaDir, 'DAT_meta.csv') # Specify file directory & name
    pd.DataFrame.from_dict(son.humDat, orient='index').T.to_csv(outFile, index=False) # Export DAT df to csv
    son.datMetaFile = outFile # Store metadata file path in sonObj
    print("Done!")
    print("Time (s):", round(time.time() - start_time, ndigits=1))

    #######################################################
    # Try copying sonObj instance for every sonar channel #
    #######################################################

    # Determine which sonar beams are present (B000,B001,..)
    chanAvail = {}
    for s in sonFiles:
        beam = os.path.split(s)[-1].split('.')[0] #Get beam number (B000,B001,..)
        chanAvail[beam] = s

    # Copy the previously created sonObj instance to make a unique sonObj for
    ## each beam.  Then update sonObj attributes specific to each beam.
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
    # Determine ping header length (varies by model)                   #
    ############################################################################

    start_time = time.time()
    print("\nGetting Header Structure...")
    cntSON = len(sonObjs) # Number of sonar files
    gotHeader = False # Flag indicating if length of header is found
    i = 0 # Counter for iterating son files
    while gotHeader is False: # Iterate each sonObj until header length determined
        try:
            son = sonObjs[i] # Get current sonObj
            headbytes = son._cntHead() # Try counting head bytes
            # Determine if header length was determined
            if headbytes > 0: # Header length found
                print("Header Length: {}".format(headbytes))
                gotHeader = True
            else: # Header length not found, iterate i to load next sonObj
                i+=1
        # Terminate program if header length not determined
        except:
            sys.exit("\n#####\nERROR: Out of SON files... \n"+
            "Unable to determine header length.")

    # Update each sonObj with header length
    if headbytes > 0:
        for son in sonObjs:
            son.headBytes = headbytes

    ############################################################################
    # Get the SON header structure and attributes                              #
    ############################################################################

    # The number of ping header bytes indicates the structure and order
    ## of ping attributes.  For known structures, the ping
    ## header structure will be stored in the sonObj.
    for son in sonObjs:
        son._getHeadStruct(exportUnknown)

    # Let's check and make sure the header structure is correct.
    for son in sonObjs:
        son._checkHeadStruct()

    for son in sonObjs:
        headValid = son.headValid # Flag indicating if sonar header structure is known.
        # ping header structure is known!
        if headValid[0] is True:
            print(son.beamName, ":", "Done!")
        # Header byte length is of a known length, but we found an inconsistency
        ## in the ping header structure.  Report byte location where
        ## mis-match occured (for debugging purposes), then try to decode automatically.
        elif headValid[0] is False:
            print("\n#####\nERROR: Wrong Header Structure")
            print("Expected {} at index {}.".format(headValid[1], headValid[2]))
            print("Found {} instead.".format(headValid[3]))
            print("Attempting to decode header structure.....")
            son._decodeHeadStruct(exportUnknown) # Try to automatically decode.
        # Header structure is completely unknown.  Try to automatically decode.
        else:
            print("\n#####\nERROR: Wrong Header Structure")
            print("Attempting to decode header structure.....")
            son._decodeHeadStruct(exportUnknown) # Try to automatically decode.

    # If we had to decode header structure, let's make sure it decoded correctly.
    ## If we are wrong, then we found a completely new Humminbird file format.
    ## Report byte location where mis-match occured (for dubugging purposes),
    ## and terminate the process.  We can't automatically decode this file.
    ## Please report to PING Mapper developers.
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

    print("Time (s):", round(time.time() - start_time, ndigits=1))
    ########################################
    # Let's get the metadata for each ping #
    ########################################

    start_time = time.time()
    # Now that we know the ping header structure, let's read that data
    ## and save it to .CSV in the meta directory.
    print("\nGetting SON file header metadata...")
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

    # See if .IDX file is available.  If it is, store file path for later use.
    for son in sonObjs:
        idxFile = son.sonFile.replace(".SON", ".IDX")
        if os.path.exists(idxFile):
            son.sonIdxFile = idxFile
        else:
            son.sonIdxFile = False

    # Get metadata for each beam in parallel.
    if len(toProcess) > 0:
        Parallel(n_jobs= np.min([len(toProcess), threadCnt]), verbose=10)(delayed(son._getSonMeta)() for son in toProcess)

    metaDir = sonObjs[0].metaDir # Get path to metadata directory
    sonMeta = sorted(glob(os.path.join(metaDir,'*B*_meta.csv'))) # Get path to metadata files
    for i in range(0,len(sonObjs)): # Iterate each metadata file
        sonObjs[i].sonMetaFile = sonMeta[i] # Store meta file path in sonObj

    # Store flag to export un-rectified sonar tiles in each sonObj.
    for son in sonObjs:
        son.wcp = wcp
        son.wcr_src = wcr

    # If Onix, need to store self._trans in object
    if sonObjs[0].isOnix:
        for son in sonObjs:
            son._loadSonMeta()
            utm_e=son.sonMetaDF.iloc[0]['utm_e']
            utm_n=son.sonMetaDF.iloc[0]['utm_n']
            son._getEPSG(utm_e, utm_n)


    ############################################################################
    # Print Metadata Summary                                                   #
    ############################################################################
    # Print a summary of min/max/avg metadata values. At same time, do simple
    ## check to make sure data are valid.
    print("\nSummary of Ping Metadata:\n")

    invalid = defaultdict() # store invalid values

    for son in sonObjs: # Iterate each sonar object
        print(son.beam, ":", son.beamName)
        print("______________________________________________________________________________")
        print("{:<15s} | {:<15s} | {:<15s} | {:<15s} | {:<5s}".format("Attribute", "Minimum", "Maximum", "Average", "Valid"))
        print("______________________________________________________________________________")
        son._loadSonMeta()
        df = son.sonMetaDF
        for att in df.columns: # Find min/max/avg of each column
            attMin = np.round(df[att].min(), 3)
            attMax = np.round(df[att].max(), 3)
            attAvg = np.round(df[att].mean(), 3)

            # Check if data are valid.
            if (attMax != 0) or ("unknown" in att) or (att =="beam"):
                valid=True
            elif (att == "inst_dep_m") and (attAvg == 0): # Automatically detect depth if no instrument depth
                valid=False
                invalid[son.beam+"."+att] = False
                detectDep=1
            else:
                valid=False
                invalid[son.beam+"."+att] = False

            print("{:<15s} | {:<15s} | {:<15s} | {:<15s} | {:<5s}".format(att, str(attMin), str(attMax), str(attAvg), str(valid)))

        print("\n")

    if len(invalid) > 0:
        print("*******************************\n****WARNING: INVALID VALUES****\n*******************************")
        print("_______________________________")
        print("{:<15s} | {:<15s}".format("Sonar Channel", "Attribute"))
        print("_______________________________")
        for key, val in invalid.items():
            print("{:<15s} | {:<15s}".format(key.split(".")[0], key.split(".")[1]))
        print("\n*******************************\n****WARNING: INVALID VALUES****\n*******************************")
        print("\nPING-Mapper detected issues with\nthe values stored in the above\nsonar channels and attributes.")



    print("\nDone!")
    print("Time (s):", round(time.time() - start_time, ndigits=1))

    ############################################################################
    # For Depth Detection                                                      #
    ############################################################################
    start_time = time.time()
    # Determine which sonObj is port/star
    portstar = []
    for son in sonObjs:
        beam = son.beamName
        if beam == "ss_port" or beam == "ss_star":
            portstar.append(son)

    # Create portstarObj
    psObj = portstarObj(portstar)

    # Load one beam's sonar metadata
    portstar[0]._loadSonMeta()
    sonMetaDF = portstar[0].sonMetaDF

    # Determine what chunks to process
    chunks = pd.unique(sonMetaDF['chunk_id']).astype('int') # Store chunk values in list
    del sonMetaDF, portstar[0].sonMetaDF

    # DISABLED: automatic depth detection disabled for now. Will return stronger
    # and better in the future!!!

    # # Automatically estimate depth
    if detectDep > 0:
        print('\n\nAutomatically estimating depth for', len(chunks), 'chunks:')

        #Dictionary to store chunk : np.array(depth estimate)
        psObj.portDepDetect = {}
        psObj.starDepDetect = {}

        # Estimate depth using:
        # Zheng et al. 2021
        if detectDep == 1:
            psObj.weights = r'./models/bedpick/Zheng2021/bedpick_ZhengApproach_20220629.h5'
            psObj.configfile = psObj.weights.replace('.h5', '.json')
            print('\n\tUsing Zheng et al. 2021 method. Loading model:', os.path.basename(psObj.weights))
            # psObj._initModel(USE_GPU)

        # With binary thresholding
        elif detectDep == 2:
            print('\n\tUsing binary thresholding...')

        # # Sequential estimate depth for each chunk using appropriate method
        # chunks = [chunks[108]]
        # # chunks = chunks[107:110]
        # # chunks = [chunks[30]]
        # # chunks = [chunks[282], chunks[332], chunks[383]]
        # for chunk in chunks:
        #     r = psObj._detectDepth(detectDep, int(chunk), USE_GPU)
        #     psObj.portDepDetect[r[2]] = r[0]
        #     psObj.starDepDetect[r[2]] = r[1]
        # sys.exit()

        # Parallel estimate depth for each chunk using appropriate method
        r = Parallel(n_jobs=np.min([len(chunks), cpu_count()]), verbose=10)(delayed(psObj._detectDepth)(detectDep, int(chunk), USE_GPU) for chunk in chunks)

        # store the depth predictions in the class
        for ret in r:
            psObj.portDepDetect[ret[2]] = ret[0]
            psObj.starDepDetect[ret[2]] = ret[1]

        # Flag indicating depth autmatically estimated
        autoBed = True
        # Cleanup
        psObj._cleanup()

    else:
        print('\n\nUsing instrument depth:')
        autoBed = False

    # Save detected depth to csv
    psObj._saveDepth(chunks, detectDep, smthDep, adjDep)
    print("Done!")
    print("Time (s):", round(time.time() - start_time, ndigits=1))

    # Plot sonar depth and auto depth estimate (if available) on sonogram
    if pltBedPick:
        start_time = time.time()

        print("\n\nExporting bedpick plots...")
        Parallel(n_jobs=np.min([len(chunks), threadCnt]), verbose=10)(delayed(psObj._plotBedPick)(int(chunk), True, autoBed) for chunk in chunks)

        print("Done!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))

    # Cleanup
    psObj._cleanup()
    del psObj, chunks

    ############################################################################
    # Export un-rectified sonar tiles                                          #
    ############################################################################

    if wcp or wcr:
        start_time = time.time()
        print("\nExporting sonogram tiles:\n")
        for son in sonObjs:
            if son.beamName == 'ss_port' or son.beamName == 'ss_star':
                son._loadSonMeta()
                sonMetaDF = son.sonMetaDF

                # Determine what chunks to process
                chunks = pd.unique(sonMetaDF['chunk_id']).astype('int')
                if son.wcr_src and son.wcp and (son.beamName=='ss_port' or son.beamName=='ss_star'):
                    chunkCnt = len(chunks)*2
                else:
                    chunkCnt = len(chunks)
                print('\n\tExporting', chunkCnt, 'sonograms for', son.beamName)

                # Parallel(n_jobs= np.min([len(chunks), cpu_count()]), verbose=10)(delayed(son._exportTiles)(i) for i in chunks)
                Parallel(n_jobs= np.min([len(chunks), threadCnt]), verbose=10)(delayed(son._exportTiles)(i) for i in chunks)
        print("Done!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))


    ############################################################################
    # Export water column removed and cropped tiles for substrate train set    #
    ############################################################################
    wcr_crop = True
    if wcr_crop:
        start_time = time.time()
        print("\n\n\nWARNING: Exporting substrate training tiles:\n")
        for son in sonObjs:
            son.wcr_crop = wcr_crop
            son.wcr_src = False
            son.wcp = False
            if son.beamName == 'ss_port' or son.beamName == 'ss_star':
                son._loadSonMeta()
                sonMetaDF = son.sonMetaDF

                # Determine what chunks to process
                chunks = pd.unique(sonMetaDF['chunk_id']).astype('int')

                Parallel(n_jobs= np.min([len(chunks), threadCnt]), verbose=10)(delayed(son._exportTiles)(i) for i in chunks)

                son.wcr_src = True
                son.wcp = True

        print("Done!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))


    ##############################################
    # Let's pickle sonObj so we can reload later #
    ##############################################

    for son in sonObjs:
        outFile = son.sonMetaFile.replace(".csv", ".meta")
        son.sonMetaPickle = outFile
        with open(outFile, 'wb') as sonFile:
            pickle.dump(son, sonFile)
