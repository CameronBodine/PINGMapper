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


from __future__ import division
import sys, os

# Add 'pingmapper' to the path, may not need after pypi package...
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.append(PACKAGE_DIR)

from pingmapper.funcs_common import *
from pingmapper.class_rectObj import rectObj
from pingmapper.class_portstarObj import portstarObj
from pingmapper.funcs_rectify import smoothTrackline

import inspect

from scipy.signal import savgol_filter

#===============================================================================
def rectify_master_func(logfilename='',
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
    Main script to rectify side scan sonar imagery from a Humminbird.

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
    nchunk : int
        DESCRIPTION - Number of pings per chunk.  Chunk size dictates size of
                      sonar tiles (sonograms).  Most testing has been on chunk
                      sizes of 500 (recommended).
        EXAMPLE -     nchunk = 500
    rect_wcp : bool
        DESCRIPTION - Flag to export georectified sonar tiles w/ water column
                      present (wcp).
                      True = export georectified wcp sonar tiles;
                      False = do not export georectified wcp sonar tiles.
        EXAMPLE -     rect_wcp = True
    rect_wcr : bool
        DESCRIPTION - Flag to export georectified sonar tiles w/ water column
                      removed (wcr) & slant range corrected.
                      True = export georectified wcr sonar tiles;
                      False = do not export georectified wcr sonar tiles.
        EXAMPLE -     rect_wcr = True
    mosaic : int
        DESCRIPTION - Mosaic exported georectified sonograms to a geotiff or
                      virtual raster (vrt) as specified with the `rect_wcp` and
                      `rect_wcr` flags. See https://gdal.org/drivers/raster/vrt.html
                      for more info.
                      Overviews are created by default.
                      0 = do not export georectified mosaic(s);
                      1 = export georectified mosaic(s) as GeoTiffs.
                      2 = export georectified mosaic(s) as vrt.
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
    Adds exported imagery to the project directory with the following structure
    and outputs, pending parameter selection:

    |--projDir
    |
    |--|meta
    |  |--Trackline_Smth_ss_port.csv : Smoothed trackline coordinates for portside
    |  |                               scan (if present)
    |  |--Trackline_Smth_ss_star.csv : Smoothed trackline coordinates for starboard
    |  |                               scan (if present)
    |
    |--|ss_port (if B002.SON OR B003.SON [transducer flipped] available)
    |  |--rect_wcr [rect_wcr=True]
    |     |--*.tif : Portside side scan (ss) georectified sonar tiles, w/
    |     |          water column removed (wcr) & slant range corrected
    |  |--rect_wcp [wcp=True]
    |     |--*.tif : Portside side scan (ss) georectified sonar tiles, w/
    |     |          water column present (wcp)
    |
    |--|ss_star (if B003.SON OR B002.SON [transducer flipped] available)
    |  |--rect_wcr [wcr=True]
    |     |--*.tif : Starboard side scan (ss) georectified sonar tiles, w/
    |     |          water column removed (wcr) & slant range corrected
    |  |--rect_wcp [wcp=True]
    |     |--*.tif : Starboard side scan (ss) georectified sonar tiles, w/
    |     |          water column present (wcp)
    |
    |--*_wcr_mosaic.tif : WCR mosaic [rect_wcr=True & mosaic=1]
    |--*_wcp_mosaic.tif : WCP mosaic [rect_wcp=True & mosaic=1]
    '''

    ############
    # Parameters
    flip = False #Flip port/star
    filter = int(nchunk*0.1) #Filters trackline coordinates for smoothing
    filterRange = filter #int(nchunk*0.05) #Filters range extent coordinates for smoothing

    # Heading or COG rectification params
    smthHeading = True
    # interpolation_distance = 100
    ## interp_method???

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
    # Create rectObj() instance from previously created sonObj() instance      #
    ############################################################################

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

    #############################################
    # Create a rectObj instance from pickle files
    rectObjs = []
    for meta in metaFiles:
        son = rectObj(meta) # Initialize rectObj()
        rectObjs.append(son) # Store rectObj() in rectObjs[]
    del meta, metaFiles

    #####################################
    # Determine which sonObj is port/star
    portstar = []
    for son in rectObjs:
        beam = son.beamName
        if beam == "ss_port" or beam == "ss_star":
            portstar.append(son)
        else:
            pass # Don't add non-port/star objects since they can't be rectified
    del son, beam, rectObjs

    ############################################################################
    # Smooth Trackline                                                         #
    ############################################################################

    # Must use COG for rubber sheeting
    if rubberSheeting:
        rectMethod = 'COG'

    cog=True
    if rectMethod != 'COG':
        cog=False

    smthTrkFilenames = smoothTrackline(projDir=projDir, x_offset=x_offset, y_offset=y_offset, nchunk=nchunk, cog=cog, threadCnt=threadCnt)
    for son in portstar:
        beam = son.beamName
        if beam == "ss_port" or beam == "ss_star":
            son.smthTrkFile = smthTrkFilenames[beam]

    ############################################################################
    # Export Coverage and Trackline                                            #
    ############################################################################

    if coverage:
        start_time = time.time()
        print("\nExporting coverage and trackline shapefiles:\n")
        portstar[0]._exportTrkShp()

        trk_files = []
        for son in portstar:
            # trk_files.append(son.smthTrkFile)

            son._exportCovShp()

        # print(trk_files)

        # portstar[0]._exportCovShp(trk_files)

        print("Done!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        gc.collect()
        printUsage()

    ############################################################################
    # COG Pre-processing                                                       #
    # ##########################################################################

    for son in portstar:
        son.rect_wcp = rect_wcp
        son.rect_wcr = rect_wcr

    # ############################################################################
    # # Rectify Heading sonar imagery - Pingwise, not Rubbersheeting             #
    # ############################################################################

    if not rubberSheeting:
        start_time = time.time()
        print("\nRectifying and Exporting Geotiffs based on heading:\n")
        for son in portstar:

            # Set output directory
            son.outDir = os.path.join(son.projDir, son.beamName)

            # # Get sonar coords dataframe
            # sonarCoordsDF = son.sonarCoordsDF

            # Get smoothed trackline file
            smth_trk_file = son.smthTrkFile
            sDF = pd.read_csv(smth_trk_file)

            # Smooth heading
            if rectMethod == 'Heading':
                heading = 'instr_heading'
                if smthHeading:
                    for name, group in sDF.groupby('transect'):
                        # Convert degrees to radians
                        hding = np.deg2rad(group[heading])
                        # Unwrap the heading because heading is circular
                        hding_unwrapped = np.unwrap(hding)
                        # Do smoothing
                        smth = savgol_filter(hding_unwrapped, 51, 3)
                        # Convert to degrees and make sure 0-360
                        smth = np.rad2deg(smth) % 360
                        group[heading] = smth
                        # Update sDF
                        sDF.update(group)
            else:
                heading = 'trk_cog'

            smth_trk_file = son.smthTrkFile
            sDF.to_csv(smth_trk_file)

            # Get chunk id
            chunks = son._getChunkID()

            # Get colormap
            son._getSonColorMap(son_colorMap)

            print('\n\tExporting', len(chunks), 'GeoTiffs for', son.beamName)

            # Parallel(n_jobs= np.min([len(sDF), threadCnt]))(delayed(son._rectSonHeadingMain)(sonarCoordsDF[sonarCoordsDF['chunk_id']==chunk], chunk) for chunk in tqdm(range(len(chunks))))
            Parallel(n_jobs= np.min([len(sDF), threadCnt]))(delayed(son._rectSonHeadingMain)(sDF[sDF['chunk_id']==chunk], chunk, heading=heading, interp_dist=rectInterpDist) for chunk in tqdm(range(len(chunks))))
            # for i in chunks:
            #     # son._rectSonHeading(sonarCoordsDF[sonarCoordsDF['chunk_id']==i], i)
            #     r = son._rectSonHeadingMain(sDF[sDF['chunk_id']==i], i, heading=heading, interp_dist=rectInterpDist)

            # #     sys.exit()

            #     # # Concatenate and store cooordinates
            #     # dfAll = pd.concat(r)
            #     # son.sonarCoordsDF = dfAll

            #     smth_trk_file = smth_trk_file.replace('.csv', 'heading.csv')
            #     r.to_csv(smth_trk_file)

            # print(dfAll)

        print("Done!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        gc.collect()
        printUsage()


    ############################################################################
    # Rectify sonar imagery - Rubbersheeting                                   #
    ############################################################################
    start_time = time.time()
    print("\nRectifying and exporting GeoTiffs:\n")

    if banklines and not (rect_wcp or rect_wcr):
        print('\n\nExporting banklines requires rectified sonar imagery')
        print('Setting rect_wcr==True...')
        rect_wcr = True

    for son in portstar:
        son.rect_wcp = rect_wcp
        son.rect_wcr = rect_wcr

    if (rect_wcp and rubberSheeting) or (rect_wcr and rubberSheeting):
        for son in portstar:
            # Set output directory
            son.outDir = os.path.join(son.projDir, son.beamName)

            # Get chunk id's
            chunks = son._getChunkID()

            # Load sonMetaDF
            son._loadSonMeta()

            # Get colormap
            son._getSonColorMap(son_colorMap)

            print('\n\tExporting', len(chunks), 'GeoTiffs for', son.beamName)
            # for i in chunks:
            #     son._rectSonRubber(i, filter, cog, wgs=False)
            #     sys.exit()
            Parallel(n_jobs= np.min([len(chunks), threadCnt]))(delayed(son._rectSonRubber)(i, filter, cog, wgs=False) for i in tqdm(range(len(chunks))))
            son._cleanup()
            gc.collect()
            printUsage()

    if rect_wcp or rect_wcr:
        for son in portstar:
            try:
                del son.sonMetaDF
            except:
                pass
            try:
                del son.smthTrk
            except:
                pass
            son._pickleSon()
        del son
    print("Done!")
    print("Time (s):", round(time.time() - start_time, ndigits=1))
    gc.collect()
    printUsage()

    ############################################################################
    # Mosaic imagery                                                           #
    ############################################################################
    overview = True # False will reduce overall file size, but reduce performance in a GIS

    if mosaic > 0:
        start_time = time.time()
        print("\nMosaicing GeoTiffs...")
        psObj = portstarObj(portstar)
        if aoi or max_heading_deviation or min_speed or max_speed:
            psObj._createMosaicTransect(mosaic, overview, threadCnt, son=True, maxChunk=mosaic_nchunk, cog=cog)
        else:
            psObj._createMosaic(mosaic, overview, threadCnt, son=True, maxChunk=mosaic_nchunk)
        print("Done!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        del psObj
        gc.collect()
        printUsage()

    ############################################################################
    # Export Banklines                                                         #
    ############################################################################
    if banklines: 
        start_time = time.time()
        print("\nExporting Banklines...")
        psObj = portstarObj(portstar)
        psObj._exportBanklines(threadCnt)
        print("Done!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        del psObj
        gc.collect()
        printUsage()

    ##############################################
    # Let's pickle sonObj so we can reload later #
    ##############################################

    for son in portstar:
        son._pickleSon()
        del son

    # Cleanup
    del portstar

    printUsage()

    # sys.stdout.log.close()
