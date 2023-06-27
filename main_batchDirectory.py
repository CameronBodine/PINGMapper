# Part of PING-Mapper software
#
# Co-Developed by Cameron S. Bodine and Dr. Daniel Buscombe
#
# Inspired by PyHum: https://github.com/dbuscombe-usgs/PyHum
#
# MIT License
#
# Copyright (c) 2022-23 Cameron S. Bodine
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
from main_mapSubstrate import map_master_func

import time
import datetime

# Get processing script's dir so we can save it to file
scriptDir = os.getcwd()
copied_script_name = os.path.basename(__file__).split('.')[0]+'_'+time.strftime("%Y-%m-%d_%H%M")+'.py'
script = os.path.join(scriptDir, os.path.basename(__file__))


inDir = r'./exampleData'
outDir = r'./procData'

#################
# User Parameters

# *** IMPORTANT ****: Overwriting project and outputs
# Export Mode: project_mode
## 0==NEW PROJECT: Create a new project. [DEFAULT]
##      If project already exists, program will exit without any project changes.
##
## 1==UPDATE PROJECT: Export additional datasets to existing project.
##      Use this mode to update an existing project.
##      If selected datasets were previously exported, they will be overwritten.
##      To ensure datasets aren't overwritten, deselect them below.
##      If project does not exist, program will exit without any project changes.
##
## 2==MAYHEM MODE: Create new project, regardless of previous project state.
##      If project exists, it will be DELETED and reprocessed.
##      If project does not exist, a new project will be created.
project_mode = 2


# General Parameters
pix_res_factor = 0.1 # Pixel resampling factor;
##                     0<pix_res_factor<1.0: Downsample output image to lower resolution/larger cellsizes;
##                     1.0: Use sonar default resolution;
##                     pix_res_factor > 1.0: Upsample output image to higher resolution/smaller cellsizes.
tempC = 10 #Temperature in Celsius
nchunk = 500 #Number of pings per chunk
cropRange = 0.0 #Crop imagery to specified range [in meters]; 0.0==No Cropping
exportUnknown = False #Option to export Unknown ping metadata
fixNoDat = True # Locate and flag missing pings; add NoData to exported imagery.
threadCnt = 0 #Number of compute threads to use; 0==All threads; <0==(Total threads + threadCnt); >0==Threads to use up to total threads


# Position Corrections
## Provide an x and y offset to account for position offset between
## control head (or external GPS) and transducer.
## Origin (0,0) is the location of control head (or external GPS)
## X-axis runs from bow (fore, or front) to stern (aft, or rear) with positive offset towards the bow, negative towards stern
## Y-axis runs from portside (left) to starboard (right), with negative values towards the portside, positive towards starboard
## Z-offsets can be provided with `adjDep` below.
x_offset = 0.0 # [meters]
y_offset = 0.0 # [meters]


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


# Substrate Mapping
# Substrate Mapping
pred_sub = 1 # Automatically predict substrates and save to npz: 0==False; 1==True, SegFormer Model
pltSubClass = True # Export plots of substrate classification and predictions
map_sub = 1 # Export substrate maps (as rasters): 0==False; 1==True. Requires substrate predictions saved to npz.
export_poly = True # Convert substrate maps to shapefile: map_sub must be > 0 or raster maps previously exported
map_predict = 0 #Export rectified tiles of the model predictions: 0==False; 1==Probabilities; 2==Logits. Requires substrate predictions saved to npz.
map_class_method = 'max' # 'max' only current option. Take argmax of substrate predictions to get final classification.



# Find all DAT and SON files in all subdirectories of inDir
inFiles=[]
for root, dirs, files in os.walk(inDir):
    for file in files:
        if file.endswith('.DAT'):
            inFiles.append(os.path.join(root, file))

inFiles = sorted(inFiles)

for i, f in enumerate(inFiles):
    print(i, ":", f)

for datFile in inFiles:
    try:
        start_time = time.time()

        inPath = os.path.dirname(datFile)
        humFile = datFile
        recName = os.path.basename(humFile).split('.')[0]
        sonPath = os.path.join(inDir, recName)
        sonFiles = sorted(glob(sonPath+os.sep+'*.SON'))

        projDir = os.path.join(outDir, recName)

        params = {
            'project_mode':project_mode,
            'pix_res_factor':pix_res_factor,
            'humFile':humFile,
            'sonFiles':sonFiles,
            'projDir':projDir,
            'tempC':tempC,
            'nchunk':nchunk,
            'cropRange':cropRange,
            'exportUnknown':exportUnknown,
            'fixNoDat':fixNoDat,
            'threadCnt':threadCnt,
            'x_offset':x_offset,
            'y_offset':y_offset,
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
            'mosaic':mosaic,
            'pred_sub': pred_sub,
            'map_sub':map_sub,
            'export_poly':export_poly,
            'map_predict':map_predict,
            'pltSubClass':pltSubClass,
            'map_class_method':map_class_method
            }

        print('sonPath',sonPath)
        print('\n\n\n+++++++++++++++++++++++++++++++++++++++++++')
        print('+++++++++++++++++++++++++++++++++++++++++++')
        print('***** Working On *****')
        print(humFile)
        print('Start Time: ', datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))

        print('\n===========================================')
        print('===========================================')
        print('***** READING *****')
        read_master_func(**params)
        # read_master_func(sonFiles, humFile, projDir, t, nchunk, exportUnknown, wcp, wcr, detectDepth, smthDep, adjDep, pltBedPick, threadCnt)

        if rect_wcp or rect_wcr:
            print('\n===========================================')
            print('===========================================')
            print('***** RECTIFYING *****')
            rectify_master_func(**params)
            # rectify_master_func(sonFiles, humFile, projDir, nchunk, rect_wcp, rect_wcr, mosaic, threadCnt)

        #==================================================
        #==================================================
        if pred_sub or map_sub or export_poly or map_predict or pltSubClass:
            print('\n===========================================')
            print('===========================================')
            print('***** MAPPING SUBSTRATE *****')
            print("working on "+projDir)
            map_master_func(**params)

    except:
        print('Could not process:', datFile)

    gc.collect()
    print("\n\nTotal Processing Time: ",datetime.timedelta(seconds = round(time.time() - start_time, ndigits=0)))
