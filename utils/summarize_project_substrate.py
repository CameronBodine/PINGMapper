

'''

1) Get project folders
2) Iterate each project
3) Load sonObj??
3) Get port meta.csv file
4) Get chunks that fall within summary distance
5) Get npzs belonging to chunks
6) Open each npz, do classification, then count pix belonging to each class
7) For last chunk, only get up to summary_dist
8) Once summarized, store in geodataframe
9) Export to .shp
'''

#########
# Imports
import sys, os

from matplotlib.colors import cnames
sys.path.insert(0, 'src')

import geopandas as gpd
import pandas as pd
from glob import glob
from class_mapSubstrateObj import mapSubObj
from class_portstarObj import portstarObj
from funcs_common import *
from shapely import Point, LineString, MultiPolygon
from shapely.ops import split
import numpy as np
from itertools import accumulate


############
# Parameters
inDirs = r'E:\SynologyDrive\GulfSturgeonProject\SSS_Data_Processed\Raw'

summary_dist = 1000 # Distance to summarize over [meters]
stride = 1000 # Distance between each summary window [meters]
d = 10 # Distance to extend window lines
export_polygon = True # Summarize to polygon (dissolved substrate map)
export_point = True # Summarize to point
point_begin = False # True == place point at beginning of summary window; False == end of summary window

###########
# Functions
def calcSmthDist(df):

    # Prepare pntA values [0:n-1]
    eA = df['trk_utm_es'].to_numpy().astype('float')
    nA = df['trk_utm_ns'].to_numpy().astype('float')
    # Omit last coordinate
    eA = eA[:-1]
    nA = nA[:-1]
    pntA = [eA,nA]

    # Prepare pntB values [0+1:n]
    eB = df['trk_utm_es'].to_numpy().astype('float')
    nB = df['trk_utm_ns'].to_numpy().astype('float')
    # Omit last coordinate
    eB = eB[1:]
    nB = nB[1:]
    pntB = [eB,nB]

    # Calculate distance
    trkDist = np.sqrt(np.square(pntA[0] - pntB[0]) + np.square(pntA[1] - pntB[1]))

    return np.cumsum(trkDist)

def extendLines(pnts, d):
    A = pnts[0]
    B = pnts[1]

    x1 = A[0]
    y1 = A[1]
    x2 = B[0]
    y2 = B[1]

    # Check slope of line
    m = (y2-y1)/(x2-x1)

    if m > 0:
        # Need to flip coords
        x1 = B[0]
        y1 = B[1]
        x2 = A[0]
        y2 = A[1]
    
    # Norm of vector
    AB = np.sqrt( (x2-x1)**2 + (y2-y1)**2 )

    x1_ = x1 - d*( (x2-x1) / AB )
    y1_ = y1 - d*( (y2-y1) / AB )
    x2_ = x2 + d*( (x2-x1) / AB )
    y2_ = y2 + d*( (y2-y1) / AB )

    return [(x1_, y1_), (x2_, y2_)]

def calcSinuosity(df):

    # Calculate channel length
    channel_len = df.iloc[-1]['trk_dist'] - df.loc[0]['trk_dist']

    # Calculate downvalley length
    x_1 = df.iloc[0]['trk_utm_es']
    y_1 = df.iloc[0]['trk_utm_ns']
    x_2 = df.iloc[-1]['trk_utm_es']
    y_2 = df.iloc[-1]['trk_utm_ns']

    down_len = np.sqrt( (x_1 - x_2)**2 + (y_1 - y_2)**2 )

    # Sinuosity
    sinuosity = round(channel_len / down_len, 2)
    
    return sinuosity

#########
# Do work

# Get project folders
projDirs = glob(os.path.join(inDirs, '*'))
projDirs = sorted(projDirs, reverse=True)

# For testing
#projDirs = projDirs[7:]
#projDirs = [r'E:\SynologyDrive\GulfSturgeonProject\SSS_Data_Processed\Raw\PRL_124_100_20230117_USM1_Rec00008']

proj_cnt = len(projDirs)

