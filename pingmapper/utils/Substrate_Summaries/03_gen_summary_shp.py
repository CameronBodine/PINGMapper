


'''
***********************************************
WARNING: Not intended for general use but may 
serve as a template for creating new workflows.
***********************************************

Generate summary csv from substrate map shapefiles.

Inputs:

1) RIV_summary_stamp_DIST_m.shp
2) RIV_Centerline_10m_Pnts.shp
3) RIV_substrate_shps_mosaic.shp

Summaries:
1) Depth (avg, std, quantiles[whislo(0.01), q1(0.25), q2(0.5), q3(0.75), whishi(0.99)])
2) Width (avg, std, quantiles[whislo(0.01), q1(0.25), q2(0.5), q3(0.75), whishi(0.99)])
3) Sinuosity (instream dist / euclidean distance[start, end])
4) Mapped Area [m2]
5) Substrate Summary (proportion (% of mapped area), patch count, area(avg, std, quantiles[whislo(0.01), q1(0.25), q2(0.5), q3(0.75), whishi(0.99)]))
'''


#########
# Imports
import os, sys
from glob import glob
import pandas as pd
import geopandas as gpd
import numpy as np
import itertools
from shapely import Point, LineString, MultiLineString
import pyproj

############
# Parameters

river_codes = ['BCH', 'PRL', 'PAS','BOU', 'LEA', 'CHI', 'CHU']
# river_codes = ['BCH', 'PAS','BOU', 'LEA', 'CHI', 'CHU']
# river_codes = ['PRL']
summaryLengths = [500, 1000, 5000, 10000] # Create stamps at specified lengths
extendDist = 100 # Distance to extend lines to clip stamp

substrateOutput = 'Raw'
mosaicDirName = '02_Substrate_Shps_Mosaic_Transects'
outProj = '03_Substrate_Shps_Summary'

# summaryTopDir = r'E:\SynologyDrive\GulfSturgeonProject\SSS_Data_Processed\Substrate_Summaries'
summaryTopDir = r'D:\redbo_science\projects\GulfSturgeonProject_2025\ProcessedData\Substrate_Summaries'
mapDir = os.path.join(summaryTopDir, mosaicDirName, substrateOutput)
stampShpDir = os.path.join(summaryTopDir, '01_summary_stamp_shps')
outDir = os.path.join(summaryTopDir, outProj, substrateOutput)

projDir = os.path.join(os.path.dirname(summaryTopDir), substrateOutput)

distField = 'ORIG_LEN'
cog = 'COG'
rr_brng = 'RR_Bearing'
rl_brng = 'RL_Bearing'


# Normalize paths
mapDir = os.path.normpath(mapDir)
stampDir = os.path.normpath(mapDir)
outDir = os.path.normpath(outDir)

if not os.path.exists(outDir):
    os.makedirs(outDir)


###########
# Functions
def getTrkShps(dir, riv, crs_out, outFile):

    filt = 50
    shpPattern = 'Trackline_Smth_ss_port.shp'

    print('Creating merged trackfile. Filter every {}th ping'.format(filt))

    # Find all shapefiles
    shpFiles = glob(os.path.join(dir, riv+'*', '**', shpPattern), recursive=True)

    crs = pyproj.CRS.from_user_input(crs_out)

    # Iterate shapefiles
    for shp in shpFiles:
        print(shp)
        date = shp.split(os.sep)[-4]
        date = date.split('_')[-3]

        shp = gpd.read_file(shp)

        # Filter to speed up
        shp = shp[::filt].reset_index(drop=True)
        shp['date'] = date

        if crs != shp.crs:
            shp = shp.to_crs(crs_out)

        if 'df' not in locals():
            df = shp
        else:
            df = pd.concat([df, shp])

    df.to_file(outFile)

    return df

