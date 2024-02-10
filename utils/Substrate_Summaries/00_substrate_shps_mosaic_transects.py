

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

############
# Parameters

inDir = r'E:\SynologyDrive\GulfSturgeonProject\SSS_Data_Processed\EGN'
outDir = os.path.join(os.path.dirname(inDir), 'Substrate_Shps_Mosaic_Trainsects')

subShpPattern = 'map_substrate*.shp'
