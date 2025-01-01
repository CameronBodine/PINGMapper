
'''
***********************************************
WARNING: Not intended for general use but may 
serve as a template for creating new workflows.
***********************************************

Generate substrate stamps from coverage and track point
shapefiles.
'''


#########
# Imports
import os, sys
from glob import glob
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import Point, LineString, MultiLineString
from shapely.ops import split


############
# Parameters

summaryLengths = [500, 1000, 5000, 10000] # Create stamps at specified lengths
extendDist = 100 # Distance to extend lines to clip stamp

inDir = r'E:\SynologyDrive\GulfSturgeonProject\SSS_Data_Processed\Centerline\FINAL'
outDir = r'E:\SynologyDrive\GulfSturgeonProject\SSS_Data_Processed\Substrate_Summaries\01_summary_stamp_shps'

covNamePattern = 'Coverage_FINAL.shp' 
pntNamePattern = 'Centerline_10m_Pnts.shp'

distField = 'ORIG_LEN'
cog = 'COG'
rr_brng = 'RR_Bearing'
rl_brng = 'RL_Bearing'


###########
# Functions
def getBearing(df):
    # Adapted from rom PINGMapper: https://github.com/CameronBodine/PINGMapper/blob/52ef34668adca509cc2c1931a1e73860901667f5/src/class_rectObj.py#L281
    '''
    Calculates course over ground (COG) from a set of coordinates.  Since the
    last coordinate pair cannot have a COG value, the length of the returned
    array is len(n-1) where n == len(df).

    ----------
    Parameters
    ----------
    df : DataFrame
        DESCRIPTION - Pandas dataframe with geographic coordinates of sonar
                        records.
    lon : str : [Default='lons']
        DESCRIPTION - DataFrame column name for longitude coordinates.
    lat : str : [Default='lats']
        DESCRIPTION - DataFrame column name for latitude coordinates.

    ----------------------------
    Required Pre-processing step
    ----------------------------
    Called from self._interpTrack()

    -------
    Returns
    -------
    Numpy array of COG values.

    --------------------
    Next Processing Step
    --------------------
    Return to self._interpTrack()
    '''
    # COG calculation will be calculated on numpy arrays for speed.  Since
    ## COG is calculated from one point to another (pntA -> pntB), we need
    ## to store pntA values, beginning with the first value and ending at
    ## second to last value, in one array and pntB values, beginning at second
    ## value and ending at last value, in another array.  We can then use
    ## vector algebra to efficiently calculate COG.

    # Prepare pntA values [0:n-1]
    lonA = df.geometry.x.to_numpy() # Store longitude coordinates in numpy array
    latA = df.geometry.y.to_numpy() # Store longitude coordinates in numpy array
    lonA = lonA[:-1] # Omit last coordinate
    latA = latA[:-1] # Omit last coordinate
    pntA = [lonA,latA] # Store in array of arrays

    # Prepare pntB values [0+1:n]
    lonB = df.geometry.x.to_numpy() # Store longitude coordinates in numpy array
    latB = df.geometry.y.to_numpy() # Store longitude coordinates in numpy array
    lonB = lonB[1:] # Omit first coordinate
    latB = latB[1:] # Omit first coordinate
    pntB = [lonB,latB] # Store in array of arrays

    # # Convert latitude values into radians
    # lat1 = np.deg2rad(pntA[1])
    # lat2 = np.deg2rad(pntB[1])

    # diffLong = np.deg2rad(pntB[0] - pntA[0]) # Calculate difference in longitude then convert to degrees
    # bearing = np.arctan2(np.sin(diffLong) * np.cos(lat2), np.cos(lat1) * np.sin(lat2) - (np.sin(lat1) * np.cos(lat2) * np.cos(diffLong))) # Calculate bearing in radians

    # db = np.degrees(bearing) # Convert radians to degrees
    # db = (db + 360) % 360 # Ensure degrees in range 0-360

    # Point coords are in utm, so don't use above conversion
    bearing = np.arctan2( (lonB - lonA), (latB - latA) )
    db = np.degrees(bearing)
    db = (db + 360) % 360

    return db

def getBearingLine(x, y, rr, rl, d):
    '''
    x: x coord
    y: y coord
    rr: bearing to river right
    rl: bearing to river left
    d: distance
    '''
    # River right coordinates
    dY = d*np.cos(np.radians(rr))
    dX = d*np.sin(np.radians(rr))
    pnt1 = Point(x+dX, y+dY)

    # River right coordinates
    dY = d*np.cos(np.radians(rl))
    dX = d*np.sin(np.radians(rl))
    pnt2 = Point(x+dX, y+dY)

    return LineString([pnt1, pnt2])



#########
# Do Work

# Create outdir
if not os.path.exists(outDir):
    os.makedirs(outDir)

# Find the coverage shapefiles
covShps = glob(os.path.join(inDir, '**', '*'+covNamePattern), recursive=True)

covShps = [f for f in covShps if 'PAS' in f or 'PRL' in f]

