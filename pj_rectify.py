

from __future__ import division
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

    # return np.round(db, 1)
    return db

#===========================================
def getRangeCoords(df, pix_m, side):
    # extent = RangeDF['ping_cnt'].to_numpy()
    # yvec = np.squeeze(np.linspace(np.squeeze(pix_m),extent*np.squeeze(pix_m),extent))

    # print(df.info(),'\n')

    lats = 'lats'
    lons = 'lons'
    range = side+'_range'
    ping_cnt = 'ping_cnt'
    ping_bearing = side+'_ping_bearing'
    lonr = side+'_lonr'
    latr = side+'_latr'

    # Calculate max range for each chunk
    chunk = df.groupby('chunk_id')
    maxPing = chunk[ping_cnt].max()
    for i in maxPing.index:
        df.loc[df['chunk_id']==i, range] = maxPing[i]*pix_m

    # https://stackoverflow.com/questions/7222382/get-lat-long-given-current-point-distance-and-bearing
    R = 6371.393*1000 #Radius of the Earth
    # R = 6378.1
    brng = np.deg2rad(df[ping_bearing]).to_numpy()
    d = (df[range].to_numpy())

    # print(df.iloc[0])
    # print((df['lats']).to_numpy())

    lat1 = np.deg2rad(df[lats]).to_numpy()
    lon1 = np.deg2rad(df[lons]).to_numpy()
    # print(np.finfo(lon1[0]).precision)

    lat2 = np.arcsin( np.sin(lat1) * np.cos(d/R) +
           np.cos(lat1) * np.sin(d/R) * np.cos(brng))

    lon2 = lon1 + np.arctan2( np.sin(brng) * np.sin(d/R) * np.cos(lat1),
                              np.cos(d/R) - np.sin(lat1) * np.sin(lat2))
    lat2 = np.degrees(lat2)
    lon2 = np.degrees(lon2)

    df[lonr] = lon2
    df[latr] = lat2

    # print(df.head())
    # print(df.tail(),'\n\n')
    return df

#===========================================
def interpTrack(df, dfOrig=None, xlon='lon', ylat='lat', xutm='utm_x',
                yutm='utm_y', zU='time_s', filt=0, dist=0, deg=3, dropDup=False):
    # Make copy of df to work on
    if dfOrig is None:
        dfOrig = df
        df = dfOrig.copy()

    # Drop Duplicates
    if dropDup is True:
        df.drop_duplicates(subset=[xlon, ylat], inplace=True)

    # Extract every `filt` record, including last value
    if filt>0:
        lastRow = df.iloc[-1].to_dict()
        try:
            dfFilt = df.iloc[::filt].reset_index(drop=False)
        except:
            dfFilt = df.iloc[::filt].reset_index(drop=True)
        dfFilt = dfFilt.append(lastRow, ignore_index=True)
    else:
        dfFilt = df.reset_index(drop=False)

    # Filter by distance
    if dist>0:
        for i, row in dfFilt.iterrows():
            pntAx, pntAy = row[xutm], row[yutm]
            try:
                pntBx, pntBy = dfFilt.iloc[i+1][xutm], dfFilt.iloc[i+1][yutm]
                pntDist = np.sqrt( (pntBx-pntAx)**2 + (pntBy - pntAy)**2)
            except:
                pntDist = 0

            if pntDist < dist and pntDist != 0:
                dfFilt.drop(i+1, inplace=True)
    else:
        pass

    # Try smoothing trackline
    x=dfFilt[xlon].to_numpy()
    y=dfFilt[ylat].to_numpy()
    t=dfFilt[zU].to_numpy()

    # Attempt to fix error
    # https://stackoverflow.com/questions/47948453/scipy-interpolate-splprep-error-invalid-inputs
    okay = np.where(np.abs(np.diff(x))+np.abs(np.diff(y))>0)
    x = np.r_[x[okay], x[-1]]
    y = np.r_[y[okay], y[-1]]
    t = np.r_[t[okay], t[-1]]

    tck, _ = splprep([x,y], u=t, k=deg, s=0)

    u_interp = dfOrig[zU].to_numpy()
    x_interp = splev(u_interp, tck)

    # Store smoothed trackpoints in df
    smooth = {xlon+'s': x_interp[0],
              ylat+'s': x_interp[1],
              'record_num': dfOrig.index.values}
    sDF = pd.DataFrame(smooth).set_index('record_num')

    dfOrig.set_index('record_num')

    for col in list(df.columns):
        sDF[col] = dfOrig[col]

    sDF.reset_index(drop=True)
    try:
        dfOrig.reset_index(drop=False)
    except:
        dfOrig.reset_index(drop=True)

    return sDF, dfFilt, dfOrig

