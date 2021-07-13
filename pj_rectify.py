
from __future__ import division
from common_funcs import *

# from c_sonObj import sonObj
from c_rectObj import rectObj

#===========================================
def rectify_master_func(sonFiles, humFile, projDir, nchunk, rect_wcp=False, rect_wcr=False):
    flip = False #Flip port/star
    # filter = 50 #For filtering pings
    filter = int(nchunk*0.1)
    # filterRange = 20
    filterRange = int(nchunk*0.05)

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
        sonTemp = pickle.load(open(meta, 'rb'))

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

    # del rectObjs

    #####################
    #####################
    # Smoothing Trackline
    # Tool:
    # https://docs.scipy.org/doc/scipy-0.14.0/reference/tutorial/interpolate.html#spline-interpolation
    # Adapted from:
    # https://github.com/remisalmon/gpx_interpolate
    print("\n\tSmoothing trackline...")

    # As side scan beams use same transducer/gps coords,
    # we will smooth one beam's trackline and use for both
    son0 =  portstar[0]
    son0._loadSonMeta()
    sonDF = son0.sonMetaDF
    sDF = son0._interpTrack(df=sonDF, dropDup=True, filt=filter, deg=3)

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
        # print(sDF.at[curRow, lons],":", lastRow[lons])

        i+=1

    son0.smthTrk = sDF

    # Update other channel with smoothed coordinates
    son1 = portstar[1]
    sDF = son0.smthTrk.copy()
    # Update with correct record_num
    son1._loadSonMeta()
    df = son1.sonMetaDF
    sDF['chunk_id'] = df['chunk_id']
    sDF['record_num'] = df['record_num']
    son1.smthTrk = sDF

    del sDF

    # Save to file
    outCSV = os.path.join(son.metaDir, "Trackline_Smth.csv")
    son0.smthTrk.to_csv(outCSV, index=False, float_format='%.14f')

    ################################################
    # Calculate ping direction
    print("\n\tCalculating range extent...")
    # Calculate range extent lat/lon
    for son in portstar:
        son._getRangeCoords(flip)

    print("\n\tSmooth and interpolate range extent...")
    # Filter pings and interpolate
    # for son in portstar:
    #     son._interpRangeCoords(filterRange)
    Parallel(n_jobs= np.min([len(portstar), cpu_count()]), verbose=10)(delayed(son._interpRangeCoords)(filterRange) for son in portstar)

    ################################################
    print("\n\tRectifying and exporting GeoTiffs...")
    # for son in portstar:
    #     son._rectSon(remWater, filter, wgs=False)
    if rect_wcp:
        print('\t\tRectifying with Water Column')
        remWater = False
        Parallel(n_jobs= np.min([len(portstar), cpu_count()]), verbose=10)(delayed(son._rectSon)(remWater, filter, wgs=False) for son in portstar)
    if rect_wcr:
        print('\t\tRectifying with Water Column Removed')
        remWater = True
        Parallel(n_jobs= np.min([len(portstar), cpu_count()]), verbose=10)(delayed(son._rectSon)(remWater, filter, wgs=False) for son in portstar)
