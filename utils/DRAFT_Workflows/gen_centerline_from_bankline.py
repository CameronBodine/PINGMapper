
'''
Create centerline from banklines
'''

#########
# Imports
import os, sys
from glob import glob
import pandas as pd
import geopandas as gpd
from shapely import LineString, MultiLineString
from centerline.geometry import Centerline


############
# Parameters
inDir = r"E:\SynologyDrive\GulfSturgeonProject\SSS_Data_Processed\EGN"
outDir = r"E:\SynologyDrive\GulfSturgeonProject\SSS_Data_Processed"
dirName = "Centerline"
tempDir = os.path.join(outDir, 'temp')

outEpsg = 32616
minLen = 20
bufFilt = 10

if not os.path.exists(tempDir):
    os.makedirs(tempDir)


###########
# Functions


#########
# Do Work
    
# Get all banklines
bnkFiles = glob(os.path.join(inDir, '**', '*bankline*.shp'), recursive=True)





bnkFiles = bnkFiles[:3]








bnkFiles ={'file_path':bnkFiles}

# Create dataframe
df = pd.DataFrame(bnkFiles)

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
        dat = dat.replace('banklines', 'meta')
        epsg = pd.read_csv(dat)['epsg'].values[0]
        del dat

        # Open shapefile
        gdf = gpd.read_file(row['file_path'])

        # Reproject
        gdf = gdf.to_crs(outEpsg)

        # Simplify
        gdf = gdf.simplify(1)
        gdf = gpd.GeoDataFrame(geometry=gdf)

        # Append to single df
        if 'dfAll' not in locals():
            dfAll = gdf.copy()
        else:
            dfAll = pd.concat([dfAll, gdf])

        gdf = None

    # Dissolve
    diss = dfAll.dissolve(by=None)

    # Explode
    diss = diss.explode(index_parts=False)

    # Calculate area
    diss['area'] = diss.area

    # Sort by area
    diss = diss.sort_values(by=['area'])

    # Get last/largest area
    diss = diss.iloc[[-1]]

    # Save to shapefile
    outShp = os.path.join(tempDir, name+'_bnk_dis.shp')
    diss.to_file(outShp)



    diss = diss.iloc[0].geometry


    centerline = Centerline(diss)

    centerline = gpd.GeoDataFrame(geometry=centerline)

    outShp = os.path.join(tempDir, name+'_centerline.shp')
    centerline.to_file(outShp)







    # ####################
    # # Deluanay traingles
    # delTri = diss.delaunay_triangles(only_edges=True)
    # delTri = gpd.GeoDataFrame(geometry=delTri)
    # delTri = delTri.explode(index_parts=False)

    # # Calculate length
    # delTri['length'] = delTri.length
    # delTri = delTri.sort_values(by=['length'])
    # delTri = delTri[delTri['length']>minLen]

    # # Save to shapefile
    # outShp = os.path.join(tempDir, name+'_del_tri.shp')
    # delTri.to_file(outShp)

    # ################################
    # # Get centroid of triangle edges
    # midPnt = delTri.centroid
    # midPnt = gpd.GeoDataFrame(geometry=midPnt)

    # # Only those within
    # midPnt = midPnt.sjoin(diss, how='left', predicate='within')
    # midPnt = midPnt.dropna()
    # print(midPnt)

    # # Save to shapefile
    # outShp = os.path.join(tempDir, name+'_mid_pnt.shp')
    # midPnt.to_file(outShp)


    # ##############################################
    # # Buffer to get points which don't touch edges
    # pntBuf = midPnt.buffer(bufFilt)
    # pntBuf = gpd.GeoDataFrame(geometry=pntBuf)

    # # Only those within
    # pntBuf = pntBuf.sjoin(diss, how='left', predicate='within')
    # pntBuf = pntBuf.dropna()

    # # Get centroid
    # pntBuf = pntBuf.centroid
    # pntBuf = gpd.GeoDataFrame(geometry=pntBuf)

    # pntBuf = pntBuf.sort_values(by=['geometry'])

    # # Save to shapefile
    # outShp = os.path.join(tempDir, name+'_pnt_buf.shp')
    # pntBuf.to_file(outShp)


    # ###################
    # # Create centerline
    # end = pntBuf.iloc[1:,]['geometry'].to_numpy()
    # start = pntBuf.iloc[:-1,]['geometry'].to_numpy()
    # # print(start)

    # # Convert to line segments
    # lines = []
    # for a, b in zip(start, end):
    #     lines.append(LineString([a,b]))

    # multiline = MultiLineString([l for l in lines])

    # mline = gpd.GeoDataFrame({'geometry': [multiline]}, geometry='geometry', crs=outEpsg)
    # mline['geometry'] = mline['geometry'].simplify(tolerance=10)

    # # Save to shapefile
    # outShp = os.path.join(tempDir, name+'_centerline.shp')
    # mline.to_file(outShp)

    # sys.exit()

