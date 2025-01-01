
'''
***********************************************
WARNING: Not intended for general use but may 
serve as a template for creating new workflows.
***********************************************


Create centerline from coverage shapefiles.
Centerlines need to be post-processed in a GIS.

Additional GIS steps require generating points along
the centerline for use in creating the summary stamps
from coverage shapefiles.
'''

#########
# Imports
import os, sys
from glob import glob
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely import LineString, MultiLineString, Polygon
from shapely.geometry import shape, mapping
from centerline.geometry import Centerline
from functools import reduce


############
# Parameters
inDir = r"E:\SynologyDrive\GulfSturgeonProject\SSS_Data_Processed\EGN"
outDir = r"E:\SynologyDrive\GulfSturgeonProject\SSS_Data_Processed"
dirName = "Centerline"
tempDir = os.path.join(outDir, dirName)

outEpsg = 32616
interpolation_distance = 5 # Higher == more generalized, measured in epsg units
holeSize = 100 # Fill holes smaller then threshold
minLen = 20
bufFilt = 10

if not os.path.exists(tempDir):
    os.makedirs(tempDir)


###########
# Functions
def around(geom,p):
    geojson = mapping(geom)
    geojson['coordinates'] = np.round(np.array(geojson['coordinates']),p)
    return  shape(geojson)

# https://gis.stackexchange.com/questions/446855/fill-holes-in-polygon-shapefile-with-geopandas-and-area-threshold
def fillit(row):
    """A function to fill holes below an area threshold in a polygon"""
    newgeom=None
    rings = [i for i in row.geometry.interiors] #List all interior rings
    if len(rings)>0: #If there are any rings
        to_fill = [Polygon(ring) for ring in rings if Polygon(ring).area<holeSize] #List the ones to fill
        if len(to_fill)>0: #If there are any to fill
            newgeom = reduce(lambda geom1, geom2: geom1.union(geom2),[row["geometry"]]+to_fill) #Union the original geometry with all holes
    if newgeom:
        return newgeom
    else:
        return row["geometry"]


#########
# Do Work
    
# Get all banklines
covFiles = glob(os.path.join(inDir, '**', '*coverage*.shp'), recursive=True)

covFiles ={'file_path':covFiles}

# Create dataframe
df = pd.DataFrame(covFiles)

# Extract some attributes
df['project'] = df.apply(lambda x: os.path.dirname(x['file_path']).split(os.sep)[-3], axis=1)
df['river_code'] = df['project'].apply(lambda x: x.split('_')[0])

# Iterate each river
for name, group in df.groupby('river_code'):
    if name == 'PRL':
        print('\n\n\n\nWorking On:', name)

        # Iterate each row
        for index, row in group.iterrows():
            print(row['file_path'])

            # Open shapefile
            gdf = gpd.read_file(row['file_path'])

            # Reproject
            gdf = gdf.to_crs(outEpsg)

            # Simplify
            gdf = gdf.simplify(1)
            gdf = gpd.GeoDataFrame(geometry=gdf)

            # # Round precision to fix topolgy
            # # https://gis.stackexchange.com/questions/217789/geopandas-shapely-spatial-difference-topologyexception-no-outgoing-diredge-f
            # gdf.geometry = gdf.geometry.apply(lambda x: around(x,2))

            try:
                # Dissolve chunks
                gdf = gdf.dissolve()
            except:
                # Round precision to fix topolgy
                # https://gis.stackexchange.com/questions/217789/geopandas-shapely-spatial-difference-topologyexception-no-outgoing-diredge-f
                gdf.geometry = gdf.geometry.apply(lambda x: around(x, 2))

                gdf = gdf.loc[gdf.geometry.is_valid]

                # Dissolve chunks
                gdf = gdf.dissolve()


            try:    
                # Fill small holes
                gdf.geometry = gdf.apply(fillit, axis=1)
            except:
                pass

            # Append to single df
            if 'dfAll' not in locals():
                dfAll = gdf.copy()
            else:
                dfAll = pd.concat([dfAll, gdf])

            gdf = None

        # Dissolve transects
        diss = dfAll.dissolve(by=None)

        del dfAll

        # Save to shapefile
        outShp = os.path.join(tempDir, name+'_cov_dis.shp')
        diss.to_file(outShp)

        buf_iter = 3
        buf_size = 10
        simp_tol = 5
        geom = diss
        for i in range(buf_iter):
            
            geom = geom.buffer(buf_size, join_style=1).buffer(buf_size*-1, join_style=1)



        ################
        # For Centerline

        # Get shapely geometry
        # geom = diss.iloc[0].geometry
        # geom = geom.iloc[0]

        print('\n\nMaking Centerline...')
        centerline = Centerline(geom.iloc[0], interpolation_distance)
        print('Done!')

        centerline = gpd.GeoDataFrame(geometry=[centerline.geometry], crs=outEpsg)

        centerline = centerline.explode()

        outShp = os.path.join(tempDir, name+'_centerline.shp')
        centerline.to_file(outShp)


        geom = geom.buffer(buf_size*-1-10, join_style=1)
        outShp = os.path.join(tempDir, name+'_cov_buf-Neg.shp')
        geom.to_file(outShp)


































# # Test
    # # Try buffer -20
    # buf = diss.buffer(-20)

    # outShp = os.path.join(tempDir, name+'_cov_buf-Neg20.shp')
    # buf.to_file(outShp)

    # # simplify
    # simp = buf.simplify(5)
    # simp = gpd.GeoDataFrame(geometry=simp)

    # outShp = os.path.join(tempDir, name+'_cov_buf-Neg20-Simp.shp')
    # simp.to_file(outShp)

    # # Try buffer +30
    # buf = simp.buffer(30)

    # outShp = os.path.join(tempDir, name+'_cov_buf-Pos30.shp')
    # buf.to_file(outShp)

    # # simplify
    # simp = buf.simplify(5)
    # geom = gpd.GeoDataFrame(geometry=simp)

    # buf_iter = 3
    # buf_size = 10
    # simp_tol = 5
    # geom = diss
    # for i in range(buf_iter):
        
    #     # Do negative buf
    #     buf_size *= -1
    #     buf = geom.buffer(buf_size)

    #     # Simplify
    #     simp = buf.simplify(simp_tol)
    #     simp = gpd.GeoDataFrame(geometry=simp)

    #     outShp = os.path.join(tempDir, name+'_cov_buf-NegSimp.shp')
    #     buf.to_file(outShp)

    #     # Do positive buf
    #     buf_size *= -1
    #     buf = simp.buffer(buf_size)

    #     # Simplify
    #     simp = buf.simplify(simp_tol)
    #     geom = gpd.GeoDataFrame(geometry=simp)

    #     outShp = os.path.join(tempDir, name+'_cov_buf-PosSimp.shp')
    #     geom.to_file(outShp)

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