for i, projDir in enumerate(projDirs):

    print(i, 'of', proj_cnt, ':', os.path.basename(projDir))

    ####################################################
    # Check if sonObj pickle exists, append to metaFiles
    metaDir = os.path.join(projDir, "meta")
    if os.path.exists(metaDir):
        metaFiles = sorted(glob(metaDir+os.sep+"*.meta"))

        if len(metaFiles) == 0:
            projectMode_2a_inval()

    else:
        projectMode_2a_inval()
    del metaDir


    ############################################
    # Create a mapObj instance from pickle files
    sonObjs = []
    for meta in metaFiles:
        son = mapSubObj(meta) # Initialize mapObj()
        sonObjs.append(son) # Store mapObj() in mapObjs[]
    del meta, metaFiles

    #####################################
    # Determine which sonObj is port/star
    mapObjs = []
    for son in sonObjs:
        beam = son.beamName
        if beam == "ss_port":
            port = son
        elif beam == "ss_star":
            star = son
        else:
            pass # Don't add non-port/star objects since they can't be rectified
    del son, beam, sonObjs

    # Set out directory
    outDir = os.path.join(port.substrateDir, 'map_summary')

    if not os.path.exists(outDir):
        os.mkdir(outDir)

    # Get smooth trackline csv
    portSmth = pd.read_csv(port.smthTrkFile).reset_index()
    starSmth = pd.read_csv(star.smthTrkFile).reset_index()

    # Calculate distance
    trkDist = calcSmthDist(portSmth)
    trkDist = np.append(trkDist, trkDist[-1])

    portSmth['trk_dist'] = trkDist
    starSmth['trk_dist'] = trkDist

    maxDist = portSmth['trk_dist'].max()

    # Get substrate map shapefile
    substrateMap = glob(os.path.join(port.substrateDir, 'map_substrate_polygon', '*.shp'))[0]

    substrateMap = gpd.read_file(substrateMap)

    # Get classes names
    c_name = pd.unique(substrateMap['Name'])
        
    # Make dict of num: num_className
    my_classes = {}
    for c in c_name:
        num = substrateMap[substrateMap.Name == c].Substrate
        num = pd.unique(num)[0].astype('int')
        c = c.replace(' ', '')
        if c != 'Shadow':
            c = '_'.join(['c', str(num), c])
            my_classes[num] = c

    # Sort by num
    myKeys = list(my_classes.keys())
    myKeys.sort()
    my_classes = {i: my_classes[i] for i in myKeys}

    # Get coordinate system
    crs_out = substrateMap.crs.to_epsg()

    # Make a dissolved layer
    #diss = substrateMap.dissolve(by=None)

    #diss.to_file(os.path.join(outDir, 'dissolve.shp'), index=False)
    diss = gpd.read_file(os.path.join(outDir, 'dissolve.shp'))


    ####################################
    # Iterate by summary_dist and stride

    start_dist = 0
    end_dist = summary_dist

    #keep_working = True
    #while keep_working:

    while start_dist < maxDist:

        print('Summarizing (', start_dist, '-', end_dist, 'meters ) of', round(maxDist, 0), 'meters')

        # Get pings that fall in current window
        portDF = portSmth.loc[(portSmth['trk_dist'] >= start_dist) & (portSmth['trk_dist'] <= end_dist)].reset_index(drop=True)
        starDF = starSmth.loc[(starSmth['trk_dist'] >= start_dist) & (starSmth['trk_dist'] <= end_dist)].reset_index(drop=True)

        # Get median record number to find coordinates that fall in middle of window for spatial query
        midPnt = int(len(portDF)/2)
        midPnt = portDF.loc[midPnt]
        midPnt = Point(midPnt['trk_utm_es'], midPnt['trk_utm_ns'])

        # Store begin and end record_num for each
        portRecnum = [portDF.record_num.values[0], portDF.record_num.values[-1]]
        starRecnum = [starDF.record_num.values[0], starDF.record_num.values[-1]]

        # Get begin window coords
        df1 = portSmth.loc[portSmth.record_num == portRecnum[0]]
        beginWin = [(df1.range_es.values[0], df1.range_ns.values[0])]

        df1 = starSmth.loc[starSmth.record_num == starRecnum[0]]
        beginWin.append((df1.range_es.values[0], df1.range_ns.values[0]))

        # Get end window coords
        df1 = portSmth.loc[portSmth.record_num == portRecnum[1]]
        endWin = [(df1.range_es.values[0], df1.range_ns.values[0])]

        df1 = starSmth.loc[starSmth.record_num == starRecnum[1]]
        endWin.append((df1.range_es.values[0], df1.range_ns.values[0]))

        # Try extending the lines
        beginWin = extendLines(beginWin, d)
        endWin = extendLines(endWin, d)

        # Create points out of coords
        beginLine = [Point(beginWin[0]), Point(beginWin[1])]
        endLine = [Point(endWin[0]), Point(endWin[1])]

        # Create lines from points
        beginLine = LineString(beginLine)
        endLine = LineString(endLine)

        # Create geodataframe from lines
        winGDF = gpd.GeoDataFrame({'geometry': [beginLine, endLine]}, geometry='geometry', crs=crs_out)
        
        #winGDF.to_file(os.path.join(outDir, str(start_dist)+'_win_lines.shp'), index=False)

        ##################################
        # Try splitting polygon with lines

        # Get polygon to split
        to_split = diss.loc[0].geometry

        # Split with first line
        polys = split(to_split, beginLine)
        polys = [p for p in polys.geoms]

        # Convert to geodataframe
        splitGDF = gpd.GeoDataFrame(geometry=polys, crs=crs_out)
        #print('\n\n\nsplit 1', splitGDF)

        # Use interior points for within geometry operation
        splitGDF = splitGDF.loc[(splitGDF.geometry.contains(midPnt))].reset_index(drop=True)

        # Get polygon which intersects endLine
        #splitGDF = splitGDF.loc[(splitGDF.geometry.intersects(endLine))].reset_index(drop=True)
        #print('\nintersect 1', splitGDF)

        # Get polygon to split
        to_split = splitGDF.loc[0].geometry

        # Split with second line
        polys = split(to_split, endLine)
        polys = [p for p in polys.geoms]

        # Get poly which touches both lines
        splitGDF = gpd.GeoDataFrame(geometry=polys, crs=crs_out)
        #print('\nsplit 2', splitGDF)
        #splitGDF.to_file(os.path.join(outDir, str(start_dist)+'_last_Split.shp'), index=False)

        winSlice = splitGDF.loc[(splitGDF.geometry.contains(midPnt))].reset_index(drop=True)
        #winSlice = splitGDF.loc[(splitGDF.geometry.intersects(beginLine)) & (splitGDF.geometry.intersects(endLine))]
        #print('\nintersect 2', winSlice)

        #winSlice.to_file(os.path.join(outDir, str(start_dist)+'_split_poly.shp'), index=False)

        # Clip substrate map
        clipSubstrate = gpd.clip(substrateMap, winSlice, keep_geom_type=True)
        #print(clipSubstrate)
        #clipSubstrate.to_file(os.path.join(outDir, str(start_dist)+'_substrate.shp'), index=False)


        ##############################
        # Calculate summary statistics
        # Dictionary to store data
        sumStats = {}
        sumStats['Project'] = os.path.basename(port.projDir)
        sumStats['Begin'] = start_dist
        sumStats['End'] = end_dist

        # Calculate sinuosity
        sinuosity = calcSinuosity(portDF)
        sumStats['Sinuosity'] = sinuosity        

        # Get total area
        clipSubstrate['Area_m'] = clipSubstrate.area
        sumStats['Area_T_m'] = [clipSubstrate.Area_m.sum()]

        # Get proportion of each class
        for k, v in my_classes.items():
            class_total = clipSubstrate[clipSubstrate['Substrate'] == k].Area_m.sum() / sumStats['Area_T_m'][0]

            sumStats[v] = round(class_total, 4)

        # Get proportion Soft, Hard, Other substrates
        soft = clipSubstrate.loc[(clipSubstrate['Substrate'] == 1) | (clipSubstrate['Substrate'] == 2), ['Area_m']].sum() / sumStats['Area_T_m'][0]
        sumStats['Soft'] = soft.values[0]

        hard = clipSubstrate.loc[(clipSubstrate['Substrate'] == 3) | (clipSubstrate['Substrate'] == 4), ['Area_m']].sum() / sumStats['Area_T_m'][0]
        sumStats['Hard'] = hard.values[0]
        
        other = clipSubstrate.loc[(clipSubstrate['Substrate'] == 5) | (clipSubstrate['Substrate'] == 6), ['Area_m']].sum() / sumStats['Area_T_m'][0]
        sumStats['Other'] = other.values[0]


        if export_polygon:
            # Add attributes to winSlice
            for k, v in sumStats.items():
                winSlice.loc[[0], k] = v

            if 'outSlice' not in locals():
                outSlice = winSlice
            else:
                outSlice = pd.concat([outSlice, winSlice], ignore_index=True)


        if export_point:
            if point_begin:
                x = portDF.iloc[0]['trk_utm_es']
                y = portDF.iloc[0]['trk_utm_ns']
            else:
                x = portDF.iloc[-1]['trk_utm_es']
                y = portDF.iloc[-1]['trk_utm_ns']

            # Make a point
            pnt = Point(x, y)

            # Add to geodataframe
            pnt = gpd.GeoDataFrame({'geometry': [pnt]}, geometry='geometry', crs=crs_out)

            # Add attributes
            for k, v in sumStats.items():
                pnt.loc[[0], k] = v

            if 'outPnt' not in locals():
                outPnt = pnt
            else:
                outPnt = pd.concat([outPnt, pnt], ignore_index=True)

        # Move to next window
        start_dist += stride
        end_dist += stride


    # Save outputs
    if export_polygon:
        fname = os.path.basename(port.projDir)+'_summary_poly_'+str(summary_dist)+'_m.shp'
        f = os.path.join(outDir, fname)
        outSlice.to_file(f, index=False)

    if export_point:
        fname = os.path.basename(port.projDir)+'_summary_pnt_'+str(summary_dist)+'_m.shp'
        f = os.path.join(outDir, fname)
        outPnt.to_file(f, index=False)

    print('Done')
