
from __future__ import division
from funcs_common import *

from c_rectObj import rectObj

from rasterio.merge import merge

#===============================================================================
def rectify_master_func(sonFiles,
                        humFile,
                        projDir,
                        nchunk,
                        rect_wcp=False,
                        rect_src=False,
                        adjDep=0,
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

    '''

    ############
    # Parameters
    flip = False #Flip port/star
    filter = int(nchunk*0.1)
    filterRange = int(nchunk*0.05)

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
        sonTemp = pickle.load(open(meta, 'rb')) # Load class attributes from pickle

        # Create rectObj class (child of sonObj)
        son = rectObj()

        # Populate rectObj attributes from sonTemp
        for attr, value in sonTemp.__dict__.items():
            setattr(son, attr, value)
        rectObjs.append(son)
        del sonTemp

    #####################################
    # Determine which sonObj is port/star
    portstar = []
    for son in rectObjs:
        beam = son.beamName
        if beam == "ss_port" or beam == "ss_star":
            portstar.append(son)
        else:
            del son

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

    # As side scan beams use same transducer/gps coords,
    ## we will smooth one beam's trackline and use for both.
    ## Use the beam with the most records.
    maxRec = 0
    maxLen = 0
    for i, son in enumerate(portstar):
        son._loadSonMeta()
        sonLen = len(son.sonMetaDF)
        if sonLen > maxLen:
            maxLen = sonLen
            maxRec = i

    # Now we will smooth
    son0 = portstar[maxRec]
    sonDF = son0.sonMetaDF
    sDF = son._interpTrack(df=sonDF, dropDup=True, filt=filter, deg=3)

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

    son0.smthTrk = sDF

    # Update other channel with smoothed coordinates
    for i, son in enumerate(portstar):
        if i != maxRec:
            son1 = son

    sDF = son0.smthTrk.copy()
    # Update with correct record_num
    son1._loadSonMeta()
    df = son1.sonMetaDF
    sDF['chunk_id'] = df['chunk_id']
    sDF['record_num'] = df['record_num']
    son1.smthTrk = sDF

    del sDF

    # Save to file
    for son in portstar:
        outCSV = os.path.join(son.metaDir, "Trackline_Smth_"+son.beamName+".csv")
        son.smthTrk.to_csv(outCSV, index=False, float_format='%.14f')
    print("Done!")

    ################################################
    # Calculate ping direction
    print("\nCalculating, smoothing, and interpolating range extent...")
    Parallel(n_jobs= np.min([len(portstar), cpu_count()]), verbose=10)(delayed(son._getRangeCoords)(flip, filterRange) for son in portstar)
    # portstar[1]._getRangeCoords(flip, filterRange)
    print("Done!")

    ################################################
    print("\nRectifying and exporting GeoTiffs:\n")
    # rect_src = False
    # rect_wcp = False

    if rect_wcp:
        print('Rectifying with Water Column Present...')
        remWater = False
        Parallel(n_jobs= np.min([len(portstar), cpu_count()]), verbose=10)(delayed(son._rectSon)(remWater, filter, adjDep, wgs=False) for son in portstar)
        # portstar[-1]._rectSon(remWater, filter, adjDep, wgs=False)
        print("Done!")

    if rect_src:
        print('\nRectifying with Water Column Removed...')
        remWater = True
        Parallel(n_jobs= np.min([len(portstar), cpu_count()]), verbose=10)(delayed(son._rectSon)(remWater, filter, adjDep, wgs=False) for son in portstar)
        print("Done!")

    ################################################
    # rect_src = True
    # rect_wcp = True

    if mosaic > 0:
        print("\nMosaicing GeoTiffs:\n")
        imgDirs = []
        for son in portstar:
            imgDirs.append(son.outDir)
            projDir = son.projDir
            filePrefix = os.path.split(projDir)[-1]
        imgsToMosaic = []
        if rect_wcp:
            wrcToMosaic = []
            for path in imgDirs:
                path = os.path.join(path, 'rect_wcp')
                imgs = glob(os.path.join(path, '*.tif'))
                for img in imgs:
                    wrcToMosaic.append(img)
            imgsToMosaic.append(wrcToMosaic)
        if rect_src:
            srcToMosaic = []
            for path in imgDirs:
                path = os.path.join(path, 'rect_src')
                imgs = glob(os.path.join(path, '*.tif'))
                for img in imgs:
                    srcToMosaic.append(img)
            imgsToMosaic.append(srcToMosaic)

        for imgs in imgsToMosaic:
            srcFilesToMosaic = []
            for img in imgs:
                src = rasterio.open(img)
                srcFilesToMosaic.append(src)
            fileSuffix = os.path.split(os.path.dirname(img))[-1] + '_mosaic.tif'
            outFile = os.path.join(projDir, filePrefix+'_'+fileSuffix)
            # crs = src.crs
            outMosaic, outTrans = merge(srcFilesToMosaic)
            outMeta = src.meta.copy()
            outMeta.update({'height': outMosaic.shape[1],
                            'width': outMosaic.shape[2],
                            'transform': outTrans})
            with rasterio.open(outFile, 'w', **outMeta) as dest:
                dest.write(outMosaic)

            # if mosaic == 2:
            #     geotiff = rasterio.open(outFile)
            #     print(geotiff)