def getBearingLineDF(x, y, rr, rl, dist, crs_out):
    '''
    x: x coord
    y: y coord
    rr: bearing to river right
    rl: bearing to river left
    d: distance
    '''

    # River right coordinates
    dY = dist*np.cos(np.radians(rr))
    dX = dist*np.sin(np.radians(rr))

    pnt1 = []
    for a, b, c, d, in zip(x, dX, y, dY):
        pnt1.append(Point(a+b, c+d))

    # River right coordinates
    dY = dist*np.cos(np.radians(rl))
    dX = dist*np.sin(np.radians(rl))

    pnt2 = []
    for a, b, c, d, in zip(x, dX, y, dY):
        pnt2.append(Point(a+b, c+d))

    # Create lines from points
    lines = []
    for a, b in zip(pnt1, pnt2):
        lines.append(LineString([a, b]))

    # Convert to geodatafram
    gdf = gpd.GeoDataFrame({'geometry': lines}, geometry='geometry', crs=crs_out)

    return gdf

def calcSinuosity(df, channel_len, stats):

    # Calculate euclidean distance from begin to end
    x_1 = df.iloc[0].geometry.x
    y_1 = df.iloc[0].geometry.y
    x_2 = df.iloc[-1].geometry.x
    y_2 = df.iloc[-1].geometry.y

    down_len = np.sqrt( (x_1 - x_2)**2 + (y_1 - y_2)**2 )

    # Sinuosity
    stats['sinuosity'] = np.around(channel_len / down_len, 2)
    
    return stats

def getStats(df, col, stats, decimals=2):

    stats[col+'_avg'] = np.around( np.mean(df[col].to_numpy()), decimals )
    stats[col+'_whisklo'] = np.around( np.quantile(df[col].to_numpy(), 0.01), decimals )
    stats[col+'_q1'] = np.around( np.quantile(df[col].to_numpy(), 0.25), decimals )
    stats[col+'_q2'] = np.around( np.quantile(df[col].to_numpy(), 0.5), decimals )
    stats[col+'_q3'] = np.around( np.quantile(df[col].to_numpy(), 0.75), decimals )
    stats[col+'_whiskhi'] = np.around( np.quantile(df[col].to_numpy(), 0.99), decimals )

    return stats

def getSubStats(df, col, subClass, stats, decimals=2):

    # Get class columns
    df = df[df[col] == subClass]

    # Remove space from class name
    subClass = subClass.replace(' ', '_')

    # Total mapped area
    maxArea = stats['mapped_area']

    # Total class area
    classArea = np.sum(df['Area_m'].to_numpy())

    # Class proportion
    stats[subClass+'_prop'] = np.around(classArea / maxArea, 4)

    # Class count
    stats[subClass+'_patch_count'] = len(df)

    return stats

