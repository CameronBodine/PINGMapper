
'''
'''

#########
# Imports
import sys, os
from glob import glob
import geopandas as gpd
from centerline.geometry import Centerline
from shapely.geometry import Polygon, MultiLineString, mapping, MultiPolygon

############
# Parameters
inDir = r'S:\temp\test_riverSummary\0_substrate_maps'
outDir = r'S:\temp\test_riverSummary\1_centerline'
tempDir = r'S:\temp\test_riverSummary\temp'

if not os.path.exists(tempDir):
    os.mkdir(tempDir)

###########
# Functions


#########
# Do Work

# ###################
# # Find all polygons
# polys = glob(os.path.join(inDir, '**', '*.shp'), recursive=True)
#
# # Open each polygon, dissolve, and save to file
# for poly in polys:
#     fname = os.path.basename(poly).replace('.shp', '_dis.shp')
#
#     # Read shapefile
#     poly = gpd.read_file(poly)
#
#     # Dissolve
#     poly = poly.dissolve(by=None)
#
#     # Write to file
#     poly.to_file(os.path.join(tempDir, fname), index=False)
#
#     poly = None
#
# ############################
# # Find all dissolve polygons
# polys = glob(os.path.join(tempDir, '*_dis.shp'))
#
# # Merge polygons
# toMerge = []
# for poly in polys:
#
#     # Read shapefile
#     poly = gpd.read_file(poly)
#
#     # Append to list
#     toMerge.append(poly)
#
# # Concatenate polygons
# merged = gpd.pd.concat(toMerge)
#
# # Do a dissolve
# merged = merged.dissolve(by=None)
#
# # Write to file
# merged.to_file(os.path.join(tempDir, 'merged_all.shp'), index=False)
#
# merged = None
#
# # Clean up temp
# files = glob(os.path.join(tempDir, '*_dis*'))
# for f in files:
#     os.remove(f)

# #########################
# # Try making a centerline
#
# # NOTE: may want to buffer first...
#
# # Open merged polygon
# gdf = gpd.read_file(os.path.join(tempDir, 'merged_all.shp'))
# crs_out = gdf.crs.to_epsg()
#
# # Try exploding
# gdf = gpd.geoseries.GeoSeries([geom for geom in gdf.geometry.iloc[0].geoms])
#
# # Create GeoDataFrame
# gdf = gpd.GeoDataFrame(crs=crs_out, geometry=gdf)
#
# # Calculate area
# gdf['area'] = gdf.area
#
# # Keep only really large polys
# gdf = gdf[gdf['area'] > 50000]
#
# # Now we simplify
# # gdf.geometry = gdf.geometry.simplify(tolerance=20).buffer(50)#.buffer(-50)
#
# gdf.geometry = gdf.geometry.buffer(50).buffer(-50).simplify(tolerance=5).buffer(0)
#
# gdf.to_file(os.path.join(tempDir, 'simplify.shp'), index=False)
#
# gdf = None
#
# gdf = gpd.read_file(os.path.join(tempDir, 'simplify.shp'))
#
# # Get geometry
# geom = gdf.loc[0, 'geometry']
# attributes = {'id':1, 'name': 'polygon', 'valid': True}
#
# # Calculate centerlines
# centerline = Centerline(geom, **attributes)
#
# # Turn in geodataframe
# centerline = gpd.GeoDataFrame(crs=crs_out, geometry=[centerline.geometry])
#
# centerline.to_file(os.path.join(tempDir, 'centerline.shp'), index=False)
#
# centerline = None

###
# Try cleaning

gdf = gpd.read_file(os.path.join(tempDir, 'centerline.shp'))

gdf = gpd.geoseries.GeoSeries([geom for geom in gdf.geometry.iloc[0].geoms])

print(gdf)
sys.exit()

gdf = gdf.simplify(tolerance=10)

gdf.to_file(os.path.join(tempDir, 'centerline_simp.shp'), index=False)
