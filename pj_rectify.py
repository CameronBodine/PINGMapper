
from __future__ import division
from common_funcs import *

# from c_sonObj import sonObj
from c_rectObj import rectObj

#===========================================
def rectify_master_func(sonFiles, humFile, projDir):
    flip = False #Flip port/star
    filter = 50 #For filtering pings
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
    # Load metadata csv from port or star
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

    ########################################
    # load some general info from first ping
    # Info used to calc pixel size in meters
    print("\n\tDetermine Pixel Size...")
    son = portstar[0] # grab first sonObj
    humDat = son.humDat # get DAT metadata

    water_type = humDat['water_type'] # load water type
    if water_type=='fresh':
        S = 1
    elif water_type=='shallow salt':
        S = 30
    elif water_type=='deep salt':
        S = 35
    else:
        S = 1

    t = df.iloc[0]['t'] # transducer length
    f = df.iloc[0]['f'] # frequency
    c = 1449.05 + 45.7*t - 5.21*t**2 + 0.23*t**3 + (1.333 - 0.126*t + 0.009*t**2)*(S - 35) # speed of sound in water

    # theta at 3dB in the horizontal
    theta3dB = np.arcsin(c/(t*(f*1000)))
    #resolution of 1 sidescan pixel to nadir
    ft = (np.pi/2)*(1/theta3dB)
    # size of pixel in meters
    pix_m = (1/ft)

    ################################################
    # Calculate ping direction
    # Calculate range extent lat/lon
    for son in portstar:
        son._getRangeCoords(flip, pix_m)

    # Filter pings and interpolate
    for son in portstar:
        son._interpRangeCoords(filter)

    ################################################
    for son in portstar:
        son._rectSon(remWater)
