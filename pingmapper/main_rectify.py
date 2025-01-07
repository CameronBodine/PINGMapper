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
                        pix_res=0.0,
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

    # #############################################
    # # Determine if smoothed trackline was created
    # if hasattr(portstar[0], 'smthTrkFile'):
    #     smthTrk = False
    # else:
    #     smthTrk = True

    # ############################################################################
    # # Smooth GPS trackpoint coordinates                                        #
    # ############################################################################

    # if smthTrk:
    #     #####################
    #     #####################
    #     # Smoothing Trackline
    #     # Tool:
    #     # https://docs.scipy.org/doc/scipy-0.14.0/reference/tutorial/interpolate.html#spline-interpolation
    #     # Adapted from:
    #     # https://github.com/remisalmon/gpx_interpolate
    #     start_time = time.time()
    #     print("\nSmoothing trackline...")

    #     # As side scan beams use same transducer/gps coords, we will smooth one
    #     ## beam's trackline and use for both. Use the beam with the most sonar records.
    #     maxRec = 0 # Stores index of recording w/ most sonar records.
    #     maxLen = 0 # Stores length of ping
    #     for i, son in enumerate(portstar):
    #         son._loadSonMeta() # Load ping metadata
    #         sonLen = len(son.sonMetaDF) # Number of sonar records
    #         if sonLen > maxLen:
    #             maxLen = sonLen
    #             maxRec = i

    #     # Now we will smooth using sonar beam w/ most records.
    #     son0 = portstar[maxRec]
    #     sonDF = son0.sonMetaDF # Get ping metadata
    #     # sDF = son._interpTrack(df=sonDF, dropDup=True, filt=filter, deg=3) # Smooth trackline and reinterpolate trackpoints along spline
    #     sDF = pd.DataFrame()
    #     for name, group in sonDF.groupby('transect'):
    #         smoothed = son._interpTrack(df=group, dropDup=True, filt=filter, deg=3)
    #         smoothed['transect'] = int(name)
    #         sDF = pd.concat([sDF, smoothed], ignore_index=True)
    #     del sonDF

    #     ####################################
    #     ####################################
    #     # To remove gap between sonar tiles:
    #     # For chunk > 0, use coords from previous chunks second to last ping
    #     # and assign as current chunk's first ping coords
    #     # chunks = pd.unique(sDF['chunk_id'])

    #     # i = 1
    #     # while i <= max(chunks):
    #     #     # Get second to last row of previous chunk
    #     #     lastRow = sDF[sDF['chunk_id'] == i-1].iloc[[-2]]
    #     #     # Get index of first row of current chunk
    #     #     curRow = sDF[sDF['chunk_id'] == i].iloc[[0]]
    #     #     curRow = curRow.index[0]
    #     #     # Update current chunks first row from lastRow
    #     #     sDF.at[curRow, "lons"] = lastRow["lons"]
    #     #     sDF.at[curRow, "lats"] = lastRow["lats"]
    #     #     sDF.at[curRow, "utm_es"] = lastRow["utm_es"]
    #     #     sDF.at[curRow, "utm_ns"] = lastRow["utm_ns"]
    #     #     sDF.at[curRow, "cog"] = lastRow["cog"]

    #     #     i+=1
    #     # del lastRow, curRow, i

    #     chunks = pd.unique(sDF['chunk_id'])

    #     i = 1
    #     t = 0
    #     while i <= max(chunks):
    #         # Get second to last row of previous chunk
    #         lastRow = sDF[sDF['chunk_id'] == i-1].iloc[[-2]]
    #         # Get index of first row of current chunk
    #         curRow = sDF[sDF['chunk_id'] == i].iloc[[0]]
    #         curTransect = curRow['transect'].values[0]
    #         curRow = curRow.index[0]
            
    #         if curTransect == t:
    #             # Update current chunks first row from lastRow
    #             sDF.at[curRow, "lons"] = lastRow["lons"]
    #             sDF.at[curRow, "lats"] = lastRow["lats"]
    #             sDF.at[curRow, "utm_es"] = lastRow["utm_es"]
    #             sDF.at[curRow, "utm_ns"] = lastRow["utm_ns"]
    #             sDF.at[curRow, "cog"] = lastRow["cog"]
    #         else:
    #             t += 1

    #         i+=1
    #     del lastRow, curRow, i

    #     son0.smthTrk = sDF # Store smoothed trackline coordinates in rectObj.

    #     # Do positional correction
    #     if x_offset != 0.0 or y_offset != 0.0:
    #         son0._applyPosOffset(x_offset, y_offset)

    #     # Update other channel with smoothed coordinates
    #     # Determine which rectObj we need to update
    #     for i, son in enumerate(portstar):
    #         if i != maxRec:
    #             son1 = son # rectObj to update

    #     sDF = son0.smthTrk.copy() # Make copy of smoothed trackline coordinates
    #     # Update with correct record_num
    #     son1._loadSonMeta() # Load ping metadata
    #     df = son1.sonMetaDF
    #     sDF['chunk_id'] = df['chunk_id'] # Update chunk_id for smoothed coordinates
    #     sDF['record_num'] = df['record_num'] # Update record_num for smoothed coordinates
    #     son1.smthTrk = sDF # Store smoothed trackline coordinates in rectObj

    #     del sDF, df, son0, son1

    #     # Save smoothed trackline coordinates to file
    #     for son in portstar:
    #         outCSV = os.path.join(son.metaDir, "Trackline_Smth_"+son.beamName+".csv")
    #         son.smthTrk.to_csv(outCSV, index=False, float_format='%.14f')
    #         son.smthTrkFile = outCSV
    #         son._cleanup()
    #     del son, outCSV
    #     print("Done!")
    #     print("Time (s):", round(time.time() - start_time, ndigits=1))
    #     gc.collect()
    #     printUsage()

    #     ############################################################################
    #     # Calculate range extent coordinates                                       #
    #     ############################################################################
    #     # cog=True

    #     start_time = time.time()
    #     if cog:
    #         print("\nCalculating, smoothing, and interpolating range extent coordinates...")
    #     else:
    #         print("\nCalculating range extent coordinates from vessel heading...")
    #     Parallel(n_jobs= np.min([len(portstar), threadCnt]), verbose=10)(delayed(son._getRangeCoords)(flip, filterRange, cog) for son in portstar)
    #     print("Done!")
    #     print("Time (s):", round(time.time() - start_time, ndigits=1))
    #     gc.collect()
    #     printUsage()

    # else:
    #     print("\nUsing existing smoothed trackline.")

    ############################################################################
    # Smooth Trackline                                                         #
    ############################################################################

    smthTrkFilenames = smoothTrackline(projDir, x_offset, y_offset, nchunk, cog, threadCnt)
    for son in portstar:
        beam = son.beamName
        if beam == "ss_port" or beam == "ss_star":
            son.smthTrkFile = smthTrkFilenames[beam]

    ####################################
    ####################################
    # To remove gap between sonar tiles:
    # For chunk > 0, use coords from previous chunks second to last ping
    # and assign as current chunk's first ping coords

    for son in portstar:
        csv = son.smthTrkFile
        sDF = pd.read_csv(csv)

        chunks = pd.unique(sDF['chunk_id'])
        transects = pd.unique(sDF['transect'])

        # Update chunkMax while we are here
        chunkMax = max(chunks)
        son.chunkMax = int(chunkMax)

        i = 1
        t = 0
        while i <= max(chunks):

        # for i in chunks:

            # # Get second to last row of previous chunk
            # lastRow = sDF[sDF['chunk_id'] == i-1].iloc[[-2]]
            # Get index of first row of current chunk
            curRow = sDF[sDF['chunk_id'] == i].iloc[[0]]
            curTransect = curRow['transect'].values[0]
            curRow = curRow.index[0]
            
            if curTransect == t:
                # Get second to last row of previous chunk
                lastRow = sDF[sDF['chunk_id'] == i-1].iloc[[-2]]

                # Update current chunks first row from lastRow
                sDF.at[curRow, "lons"] = lastRow["lons"]
                sDF.at[curRow, "lats"] = lastRow["lats"]
                sDF.at[curRow, "utm_es"] = lastRow["utm_es"]
                sDF.at[curRow, "utm_ns"] = lastRow["utm_ns"]
                sDF.at[curRow, "cog"] = lastRow["cog"]
            else:
                t += 1

            i+=1
        del lastRow, curRow, i

        sDF.to_csv(csv, index=False)
        del sDF


    ############################################################################
    # Calculate range extent coordinates                                       #
    ############################################################################
    # cog=True

    start_time = time.time()
    if cog:
        print("\nCalculating, smoothing, and interpolating range extent coordinates...")
    else:
        print("\nCalculating range extent coordinates from vessel heading...")
    Parallel(n_jobs= np.min([len(portstar), threadCnt]), verbose=10)(delayed(son._getRangeCoords)(flip, filterRange, cog) for son in portstar)
    # for son in portstar:
    #     son._getRangeCoords(flip, filterRange, cog)
    print("Done!")
    print("Time (s):", round(time.time() - start_time, ndigits=1))
    gc.collect()
    printUsage()

    ############################################################################
    # Export Coverage and Trackline                                            #
    ############################################################################

    if coverage:
        start_time = time.time()
        print("\nExporting coverage and trackline shapefiles:\n")
        portstar[0]._exportTrkShp()

        trk_files = []
        for son in portstar:
            trk_files.append(son.smthTrkFile)

        portstar[0]._exportCovShp(trk_files)

        print("Done!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        gc.collect()
        printUsage()     

    ############################################################################
    # Rectify sonar imagery                                                    #
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

    if rect_wcp or rect_wcr:
        for son in portstar:
            # Set output directory
            son.outDir = os.path.join(son.projDir, son.beamName)

            # Get chunk id's
            if cog:
                chunks = son._getChunkID()
            else:
                chunks = son._getChunkID_Update()
                chunks = chunks[:-1]

            # Load sonMetaDF
            son._loadSonMeta()

            # Get colormap
            son._getSonColorMap(son_colorMap)

            print('\n\tExporting', len(chunks), 'GeoTiffs for', son.beamName)
            # for i in chunks:
            #     son._rectSonParallel(i, filter, cog, wgs=False)
            #     sys.exit()
            Parallel(n_jobs= np.min([len(chunks), threadCnt]))(delayed(son._rectSonParallel)(i, filter, cog, wgs=False) for i in tqdm(range(len(chunks))))
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

    # if banklines and not mosaic:
    #     print('\n\nExporting banklines requires sonar mosaic')
    #     print('Setting mosaic==1...')
    #     mosaic = 1

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
