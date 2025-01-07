# Part of PING-Mapper software
#
# Co-Developed by Cameron S. Bodine and Dr. Daniel Buscombe
#
# Inspired by PyHum: https://github.com/dbuscombe-usgs/PyHum
#
# MIT License
#
# Copyright (c) 2022-23 Cameron S. Bodine
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

import os, sys

# Add 'pingmapper' to the path, may not need after pypi package...
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.append(PACKAGE_DIR)

from pingmapper.funcs_common import *
from pingmapper.class_sonObj import sonObj
from pingmapper.class_portstarObj import portstarObj
import shutil
from doodleverse_utils.imports import *

# sys.path.insert(0, r'C:\Users\cbodine\PythonRepos\PINGVerter')

from pingverter import hum2pingmapper, low2pingmapper


#===========================================
def read_master_func(logfilename='',
                     project_mode=0,
                     script='',
                     inFile='',
                     sonFiles='',
                     projDir='',
                     coverage=False,
                     aoi=False,
                     max_heading_deviation = False,
                     max_heading_distance = False,
                     min_speed = False,
                     max_speed = False,
                     tempC=10,
                     nchunk=500,
                     cropRange=0,
                     exportUnknown=False,
                     fixNoDat=False,
                     threadCnt=0,
                     pix_res_son=0,
                     pix_res_map=0,
                     x_offset=0,
                     y_offset=0,
                     tileFile=False,
                     egn=False,
                     egn_stretch=0,
                     egn_stretch_factor=1,
                     wcp=False,
                     wcr=False,
                     lbl_set=False,
                     spdCor=0,
                     maxCrop=False,
                     USE_GPU=False,
                     remShadow=0,
                     detectDep=0,
                     smthDep=0,
                     adjDep=0,
                     pltBedPick=False,
                     cog=True,
                     rect_wcp=False,
                     rect_wcr=False,
                     son_colorMap='Greys',
                     pred_sub=0,
                     map_sub=0,
                     export_poly=False,
                     map_predict=0,
                     pltSubClass=False,
                     map_class_method='max',
                     mosaic_nchunk=50,
                     mosaic=False,
                     map_mosaic=0,
                     banklines=False):

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


    #####################################
    # Download models if they don't exist
    # modelDir = "./models/PINGMapperv2.0_SegmentationModelsv1.0"
    modelDir = os.path.join(SCRIPT_DIR, 'models', 'PINGMapperv2.0_SegmentationModelsv1.0')
    modelDir = os.path.normpath(modelDir)
    if not os.path.exists(modelDir):
        downloadSegmentationModelsv1_0(modelDir)
        getSegformer = True
    else:
        getSegformer = False

    ###############
    # Get segformer
    if getSegformer:
        NCLASSES = 8
        id2label = {}
        for k in range(NCLASSES):
            id2label[k] = str(k)
        
        # try downloading segformer pretrained model
        try:
            _ = segformer(id2label, NCLASSES)
        except:
            print('\n\n\n\n')
            print('ERROR! Unable to download pretrained SegFormer model!')
            print('Your network settings are blocking the download.')
            print('Please try running on a different network.')
            print('Once the script has been run successfully, you should be able')
            print('to run PING-Mapper on the current network.')


    ###############################################
    # Specify multithreaded processing thread count
    if threadCnt==0: # Use all threads
        threadCnt=cpu_count()
    elif threadCnt<0: # Use all threads except threadCnt; i.e., (cpu_count + (-threadCnt))
        threadCnt=cpu_count()+threadCnt
        if threadCnt<0: # Make sure not negative
            threadCnt=1
    elif threadCnt<1: # Use proportion of available threads
        threadCnt = int(cpu_count()*threadCnt)
        # Make even number
        if threadCnt % 2 == 1:
            threadCnt -= 1
    else: # Use specified threadCnt if positive
        pass

    if threadCnt>cpu_count(): # If more than total avail. threads, make cpu_count()
        threadCnt=cpu_count();
        print("\nWARNING: Specified more process threads then available, \nusing {} threads instead.".format(threadCnt))


    #######################################
    # Use PINGVerter to read the sonar file
    #######################################

    start_time = time.time()
    # Determine sonar recording type
    _, file_type = os.path.splitext(inFile)

    # Prepare Humminbird file for PINGMapper
    if file_type == '.DAT':
        sonar_obj = hum2pingmapper(inFile, projDir, nchunk, tempC, exportUnknown)

    # Prepare Lowrance file for PINGMapper    
    elif file_type == '.sl2' or file_type == '.sl3':
        sonar_obj = low2pingmapper(inFile, projDir, nchunk, tempC, exportUnknown)

    ####################
    # Create son objects
    ####################

    # Get available beams and metadata
    beamMeta = sonar_obj.beamMeta

    # Create son objects
    sonObjs = []
    for beam, meta in beamMeta.items():

        # Create the sonObj
        son = sonObj(meta['sonFile'], sonar_obj.humFile, projDir, sonar_obj.tempC, sonar_obj.nchunk)

        son.flip_port = False
        if beam == 'B002':
            if file_type == '.sl2' or file_type == '.sl3':
                son.flip_port = True

        # Store other parameters as attributes
        son.fixNotDat = fixNoDat
        son.metaDir = sonar_obj.metaDir
        son.beamName = meta['beamName']
        son.beam = beam
        son.headBytes = sonar_obj.headBytes
        son.pixM = sonar_obj.pixM
        son.isOnix = sonar_obj.isOnix
        son.trans = sonar_obj.trans
        son.humDat = sonar_obj.humDat

        if pix_res_son == 0:
            son.pix_res_son = son.pixM
        else:
            son.pix_res_son = pix_res_son
        if pix_res_map == 0:
            son.pix_res_map = son.pixM
        else:
            son.pix_res_map = pix_res_map

        son.sonMetaFile = meta['metaCSV']

        sonObjs.append(son)

    ####
    # OLD    

    ############################################################################
    # Decode DAT file (varies by model)                                        #
    ############################################################################

    if (project_mode != 2):
        # printUsage()
        # start_time = time.time()
        # print("\nGetting DAT Metadata...")
        # print(humFile)
        # # Create sonObj to store sonar attributes, access processing functions,
        # ## and access sonar data.  We will use the first sonar beam to make an
        # ## initial sonar object, then create a copy for each beam.
        # tempC = float(tempC)/10 # Divide temperature by 10

        # # cog = False
        # # if not cog:
        # #     nchunk= 1

        # son = sonObj(sonFiles[0], humFile, projDir, tempC, nchunk) # Initialize sonObj instance from first sonar beam

        # #######################################
        # # Store needed parameters as attributes
        # # son.pix_res_factor = pix_res_factor
        # son.fixNoDat = fixNoDat


        # son.datLen = os.path.getsize(son.humFile) #Length (in bytes) of .DAT

        # # Determine .DAT (humDat) structure
        # son._getHumDatStruct()

        # # Read in the humdat data
        # if son.isOnix == 0:
        #     son._getHumdat()

        #     # Determine epsg code and transformation (if we can, ONIX doesn't have
        #     ## lat/lon in DAT, so will determine at a later processing step).
        #     son._getEPSG()
        # else:
        #     son._decodeOnix()

        # # Create 'meta' directory if it doesn't exist
        # metaDir = os.path.join(projDir, 'meta')
        # try:
        #     os.mkdir(metaDir)
        # except:
        #     pass
        # son.metaDir = metaDir #Store metadata directory in sonObj

        # # Save main script to metaDir
        # scriptDir = os.path.join(os.path.dirname(logfilename), 'processing_scripts')
        # if not os.path.exists(scriptDir):
        #     os.mkdir(scriptDir)
        # outScript = os.path.join(scriptDir, script[1])
        # shutil.copy(script[0], outScript)

        # # Save DAT metadata to file (csv)
        # outFile = os.path.join(metaDir, 'DAT_meta.csv') # Specify file directory & name
        # pd.DataFrame.from_dict(son.humDat, orient='index').T.to_csv(outFile, index=False) # Export DAT df to csv
        # son.datMetaFile = outFile # Store metadata file path in sonObj
        # del outFile


        # # Cleanup
        # son._cleanup()

        # print("\nDone!")
        # print("Time (s):", round(time.time() - start_time, ndigits=1))
        # printUsage()

        #######################################################
        # Try copying sonObj instance for every sonar channel #
        #######################################################

        # # Determine which sonar beams are present (B000,B001,..)
        # chanAvail = {}
        # for s in sonFiles:
        #     beam = os.path.split(s)[-1].split('.')[0] #Get beam number (B000,B001,..)
        #     chanAvail[beam] = s
        # del s, beam

        # # Copy the previously created sonObj instance to make a unique sonObj for
        # ## each beam.  Then update sonObj attributes specific to each beam.
        # sonObjs = []
        # for chan, file in chanAvail.items():
        #     if chan == 'B000':
        #         B000 = deepcopy(son)
        #         B000.beamName = 'ds_lowfreq' #Update beam name
        #         B000.outDir = os.path.join(B000.projDir, B000.beamName) #Update output directory
        #         B000.beam = chan #Update beam number
        #         B000.sonFile = file #Update sonar file path
        #         sonObjs.append(B000) #Store in sonObjs list

        #     elif chan == 'B001':
        #         B001 = deepcopy(son)
        #         B001.beamName = 'ds_highfreq' #Update beam name
        #         B001.outDir = os.path.join(B001.projDir, B001.beamName) #Update output directory
        #         B001.beam = chan #Update beam number
        #         B001.sonFile = file #Update sonar file path
        #         sonObjs.append(B001) #Store in sonObjs list

        #     elif chan == 'B002':
        #         B002 = deepcopy(son)
        #         B002.beamName = 'ss_port' #Update beam name
        #         B002.outDir = os.path.join(B002.projDir, B002.beamName) #Update output directory
        #         B002.beam = chan #Update beam number
        #         B002.sonFile = file #Update sonar file path
        #         sonObjs.append(B002) #Store in sonObjs list

        #     elif chan == 'B003':
        #         B003 = deepcopy(son)
        #         B003.beamName = 'ss_star' #Update beam name
        #         B003.outDir = os.path.join(B003.projDir, B003.beamName) #Update output directory
        #         B003.beam = chan #Update beam number
        #         B003.sonFile = file #Update sonar file path
        #         sonObjs.append(B003) #Store in sonObjs list

        #     elif chan == 'B004':
        #         B004 = deepcopy(son)
        #         B004.beamName = 'ds_vhighfreq' #Update beam name
        #         B004.outDir = os.path.join(B004.projDir, B004.beamName) #Update output directory
        #         B004.beam = chan #Update beam number
        #         B004.sonFile = file #Update sonar file path
        #         sonObjs.append(B004) #Store in sonObjs list

        #     else:
        #         pass

        # del chanAvail, chan, file

        ############################################################################
        # Determine ping header length (varies by model)                           #
        ############################################################################

        # start_time = time.time()
        # print("\nGetting Header Structure...")
        # cntSON = len(sonObjs) # Number of sonar files
        # gotHeader = False # Flag indicating if length of header is found
        # i = 0 # Counter for iterating son files
        # while gotHeader is False: # Iterate each sonObj until header length determined
        #     try:
        #         son = sonObjs[i] # Get current sonObj
        #         headbytes = son._cntHead() # Try counting head bytes
        #         # Determine if header length was determined
        #         if headbytes > 0: # Header length found
        #             print("Header Length: {}".format(headbytes))
        #             gotHeader = True
        #         else: # Header length not found, iterate i to load next sonObj
        #             i+=1
        #     # Terminate program if header length not determined
        #     except:
        #         sys.exit("\n#####\nERROR: Out of SON files... \n"+
        #         "Unable to determine header length.")
        # del i, gotHeader, cntSON

        # # Update each sonObj with header length
        # if headbytes > 0:
        #     for son in sonObjs:
        #         son.headBytes = headbytes

        # # Cleanup
        # del son, headbytes

        ############################################################################
        # Get the SON header structure and attributes                              #
        ############################################################################

        # # The number of ping header bytes indicates the structure and order
        # ## of ping attributes.  For known structures, the ping
        # ## header structure will be stored in the sonObj.
        # for son in sonObjs:
        #     son._getHeadStruct(exportUnknown)
        # del son

        # # Let's check and make sure the header structure is correct.
        # for son in sonObjs:
        #     son._checkHeadStruct()
        # del son

        # for son in sonObjs:
        #     headValid = son.headValid # Flag indicating if sonar header structure is known.
        #     # ping header structure is known!
        #     if headValid[0] is True:
        #         print(son.beamName, ":", "Done!")
        #     # Header byte length is of a known length, but we found an inconsistency
        #     ## in the ping header structure.  Report byte location where
        #     ## mis-match occured (for debugging purposes), then try to decode automatically.
        #     elif headValid[0] is False:
        #         print("\n#####\nERROR: Wrong Header Structure")
        #         print("Expected {} at index {}.".format(headValid[1], headValid[2]))
        #         print("Found {} instead.".format(headValid[3]))
        #         print("Attempting to decode header structure.....")
        #         son._decodeHeadStruct(exportUnknown) # Try to automatically decode.
        #     # Header structure is completely unknown.  Try to automatically decode.
        #     else:
        #         print("\n#####\nERROR: Wrong Header Structure")
        #         print("Attempting to decode header structure.....")
        #         son._decodeHeadStruct(exportUnknown) # Try to automatically decode.
        # del son, headValid

        # # If we had to decode header structure, let's make sure it decoded correctly.
        # ## If we are wrong, then we found a completely new Humminbird file format.
        # ## Report byte location where mis-match occured (for dubugging purposes),
        # ## and terminate the process.  We can't automatically decode this file.
        # ## Please report to PING Mapper developers.
        # for son in sonObjs:
        #     if son.headValid[0] is not True:
        #         son._checkHeadStruct()
        #         headValid = son.headValid
        #         if headValid[0] is True:
        #             print("Succesfully determined header structure!")
        #         else:
        #             print("\n#####\nERROR:Unable to decode header structure")
        #             print("Expected {} at index {}.".format(headValid[1], headValid[2]))
        #             print("Found {} instead.".format(headValid[3]))
        #             print("Terminating srcipt.")
        #             sys.exit()
        # del son

        # print("Time (s):", round(time.time() - start_time, ndigits=1))
        # printUsage()

        ########################################
        # Let's get the metadata for each ping #
        ########################################

        # start_time = time.time()
        # # Now that we know the ping header structure, let's read that data
        # ## and save it to .CSV in the meta directory.
        # print("\nGetting SON file header metadata...")
        # # Check to see if metadata is already saved to csv.
        # toProcess = []
        # for son in sonObjs:
        #     beam = os.path.split(son.sonFile)[-1].split(".")[0]
        #     file = os.path.join(son.metaDir, beam+"_meta.csv")
        #     if os.path.exists(file):
        #         print("File {0} exists. No need to re-process.".format(file))
        #         son.sonMetaFile = file
        #     else:
        #         toProcess.append(son)
        # del son, file

        # # See if .IDX file is available.  If it is, store file path for later use.
        # for son in sonObjs:
        #     idxFile = son.sonFile.replace(".SON", ".IDX")
        #     if os.path.exists(idxFile):
        #         son.sonIdxFile = idxFile
        #     else:
        #         son.sonIdxFile = False
        # del son, idxFile

        # # Get metadata for each beam in parallel.
        # if len(toProcess) > 0:
        #     r = Parallel(n_jobs= np.min([len(toProcess), threadCnt]), verbose=10)(delayed(son._getSonMeta)() for son in toProcess)
        #     # for son in toProcess:
        #     #     son._getSonMeta()
        #     # Store pix_m in object
        #     for son, pix_m in zip(sonObjs, r):
        #         son.pixM = pix_m # Sonar instrument pixel resolution
        #         if pix_res_son == 0:
        #             son.pix_res_son = son.pixM
        #         else:
        #             son.pix_res_son = pix_res_son # Store output pixel resolution
        #         if pix_res_map == 0:
        #             son.pix_res_map = son.pixM
        #         else:
        #             son.pix_res_map = pix_res_map
        #     del toProcess

        # metaDir = sonObjs[0].metaDir # Get path to metadata directory
        # sonMeta = sorted(glob(os.path.join(metaDir,'*B*_meta.csv'))) # Get path to metadata files
        # for i in range(0,len(sonObjs)): # Iterate each metadata file
        #     sonObjs[i].sonMetaFile = sonMeta[i] # Store meta file path in sonObj
        # del i, sonMeta

        # sys.exit()


        ###################################
        # Above can be ported to PINGVerter
        ###################################



        #####
        ### 
        # Save main script to metaDir
        scriptDir = os.path.join(os.path.dirname(logfilename), 'processing_scripts')
        if not os.path.exists(scriptDir):
            os.mkdir(scriptDir)
        outScript = os.path.join(scriptDir, script[1])
        shutil.copy(script[0], outScript)
        

        ###
        ####


        # Store cropRange in object
        for son in sonObjs:
            son.cropRange = cropRange
            # Do range crop, if necessary
            if cropRange > 0.0:
                # Convert to distance in pix
                d = round(cropRange / son.pixM, 0).astype(int)

                # Get sonMetaDF
                son._loadSonMeta()
                son.sonMetaDF.loc[son.sonMetaDF['ping_cnt'] > d, 'ping_cnt'] = d
                son._saveSonMetaCSV(son.sonMetaDF)

        # Store flag to export un-rectified sonar tiles in each sonObj.
        for son in sonObjs:
            beam = son.beamName

            son.wcp = wcp

            if wcr:
                if beam == "ss_port" or beam == "ss_star":
                    son.wcr_src = True
                else:
                    son.wcr_src = False

            else:
                son.wcr_src = False

            del beam
        del son


        # If Onix, need to store self._trans in object
        if sonObjs[0].isOnix:
            for son in sonObjs:
                son._loadSonMeta()
                utm_e=son.sonMetaDF.iloc[0]['utm_e']
                utm_n=son.sonMetaDF.iloc[0]['utm_n']
                son._getEPSG(utm_e, utm_n)
            del son


    else:

        ####################################################
        # Check if sonObj pickle exists, append to metaFiles
        metaDir = os.path.join(projDir, "meta")
        if os.path.exists(metaDir):
            metaFiles = sorted(glob(metaDir+os.sep+"*.meta"))

            if len(metaFiles) == 0:
                projectMode_2a_inval()

        else:
            projectMode_2a_inval()
        del metaDir

        ############################################
        # Create a sonObj instance from pickle files
        sonObjs=[]
        for m in metaFiles:
            # Initialize empty sonObj
            son = sonObj(sonFile=None, humFile=None, projDir=None, tempC=None, nchunk=None)

            # Open metafile
            metaFile = pickle.load(open(m, 'rb'))

            # Update sonObj with metadat items
            for attr, value in metaFile.__dict__.items():
                setattr(son, attr, value)

            sonObjs.append(son)

        #################################################
        # Gulf Sturgeon Project: Make sure paths match OS
        if 'GulfSturgeonProject' in projDir:

            toReplace = son.projDir.split('GulfSturgeonProject')[0]
            replaceWith = projDir.split('GulfSturgeonProject')[0]
            for son in sonObjs:
                temp = vars(son)
                for t in temp:
                    if 'Dir' in t or 'File' in t or 'file' in t or 'Pickle' in t:
                        dir = temp[t]
                        dir = dir.replace(toReplace, replaceWith)
                        dir = os.path.normpath(dir)
                        setattr(son, t, dir)
        

        #############################
        # Save main script to metaDir
        scriptDir = os.path.join(projDir, 'meta', 'processing_scripts')
        if not os.path.exists(scriptDir):
            os.mkdir(scriptDir)
        outScript = os.path.join(scriptDir, script[1])
        shutil.copy(script[0], outScript)

        ##########################################################
        # Do some checks to see if additional processing is needed

        # Output pixel resolution
        if son.pix_res_son != pix_res_son:
            print("\nSetting output pixel resolution to {}".format(pix_res_son))
            for son in sonObjs:
                if pix_res_son == 0:
                    son.pix_res_son = son.pixM
                else:
                    son.pix_res_son = pix_res_son # Store output pixel resolution
                if pix_res_map == 0:
                    son.pix_res_map = son.pixM
                else:
                    son.pix_res_map = pix_res_map

        # If missing pings already located, no need to reprocess.
        if son.fixNoDat == True:
            # Missing pings already located, set fixNoDat to False
            fixNoDat = False
            print("\nMissing pings detected previously.")
            print("\tSetting fixNoDat to FALSE.")


        if son.detectDep == detectDep:
            detectDep = -1
            print("\nUsing previously exported depths.")
            print("\tSetting detectDep to -1.")
            if detectDep > 0:
                autoBed = True
            else:
                autoBed = False


        if remShadow:
            for son in sonObjs:
                if son.beamName == "ss_port":
                    if son.remShadow == remShadow:
                        remShadow = -1*remShadow
                        print("\nUsing previous shadow settings. No need to re-process.")
                        print("\tSetting remShadow to {}.".format(remShadow))
                else:
                    pass


        if egn:
            for son in sonObjs:
                if son.beamName == "ss_port":
                    if son.egn == egn:
                        egn = False
                        print("\nUsing previous empiracal gain normalization settings. No need to re-process.")
                        print("\tSetting egn to 0.")
                else:
                    pass

        if pred_sub:
            for son in sonObjs:
                if son.beamName == "ss_port":
                    if son.remShadow > 0:
                        pred_sub = 0
                        # remShadow = 0
                        print("\nSetting pred_sub to 0 so shadow settings aren't effected.")
                        print("\tDon't worry, substrate will still be predicted...")
                else:
                    pass

        for son in sonObjs:
            son.wcp = wcp

            beam = son.beamName
            if wcr:
                if beam == "ss_port" or beam == "ss_star":
                    son.wcr_src = True
                else:
                    son.wcr_src = False
            else:
                son.wcr_src = False

        for son in sonObjs:
            son._pickleSon()
        gc.collect()

        del son


    ############################################################################
    # Locating missing pings                                                   #
    ############################################################################

    if fixNoDat:
        # Open each beam df, store beam name in new field, then concatenate df's into one
        print("\nLocating missing pings and adding NoData...")
        frames = []
        for son in sonObjs:
            son._loadSonMeta()
            df = son.sonMetaDF
            df['beam'] = son.beam
            frames.append(df)
            son._cleanup()
            del df

        dfAll = pd.concat(frames)
        del frames
        # Sort by record_num
        dfAll = dfAll.sort_values(by=['record_num'], ignore_index=True)
        dfAll = dfAll.reset_index(drop=True)
        beams = dfAll['beam'].unique()

        # 'Evenly' allocate work to process threads.
        # Future: Add workflow to balance workload (histogram). Determine total 'missing' pings
        ## and divide by processors, then subsample until workload is balanced
        rowCnt = len(dfAll)
        rowsToProc = []
        c = 0
        r = 0
        n = int(rowCnt/threadCnt)
        startB = dfAll.iloc[0]['beam']

        while (r < threadCnt) and (n < rowCnt):
            if (dfAll.loc[n]['beam']) != startB:
                n+=1
            else:
                rowsToProc.append((c, n))
                c = n
                n = c+int(rowCnt/threadCnt)
                r+=1
        rowsToProc.append((rowsToProc[-1][-1], rowCnt))
        del c, r, n, startB, rowCnt

        # Fix no data in parallel
        r = Parallel(n_jobs=threadCnt)(delayed(son._fixNoDat)(dfAll[r[0]:r[1]].copy().reset_index(drop=True), beams) for r in tqdm(range(len(rowsToProc))))
        gc.collect()

        # Concatenate results from parallel processing
        dfAll = pd.concat(r)
        del r

        # Store original record_num and update record_num with new index
        dfAll = dfAll.sort_values(by=['record_num'], ignore_index=True)
        dfAll['orig_record_num'] = dfAll['record_num']
        dfAll['record_num'] = dfAll.index

        # Slice dfAll by beam, update chunk_id, then save to file.
        for son in sonObjs:
            df = dfAll[dfAll['beam'] == son.beam]

            if (len(df)%nchunk) != 0:
                rdr = nchunk-(len(df)%nchunk)
                chunkCnt = int(len(df)/nchunk)
                chunkCnt += 1
            else:
                rdr = False
                chunkCnt = int(len(df)/nchunk)

            chunks = np.arange(chunkCnt)
            chunks = np.repeat(chunks, nchunk)
            del chunkCnt

            if rdr:
                chunks = chunks[:-rdr]

            df['chunk_id'] = chunks

            # Make sure last chunk is long enough
            c=df['chunk_id'].max() # Get last chunk value
            lastChunk=df[df['chunk_id']==c] # Get last chunk rows
            if len(lastChunk) <= (nchunk/2):
                df.loc[df['chunk_id']==c, 'chunk_id'] = c-1

            df.drop(columns = ['beam'], inplace=True)

            # Check that last chunk has index anywhere in the chunk.
            ## If not, a bunch of NoData was added to the end.
            ## Trim off the NoData
            maxIdx = df[['index']].idxmax().values[0]
            maxIdxChunk = df.at[maxIdx, 'chunk_id']
            maxChunk = df['chunk_id'].max()

            if maxIdxChunk <= maxChunk:
                df = df[df['chunk_id'] <= maxIdxChunk]

            son._saveSonMetaCSV(df)
            son._cleanup()
        del df, rowsToProc, dfAll, son, chunks, rdr, beams

        printUsage()

    else:
        if project_mode != 2:
            for son in sonObjs:
                son.fixNoDat = fixNoDat

    ############################################################################
    # Print Metadata Summary                                                   #
    ############################################################################
    # Print a summary of min/max/avg metadata values. At same time, do simple
    ## check to make sure data are valid.

    if project_mode != 2:
        print("\nSummary of Ping Metadata:\n")

        invalid = defaultdict() # store invalid values

        for son in sonObjs: # Iterate each sonar object
            print(son.beam, ":", son.beamName)
            son._loadSonMeta()
            df = son.sonMetaDF
            print("Ping Count:", len(df))
            print("______________________________________________________________________________")
            print("{:<20s} | {:<15s} | {:<15s} | {:<15s} | {:<5s}".format("Attribute", "Minimum", "Maximum", "Average", "Valid"))
            print("______________________________________________________________________________")
            for att in df.columns:

                # Find min/max/avg of each column
                if (att == 'date') or (att == 'time'):
                    attAvg = '-'
                    attMin = df.at[0, att]
                    attMax = df.at[df.tail(1).index.item(), att]
                    if att == 'time':
                        attMin = str(attMin).split('.')[0]
                        attMax = str(attMax).split('.')[0]
                else:
                    attMin = np.round(np.nanmin(df[att]), 3)
                    attMax = np.round(np.nanmax(df[att]), 3)
                    attAvg = np.round(np.nanmean(df[att]), 3)

                    # Store number of chunks
                    if (att == 'chunk_id'):
                        son.chunkMax = int(attMax)

                # Check if data are valid.
                if (att == "date") or (att == "time") or (att == "transect"):
                    valid=True
                elif (attMax != 0) or ("unknown" in att) or (att =="beam"):
                    valid=True
                elif (att == "inst_dep_m") and (attAvg == 0): # Automatically detect depth if no instrument depth
                    valid=False
                    invalid[son.beam+"."+att] = False
                    detectDep=0#1
                else:
                    valid=False
                    invalid[son.beam+"."+att] = False

                print("{:<15s} | {:<15s} | {:<15s} | {:<15s} | {:<5s}".format(att, str(attMin), str(attMax), str(attAvg), str(valid)))

            son._cleanup()
            print("\n")
        del son, df, att, attAvg, attMin, attMax, valid

        if len(invalid) > 0:
            print("*******************************\n****WARNING: INVALID VALUES****\n*******************************")
            print("_______________________________")
            print("{:<15s} | {:<15s}".format("Sonar Channel", "Attribute"))
            print("_______________________________")
            for key, val in invalid.items():
                print("{:<15s} | {:<15s}".format(key.split(".")[0], key.split(".")[1]))
            print("\n*******************************\n****WARNING: INVALID VALUES****\n*******************************")
            print("\nPING-Mapper detected issues with\nthe values stored in the above\nsonar channels and attributes.")
        del invalid

        print("\nDone!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        printUsage()

    for son in sonObjs:
        son._pickleSon()

    
    # ############################################################################
    # # For AOI                                                                  #
    # ############################################################################
    # # Use AOI to clip metadata to facilitate processing multiple transects in a
    # ## single sonar recording.

    # if aoi: 

    #     print('\n\nProcessing AOI...')

    #     # # # For extracting value from nested dictionaries and lists
    #     # def getPolyCoords(nested_dict, value):
    #     #     # polys = []
    #     #     for k, v in nested_dict.items():
    #     #         if k == value:
    #     #             return v
    #     #         elif hasattr(v, 'items'):
    #     #             p = getPolyCoords(v, value)
    #     #             if p is not None and p:
    #     #                 # return p
    #     #                 polys.append(p)
    #     #         elif isinstance(v, list):
    #     #             for i in v:
    #     #                 if hasattr(i, 'items'):
    #     #                     p = getPolyCoords(i, value)
    #     #                     if p is not None and p:
    #     #                         # return p
    #     #                         polys.append(p)
    #     #     return polys

    #     # If .plan file (from Hydronaulix)
    #     if os.path.basename(aoi.split('.')[-1]) == 'plan':            
    #         with open(aoi, 'r', encoding='utf-8') as f:
    #             f = json.load(f)
    #             # Find 'polygon' coords in nested json
    #             # polys = []
    #             # poly_coords = getPolyCoords(f, 'polygon')
    #             # print(poly_coords)

    #             f = f['mission']
    #             f = f['items']
    #             poly_coords = []
    #             for i in f:
    #                 for k, v in i.items():
    #                     if k == 'polygon':
    #                         poly_coords.append(v)

    #             aoi_poly_all = gpd.GeoDataFrame()

    #             for poly in poly_coords:
                
    #                 # Extract coordinates
    #                 lat_coords = [i[0] for i in poly]
    #                 lon_coords = [i[1] for i in poly]

    #                 polygon_geom = Polygon(zip(lon_coords, lat_coords))
    #                 aoi_poly = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[polygon_geom])

    #                 aoi_poly_all = pd.concat([aoi_poly_all, aoi_poly], ignore_index=True)

    #     # If shapefile
    #     elif os.path.basename(aoi.split('.')[-1]) == 'shp':
    #         aoi_poly_all = gpd.read_file(aoi)

    #     else:
    #         print(os.path.basename, ' is not a valid aoi file type.')
    #         sys.exit()

    #     # Reproject to utm
    #     epsg = int(sonObjs[0].humDat['epsg'].split(':')[-1])
    #     aoi_poly = aoi_poly_all.to_crs(crs=epsg)
    #     aoi_poly = aoi_poly.dissolve()

    #     # Buffer aoi
    #     if os.path.basename(aoi.split('.')[-1]) == 'plan': 
    #         buf_dist = 0.5
    #         aoi_poly['geometry'] = aoi_poly.geometry.buffer(buf_dist)

    #     # Save aoi
    #     aoi_dir = os.path.join(sonObjs[0].projDir, 'aoi')
    #     aoiOut = os.path.basename(sonObjs[0].projDir) + '_aoi.shp'
    #     if not os.path.exists(aoi_dir):
    #         os.makedirs(aoi_dir)

    #     aoiOut = os.path.join(aoi_dir, aoiOut)
    #     aoi_poly.to_file(aoiOut)

    #     # Iterate each son file, clip with aoi, and save
    #     for son in sonObjs:
    #         son._loadSonMeta()
    #         sonDF = son.sonMetaDF

    #         # Convert to geodataframe
    #         epsg = int(son.humDat['epsg'].split(':')[-1])
    #         sonDF = gpd.GeoDataFrame(sonDF, geometry=gpd.points_from_xy(sonDF.e, sonDF.n), crs=epsg)

    #         # Clip with aoi
    #         sonDF = gpd.clip(sonDF, aoi_poly, keep_geom_type=False)
    #         sonDF = sonDF.sort_index()

    #         # Make transects from consective pings using dataframe index
    #         idx = sonDF.index.values
    #         transect_groups = np.split(idx, np.where(np.diff(idx) != 1)[0]+1)

    #         # Assign transect
    #         transect = 0
    #         for t in transect_groups:
    #             sonDF.loc[sonDF.index>=t[0], 'transect'] = transect
    #             transect += 1

    #         # Set chunks
    #         lastChunk = 0
    #         newChunk = []
    #         for name, group in sonDF.groupby('transect'):

    #             if (len(group)%nchunk) != 0:
    #                 rdr = nchunk-(len(group)%nchunk)
    #                 chunkCnt = int(len(group)/nchunk)
    #                 chunkCnt += 1
    #             else:
    #                 rdr = False
    #                 chunkCnt = int(len(group)/nchunk)

    #             chunks = np.arange(chunkCnt) + lastChunk
    #             chunks = np.repeat(chunks, nchunk)
                
    #             if rdr:
    #                 chunks = chunks[:-rdr]
                
    #             newChunk += list(chunks)
    #             lastChunk = chunks[-1] + 1
    #             del chunkCnt

    #         sonDF['chunk_id'] = newChunk

    #         son._saveSonMetaCSV(sonDF)
    #         son._cleanup()


    ############################################################################
    # For Depth Detection                                                      #
    ############################################################################
    # Automatically detect depth from side scan channels. Two options are avail:
    ## Method based on Zheng et al. 2021 using deep learning for segmenting
    ## water-bed interface.
    ## Second is rule's based binary segmentation (may be deprecated in future..)

    start_time = time.time()

    # Determine which sonObj is port/star
    portstar = []
    for son in sonObjs:
        beam = son.beamName
        if beam == "ss_port" or beam == "ss_star":
            portstar.append(son)

    # Create portstarObj
    psObj = portstarObj(portstar)

    chunks = []
    for son in portstar:
        # Get chunk id's, ignoring those with nodata
        c = son._getChunkID()

        chunks.extend(c)
        del c
    del son

    chunks = np.unique(chunks).astype(int)

    # # Automatically estimate depth
    if detectDep > 0:
        print('\n\nAutomatically estimating depth for', len(chunks), 'chunks:')

        #Dictionary to store chunk : np.array(depth estimate)
        psObj.portDepDetect = {}
        psObj.starDepDetect = {}

        # Estimate depth using:
        # Zheng et al. 2021
        # Load model weights and configuration file
        if detectDep == 1:

            # Store configuration file and model weights
            # These were downloaded at the beginning of the script
            depthModelVer = 'Bedpick_Zheng2021_Segmentation_unet_v1.0'
            psObj.configfile = os.path.join(modelDir, depthModelVer, 'config', depthModelVer+'.json')
            psObj.weights = psObj.configfile.replace('.json', '_fullmodel.h5').replace('config', 'weights')
            print('\n\tUsing Zheng et al. 2021 method. Loading model:', os.path.basename(psObj.weights))

        # With binary thresholding
        elif detectDep == 2:
            print('\n\tUsing binary thresholding...')

        # Parallel estimate depth for each chunk using appropriate method
        r = Parallel(n_jobs=np.min([len(chunks), threadCnt]))(delayed(psObj._detectDepth)(detectDep, int(chunk), USE_GPU, tileFile) for chunk in tqdm(range(len(chunks))))

        # store the depth predictions in the class
        for ret in r:
            psObj.portDepDetect[ret[2]] = ret[0]
            psObj.starDepDetect[ret[2]] = ret[1]
            del ret
        del r

        # Flag indicating depth autmatically estimated
        autoBed = True

        saveDepth = True

    # Don't estimate depth, use instrument depth estimate (sonar derived)
    elif detectDep == 0:
        print('\n\nUsing instrument depth:')
        autoBed = False
        saveDepth = True

    else:
        saveDepth = False

    if saveDepth:
        # Save detected depth to csv
        depDF = psObj._saveDepth(chunks, detectDep, smthDep, adjDep)

        # Store depths in downlooking sonar files also
        for son in sonObjs:
            # Store detectDep
            son.detectDep = detectDep

            beam = son.beamName
            if beam != "ss_port" and beam != "ss_star":
                son._loadSonMeta()
                sonDF = son.sonMetaDF

                # If reprocessing, delete existing depth columns
                try:
                    sonDF.drop('dep_m', axis=1, inplace=True)
                    sonDF.drop('dep_m_Method', axis=1, inplace=True)
                    sonDF.drop('dep_m_smth', axis=1, inplace=True)
                    sonDF.drop('dep_m_adjBy', axis=1, inplace=True)
                except:
                    pass

                sonDF = pd.concat([sonDF, depDF], axis=1)

                sonDF.to_csv(son.sonMetaFile, index=False, float_format='%.14f')
                del sonDF, son.sonMetaDF
                son._cleanup()

        del depDF

        # Cleanup
        psObj._cleanup()

        print("\nDone!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        printUsage()

    # Plot sonar depth and auto depth estimate (if available) on sonogram
    if pltBedPick:
        start_time = time.time()

        print("\n\nExporting bedpick plots to {}...".format(tileFile))
        Parallel(n_jobs=np.min([len(chunks), threadCnt]))(delayed(psObj._plotBedPick)(int(chunk), True, autoBed, tileFile) for chunk in tqdm(range(len(chunks))))

        print("\nDone!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        printUsage()

    # Cleanup
    psObj._cleanup()
    del psObj, portstar

    for son in sonObjs:
        son._cleanup()
        son._pickleSon()
    del son


    ############################################################################
    # For shadow removal                                                       #
    ############################################################################
    # Use deep learning segmentation algorithms to automatically detect shadows.
    ## 1: Remove all shadows (those cause by boulders/objects)
    ## 2: Remove only contiguous shadows touching max range extent. May be
    ## useful for locating river banks...

    if remShadow > 0:
        keepShadow = False
    else:
        keepShadow = True
        for son in sonObjs:
            son.remShadow = 0

    # Exporting banklines require shadows
    if banklines and remShadow==0:
        for son in sonObjs:
            if son.beamName == "ss_port":
                    if son.remShadow == 0:
                        print('\n\nExporting banklines requires shadow removal')
                        print('Setting remShadow==2...')
                        remShadow = 2
                        keepShadow = False            

    # Need to detect shadows if mapping substrate
    if pred_sub:
        if remShadow == 0:
            print('\n\nSubstrate mapping requires shadow removal')
            print('Setting remShadow==2...')
            remShadow = 2
            keepShadow = True
        else:
            keepShadow = False

    if remShadow > 0:
        start_time = time.time()
        print('\n\nAutomatically detecting shadows for', len(chunks), 'chunks:')

        if remShadow == 1:
            print('MODE: 1 | Remove all shadows...')
        elif remShadow == 2:
            print('MODE: 2 | Remove shadows in far-field (river bankpick)...')

        # Determine which sonObj is port/star
        portstar = []
        for son in sonObjs:
            beam = son.beamName
            if beam == "ss_port" or beam == "ss_star":
                if keepShadow:
                    son.remShadow = False
                else:
                    son.remShadow = remShadow
                portstar.append(son)
            # Don't remove shadows from down scans
            else:
                son.remShadow = False
        del son

        # Create portstarObj
        psObj = portstarObj(portstar)

        # Model weights and config file
        shadowModelVer = 'Shadow_Segmentation_unet_v1.0'
        psObj.configfile = os.path.join(modelDir, shadowModelVer, 'config', shadowModelVer+'.json')
        psObj.weights = psObj.configfile.replace('.json', '_fullmodel.h5').replace('config', 'weights')

        psObj.port.shadow = defaultdict()
        psObj.star.shadow = defaultdict()

        r = Parallel(n_jobs=np.min([len(chunks), threadCnt]))(delayed(psObj._detectShadow)(remShadow, int(chunk), USE_GPU, False, tileFile) for chunk in tqdm(range(len(chunks))))

        for ret in r:
            psObj.port.shadow[ret[0]] = ret[1]
            psObj.star.shadow[ret[0]] = ret[2]
            del ret

        del r

        print("\nDone!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        printUsage()

    else:
        if project_mode != 2:
            for son in sonObjs:
                son.remShadow = False

    if remShadow < 0:
        for son in sonObjs:
            son.remShadow = -1*son.remShadow

    for son in sonObjs:
        son._pickleSon()

    # for son in sonObjs:
    #     if son.beamName == 'ss_port':
    #         son.remShadow = 2

    # Cleanup
    try:
        psObj._cleanup()
        del psObj, portstar
    except:
        pass


    # ############################################################################
    # # Smooth Trackline                                                         #
    # ############################################################################

    # smthTrkFilenames = smoothTrackline(projDir, x_offset, y_offset, nchunk, cog, threadCnt)
    # for son in sonObjs:
    #     beam = son.beamName
    #     if beam == "ss_port" or beam == "ss_star":
    #         son.smthTrkFile = smthTrkFilenames[beam]


    ############################################################################
    # For Filtering                                                            #
    ############################################################################

    if max_heading_deviation > 0 or min_speed > 0 or max_speed > 0 or aoi:

        # Do port/star and down beams seperately
        downbeams = []
        portstar = []
        for son in sonObjs:
            beam = son.beamName
            if beam == "ss_port" or beam == "ss_star":
                portstar.append(son)
            else:
                # pass # Don't add non-port/star objects since they can't be rectified
                downbeams.append(son)
        del son, beam

        # Find longest recording
        minRec = 0
        maxRec = 0 # Stores index of recording w/ most sonar records.
        maxLen = 0 # Stores length of ping
        for i, son in enumerate(portstar):
            son._loadSonMeta() # Load ping metadata
            sonLen = len(son.sonMetaDF) # Number of sonar records
            if sonLen > maxLen:
                maxLen = sonLen
                maxRec = i
            else:
                minRec = i

        # Do filtering on longest recording
        son0 = portstar[maxRec]
        df0 = son0._doSonarFiltering(max_heading_deviation, max_heading_distance, min_speed, max_speed, aoi)

        # # Determine pings to filter
        # Parallel(n_jobs= np.min([len(portstar), threadCnt]), verbose=10)(delayed(son._doSonarFiltering)(max_heading_deviation, max_heading_distance) for son in portstar)

        # Add filter to other beam
        son1 = portstar[minRec]
        son1._loadSonMeta()
        df1 = son1.sonMetaDF
        df1['filter'] = df0['filter']

        # # Add filter to smoothed tracklines
        # csv0 = son0.smthTrkFile
        # sDF0 = pd.read_csv(csv0)
        # sDF0['filter'] = df0['filter']

        # csv1 = son1.smthTrkFile
        # sDF1 = pd.read_csv(csv1)
        # sDF1['filter'] = df1['filter']

        # Apply the filter
        df0 = df0[df0['filter'] == True]
        df1 = df1[df1['filter'] == True]

        # sDF0 = sDF0[sDF0['filter'] == True]
        # sDF1 = sDF1[sDF1['filter'] == True]

        # Reasign the chunks
        df0 = son0._reassignChunks(df0)
        df1['chunk_id'] = df0['chunk_id']
        df1['transect'] = df0['transect']


        # sDF0['chunk_id'] = df0['chunk_id']
        # sDF0['transect'] = df0['transect']

        # sDF1['chunk_id'] = df1['chunk_id']
        # sDF1['transect'] = df1['transect']

        # Save the csvs
        son0._saveSonMetaCSV(df0)
        son1._saveSonMetaCSV(df1)

        # sDF0.to_csv(csv0, index=False)
        # sDF1.to_csv(csv1, index=False)

        del df0, df1, #sDF0, sDF1
        son0._cleanup()
        son1._cleanup()


        # # Add filtering to smth track files
        # for son in portstar:
        #     son._loadSonMeta()
        #     df = son.sonMetaDF

        #     csv = son.smthTrkFile
        #     sDF = pd.read_csv(csv)

        #     sDF['filter'] = df['filter']

    ############################################################################
    # For sonar intensity corrections/normalization                            #
    ############################################################################

    if egn:
        start_time = time.time()
        print("\nPerforming empirical gain normalization (EGN) on sonar intensities:\n")
        for son in sonObjs:
            if son.beamName == 'ss_port' or son.beamName == 'ss_star':
                print('\n\tCalculating EGN for', son.beamName)
                son.egn = True
                son.egn_stretch = egn_stretch

                # Determine what chunks to process
                chunks = son._getChunkID()
                chunks = chunks[:-1] # remove last chunk

                # Load sonMetaDF
                son._loadSonMeta()

                # Calculate range-wise mean intensity for each chunk
                print('\n\tCalculating range-wise mean intensity for each chunk...')
                chunk_means = Parallel(n_jobs= np.min([len(chunks), threadCnt]))(delayed(son._egnCalcChunkMeans)(i) for i in tqdm(range(len(chunks))))

                # Calculate global means
                print('\n\tCalculating range-wise global means...')
                son._egnCalcGlobalMeans(chunk_means)
                del chunk_means

                # Calculate egn min and max for each chunk
                print('\n\tCalculating EGN min and max values for each chunk...')
                min_max = Parallel(n_jobs= np.min([len(chunks)]))(delayed(son._egnCalcMinMax)(i) for i in tqdm(range(len(chunks))))

                # Calculate global min max for each channel
                son._egnCalcGlobalMinMax(min_max)
                del min_max

                son._cleanup()
                son._pickleSon()

                gc.collect()
                printUsage()

            else:
                son.egn = False # Dont bother with down-facing beams

        # Get true global min and max

        bed_mins = []
        bed_maxs = []
        wc_mins = []
        wc_maxs = []
        for son in sonObjs:
            if son.beamName == 'ss_port' or son.beamName == 'ss_star':
                bed_mins.append(son.egn_bed_min)
                bed_maxs.append(son.egn_bed_max)
                wc_mins.append(son.egn_wc_min)
                wc_maxs.append(son.egn_wc_max)
        bed_min = np.min(bed_mins)
        bed_max = np.max(bed_maxs)
        wc_min = np.min(wc_mins)
        wc_max = np.max(wc_maxs)
        for son in sonObjs:
            if son.beamName == 'ss_port' or son.beamName == 'ss_star':
                son.egn_bed_min = bed_min
                son.egn_bed_max = bed_max
                son.egn_wc_min = wc_min
                son.egn_wc_max = wc_max

            # Tidy up
            son._cleanup()
            son._pickleSon()
            gc.collect()

        # Need to calculate histogram if egn_stretch is greater then 0
        if egn_stretch > 0:
            for son in sonObjs:
                if son.beamName == 'ss_port' or son.beamName == 'ss_star':
                    # Determine what chunks to process
                    chunks = son._getChunkID()
                    chunks = chunks[:-1] # remove last chunk

                    print('\n\tCalculating EGN corrected histogram for', son.beamName)
                    hist = Parallel(n_jobs= np.min([len(chunks), threadCnt]))(delayed(son._egnCalcHist)(i) for i in tqdm(range(len(chunks))))

                    print('\n\tCalculating global EGN corrected histogram')
                    son._egnCalcGlobalHist(hist)

            # Now calculate true global histogram
            egn_wcp_hist = np.zeros((255))
            egn_wcr_hist = np.zeros((255))

            for son in sonObjs:
                if son.beamName == 'ss_port' or son.beamName == 'ss_star':
                    egn_wcp_hist += son.egn_wcp_hist
                    egn_wcr_hist += son.egn_wcr_hist

            for son in sonObjs:
                if son.beamName == 'ss_port' or son.beamName == 'ss_star':
                    son.egn_wcp_hist = egn_wcp_hist
                    son.egn_wcr_hist = egn_wcr_hist

            # Calculate global percentages and standard deviation
            wcp_pcnt = np.zeros((egn_wcp_hist.shape))
            wcr_pcnt = np.zeros((egn_wcr_hist.shape))

            # Calculate total pixels
            wcp_sum = np.sum(egn_wcp_hist)
            wcr_sum = np.sum(egn_wcr_hist)

            # Caclulate percentages
            for i, v in enumerate(egn_wcp_hist):
                wcp_pcnt[i] = egn_wcp_hist[i] / wcp_sum

            for i, v in enumerate(egn_wcr_hist):
                wcr_pcnt[i] = egn_wcr_hist[i] / wcr_sum

            for son in sonObjs:
                if son.beamName == 'ss_port' or son.beamName == 'ss_star':
                    son.egn_wcp_hist_pcnt = wcp_pcnt
                    son.egn_wcr_hist_pcnt = wcr_pcnt


            del egn_wcp_hist, egn_wcr_hist, wcp_pcnt, wcr_pcnt
            # del egn_wcr_hist, wcr_pcnt

            # Calculate min and max for rescale
            for son in sonObjs:
                if son.beamName == 'ss_port':
                    wcp_stretch, wcr_stretch = son._egnCalcStretch(egn_stretch, egn_stretch_factor)
                    # wcr_stretch = son._egnCalcStretch(egn_stretch, egn_stretch_factor)

                    # Tidy up
                    son._cleanup()
                    son._pickleSon()
                    gc.collect()

            for son in sonObjs:
                if son.beamName == 'ss_star':
                    son.egn_stretch = egn_stretch
                    son.egn_stretch_factor = egn_stretch_factor

                    son.egn_wcp_stretch_min = wcp_stretch[0]
                    son.egn_wcp_stretch_max = wcp_stretch[1]

                    son.egn_wcr_stretch_min = wcr_stretch[0]
                    son.egn_wcr_stretch_max = wcr_stretch[1]

                    print('\n\n\nMinMax Global Stretch Vals')
                    print('wcr', son.egn_wcr_stretch_min, son.egn_wcr_stretch_max)
                    print('wcp', son.egn_wcp_stretch_min, son.egn_wcp_stretch_max)

                    # Tidy up
                    son._cleanup()
                    son._pickleSon()
                    gc.collect()


        print("\nDone!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        printUsage()
    else:
        if project_mode != 2:
            for son in sonObjs:
                son.egn=False




    ############################################################################
    # Export un-rectified sonar tiles                                          #
    ############################################################################

    if wcp or wcr:
        start_time = time.time()
        print("\nExporting sonogram tiles:\n")
        for son in sonObjs:
            if son.wcp or son.wcr_src:
                # Set outDir
                son.outDir = os.path.join(son.projDir, son.beamName)

                # Determine what chunks to process
                chunks = son._getChunkID()
                if son.wcr_src and son.wcp:
                    chunkCnt = len(chunks)*2
                else:
                    chunkCnt = len(chunks)
                print('\n\tExporting', chunkCnt, 'sonograms for', son.beamName)

                # Load sonMetaDF
                son._loadSonMeta()

                Parallel(n_jobs= np.min([len(chunks), threadCnt]))(delayed(son._exportTiles)(i, tileFile) for i in tqdm(range(len(chunks))))

                son._pickleSon()

            # Tidy up
            son._cleanup()
            gc.collect()

        del son
        print("\nDone!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        printUsage()

    ############################################################################
    # Export imagery for labeling                                              #
    ############################################################################
    # Export speed corrected or stretched non-rectified imagery for purpose of
    ## labeling for subsequent model training. Optionally remove water column
    ## and shadows (essentially NoData if interested in substrate related pixels)

    if lbl_set:
        start_time = time.time()
        for son in sonObjs:
            if son.beamName == 'ss_port' or son.beamName == 'ss_star':
                # Set outDir
                son.outDir = os.path.join(son.projDir, son.beamName)

                # Determine what chunks to process
                chunks = son._getChunkID()
                chunkCnt = len(chunks)

                print('\n\tExporting', chunkCnt, 'label-ready sonograms for', son.beamName)

                # Load sonMetaDF
                son._loadSonMeta()

                Parallel(n_jobs= np.min([len(chunks), threadCnt]))(delayed(son._exportLblTiles)(i, lbl_set, spdCor, maxCrop, tileFile) for i in tqdm(range(len(chunks))))
                son._cleanup()

            gc.collect()
        print("\nDone!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        printUsage()

    try:
        del chunkCnt
    except:
        pass


    ##############################################
    # Let's pickle sonObj so we can reload later #
    ##############################################

    for son in sonObjs:
        son._pickleSon()
    gc.collect()
    printUsage()
