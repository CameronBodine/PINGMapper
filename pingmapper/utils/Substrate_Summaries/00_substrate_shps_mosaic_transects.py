

'''
***********************************************
WARNING: Not intended for general use but may 
serve as a template for creating new workflows.
***********************************************

Workflow for mosaicing substrate shapefiles from multiple transects.
Not ideal as averaging logits then argmax would be better, but this
will have to do for now.
'''

#########
# Imports
import os, sys
from glob import glob
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely import Point, LineString, MultiLineString

############
# Parameters

substrateOutputs = ['Raw', 'EGN']
topDir = r'E:/SynologyDrive/GulfSturgeonProject/SSS_Data_Processed'

subShpPattern = '*map_substrate*.shp'
least2mostImport = ['Other', 'Fines Flat', 'Fines Ripple', 'Hard Bottom', 'Cobble Boulder', 'Wood']
outEpsg = 32616

# Normalize Paths
topDir = os.path.normpath(topDir)

###########
# Functions
def get_river_code(row):
    project = row.proj
    river_code = project.split('_')[0]
    
    if river_code == 'PRL':
        river = 'Pearl'
    elif river_code == 'BCH':
        river = 'Bogue Chitto'
    elif river_code == 'CHI':
        river = 'Chickasawhay'
    elif river_code == 'CHU':
        river = 'Chunky'
    elif river_code == 'LEA':
        river = 'Leaf'
    elif river_code == 'BOU':
        river = 'Bouie'
    elif river_code == 'PAS':
        river = 'Pascagoula'
    # For testing
    elif river_code == 'RIV':
        river = 'River'
    else:
        print('No River Code:', river_code)
        sys.exit()

    return river, river_code

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
for substrateOutput in substrateOutputs:

    # Prepare Paths
    transectDir = os.path.join(topDir, substrateOutput)
    outDir = os.path.join(topDir, 'Substrate_Summaries', '02_Substrate_Shps_Mosaic_Transects', substrateOutput)

    # Normalize Paths
    transectDir = os.path.normpath(transectDir)
    outDir = os.path.normpath(outDir)

    # Prepare directories
    transectDir = os.path.abspath(os.path.normpath(transectDir))

    if not os.path.exists(outDir):
        os.makedirs(outDir)

    # Get shps
    shpFiles = glob(os.path.join(transectDir, '**', subShpPattern), recursive=True)

    # Remove projName from dirs
    shpFiles = [f for f in shpFiles if outDir not in f]



    ####################################################
    # shpFiles = [f for f in shpFiles if 'PRL_' in f]
    ####################################################





    # Store shps in dataframe
    shpDF = pd.DataFrame()
    shpDF['shp'] = shpFiles

    # Add projName to df
    shpDF['proj'] = shpDF['shp'].apply(lambda d: os.path.basename(d))

    # Add river and code
    shpDF[['river', 'river_code']] = shpDF.apply(lambda row: get_river_code(row), axis=1).values.tolist()

    # Get RKM
    shpDF['up_rkm'] = shpDF['proj'].apply(lambda d: d.split('_')[1]).astype(int)
    shpDF['dn_rkm'] = shpDF['proj'].apply(lambda d: d.split('_')[2]).astype(int)

    # Sort by river code and up rkm
    shpDF = shpDF.sort_values(['river_code', 'up_rkm'], ascending=False).reset_index()


    # shpDF = shpDF[1:4]  ####### For testing



    # Create a map based on river
    for name, group in shpDF.groupby('river_code'):

        print('\n\nWorking On:', name)

        # Get shapefiles
        shpFiles = group.shp.values.tolist()

        # Iterate classes
        for subClassName in least2mostImport:
            print('\t', substrateOutput, ':', subClassName)

            allClassPolys = gpd.GeoDataFrame()

            for shpFile in shpFiles:

                print('\t\t', os.path.basename(shpFile))

                # Open the shapefile
                shp = gpd.read_file(shpFile)

                if shp.crs is None:
                    shp = shp.set_crs(outEpsg)

                # Reproject
                shp = shp.to_crs(outEpsg)

                # Get the class polys
                classPolys = shp.loc[shp['Name'] == subClassName]

                # Explode
                classPolys = classPolys.explode(index_parts=False)

                # Concatenate with allClass Polys
                allClassPolys = pd.concat([allClassPolys, classPolys])

                del shp

            # Calculate area
            allClassPolys['Area_m'] = np.around(allClassPolys.geometry.area, 2)

            # Dissolve
            allClassPolys = allClassPolys.dissolve()

            # Explode
            allClassPolys = allClassPolys.explode(index_parts=False).reset_index(drop=True)

            # Overlay (opposite of clip)
            if 'finalSubMap' not in locals():
                finalSubMap = allClassPolys
            else:
                finalSubMap = finalSubMap.overlay(allClassPolys, how='difference', keep_geom_type=True)
                finalSubMap = pd.concat([finalSubMap, allClassPolys])

            del allClassPolys
                
        
        
        outShp = name+'_substrate_shps_mosaic.shp' 
        outShp = os.path.join(outDir, outShp)
        finalSubMap.to_file(outShp)

        del finalSubMap

        print(outShp)