def doWork(riv, dist):

    # Get shapefiles
    covShps = glob(os.path.join(stampShpDir, riv, '*stamp*'+str(dist)+'_m.shp'))[0]
    pntShps = glob(os.path.join(stampShpDir, riv, '*Centerline_10m_Pnts.shp'))[0]
    mapShps = glob(os.path.join(mapDir, riv+'*postproc.shp'))[0]
    # mapShps = glob(os.path.join(mapDir, riv+'*mosaic.shp'))[0]

    print(covShps)

    # Open as gdf
    covShps = gpd.read_file(covShps)
    pntShps = gpd.read_file(pntShps)
    mapShps = gpd.read_file(mapShps)

    substrateClasses = np.unique(mapShps['Name'].to_numpy())

    # Get coordinate system
    map_crs = mapShps.crs.to_epsg()
    cov_crs = covShps.crs.to_epsg()

    if map_crs != cov_crs:
        covShps = covShps.to_crs(map_crs)

    crs_out = map_crs

    # Get project tracklines as shapefile (for depth)
    trkShpFile = os.path.join(outDir, riv+'_Trackline_Merge.shp')
    
    if not os.path.exists(trkShpFile):
        trkShp = getTrkShps(projDir, riv, crs_out, trkShpFile)
    else:
        print('Using Existing Trackfile:', trkShpFile)
        trkShp = gpd.read_file(trkShpFile)

    # print(covShps)
    
    # Iterate each stamp feature
    for i, row in covShps.iterrows():

        try:

            # Get row values
            rkm_ds = row['RKM_DS']
            rkm_us = row['RKM_US']
            covGeom = gpd.GeoDataFrame(geometry=[row.geometry], crs=crs_out)

            print('\tRKM:', rkm_ds)

            # Store row summaries
            rowSummary = {}
            rowSummary['river_code'] = riv
            rowSummary['rkm'] = rkm_ds

            # Clip map
            print('\t\tClip Map')
            mapShp = gpd.clip(mapShps, covGeom)

            # Dissolve map
            print('\t\tDissolve Map')
            mapDis = mapShp.dissolve()

            #############
            # Get Lat Lon

            # Clip points
            print('\t\tClip Tracks')
            pnts = gpd.clip(pntShps, covGeom)
            pnts = pnts.sort_values(by=distField)

            pntsLatLon = pnts.copy()
            pntsLatLon = pntsLatLon.to_crs(4326)

            rowSummary['lon_ds'] = pntsLatLon.iloc[0].geometry.x
            rowSummary['lat_ds'] = pntsLatLon.iloc[0].geometry.y
            rowSummary['lon_us'] = pntsLatLon.iloc[-1].geometry.x
            rowSummary['lat_us'] = pntsLatLon.iloc[-1].geometry.y

            #################
            # Calculate Depth
            print('\t\tDepth')
            trks = gpd.clip(trkShp, covGeom)
            
            # Calculate stats
            rowSummary = getStats(trks, 'dep_m', rowSummary, decimals=2)

            del trks


            #################
            # Calculate Width
            print('\t\tWidth')
            # Get bearing line
            blDF = getBearingLineDF(pnts.geometry.x.to_numpy(),
                                    pnts.geometry.y.to_numpy(),
                                    pnts[rr_brng].to_numpy(),
                                    pnts[rl_brng].to_numpy(),
                                    extendDist,
                                    crs_out)
            

            # Clip bearing lines
            blDF = gpd.clip(blDF, mapDis)

            # Calculate river width
            blDF['width'] = blDF.geometry.length

            # Calculate stats
            try:
                rowSummary = getStats(blDF, 'width', rowSummary, decimals=2)
            except:
                pass

            del blDF

            #####################
            # Calculate Sinuosity
            print('\t\tSinuosity')
            rowSummary = calcSinuosity(pnts, dist, rowSummary)
            
            #######################
            # Calculate Mapped Area
            rowSummary['mapped_area'] = np.around(mapDis.geometry.area.values[0], 2)


            ###########################
            # Calculate Substrate Stats
            print('\t\tSubstrate')

            # Make sure area updated
            mapShp['Area_m'] = np.around(mapShp.geometry.area, 2)

            # Iterate each class
            for subClass in substrateClasses:
                rowSummary = getSubStats(mapShp, 'Name', subClass, rowSummary, decimals=2)

            ##############################
            # Convert summary to dataframe
                
            # Values must be in a list
            for k, v in rowSummary.items():
                rowSummary[k] = [v]
                
            dfSummary = pd.DataFrame.from_dict(rowSummary)

            if 'dfSummaryAll' not in locals():
                dfSummaryAll = dfSummary
            else:
                dfSummaryAll = pd.concat([dfSummaryAll, dfSummary], ignore_index=True)
        except:
            pass



    outFile = '_'.join([substrateOutput, riv, str(dist), 'summary.csv' ])
    dfSummaryAll.to_csv(os.path.join(outDir, outFile), index=False)

    del dfSummaryAll

    return

#########
# Do Work

# Combine all permutations of river_codes and summaryLengths
riv_sum_all = list(itertools.product(river_codes, summaryLengths))

# Iterate (or parallelize)
for riv_sum in riv_sum_all:

    print('\n\n\n\n', riv_sum)

    doWork(riv_sum[0], riv_sum[1])