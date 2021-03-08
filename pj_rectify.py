


from common_funcs import *
from c_sonObj import sonObj
from osgeo import ogr
import fiona
import shapely
from shapely.geometry import mapping, LineString, Point, Polygon
import geopandas as gpd
from centerline.geometry import Centerline
import time
import math

# #===========================================
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

# #===========================================
# def getMidpoint(gdf, df_out, i, geometry = 'geometry'):
#     pntA = gdf.loc[i][geometry]
#     pntB = gdf.loc[i+1][geometry]
#
#     midX = (pntA.x + pntB.x)/2
#     midY = (pntA.y + pntB.y)/2
#     midpoint = Point(midX, midY)
#
#     data = {'geometry': [midpoint]}
#     df_pnt = pd.DataFrame(data, columns =['geometry'])
#
#     df_out = pd.concat([df_out, df_pnt])
#
#     return df_out

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

    ###################################
    # Delete duplicates sharing lat/lon
    pd.options.display.float_format = '{:.6f}'.format

    son = portstar[0]
    dfOrig = son.sonMetaDF
    df = dfOrig.copy()
    df.drop_duplicates(subset=['e', 'n'], inplace=True)
    df.reset_index(inplace=True)

    ########################################
    # Make a trackline from raw track points
    # Export raw track points (duplicate lat/lon removed)
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs=son.humDat['epsg'])
    gdf.to_file(os.path.join(portstar[0].metaDir, "Trackpnts_raw.shp"))

    ###############################
    # Create lines from trackpoints
    x = 0
    df = pd.DataFrame(columns = ['id', 'timeStart', 'timeEnd', 'geometry', 'cog_raw'])
    while x < len(gdf) - 1:
        df = makeLines(gdf, df, x)
        x = x+1
    df.set_index('id', inplace=True)

    # Calculate COG from tracklines
    for i, row in df.iterrows():
        geom = row['geometry']
        pntA = geom.coords[0]
        pntB = geom.coords[1]
        bearing = getBearing(pntA, pntB)
        df.loc[i, 'cog_raw'] = bearing

    # Save raw trackline to file
    line = gpd.GeoDataFrame(df, geometry='geometry', crs=son.humDat['epsg'])
    line.to_file(os.path.join(portstar[0].metaDir, "Tracklines_raw.shp"))

    ############################################
    # Merge consecutive tracklines with same COG
    filt = pd.DataFrame(columns = ['geometry', 'cog_raw'])
    i = 0
    next = i+1
    while i < len(df) - 1:
        bA = df.loc[i, 'cog_raw']
        bB = df.loc[next, 'cog_raw']
        if bA == bB:
            next+=1
        else:
            if next-i==1: #Didn't find another seg w/ same heading
                row = df.loc[i].to_dict()
                filt = filt.append(row, ignore_index=True)
            else:
                rowA = df.loc[i].to_dict()
                rowB = df.loc[next-1].to_dict()
                start = rowA['geometry'].coords[0]
                end = rowB['geometry'].coords[1]
                timeStart = rowA['timeStart']
                timeEnd = rowB['timeEnd']
                geom = LineString([start, end])

                dict = {'geometry': geom,
                        'cog_raw': rowA['cog_raw'],
                        'timeStart': timeStart,
                        'timeEnd': timeEnd}
                filt = filt.append(dict, ignore_index=True)

            i=next
            next=i+1

    # Export merged tracklines
    line = gpd.GeoDataFrame(filt, geometry='geometry', crs=son.humDat['epsg'])
    line.to_file(os.path.join(portstar[0].metaDir, "Tracklines_merge.shp"))

    #########################################
    # Calculate midpoint of merged tracklines
    dfMid = pd.DataFrame(columns = ['geometry'])
    x=0
    while x < len(line) - 1:
        dfMid = getMidpoint(line, dfMid, x)
        x+=1
    dfMid.reset_index(inplace=True)

    # Save midpoints to file
    gdf = gpd.GeoDataFrame(dfMid, geometry='geometry', crs=son.humDat['epsg'])
    gdf.to_file(os.path.join(portstar[0].metaDir, "Trackpnts_midpnt.shp"))

    ############################################
    # Create 'smoothed' trackline from midpoints
    x = 0
    df = pd.DataFrame(columns = ['geometry'])
    while x < len(gdf) - 1:
        df = makeLines(gdf, df, x)
        x = x+1

    # Save 'smoothed' trackline to file
    df = gpd.GeoDataFrame(df, geometry='geometry', crs=son.humDat['epsg'])
    df.to_file(os.path.join(portstar[0].metaDir, "Tracklines_midpnt.shp"))











    #################################################
    # gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.e, df.n), crs=son.humDat['epsg'])
    # gdf.to_file(os.path.join(portstar[0].metaDir, "Trackpnts_raw.shp"))
    #
    # dfMid = pd.DataFrame(columns = ['geometry'])
    # x = 0
    # while x < len(gdf) - 1:
    #     dfMid = getMidpoint(gdf, dfMid, x)
    #     x+=1
    # dfMid.reset_index(inplace=True)
    #
    # gdf = gpd.GeoDataFrame(dfMid, geometry='geometry', crs=son.humDat['epsg'])
    # gdf.to_file(os.path.join(portstar[0].metaDir, "Trackpnts_midpnt.shp"))
    # print(gdf)
    #
    # x = 0
    # df = pd.DataFrame(columns = ['geometry'])
    # while x < len(gdf) - 1:
    #     df = makeLines(gdf, df, x)
    #     x = x+1
    #
    # df = gpd.GeoDataFrame(df, geometry='geometry', crs=son.humDat['epsg'])
    # df.to_file(os.path.join(portstar[0].metaDir, "Tracklines_midpnt.shp"))
    #################################################




    #################################################
    # # Below works, but relies on centerline library
    # # which doesn't perform well (noisy output)
    # gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.e, df.n), crs=son.humDat['epsg'])
    # gdf.to_file(os.path.join(portstar[0].metaDir, "Trackpnts_raw.shp"))
    #
    # df = pd.DataFrame(columns = ['geometry'])
    #
    # x = 0
    # while x < len(gdf) - 1:
    #     df = makeLines(gdf, df, x)
    #     x = x+1
    #
    # df = gpd.GeoDataFrame(df, geometry='geometry', crs=son.humDat['epsg'])
    # df.to_file(os.path.join(portstar[0].metaDir, "Tracklines_raw.shp"))
    #
    # gdf = gpd.GeoDataFrame(df, geometry='geometry', crs=son.humDat['epsg'])
    # gdf['diss'] = 1
    # dis = gdf.dissolve(by="diss")
    # dis.to_file(os.path.join(portstar[0].metaDir, "Trackline_dis_raw.shp"))
    #
    # buf = dis.geometry.buffer(10)
    # # buf = buf.simplify(0.5)
    # buf.to_file(os.path.join(portstar[0].metaDir, "Trackline_buf.shp"))
    #
    # cntr = Centerline(buf.geometry[1])
    # cntr = shapely.ops.linemerge(cntr)
    # cntr = cntr.simplify(5)
    # cntr = gpd.GeoSeries(cntr, crs=son.humDat['epsg'])
    # cntr.to_file(os.path.join(portstar[0].metaDir, "Trackline_cntr.shp"))
    ################################################


    # smth = interp1d(df.e, df.n, kind='cubic')
    # df['e_smth'] = smth.x
    # df['n_smth'] = smth.y
    #
    # df.to_csv(os.path.join(portstar[0].metaDir, "test.csv"))
    #
    # gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.e, df.n), crs=son.humDat['epsg'])
    # print(gdf.head())
    # # gdf.reset_index(inplace=True)
    # gdf.to_file(os.path.join(portstar[0].metaDir, "Trackpnts_raw.shp"))
    #
    # smth = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df['e_smth'], df['n_smth']), crs=son.humDat['epsg'])
    # print(smth.head())
    # # smth.reset_index(inplace=True)
    # smth.to_file(os.path.join(portstar[0].metaDir, "Trackpnts_smth.shp"))

    # pnt = []
    # for index, row in df.iterrows():
    #     pnt.append([Point(row['e'], row['n'])])
    # print(pnt)

    # line = []
    # x = 0
    # while x < len(pnt) - 1:
    #     A = pnt[x]
    #     B = pnt[x+1]
    #     line.append(LineString([A, B]))
    #     x+=1
    # print(line)

    # line = ogr.Geometry(ogr.wkbLineString)
    # for index, row in df.iterrows():
    #     line.AddPoint(row['e'], row['n'])
    # print(line)




    #
    # df = pd.DataFrame(columns = ['id', 'geometry'])
    # x = 0
    # while x < len(gdf) - 1:
    #     df = makeLines(gdf, df, x)
    #     x = x+1
    # gdf = gpd.GeoDataFrame(df, geometry='geometry', crs=son.humDat['epsg'])
    # gdf['diss'] = 1
    # dis = gdf.dissolve(by="diss")
    # dis.to_file(os.path.join(portstar[0].metaDir, "Trackline_raw.shp"))
    #
    # geo = shapely.ops.linemerge(gdf.geometry)
    # print(geo)
    #
    # s = gpd.GeoSeries(gdf.geometry)
    # s.simplify(10, False)
    # s.to_file(os.path.join(portstar[0].metaDir, "Trackline_smooth.shp"))









    # for son in sonObjs:
    #     print("\n\n")
    #     print(son)