# #===========================================
# def lineIntersect(line1, line2):
#     xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
#     ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])
#     print(line1[0][0])
#     print(line1[1][0])
#
#     def det(a, b):
#         return a[0] * b[1] - a[1] * b[0]
#
#     div = det(xdiff, ydiff)
#     if div == 0:
#         isIntersect = False
#     else:
#         isIntersect = True
#
#     return isIntersect

#===========================================
def lineIntersect(line1, line2):
    #https://stackoverflow.com/questions/20677795/how-do-i-compute-the-intersection-point-of-two-lines
    def line(p1, p2):
        A = (p1[1] - p2[1])
        B = (p2[0] - p1[0])
        C = (p1[0]*p2[1] - p2[0]*p1[1])
        return A, B, -C

    def intersection(L1, L2):
        D  = L1[0] * L2[1] - L1[1] * L2[0]
        Dx = L1[2] * L2[1] - L1[1] * L2[2]
        Dy = L1[0] * L2[2] - L1[2] * L2[0]
        if D != 0:
            x=Dx/D
            y=Dy/D
            return x,y
        else:
            return False

    def isBetween(line1, c):
        ax, ay = line1[0][0], line1[0][1]
        bx, by = line1[1][0], line2[1][1]
        cx, cy = c[0], c[1]
        xIntersect=yIntersect=False

        print(min(ax,bx),':',cx,':',max(ax,bx))
        print(min(ay,by),':',cy,':',max(ay,by))

        if (cx >= min(ax,bx)-5) and (cx <= max(ax,bx)+5):
            xIntersect = True
        if (cy >= min(ay,by)-5) and (cy <= max(ay,by)+5):
            yIntersect = True
        if xIntersect is True and yIntersect is True:
            isIntersect = True
        else:
            isIntersect = False
        return isIntersect

    L1 = line(line1[0], line1[1])
    L2 = line(line2[0], line2[1])
    c = intersection(L1, L2)
    if c is not False:
        I = isBetween(line1, c)
    else:
        I = False
    return I

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
    print("\n\tSmoothing trackline...")
    ###################################
    # Load sonMetaDF
    son = portstar[0]
    df = son.sonMetaDF

    ##########################################
    # Filter, smooth and interpolate Trackpoints:
    sDF, dfFilt, dfOrig = interpTrack(df, xlon='lon', ylat='lat', xutm='utm_x', yutm='utm_y',
                                      zU='time_s', filt=50, dist=0, deg=3, dropDup=True)

    # ##########################################################
    # Get first ping for each chunk, and last ping for recording
    # chunkDF = df.groupby('chunk_id').first().reset_index(drop=False)
    # chunkDF = chunkDF.append(df.iloc[-1], ignore_index=True)
    #
    # sDF, dfFilt, dfOrig = interpTrack(chunkDF, df, xlon='lon', ylat='lat', xutm='utm_x', yutm='utm_y',
    #                                   zU='time_s', filt=0, dist=0, deg=3, dropDup=False)

    ############################################
    # Smooth trackline and interpolate all pings
    trans = sonObjs[0].trans
    e_smth, n_smth = trans(sDF['lons'].to_numpy(), sDF['lats'].to_numpy())
    sDF['es'] = e_smth
    sDF['ns'] = n_smth

    #####################################
    # Calculate COG from smoothed lat/lon
    print("\n\tCalculating COG...")
    # SLOWWWWWW
    # i = 0
    # while i < len(sDF) - 1:
    #     pntA = sDF.loc[i, ['lons', 'lats']]
    #     pntB = sDF.loc[i+1, ['lons', 'lats']]
    #     cog = getBearing(pntA, pntB)
    #     sDF.loc[i, 'cog'] = cog
    #     i+=1
    # sDF.loc[len(sDF) - 1, 'cog'] = cog

    lonA = sDF['lons'].to_numpy()
    latA = sDF['lats'].to_numpy()
    lonA = lonA[:-1]
    latA = latA[:-1]
    pntA = [lonA,latA]

    lonB = sDF['lons'].to_numpy()
    latB = sDF['lats'].to_numpy()
    lonB = lonB[1:]
    latB = latB[1:]
    pntB = [lonB,latB]

    brng = getBearing(pntA,pntB)
    last = brng[-1]
    brng = np.append(brng, last)

    sDF['cog'] = brng


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

    ################################################
    # Get record number for port and starboard pings
    # Calculate ping direction
    # Calculate range extent lat/lon
    print("\n\tCalculate Ping Range Extent Lat/Lon...")
    for son in sonObjs:
        son._loadSonMeta()
        record_num = son.sonMetaDF['record_num'].to_numpy()
        time_s = son.sonMetaDF['time_s'].to_numpy()
        beam = son.beamName
        trans = son.trans
        if beam == "sidescan_port":
            sDF['port_record_num'] = record_num
            sDF['port_ping_bearing'] = (sDF['cog'] - 90) % 360
            sDF['port_time_s'] = time_s
            sDF = getRangeCoords(sDF, pix_m, 'port')
            e_smth, n_smth = trans(sDF['port_lonr'].to_numpy(), sDF['port_latr'].to_numpy())
            sDF['port_er'] = e_smth
            sDF['port_nr'] = n_smth
            # sDF, dfFilt, dfOrig = interpTrack(sDF, xlon='port_lonr', ylat='port_latr', xutm='port_er', yutm='port_nr',
                                              # zU='time_s', filt=100, dist=0, deg=3, dropDup=True)
        elif beam == "sidescan_starboard":
            sDF['star_record_num'] = record_num
            sDF['star_ping_bearing'] = (sDF['cog'] + 90) % 360
            sDF['star_time_s'] = time_s
            sDF = getRangeCoords(sDF, pix_m, 'star')
            e_smth, n_smth = trans(sDF['star_lonr'].to_numpy(), sDF['star_latr'].to_numpy())
            sDF['star_er'] = e_smth
            sDF['star_nr'] = n_smth
            # sDF, dfFilt, dfOrig = interpTrack(sDF, dfOrig=dfOrig, xlon='star_lonr', ylat='star_latr', xutm='star_er', yutm='star_nr',
                                              # zU='time_s', filt=500, dist=0, deg=3, dropDup=True)

    ################################
    # Try determining if pings cross
    starDF = sDF.iloc[::100].reset_index(drop=True)
    starDF = starDF.append(sDF.iloc[-1])
    print(len(starDF))
    starDForig = starDF.copy()

    

    # ############################################################################
    # # This works ok (start) #
    # drop = np.empty((len(starDF)), dtype=bool)
    # drop[:] = np.nan
    # drop[0] = False
    # # drop = []
    # i=0
    # next = i+1
    # while next < len(starDF)-1:
    #     row = starDF.iloc[i]
    #     row2 = starDF.iloc[next]
    #     line1 = ((row['es'],row['ns']), (row['star_er'], row['star_nr']))
    #     line2 = ((row2['es'],row2['ns']), (row2['star_er'], row2['star_nr']))
    #     isIntersect = lineIntersect(line1,line2)
    #     print(row['record_num'],i,next,isIntersect,'\n')
    #     if drop[i] is np.nan:
    #         drop[i] = isIntersect
    #     # drop[i] = isIntersect
    #     if isIntersect is True:
    #         # drop[i] = isIntersect
    #         drop[i-1] = isIntersect #Try dropping point before too
    #         drop[next] = isIntersect
    #         next+=1
    #     else:
    #         # drop[i] = isIntersect
    #         drop[next] = isIntersect
    #         i+=1
    #         next=i+1
    # drop[-1] = False
    # # drop=np.array(drop)
    # print(np.count_nonzero(np.isnan(drop)))
    #
    # starDF = starDF[~drop]
    #
    # starSmthDF, dfFilt, sDF = interpTrack(starDF, dfOrig=sDF, xlon='star_lonr', ylat='star_latr', xutm='star_er', yutm='star_nr',
    #                                   zU='time_s', filt=0, dist=0, deg=3, dropDup=True)
    # # This works ok (end) #
    # ############################################################################


    ##############
    # Save to file
    print("\n\tExport tracks...")
    outCSV = os.path.join(portstar[0].metaDir, "forTrackline.csv")
    dfFilt.to_csv(outCSV, index=False, float_format='%.14f')

    outCSV = os.path.join(portstar[0].metaDir, "Trackline_smooth.csv")
    sDF.to_csv(outCSV, index=False, float_format='%.14f')

    outCSV = os.path.join(portstar[0].metaDir, "Trackline_star.csv")
    starDF.to_csv(outCSV, index=False, float_format='%.14f')

    outCSV = os.path.join(portstar[0].metaDir, "Trackline_starOrig.csv")
    starDForig.to_csv(outCSV, index=False, float_format='%.14f')

    outCSV = os.path.join(portstar[0].metaDir, "Trackline_starsmth.csv")
    starSmthDF.to_csv(outCSV, index=False, float_format='%.14f')

    print('\nSLAMMA JAMMA DING DONG!!!')
