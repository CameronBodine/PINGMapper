


from common_funcs import *
from c_sonObj import sonObj
# from osgeo import ogr
# import fiona
# from shapely.geometry import mapping, LineString, Point, Polygon
# import geopandas as gpd
import time
import matplotlib.pyplot as plt
from scipy.interpolate import splprep, splev

pd.set_option('precision', 16)

#===========================================


#===========================================
def getBearing(pntA, pntB):

    lonA, latA = pntA[0], pntA[1]
    lonB, latB = pntB[0], pntB[1]

    lat1 = np.deg2rad(latA)
    lat2 = np.deg2rad(latB)

    diffLong = np.deg2rad(lonB - lonA)
    bearing = np.arctan2(np.sin(diffLong) * np.cos(lat2), np.cos(lat1) * np.sin(lat2) - (np.sin(lat1) * np.cos(lat2) * np.cos(diffLong)))

    db = np.degrees(bearing)
    db = (db + 360) % 360

    return round(db, 1)

#===========================================
def getRangeCoords(df, pix_m):
    # extent = RangeDF['ping_cnt'].to_numpy()
    # yvec = np.squeeze(np.linspace(np.squeeze(pix_m),extent*np.squeeze(pix_m),extent))

    # print(df.info(),'\n')

    df['range'] = df['ping_cnt'] * pix_m

    # https://stackoverflow.com/questions/7222382/get-lat-long-given-current-point-distance-and-bearing
    R = 6371.393*1000 #Radius of the Earth
    # R = 6378.1
    brng = np.deg2rad(df['ping_bearing']).to_numpy()
    d = (df['range'].to_numpy())

    # print(df.iloc[0])
    # print((df['lats']).to_numpy())

    lat1 = np.deg2rad(df['lats']).to_numpy()
    lon1 = np.deg2rad(df['lons']).to_numpy()
    # print(np.finfo(lon1[0]).precision)

    lat2 = np.arcsin( np.sin(lat1) * np.cos(d/R) +
           np.cos(lat1) * np.sin(d/R) * np.cos(brng))


    lon2 = lon1 + np.arctan2( np.sin(brng) * np.sin(d/R) * np.cos(lat1),
                              np.cos(d/R) - np.sin(lat1) * np.sin(lat2))
    lat2 = np.degrees(lat2)
    lon2 = np.degrees(lon2)

    df['latr'] = lat2
    df['lonr'] = lon2
    print(df.lats)

    # print(df.head())
    # print(df.tail(),'\n\n')
    return df

#===========================================
def getMidpoint(gdf, df_out, i, geometry = 'geometry'):
    row = gdf.loc[i]
    geom = row[geometry]
    pntA = geom.coords[0]
    pntB = geom.coords[1]

    midX = (pntA[0] + pntB[0])/2
    midY = (pntA[1] + pntB[1])/2
    midpoint = Point(midX, midY)

    caltime = (row['timeStart'] + row['timeEnd'])/2

    data = {'geometry': [midpoint],
            'caltime': caltime}
    df_pnt = pd.DataFrame(data, columns =list(data.keys()))

    df_out = pd.concat([df_out, df_pnt])

    return df_out

#===========================================
def makeLines(gdf, df_out, i, geometry = 'geometry'):
    # http://ryan-m-cooper.com/blog/gps-points-to-line-segments.html
    row0 = gdf.loc[i]
    row1 = gdf.loc[i + 1]

    time0 = row0['caltime']
    time1 = row1['caltime']

    geom0 = row0[geometry]
    geom1 = row1[geometry]

    start, end = [(geom0.x, geom0.y), (geom1.x, geom1.y)]
    line = LineString([start, end])

    # Create a DataFrame to hold record
    data = {'id': int(i),
            'timeStart': time0,
            'timeEnd': time1,
            'geometry': [line]}
    df_line = pd.DataFrame(data, columns = list(data.keys()))

    # Add record DataFrame of compiled records
    df_out = pd.concat([df_out, df_line])
    return df_out

