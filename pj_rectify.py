


from common_funcs import *
from c_sonObj import sonObj
# from osgeo import ogr
# import fiona
# from shapely.geometry import mapping, LineString, Point, Polygon
# import geopandas as gpd
import time
import matplotlib.pyplot as plt
from scipy.interpolate import splprep, splev

#===========================================


#===========================================
def getBearing(pntA, pntB, geometry='geometry'):

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
    outCSV = os.path.join(portstar[0].metaDir, "forTrackline.csv")
    df.to_csv(outCSV, index=False, float_format='%.14f')

    ############################################
    # Smooth trackline and interpolate all pings
    n = len(dfOrig) # Total pings to interpolate

    #User params
    deg = 5 # interp in degree: 1 for linear; 2-5 for spline
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
    smooth = {'lon_smth': x_interp[0],
              'lat_smth': x_interp[1]}
    smoothDF = pd.DataFrame(smooth)

    # Calculate utm coordinates from smooth trackpoints
    trans = sonObjs[0].trans
    e_smth, n_smth = trans(smooth['lon_smth'], smooth['lat_smth'])
    smoothDF['e_smth'] = e_smth
    smoothDF['n_smth'] = n_smth

    # Get record number for port and starboard pings
    for son in sonObjs:
        son._loadSonMeta()
        record_num = son.sonMetaDF['record_num']
        beam = son.beamName
        if beam == "sidescan_port":
            smoothDF['port_record_num'] = record_num
        elif beam == "sidescan_starboard":
            smoothDF['star_record_num'] = record_num

    # Save interpolated points to file
    outCSV = os.path.join(portstar[0].metaDir, "Trackline_smooth.csv")
    smoothDF.to_csv(outCSV, index=False, float_format='%.14f')

    # Plot smoothed trackline
    # plt.figure()
    # plt.plot(x, y, 'x', x_interp[0], x_interp[1])
    # plt.savefig(os.path.join(portstar[0].metaDir, "test.png"))


    ############################################################################
