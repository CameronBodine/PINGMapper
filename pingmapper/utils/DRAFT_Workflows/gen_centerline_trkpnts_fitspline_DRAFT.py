

'''
Try fitting a spline to trackpoints to get a reasonable centerline
'''

#########
# Imports
import os, sys
from glob import glob
import pandas as pd
import geopandas as gpd


############
# Parameters
inDir = r"E:\SynologyDrive\GulfSturgeonProject\SSS_Data_Processed\EGN"
outDir = r"E:\SynologyDrive\GulfSturgeonProject\SSS_Data_Processed"
dirName = "Centerline"
tempDir = os.path.join(outDir, 'temp')

outEpsg = 32616

if not os.path.exists(tempDir):
    os.makedirs(tempDir)


###########
# Functions


#########
# Do Work
    
# Get all port smoothed tracklines
trkFiles = glob(os.path.join(inDir, '**', 'Trackline_Smth_ss_port.csv'), recursive=True)
trkFiles ={'file_path':trkFiles}

# Create dataframe
df = pd.DataFrame(trkFiles)

# Extract some attributes
df['project'] = df.apply(lambda x: os.path.dirname(x['file_path']).split(os.sep)[-2], axis=1)
df['river_code'] = df['project'].apply(lambda x: x.split('_')[0])

# Iterate each river
for name, group in df.groupby('river_code'):
    print('\n\nWorking On:', name)

    # Iterate each row
    for index, row in group.iterrows():
        print(row['file_path'])

        # Get epsg
        dat = os.path.join(os.path.dirname(row['file_path']), 'DAT_meta.csv')
        epsg = pd.read_csv(dat)['epsg'].values[0]
        del dat

        # Open file
        dfTrk = pd.read_csv(row['file_path'])

        #Filter
        lastRow = dfTrk.iloc[-1].to_frame().T
        dfTrk = dfTrk.iloc[::100]

        #Create geopandas
        gdf = gpd.GeoDataFrame(dfTrk, geometry=gpd.points_from_xy(dfTrk.trk_utm_es, dfTrk.trk_utm_ns), crs=epsg)

        # Reproject
        gdf = gdf.to_crs(outEpsg)

        # Append to single df
        if 'dfAll' not in locals():
            dfAll = gdf.copy()
        else:
            dfAll = pd.concat([dfAll, gdf])

    
    print(dfAll)

    # Create concave hull arounnd points
    conHull = dfAll.concave_hull

    print(conHull)


    del dfAll
    sys.exit()

