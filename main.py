# Part of PING-Mapper software
#
# Co-Developed by Cameron S. Bodine and Dr. Daniel Buscombe
#
# Inspired by PyHum: https://github.com/dbuscombe-usgs/PyHum
#
# MIT License
#
# Copyright (c) 2022 Cameron S. Bodine
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import sys
sys.path.insert(0, 'src')

from funcs_common import *
from main_readFiles import read_master_func
from main_rectify import rectify_master_func

# Get processing script's dir so we can save it to file
scriptDir = os.getcwd()
copied_script_name = os.path.basename(__file__).split('.')[0]+'_'+time.strftime("%Y-%m-%d_%H%M")+'.py'
script = os.path.join(scriptDir, os.path.basename(__file__))


start_time = time.time()

#============================================

#################
# User Parameters
#################

# Path to data/output
humFile = r'./exampleData/Test-Small-DS.DAT'
sonPath = r'./exampleData/Test-Small-DS'
projDir = r'./procData/PINGMapper-Test-Small-DS'

# General Parameters
tempC = 10 #Temperature in Celsius
nchunk = 500 #Number of pings per chunk
exportUnknown = False #Option to export Unknown ping metadata
fixNoDat = True # Locate and flag missing pings; add NoData to exported imagery.
threadCnt = 0 #Number of compute threads to use; 0==All threads; <0==(Total threads + threadCnt); >0==Threads to use up to total threads


# Sonogram Exports
tileFile = '.jpg'
wcp = 2 #Export tiles with water column present: 0==False; 1==True, side scan channels only; 2==True, all available channels.
wcr = 2 #Export Tiles with water column removed (and slant range corrected): 0==False; 1==True, side scan channels only; 2==True, all available channels.

lbl_set = 0 # Export images for labeling: 0==False; 1==True, keep water column & shadows; 2==True, remove water column & shadows
spdCor = 1 # Speed correction: 0==No Speed Correction; 1==Stretch by GPS distance; !=1 or !=0 == Stretch factor.
maxCrop = True # True==Ping-wise crop; False==Crop tile to max range.


# Segmentation Parameters
remShadow = 1  # 0==Leave Shadows; 1==Remove all shadows; 2==Remove only bank shadows
detectDep = 1 #0==Use Humminbird depth; 1==Auto detect depth w/ Zheng et al. 2021;
## 2==Auto detect depth w/ Thresholding

smthDep = True #Smooth depth before water column removal
adjDep = 0 #Aditional depth adjustment (in pixels) for water column removaL
pltBedPick = True #Plot bedpick on sonogram


# Rectification Parameters
rect_wcp = True #Export rectified tiles with water column present
rect_wcr = True #Export rectified tiles with water column removed/slant range corrected
mosaic = 1 #Export rectified tile mosaic; 0==Don't Mosaic; 1==Do Mosaic - GTiff; 2==Do Mosaic - VRT

#################
#################

#============================================

sonFiles = sorted(glob(sonPath+os.sep+'*.SON'))
print(sonFiles)

#============================================

params = {
    'script':[script, copied_script_name],
    'humFile':humFile,
    'sonFiles':sonFiles,
    'projDir':projDir,
    'tempC':tempC,
    'nchunk':nchunk,
    'exportUnknown':exportUnknown,
    'fixNoDat':fixNoDat,
    'threadCnt':threadCnt,
    'tileFile':tileFile,
    'wcp':wcp,
    'wcr':wcr,
    'lbl_set':lbl_set,
    'spdCor':spdCor,
    'maxCrop':maxCrop,
    'USE_GPU':False,
    'remShadow':remShadow,
    'detectDep':detectDep,
    'smthDep':smthDep,
    'adjDep':adjDep,
    'pltBedPick':pltBedPick,
    'rect_wcp':rect_wcp,
    'rect_wcr':rect_wcr,
    'mosaic':mosaic
    }
#==================================================
print('\n===========================================')
print('===========================================')
print('***** READING *****')
print("working on "+projDir)
read_master_func(**params)
# read_master_func(sonFiles, humFile, projDir, t, nchunk, exportUnknown, wcp, wcr, tileFile, detectDepth, smthDep, adjDep, pltBedPick, threadCnt)

#==================================================
if rect_wcp or rect_wcr:
    print('\n===========================================')
    print('===========================================')
    print('***** RECTIFYING *****')
    print("working on "+projDir)
    rectify_master_func(**params)
    # rectify_master_func(sonFiles, humFile, projDir, nchunk, rect_wcp, rect_wcr, mosaic, threadCnt)

gc.collect()
print("\n\nTotal Processing Time: ",datetime.timedelta(seconds = round(time.time() - start_time, ndigits=0)))
