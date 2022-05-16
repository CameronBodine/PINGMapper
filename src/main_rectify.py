
from __future__ import division
from funcs_common import *

from class_rectObj import rectObj
from class_portstarObj import portstarObj

#===============================================================================
def rectify_master_func(sonFiles,
                        humFile,
                        projDir,
                        nchunk=500,
                        rect_wcp=False,
                        rect_src=False,
                        mosaic=0):
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
    rect_src : bool
        DESCRIPTION - Flag to export georectified sonar tiles w/ water column
                      removed & slant range corrected (src).
                      True = export georectified src sonar tiles;
                      False = do not export georectified src sonar tiles.
        EXAMPLE -     rect_src = True
    mosaic : int
        DESCRIPTION - Mosaic exported georectified sonograms to a virtual raster
                      (vrt) as specified with the `rect_wcp` and `rect_src` flags.
                      See https://gdal.org/drivers/raster/vrt.html for more info.
                      Overviews are created by default.
                      0 = do not export georectified mosaic(s);
                      1 = export georectified mosaic(s).

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
    |--|ss_port (if B002.SON OR B003.SON [tranducer flipped] available)
    |  |--rect_src [rect_src=True]
    |     |--*.tif : Portside side scan (ss) georectified sonar tiles, w/
    |     |          water column removed & slant range corrected (src)
    |  |--rect_wcp [wcp=True]
    |     |--*.tif : Portside side scan (ss) georectified sonar tiles, w/
    |     |          water column present (wcp)
    |
    |--|ss_star (if B003.SON OR B002.SON [tranducer flipped] available)
    |  |--rect_src [src=True]
    |     |--*.tif : Starboard side scan (ss) georectified sonar tiles, w/
    |     |          water column removed & slant range corrected (src)
    |  |--rect_wcp [wcp=True]
    |     |--*.tif : Starboard side scan (ss) georectified sonar tiles, w/
    |     |          water column present (wcp)
    |
    |--*_src_mosaic.tif : SRC mosaic [rect_src=True & mosaic=1]
    |--*_wcp_mosaic.tif : WCP mosaic [rect_wcp=True & mosaic=1]
    '''

    ############
    # Parameters
    flip = False #Flip port/star
    filter = int(nchunk*0.1) #Filters trackline coordinates for smoothing
    filterRange = filter #int(nchunk*0.05) #Filters range extent coordinates for smoothing

    ############################################################################
    # Create rectObj() instance from previously created sonObj() instance      #
    ############################################################################

    ####################################################
    # Check if sonObj pickle exists, append to metaFiles
    metaDir = os.path.join(projDir, "meta")
    if os.path.exists(metaDir):
        metaFiles = sorted(glob(metaDir+os.sep+"*.meta"))
    else:
        sys.exit("No SON metadata files exist")

    #############################################
    # Create a rectObj instance from pickle files
    rectObjs = []
    for meta in metaFiles:
        son = rectObj(meta) # Initialize rectObj()
        rectObjs.append(son) # Store rectObj() in rectObjs[]

    #####################################
    # Determine which sonObj is port/star
    portstar = []
    for son in rectObjs:
        beam = son.beamName
        if beam == "ss_port" or beam == "ss_star":
            portstar.append(son)
        else:
            del son # Remove non-port/star objects since they can't be rectified

    ############################################################################
    # Smooth GPS trackpoint coordinates                                        #
    ############################################################################

    #####################
    #####################
    # Smoothing Trackline
    # Tool:
    # https://docs.scipy.org/doc/scipy-0.14.0/reference/tutorial/interpolate.html#spline-interpolation
    # Adapted from:
    # https://github.com/remisalmon/gpx_interpolate
    print("\nSmoothing trackline...")

    # As side scan beams use same transducer/gps coords, we will smooth one
    ## beam's trackline and use for both. Use the beam with the most sonar records.
    maxRec = 0 # Stores index of recording w/ most sonar records.
    maxLen = 0 # Stores length of sonar record
    for i, son in enumerate(portstar):
        son._loadSonMeta() # Load sonar record metadata
        sonLen = len(son.sonMetaDF) # Number of sonar records
        if sonLen > maxLen:
            maxLen = sonLen
            maxRec = i

    # Now we will smooth using sonar beam w/ most records.
    son0 = portstar[maxRec]
    sonDF = son0.sonMetaDF # Get sonar record metadata
    sDF = son._interpTrack(df=sonDF, dropDup=True, filt=filter, deg=3) # Smooth trackline and reinterpolate trackpoints along spline

    ####################################
    ####################################
    # To remove gap between sonar tiles:
    # For chunk > 0, use coords from previous chunks last ping
    # and assign as current chunk's first ping coords
    chunks = pd.unique(sDF['chunk_id'])

    i = 1
    while i <= max(chunks):
        # Get last row of previous chunk
        lastRow = sDF[sDF['chunk_id'] == i-1].iloc[[-1]]
        # Get index of first row of current chunk
        curRow = sDF[sDF['chunk_id'] == i].iloc[[0]]
        curRow = curRow.index[0]
        # Update current chunks first row from lastRow
        sDF.at[curRow, "lons"] = lastRow["lons"]
        sDF.at[curRow, "lats"] = lastRow["lats"]
        sDF.at[curRow, "utm_es"] = lastRow["utm_es"]
        sDF.at[curRow, "utm_ns"] = lastRow["utm_ns"]
        sDF.at[curRow, "cog"] = lastRow["cog"]

        i+=1

    son0.smthTrk = sDF # Store smoothed trackline coordinates in rectObj.

    # Update other channel with smoothed coordinates
    # Determine which rectObj we need to update
    for i, son in enumerate(portstar):
        if i != maxRec:
            son1 = son # rectObj to update

    sDF = son0.smthTrk.copy() # Make copy of smoothed trackline coordinates
    # Update with correct record_num
    son1._loadSonMeta() # Load sonar record metadata
    df = son1.sonMetaDF
    sDF['chunk_id'] = df['chunk_id'] # Update chunk_id for smoothed coordinates
    sDF['record_num'] = df['record_num'] # Update record_num for smoothed coordinates
    son1.smthTrk = sDF # Store smoothed trackline coordinates in rectObj

    del sDF

    # Save smoothed trackline coordinates to file
    for son in portstar:
        outCSV = os.path.join(son.metaDir, "Trackline_Smth_"+son.beamName+".csv")
        son.smthTrk.to_csv(outCSV, index=False, float_format='%.14f')
    print("Done!")

    ############################################################################
    # Calculate range extent coordinates                                       #
    ############################################################################
    print("\nCalculating, smoothing, and interpolating range extent coordinates...")
    Parallel(n_jobs= np.min([len(portstar), cpu_count()]), verbose=10)(delayed(son._getRangeCoords)(flip, filterRange) for son in portstar)
    print("Done!")

    ############################################################################
    # Rectify sonar imagery                                                    #
    ############################################################################
    print("\nRectifying and exporting GeoTiffs:\n")

    if rect_wcp:
        print('Rectifying with Water Column Present...')
        remWater = False
        for son in portstar:
            son.rect_wcp = True
            # Locate and open smoothed trackline/range extent file
            trkMetaFile = os.path.join(son.metaDir, "Trackline_Smth_"+son.beamName+".csv")
            trkMeta = pd.read_csv(trkMetaFile)

            # Determine what chunks to process
            chunks = pd.unique(trkMeta['chunk_id']).astype('int') # Store chunk values in list
            print('\n\tExporting', len(chunks), 'GeoTiffs for', son.beamName)
            Parallel(n_jobs= np.min([len(chunks), cpu_count()]), verbose=10)(delayed(son._rectSonParallel)(i, remWater, filter, wgs=False) for i in chunks)

    if rect_src:
        print('\nRectifying with Water Column Removed...')
        remWater = True
        for son in portstar:
            son.rect_src = True
            # Locate and open smoothed trackline/range extent file
            trkMetaFile = os.path.join(son.metaDir, "Trackline_Smth_"+son.beamName+".csv")
            trkMeta = pd.read_csv(trkMetaFile)

            # Determine what chunks to process
            chunks = pd.unique(trkMeta['chunk_id']).astype('int') # Store chunk values in list
            print('\n\tExporting', len(chunks), 'GeoTiffs for', son.beamName)
            Parallel(n_jobs= np.min([len(chunks), cpu_count()]), verbose=10)(delayed(son._rectSonParallel)(i, remWater, filter, wgs=False) for i in chunks)

    if rect_wcp or rect_src:
        for son in portstar:
            del son.sonMetaDF
            del son.smthTrk
    print("Done!")

    ############################################################################
    # Mosaic imagery                                                           #
    ############################################################################
    overview = True
    if mosaic > 0:
        print("\nMosaicing GeoTiffs...")
        psObj = portstarObj(portstar)
        psObj._createMosaic(mosaic, overview)
        print("Done!")