#===========================================
def rectify_master_func(sonFiles, humFile, projDir):
    start_time = time.time()

    ####################################################
    # Check if sonObj pickle exists, append to metaFiles
    metaDir = os.path.join(projDir, "meta")
    if os.path.exists(metaDir):
        metaFiles = sorted(glob(metaDir+os.sep+"*.meta"))
    else:
        sys.exit("No SON metadata files exist")

    ############################################
    # Create a sonObj instance from pickle files
    sonObjs = []
    for meta in metaFiles:
        son = pickle.load(open(meta, 'rb'))
        sonObjs.append(son)

    #####################################
    # Load metadata csv from port or star
    # Determine which sonObj is port/star
    portstar = []
    for son in sonObjs:
        beam = son.beamName
        if beam == "sidescan_port" or beam == "sidescan_starboard":
            portstar.append(son)

    # Load sonar metadata
    for son in portstar:
        son._loadSonMeta()


    ############################################################################
    # Smoothing Trackline
    # Tool:
    # https://docs.scipy.org/doc/scipy-0.14.0/reference/tutorial/interpolate.html#spline-interpolation
    # Adapted from:
    # https://github.com/remisalmon/gpx_interpolate
    print("\nSmoothing trackline...")
    ###################################
    # Delete duplicates sharing lat/lon
    pd.options.display.float_format = '{:.6f}'.format

    son = portstar[0]
    dfOrig = son.sonMetaDF
    df = dfOrig.copy()
    df.drop_duplicates(subset=['e', 'n'], inplace=True)

    ##########################################
    # Filter Trackpoints:
    # Select every 10 position, including last
    last = dfOrig.iloc[-1].to_dict()
    df20 = df.iloc[::10].reset_index(drop=True)
    df = df20.append(last, ignore_index=True)

    # Save to file
    # outCSV = os.path.join(portstar[0].metaDir, "forTrackline.csv")
    # df.to_csv(outCSV, index=False, float_format='%.14f')

    ############################################
    # Smooth trackline and interpolate all pings
    n = len(dfOrig) # Total pings to interpolate

    #User params
    deg = 3 # interp in degree: 1 for linear; 2-5 for spline
    num = n # Number of interpolated track points

    # Collect lon, lat, and time ellapsed
    x = df.lon.to_numpy()
    y = df.lat.to_numpy()
    t = df.time_s.to_numpy() # Cumulative time elapsed

    # Fit spline to filtered trackpoints
    tck, _ = splprep([x,y], u=t, k=deg, s=0)

    # Interpolate positions
    print("\nInterpolating ping locations...")
    u_interp = dfOrig.time_s.to_numpy() # Collect time elapsed from all pings
    x_interp = splev(u_interp, tck) # Interpolate positions based on time elapsed

    # Store smoothed trackpoints in df
    smooth = {'lons': x_interp[0],
              'lats': x_interp[1]}
    sDF = pd.DataFrame(smooth) # smoothed DF

    # Calculate utm coordinates from smooth trackpoints
    trans = sonObjs[0].trans
    e_smth, n_smth = trans(smooth['lons'], smooth['lats'])
    sDF['es'] = e_smth
    sDF['ns'] = n_smth

    # Calculate COG from smoothed lat/lon
    i = 0
    while i < len(sDF) - 1:
        pntA = sDF.loc[i, ['lons', 'lats']]
        pntB = sDF.loc[i+1, ['lons', 'lats']]
        cog = getBearing(pntA, pntB)
        sDF.loc[i, 'cog'] = cog
        i+=1
    sDF.loc[len(sDF) - 1, 'cog'] = cog

    # Get record number for port and starboard pings
    # Calculate ping direction
    for son in sonObjs:
        son._loadSonMeta()
        record_num = son.sonMetaDF['record_num']
        beam = son.beamName
        if beam == "sidescan_port":
            sDF['port_record_num'] = record_num
            sDF['port_ping_bearing'] = (sDF['cog'] - 90) % 360
        elif beam == "sidescan_starboard":
            sDF['star_record_num'] = record_num
            sDF['star_ping_bearing'] = (sDF['cog'] + 90) % 360

    # Plot smoothed trackline
    # plt.figure()
    # plt.plot(x, y, 'x', x_interp[0], x_interp[1])
    # plt.savefig(os.path.join(portstar[0].metaDir, "SmoothedTrackPlt.png"))
    ############################################################################

    # Workflow for getting outer extent of rectified image
    # Need to make some sort of loop???? (maybe not yet)

    # 3) Calculate pixel size
    # load some general info from first ping
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

    # What 't' to use?????
    # t = dfOrig.iloc[0]['tempC']/100 # water temperature/10
    t = dfOrig.iloc[0]['t']
    f = dfOrig.iloc[0]['f'] # frequency
    c = 1449.05 + 45.7*t - 5.21*t**2 + 0.23*t**3 + (1.333 - 0.126*t + 0.009*t**2)*(S - 35) # speed of sound in water

    # theta at 3dB in the horizontal
    theta3dB = np.arcsin(c/(t*(f*1000)))
    #resolution of 1 sidescan pixel to nadir
    ft = (np.pi/2)*(1/theta3dB) #/ (f/455)

    # theta = np.squeeze(metadata['heading'].values)/(180/np.pi)
    #
    # #dx = np.arcsin(c/(1000*t*f))
    pix_m = (1/ft)#*1.1 # size of pixel in meters (??)

    # Prepare portside data
    pRangeDF = sDF[['lons','lats','port_record_num','port_ping_bearing']].set_index('port_record_num')
    for son in portstar:
        if son.beamName=='sidescan_port':
            sonDF = son.sonMetaDF
        else:
            pass
    sonDF = sonDF[['ping_cnt', 'record_num']].set_index('record_num')
    pRangeDF = pRangeDF.join(sonDF)
    pRangeDF.rename(columns={'port_ping_bearing':'ping_bearing'}, inplace=True)

    # Prepare starboard data
    sRangeDF = sDF[['lons','lats','star_record_num','star_ping_bearing']].set_index('star_record_num')
    for son in portstar:
        if son.beamName=='sidescan_starboard':
            sonDF = son.sonMetaDF
        else:
            pass
    sonDF = sonDF[['ping_cnt', 'record_num']].set_index('record_num')
    sRangeDF = sRangeDF.join(sonDF)
    sRangeDF.rename(columns={'star_ping_bearing':'ping_bearing'}, inplace=True)

    pRangeDF = getRangeCoords(pRangeDF, pix_m)
    sRangeDF = getRangeCoords(sRangeDF, pix_m)

    # Save interpolated points to file
    outCSV = os.path.join(portstar[0].metaDir, "Trackline_smooth.csv")
    sDF.to_csv(outCSV, index=False, float_format='%.14f')

    outCSV = os.path.join(portstar[0].metaDir, "Port_extent.csv")
    pRangeDF.to_csv(outCSV, index=False, float_format='%.14f')

    outCSV = os.path.join(portstar[0].metaDir, "Star_extent.csv")
    sRangeDF.to_csv(outCSV, index=False, float_format='%.14f')
