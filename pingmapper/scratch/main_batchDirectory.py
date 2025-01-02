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

# For the logfile
oldOutput = sys.stdout

#============================================

#######################
# Start User Parameters
#######################

# Path to data/output
inDir = r'./exampleData/' # Parent folder of sonar recordings
outDir = r'./procData' # Parent folder for export files
prefix = r''
suffix = r''
aoi = False #r"path/to/.shp"

# *** IMPORTANT ****
# Export Mode: project_mode
## 0==NEW PROJECT: Create a new project. [DEFAULT]
##      If project already exists, program will exit without any project changes.
##
## 1==OVERWRITE MODE: Create new project, regardless of previous project state.
##      If project exists, it will be DELETED and reprocessed.
##      If project does not exist, a new project will be created.
project_mode = 1


# General Parameters
tempC = 10 #Temperature in Celsius
nchunk = 500 #Number of pings per chunk
cropRange = 0.0 #Crop imagery to specified range [in meters]; 0.0==No Cropping
exportUnknown = False #Option to export Unknown ping metadata
fixNoDat = True # Locate and flag missing pings; add NoData to exported imagery.
threadCnt = 0 #Number of compute threads to use; 0==All threads; <0==(Total threads + threadCnt); >0==Threads to use up to total threads


# Output Pixel Resolution [meters]
pix_res_son = 0.05 # 0 = Default (~0.02 m)
pix_res_map = 0.25 # 0 = Default (~0.02 m)


# Position Corrections
## Provide an x and y offset to account for position offset between
## control head (or external GPS) and transducer.
## Origin (0,0) is the location of control head (or external GPS)
## X-axis runs from bow (fore, or front) to stern (aft, or rear) with positive offset towards the bow, negative towards stern
## Y-axis runs from portside (left) to starboard (right), with negative values towards the portside, positive towards starboard
## Z-offsets can be provided with `adjDep` below.
x_offset = 0.0 # [meters]
y_offset = 0.0 # [meters]


# Sonar Intensity Corrections
egn = True
egn_stretch = 1 # 0==Min-Max; 1==% Clip
egn_stretch_factor = 0.5 # If % Clip, the percent of histogram tails to clip (1.0 == 1%)


# Sonogram Exports
tileFile = '.jpg' # Img format for plots and sonogram exports
wcp = True #Export tiles with water column present: 0==False; 1==True, side scan channels only; 2==True, all available channels.
wcr = True #Export Tiles with water column removed (and slant range corrected): 0==False; 1==True, side scan channels only; 2==True, all available channels.


# Speed corrected sonogram Exports
lbl_set = 2 # Export images for labeling: 0==False; 1==True, keep water column & shadows; 2==True, remove water column & shadows
spdCor = 1 # Speed correction: 0==No Speed Correction; 1==Stretch by GPS distance; !=1 or !=0 == Stretch factor.
maxCrop = False # True==Ping-wise crop; False==Crop tile to max range.


# Depth Detection and Shadow Removal Parameters
remShadow = 2  # 0==Leave Shadows; 1==Remove all shadows; 2==Remove only bank shadows
detectDep = 1 #0==Use Humminbird depth; 1==Auto detect depth w/ Zheng et al. 2021;
## 2==Auto detect depth w/ Thresholding

smthDep = True #Smooth depth before water column removal
adjDep = 0 #Aditional depth adjustment (in pixels) for water column removaL
pltBedPick = True #Plot bedpick on sonogram


# Rectification Parameters
rect_wcp = True #Export rectified tiles with water column present
rect_wcr = True #Export rectified tiles with water column removed/slant range corrected
son_colorMap = 'Greys_r' # Specify colorramp for rectified imagery. '_r'==reverse the ramp: https://matplotlib.org/stable/tutorials/colors/colormaps.html


# Substrate Mapping
pred_sub = 1 # Automatically predict substrates and save to npz: 0==False; 1==True, SegFormer Model
pltSubClass = True # Export plots of substrate classification and predictions
map_sub = 1 # Export substrate maps (as rasters): 0==False; 1==True. Requires substrate predictions saved to npz.
export_poly = True # Convert substrate maps to shapefile: map_sub must be > 0 or raster maps previously exported
map_predict = 0 #Export rectified tiles of the model predictions: 0==False; 1==Probabilities; 2==Logits. Requires substrate predictions saved to npz.
map_class_method = 'max' # 'max' only current option. Take argmax of substrate predictions to get final classification.


# Mosaic Exports
mosaic_nchunk = 0 # Number of chunks per mosaic: 0=All chunks. Specifying a value >0 generates multiple mosaics if number of chunks exceeds mosaic_nchunk.
mosaic = 1 #Export sonar mosaic; 0==Don't Mosaic; 1==Do Mosaic - GTiff; 2==Do Mosaic - VRT
map_mosaic = 1 #Export substrate mosaic; 0==Don't Mosaic; 1==Do Mosaic - GTiff; 2==Do Mosaic - VRT


