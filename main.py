"""
Part of PING Mapper software

Co-Developed by Cameron S. Bodine and Dr. Daniel Buscombe

This software builds upon PyHum software,
originally developed by Dr. Daniel Buscombe

https://github.com/dbuscombe-usgs/PyHum

"""

import sys
sys.path.insert(0, 'src')

from funcs_common import *
from main_readFiles import read_master_func
from main_rectify import rectify_master_func

import time
import datetime
start_time = time.time()

#============================================

#################
# User Parameters
#################

# Path to data/output
humFile = '.\\exampleData\\test.DAT'
sonPath = '.\\exampleData\\test'
projDir = '.\\procData\\PINGMapperTest'

t = 10 #Temperature in Celsius
nchunk = 500 #Number of pings per chunk
exportUnknown = True #Option to export Unknown sonar record metadata
wcp = True #Export tiles with water column present
src = True #Export Tiles with water column removed/slant range corrected
detectDepth = 0 #0==Use Humminbird depth; 1==Auto detect depth w/ Zheng et al. 2021;
## 2==Auto detect depth w/ Thresholding
smthDep = True #Smooth depth before water column removal
adjDep = 0 #Aditional depth adjustment (in pixels) for water column removaL
pltBedPick = True #Plot bedpick on sonogram

rect_wcp = True #Export rectified tiles with water column present
rect_src = True #Export rectified tiles with water column removed/slant range corrected

mosaic = 1 #Export rectified tile mosaic; 0==Don't Mosaic; 1==Do Mosaic - GTiff; 2==Do Mosaic - VRT

#################
#################

#============================================

sonFiles = sorted(glob(sonPath+os.sep+'*.SON'))
print(sonFiles)

#==================================================
print('\n===========================================')
print('===========================================')
print('***** READING *****')
print("working on "+projDir)
read_master_func(sonFiles, humFile, projDir, t, nchunk, exportUnknown, wcp, src, detectDepth, smthDep, adjDep, pltBedPick)

#==================================================
if rect_wcp or rect_src:
    print('\n===========================================')
    print('===========================================')
    print('***** RECTIFYING *****')
    print("working on "+projDir)
    rectify_master_func(sonFiles, humFile, projDir, nchunk, rect_wcp, rect_src, mosaic)

gc.collect()
print("\n\nTotal Processing Time: ",datetime.timedelta(seconds = round(time.time() - start_time, ndigits=0)))
