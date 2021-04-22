
from __future__ import division
from common_funcs import *

# from c_sonObj import sonObj
from c_rectObj import rectObj

#===========================================
def rectify_master_func(sonFiles, humFile, projDir):
    flip = False #Flip port/star
    filter = 50 #For filtering pings
    filterRange = 20
    remWater = False # Export geotiff w/o water

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
    # for son in portstar:
    #     son._rectSon(remWater, filter, wgs=False)
    print("\n\tRectifying and exporting GeoTiffs...")
    Parallel(n_jobs= np.min([len(portstar), cpu_count()]), verbose=10)(delayed(son._rectSon)(remWater, filter, wgs=False) for son in portstar)