# Iterate the coverage shapefiles
for covShpFile in covShps:
    print('Working on:', covShpFile)
    # Get the associate pnt shapefile
    pntShpFile = covShpFile.replace(covNamePattern, pntNamePattern)

    # Open shapefiles in geopandas frame
    covShp = gpd.read_file(covShpFile)
    pntShpAll = gpd.read_file(pntShpFile)

    # Get coordinate system
    crs_out = covShp.crs.to_epsg()

    # Find total upstream dist
    maxDist = pntShpAll[distField].max()

    # Calculate COG for points
    brng = getBearing(pntShpAll)
     # getBearing() returns n-1 values because last ping can't
    ## have a COG value.  We will duplicate the last COG value and use it for
    ## the last ping.
    last = brng[-1]
    brng = np.append(brng, last)
    pntShpAll[cog] = brng # Store COG in sDF

    # River Right (RR) is right bank facing downstread, left facing US (-90 degrees)
    # River Left (LL) is left bank facing DS, right facing US (+90 degrees)
    pntShpAll[rr_brng] = (pntShpAll[cog] - 90) % 360
    pntShpAll[rl_brng] = (pntShpAll[cog] + 90) % 360

    # Iterate each summary distance
    for summaryDist in summaryLengths:
        print('\tDistance: ', summaryDist)

        # Filter pntShp by covShp, round to nearest summaryDist, reselect by pntShp, set startDist to min of pntShp
        pntShp = gpd.sjoin(pntShpAll, covShp, predicate='within').reset_index(drop=True)
        
        # Get downstream most point
        minDist = pntShp[distField].min()

        # In order to keep the summaries at whole numbers (500, 1000, 1500, etc.), find the next whole value downstream
        # based on summary distance
        start_dist = summaryDist * round(minDist/summaryDist)

        # Check if difference is large enough
        p = 0.75
        dif = abs(start_dist - minDist)

        if start_dist > minDist:
            # see if need to round down
            if dif > 0.75*summaryDist:
                start_dist -= summaryDist
        else:
            # see if need to round up
            if dif < 0.75*summaryDist:
                start_dist += summaryDist

        # set remaining counters
        end_dist = start_dist+summaryDist
        stride = summaryDist

        while (start_dist + 0.75*summaryDist) < maxDist:
            print(start_dist, end_dist, ":", maxDist)

            # Get track points that fall in current window
            chunkShp = pntShp.loc[(pntShp[distField] >= start_dist) & (pntShp[distField] <= end_dist)].reset_index(drop=True)

            # Try intersection with trackline
            # Get trackpoint coordinates
            x = chunkShp.geometry.x.to_numpy()
            y = chunkShp.geometry.y.to_numpy()

            # Make sure trackline contained within desired area
            x = x[5:-5]
            y = y[5:-5]

            # Make point gdf
            start = gpd.points_from_xy(x, y, crs=crs_out)
            end = start[1:]
            start = start[:-1]

            # Convert to line segments
            lines = []
            for a, b in zip(start, end):
                lines.append(LineString([a, b]))

            # Convert to multiline
            multiline = MultiLineString([l for l in lines])

            # Convert to geodataframe
            mline = gpd.GeoDataFrame({'geometry': [multiline]}, geometry='geometry', crs=crs_out)

            # Simplify line
            mline['geometry'] = mline['geometry'].simplify(tolerance=10)
            
            # Create clip lines from first and last points
            # get start point
            beginLine = getBearingLine(chunkShp.geometry.x.to_numpy()[0],
                                       chunkShp.geometry.y.to_numpy()[0],
                                       chunkShp[rr_brng].to_numpy()[0],
                                       chunkShp[rl_brng].to_numpy()[0],
                                       extendDist)
            
            endLine = getBearingLine(chunkShp.geometry.x.to_numpy()[-1],
                                       chunkShp.geometry.y.to_numpy()[-1],
                                       chunkShp[rr_brng].to_numpy()[-1],
                                       chunkShp[rl_brng].to_numpy()[-1],
                                       extendDist)
            
            ##################################
            # Try splitting polygon with lines

            # Get polygon to split
            to_split = covShp.loc[0].geometry

            # Split with first line
            polys = split(to_split, beginLine)
            polys = [p for p in polys.geoms]

            # Convert to geodataframe
            splitGDF = gpd.GeoDataFrame(geometry=polys, crs=crs_out)

            try:
                # splitGDF = splitGDF.loc[(splitGDF.geometry.intersects(mline))].reset_index(drop=True)
                splitGDF = gpd.sjoin(splitGDF, mline, predicate='intersects').reset_index(drop=True)
            except:
                print('Unable to intersect 1:', covShpFile, '\n', beginLine, endLine)

            splitGDF = splitGDF.dissolve(by=None)

            # Get polygon to split
            to_split = splitGDF.loc[0].geometry

            # Split with second line
            polys = split(to_split, endLine)
            polys = [p for p in polys.geoms]

            # Get poly which touches both lines
            splitGDF = gpd.GeoDataFrame(geometry=polys, crs=crs_out)

            try:
                # winSlice = splitGDF.loc[(splitGDF.geometry.intersects(mline))].reset_index(drop=True)
                winSlice = gpd.sjoin(splitGDF, mline, predicate='intersects').reset_index(drop=True)
            except:
                print('Unable to intersect 1:', covShpFile, '\n', beginLine, endLine)

            winSlice = winSlice.dissolve(by=None)

            # Add RKM Id
            winSlice['RKM_DS'] = start_dist
            winSlice['RKM_US'] = end_dist

            # Drop columns
            winSlice = winSlice.drop(columns=['index_right'])

            if 'stamp' not in locals():
                stamp = winSlice
            else:
                stamp = pd.concat([stamp, winSlice])        

            # update counters
            start_dist += stride
            end_dist += stride

        river_code = os.path.basename(covShpFile).split('_')[0]
        outShpDir = os.path.join(outDir, river_code)
        if not os.path.exists(outShpDir):
            os.makedirs(outShpDir)

        outShp = '_'.join([river_code, 'summary', 'stamp', str(summaryDist), 'm'])+'.shp'
        outShp = os.path.join(outShpDir, outShp)
        stamp.to_file(outShp)

        del stamp


    outShp = os.path.basename(pntShpFile)
    outShp = os.path.join(outShpDir, outShp)
    pntShp.to_file(outShp)

    # Close files
    del covShp, pntShp