# Miscellaneous Exports
banklines = True # Export banklines from sonar imagery


#####################
# End User Parameters
#####################

#============================================
# Normalize paths
inDir = os.path.normpath(inDir)
outDir = os.path.normpath(outDir)

# Find all DAT and SON files in all subdirectories of inDir
inFiles=[]
for root, dirs, files in os.walk(inDir):
    for file in files:
        if file.endswith('.DAT'):
            inFiles.append(os.path.join(root, file))

inFiles = sorted(inFiles)

for i, f in enumerate(inFiles):
    print(i, ":", f)

errorRecording = []
for datFile in inFiles:
    try:
        copied_script_name = os.path.basename(__file__).split('.')[0]+'_'+time.strftime("%Y-%m-%d_%H%M")+'.py'
        script = os.path.join(scriptDir, os.path.basename(__file__))

        logfilename = 'log_'+time.strftime("%Y-%m-%d_%H%M")+'.txt'
        
        start_time = time.time()

        inPath = os.path.dirname(datFile)
        humFile = datFile
        recName = os.path.basename(humFile).split('.')[0]
        sonPath = humFile.split('.DAT')[0]
        sonFiles = sorted(glob(sonPath+os.sep+'*.SON'))

        recName = prefix + recName + suffix

        projDir = os.path.join(outDir, recName)

        params = {
            'logfilename':logfilename,
            'project_mode':project_mode,
            'script':[script, copied_script_name],
            'humFile':humFile,
            'sonFiles':sonFiles,
            'projDir':projDir,
            'tempC':tempC,
            'nchunk':nchunk,
            'cropRange':cropRange,
            'exportUnknown':exportUnknown,
            'fixNoDat':fixNoDat,
            'threadCnt':threadCnt,
            'pix_res_son': pix_res_son,
            'pix_res_map': pix_res_map,
            'x_offset':x_offset,
            'y_offset':y_offset,
            'egn':egn,
            'egn_stretch':egn_stretch,
            'egn_stretch_factor':egn_stretch_factor,
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
            'son_colorMap':son_colorMap,
            'pred_sub':pred_sub,
            'map_sub':map_sub,
            'export_poly':export_poly,
            'map_predict':map_predict,
            'pltSubClass':pltSubClass,
            'map_class_method':map_class_method,
            'mosaic_nchunk':mosaic_nchunk,
            'mosaic':mosaic,
            'map_mosaic':map_mosaic,
            'banklines':banklines,
            }
        
        globals().update(params)
        
        # =========================================================
        # Determine project_mode
        print(project_mode)
        if project_mode == 0:
            # Create new project
            if not os.path.exists(projDir):
                os.mkdir(projDir)
            else:
                projectMode_1_inval()

        elif project_mode == 1:
            # Overwrite existing project
            if os.path.exists(projDir):
                shutil.rmtree(projDir)

            os.mkdir(projDir)        

        elif project_mode == 2:
            # Update project
            # Make sure project exists, exit if not.
            
            if not os.path.exists(projDir):
                projectMode_2_inval()

        # =========================================================
        # For logging the console output

        logdir = os.path.join(projDir, 'logs')
        if not os.path.exists(logdir):
            os.makedirs(logdir)

        logfilename = os.path.join(logdir, logfilename)

        sys.stdout = Logger(logfilename)

        print('\n\n', '***User Parameters***')
        for k,v in params.items():
            print("| {:<20s} : {:<10s} |".format(k, str(v)))

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

        if rect_wcp or rect_wcr or banklines:
            print('\n===========================================')
            print('===========================================')
            print('***** RECTIFYING *****')
            rectify_master_func(**params)
            # rectify_master_func(sonFiles, humFile, projDir, nchunk, rect_wcp, rect_wcr, mosaic, threadCnt)

        #==================================================
        #==================================================
        if pred_sub or map_sub or export_poly or pltSubClass:
            print('\n===========================================')
            print('===========================================')
            print('***** MAPPING SUBSTRATE *****')
            print("working on "+projDir)
            map_master_func(**params)

        sys.stdout.log.close()

    except Exception as Argument:
        unableToProcessError(logfilename)
        print('\n\nCould not process:', datFile)

    sys.stdout = oldOutput

    gc.collect()
    print("\n\nTotal Processing Time: ",datetime.timedelta(seconds = round(time.time() - start_time, ndigits=0)))

if len(errorRecording) > 0:
    print('\n\nUnable to process the following:')
    for d in errorRecording:
        print('\n',d)