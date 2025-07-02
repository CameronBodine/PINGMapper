# Part of PING-Mapper software
#
# GitHub: https://github.com/CameronBodine/PINGMapper
# Website: https://cameronbodine.github.io/PINGMapper/ 
#
# Co-Developed by Cameron S. Bodine and Dr. Daniel Buscombe
#
# Inspired by PyHum: https://github.com/dbuscombe-usgs/PyHum
#
# MIT License
#
# Copyright (c) 2025 Cameron S. Bodine
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

# # For debug
# from funcs_common import *
# from class_mapSubstrateObj import mapSubObj
# from class_portstarObj import portstarObj
# from funcs_model import *

from pingmapper.funcs_common import *
from pingmapper.class_mapSubstrateObj import mapSubObj
from pingmapper.class_portstarObj import portstarObj
from pingmapper.funcs_model import *

import itertools

#===============================================================================
def map_master_func(logfilename='',
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
                    time_table = False,
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
                    wcm=False,
                    wcr=False,
                    wco=False,
                    sonogram_colorMap='Greys',
                    mask_shdw=False,
                    mask_wc=False,
                    spdCor=False,
                    maxCrop=False,
                    moving_window=False,
                    window_stride=0.1,
                    USE_GPU=False,
                    remShadow=0,
                    detectDep=0,
                    smthDep=0,
                    adjDep=0,
                    pltBedPick=False,
                    rect_wcp=False,
                    rect_wcr=False,
                    rubberSheeting=True,
                    rectMethod='COG',
                    rectInterpDist=50,
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
    Main script to map substrates from side scan sonar imagery.

    ----------
    Parameters
    ----------

    -------
    Returns
    -------
    '''

    ############
    # Parameters
    # modelDir = os.path.join(SCRIPT_DIR, 'models', 'PINGMapperv2.0_SegmentationModelsv1.0')
    d = os.environ['CONDA_PREFIX']
    modelDir = os.path.join(d, 'pingmapper_config', 'models', 'PINGMapperv2.0_SegmentationModelsv1.0')
    flip = False #Flip port/star
    filter = int(nchunk*0.1) #Filters trackline coordinates for smoothing
    filterRange = filter #int(nchunk*0.05) #Filters range extent coordinates for smoothing


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


    ############################################################################
    # Create mapObj() instance from previously created sonObj() instance       #
    ############################################################################

    ####################################################
    # Check if sonObj pickle exists, append to metaFiles
    metaDir = os.path.join(projDir, "meta")
    if os.path.exists(metaDir):
        metaFiles = sorted(glob(metaDir+os.sep+"*.meta"))
    else:
        sys.exit("No SON metadata files exist")
    del metaDir

    ############################################
    # Create a mapObj instance from pickle files
    sonObjs = []
    for meta in metaFiles:
        son = mapSubObj(meta) # Initialize mapObj()
        sonObjs.append(son) # Store mapObj() in mapObjs[]
    del meta, metaFiles

    #####################################
    # Determine which sonObj is port/star
    mapObjs = []
    for son in sonObjs:
        beam = son.beamName
        if beam == "ss_port" or beam == "ss_star":
            mapObjs.append(son)
        else:
            pass # Don't add non-port/star objects since they can't be rectified
    del son, beam, sonObjs

    ################################################
    # Prepare output directory and update attributes
    for son in mapObjs:
        son.substrateDir = os.path.join(son.projDir, 'substrate')
        # son.map_sub = map_sub
        # son.pix_res_map = pix_res_map

    outDir = son.substrateDir
    if not os.path.exists(outDir):
        os.mkdir(outDir)

    del son

    ##########################################################
    # If pred_sub == 0, make sure data was previously exported
    if pred_sub == 0:
        try:
            files = mapObjs[0]._getSubstrateNpz()
        except:
            error_noSubNpz()

    #########################################################
    # If map_sub == 0, make sure data was previously exported
    if not map_sub and map_mosaic:
        # Get directory
        mapPath = os.path.join(mapObjs[0].substrateDir, 'map_substrate_raster')
        maps = glob(os.path.join(mapPath, '*.tif'))

        if len(maps) == 0:
            # if export_poly:
            #     error_noSubMap_poly()
            # if map_mosaic:
            #     error_noSubMap_mosaic()
            map_sub = True

    #########################################################
    # If map_sub == 0, make sure data was previously exported
    if not map_sub and export_poly:
        # Get directory
        mapPath = os.path.join(mapObjs[0].substrateDir, 'map_substrate_raster')
        maps = glob(os.path.join(mapPath, '*.tif'))

        if len(maps) == 0:
            # if export_poly:
            #     error_noSubMap_poly()
            # if map_mosaic:
            #     error_noSubMap_mosaic()
            map_sub = True

    #############################################
    # Determine if smoothed trackline was created
    if hasattr(mapObjs[0], 'smthTrkFile'):
        smthTrk = True
    else:
        smthTrk = False


    ############################################################################
    # For Substrate Prediction                                                 #
    ############################################################################

    if pred_sub > 0:
        start_time = time.time()

        print('\n\nAutomatically predicting and segmenting substrate...')

        outDir = os.path.join(mapObjs[0].substrateDir, 'predict_npz')
        if not os.path.exists(outDir):
            os.mkdir(outDir)

        # Get chunk id for mapping substrate
        for son in mapObjs:
            # Set outDir
            son.outDir = outDir

            # Get chunk id's
            chunks = son._getChunkID()

            # Prepare model
            if pred_sub == 1:
                # Load model weights and config file
                if son.egn:
                    # EGN model
                    substrateModelVer = 'EGN_Substrate_Segmentation_segformer_v1.0'
                    son.configfile = os.path.join(modelDir, substrateModelVer, 'config', substrateModelVer+'.json')
                    son.weights = os.path.join(modelDir, substrateModelVer, 'weights', substrateModelVer+'_fullmodel.h5')

                else:
                    # Raw model
                    substrateModelVer = 'Raw_Substrate_Segmentation_segformer_v1.0'
                    son.configfile = os.path.join(modelDir, substrateModelVer, 'config', substrateModelVer+'.json')
                    son.weights = os.path.join(modelDir, substrateModelVer, 'weights', substrateModelVer+'_fullmodel.h5')

            # Do prediction (make parallel later)
            print('\n\tPredicting substrate for', len(chunks), son.beamName, 'chunks')

            Parallel(n_jobs=np.min([len(chunks), threadCnt]))(delayed(son._detectSubstrate)(i, USE_GPU) for i in tqdm(chunks))

            son._cleanup()
            son._pickleSon()
            del chunks

        del son
        print("\nDone!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        gc.collect()
        printUsage()

    ############################################################################
    # Fot Substrate Plotting                                                   #
    ############################################################################

    print(pltSubClass)

    if pltSubClass:
        start_time = time.time()

        print('\n\nExporting substrate plots...')

        # Determine if probabilities or logits are plotted
        if map_predict == 1:
            probs = True
        elif map_predict == 2:
            probs = False
        else:
            probs = True


        # Out directory
        outDir = os.path.join(mapObjs[0].substrateDir, 'plots')
        if not os.path.exists(outDir):
            os.mkdir(outDir)

        # Get chunk id for mapping substrate
        for son in mapObjs:
            # Set outDir
            son.outDir = outDir

            # Get Substrate npz's
            toMap = son._getSubstrateNpz()

            print('\n\tExporting substrate plots for', len(toMap), son.beamName, 'chunks:')

            # Plot substrate classification()
            # sys.exit()
            Parallel(n_jobs=np.min([len(toMap), threadCnt]))(delayed(son._pltSubClass)(map_class_method, c, f, spdCor=spdCor, maxCrop=maxCrop, probs=probs) for c, f in tqdm((toMap.items())))
            son._pickleSon()
            del toMap

        del son
        print("\nDone!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        gc.collect()
        printUsage()


    ############################################################################
    # For Substrate Mapping                                                    #
    ############################################################################

    # threadCnt = 2

    if map_sub > 0:
        start_time = time.time()

        print('\n\nMapping substrate classification...')

        # Set output directory
        outDir = os.path.join(mapObjs[0].substrateDir, 'map_substrate_raster')
        if not os.path.exists(outDir):
            os.mkdir(outDir)

        # Get each son's npz's
        for son in mapObjs:
            son.map_sub = map_sub

            # Set outDir
            son.outDir = outDir

            # Store substrate npz filenames
            npz = son._getSubstrateNpz()

            # Create dictionary to store port/star pairs
            if not 'toMap' in locals():
                toMap = npz
            else:
                for k, v in npz.items():
                    # Get existing npz file
                    e = toMap[k]

                    # Add existing and new npz as list. Add port as first element
                    if 'port' in e:
                        toMap[k] = [e, v]
                    else:
                        toMap[k] = [v, e]

        del son



        # Do rectification as portstarObj to eliminate NoData at NADIR
        print('\n\tMapping substrate classification. Processing', len(toMap), 'port and starboard pairs...')
        # Create portstarObj
        psObj = portstarObj(mapObjs)

        Parallel(n_jobs=np.min([len(toMap), threadCnt]))(delayed(psObj._mapSubstrate)(map_class_method, c, f) for c, f in tqdm(toMap.items()))

        del toMap
        print("\nDone!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        gc.collect()
        printUsage()

    ############################################################################
    # For Substrate Mosaic                                                     #
    ############################################################################

    overview = True # False will reduce overall file size, but reduce performance in a GIS
    if map_mosaic > 0:
        start_time = time.time()
        print("\nMosaicing GeoTiffs...")

        # Create portstar object
        psObj = portstarObj(mapObjs)

        # Switch off rect_wcp and rect_wcr
        psObj.port.rect_wcp = False
        psObj.port.rect_wcr = False
        psObj.port.map_predict = False

        # Make sure map_sub is set to true
        psObj.port.map_sub = True

        # # Create the mosaic
        # psObj._createMosaic(mosaic=map_mosaic, overview=overview, threadCnt=threadCnt, son=False, maxChunk=mosaic_nchunk)

        if not aoi:
            psObj._createMosaic(mosaic=map_mosaic, overview=overview, threadCnt=threadCnt, son=False, maxChunk=mosaic_nchunk)
        else:
            psObj._createMosaicTransect(mosaic=map_mosaic, overview=overview, threadCnt=threadCnt, son=False, maxChunk=mosaic_nchunk, cog=cog)

        # Revert rect_wcp and rect_wcr
        psObj.port.rect_wcp = rect_wcp
        psObj.port.rect_wcr = rect_wcr
        psObj.port.map_predict = map_predict
        psObj.port.map_substrate = map_sub

        del psObj
        print("\nDone!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        gc.collect()
        printUsage()

    ############################################################################
    # For Substrate Polygon                                                    #
    ############################################################################

    if export_poly:
         start_time = time.time()
         print("\nConverting substrate rasters into shapefile...")

         # Create portstar object
         psObj = portstarObj(mapObjs)

         # Switch off rect_wcp and rect_wcr
         psObj.port.rect_wcp = False
         psObj.port.rect_wcr = False
         psObj.port.map_predict = False

         # Make sure map_sub is set to true
         psObj.port.map_sub = True

         psObj._rasterToPoly(map_mosaic, threadCnt, mosaic_nchunk)

         # Revert rect_wcp and rect_wcr
         psObj.port.rect_wcp = rect_wcp
         psObj.port.rect_wcr = rect_wcr
         psObj.port.map_predict = map_predict
         psObj.port.map_sub = map_sub

         del psObj
         print("\nDone!")
         print("Time (s):", round(time.time() - start_time, ndigits=1))
         gc.collect()
         printUsage()

    ############################################################################
    # For Prediction Mapping                                                   #
    ############################################################################


    if map_predict > 0:
        start_time = time.time()

        # Reduce to avoid OOM
        threadPrcnt = 0.75
        if threadCnt == cpu_count():
            threadCnt = int(threadCnt * threadPrcnt)

            print("\nPrediction Map requires a lot of RAM...")
            print("Lowering threadCnt to:", threadCnt)

        if map_predict == 1:
            a = 'probability'
        else:
            a = 'logit'
        print('\n\nMapping substrate prediction as ***{}***...'.format(a.upper()))

        # Set output directory
        outDir = os.path.join(mapObjs[0].substrateDir, 'map_'+a+'_raster')
        if not os.path.exists(outDir):
            os.mkdir(outDir)

        # Get each son's npz's
        for son in mapObjs:
            # Set outDir
            son.outDir = outDir

            # Store map_predict
            son.map_predict = map_predict

            # Store substrate npz filenames
            npz = son._getSubstrateNpz()

            # Create dictionary to store port/star pairs
            if not 'toMap' in locals():
                toMap = npz
            else:
                for k, v in npz.items():
                    # Get existing npz file
                    e = toMap[k]

                    # Add existing and new npz as list. Add port as first element
                    if 'port' in e:
                        toMap[k] = [e, v]
                    else:
                        toMap[k] = [v, e]
        del son


        # Do rectification as portstarObj to eliminate NoData at NADIR
        print('\n\tMapping substrate predictions. Processing', len(toMap), 'port and starboard pairs...')
        # Create portstarObj
        psObj = portstarObj(mapObjs)

        Parallel(n_jobs=np.min([len(toMap), threadCnt]))(delayed(psObj._mapPredictions)(map_predict, 'map_'+a, c, f) for c, f in tqdm(toMap.items()))

        del toMap, psObj
        print("\nDone!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        gc.collect()
        printUsage()


    # ############################################################################
    # # For Prediction Mosaic                                                    #
    # ############################################################################

    # overview = True # False will reduce overall file size, but reduce performance in a GIS
    # if map_predict > 0 and map_mosaic > 0:
    #     start_time = time.time()
    #     print("\nMosaicing GeoTiffs...")

    #     # Create portstar object
    #     psObj = portstarObj(mapObjs)

    #     # Switch off rect_wcp, rect_wcr, and mapSub
    #     psObj.port.rect_wcp = False
    #     psObj.port.rect_wcr = False
    #     psObj.port.map_sub = False
    #     # psObj.port.map_predict = True

    #     # Create the mosaic
    #     psObj._createMosaic(mosaic=1, overview=overview, threadCnt=threadCnt, son=False, maxChunk=mosaic_nchunk)

    #     # Revert rect_wcp, rect_wcr, mapSub
    #     psObj.port.rect_wcp = rect_wcp
    #     psObj.port.rect_wcr = rect_wcr
    #     psObj.port.map_sub = map_sub
    #     # psObj.port.map_predict = map_predict

    #     del psObj
    #     print("Done!")
    #     print("Time (s):", round(time.time() - start_time, ndigits=1))
    #     gc.collect()
    #     printUsage()

    ##############################################
    # Let's pickle sonObj so we can reload later #
    ##############################################

    for son in mapObjs:
        son._cleanup()
        son._pickleSon()
    gc.collect()
    printUsage()
