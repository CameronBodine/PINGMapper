---
layout: default
title: Running PING-Mapper
nav_order: 3
parent: Getting Started

nav_exclude: false

---

# Running `PING-Mapper`

After you have [tested](./Testing.md) `PING-Mapper` on the sample datasets, you are ready to process your own sonar recordings! Two scripts have been included with `PING-Mapper` and are found in the top-level directory. The first is `main.py` which allows you to process a single sonar recording. It is recommended that you start with this script when first processing sonar recordings with the software. A second script called `main_batchDirectory.py` provides an example of how to batch process many sonar recordings at once. Both approaches are covered below.

## Process single sonar recording

- Open the Anaconda Prompt (*Windows users: Anaconda Powershell Prompt is preferred*). Navigate to the `PINGMapper` directory using the `cd` command. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

- Open `main.py` in a text editor/IDE (I use [Atom](https://atom.io/)). Here is an example of the script:

```
import sys
sys.path.insert(0, 'src')

from funcs_common import *
from main_readFiles import read_master_func
from main_rectify import rectify_master_func

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
wcp = True #Export tiles with water column present
wcr = True #Export Tiles with water column removed (and slant range corrected)

lbl_set = 0 # Export images for labeling: 0==False; 1==True, keep water column & shadows; 2==True, remove water column & shadows
spdCor = 1 # Speed correction: 0==No Speed Correction; 1==Stretch by GPS distance; !=1 or !=0 == Stretch factor.
maxCrop = True # True==Ping-wise crop; False==Crop tile to max range.


# Segmentation Parameters
USE_GPU = False # Use GPU for predictions
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
    'USE_GPU':USE_GPU,
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
```

We are going to update this script with new parameters that we define, specifically this chunk of code:

```
#################
# User Parameters
#################

# Path to data/output
humFile = "C:/user/cam/myHumDat.DAT"
sonPath = "C:/user/cam/myHumDat"
projDir = "C:/user/cam/myHumAnswerBox/myHumDat"

# General Parameters
tempC = 10 #Temperature in Celsius
nchunk = 500 #Number of pings per chunk
exportUnknown = False #Option to export Unknown ping metadata
fixNoDat = True # Locate and flag missing pings; add NoData to exported imagery.
threadCnt = 0 #Number of compute threads to use; 0==All threads; <0==(Total threads + threadCnt); >0==Threads to use up to total threads


# Sonogram Exports
tileFile = '.jpg'
wcp = True #Export tiles with water column present
wcr = True #Export Tiles with water column removed (and slant range corrected)

lbl_set = 0 # Export images for labeling: 0==False; 1==True, keep water column & shadows; 2==True, remove water column & shadows
spdCor = 1 # Speed correction: 0==No Speed Correction; 1==Stretch by GPS distance; !=1 or !=0 == Stretch factor.
maxCrop = True # True==Ping-wise crop; False==Crop tile to max range.


# Segmentation Parameters
USE_GPU = False # Use GPU for predictions
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
```

- Enter paths to DAT, SON, and output directory:
```
humFile = "C:/user/cam/myHumDat.DAT"
sonPath = "C:/user/cam/myHumDat"
projDir = "C:/user/cam/myHumAnswerBox/myHumDat"
```

{: .warning }
> Windows users: Make sure your filepaths are structured in one of the three following file formats:
> - (Double backslashes): `humFile = “C:\\Users\\cam\\Documents\\Programs\\PINGMapper\\Rec00012.DAT”`
> - (Path preceded by `r`): `humFile = r“C:\Users\cam\Documents\Programs\PINGMapper\Rec00012.DAT”`
> - (Single forward slash): `humFile = “C:/Users/cam/Documents/Programs/PINGMapper/Rec00012.DAT”`

- Update temperature (in Celcius) with average temperature during scan:
```
tempC=10
```


- Choose the number of pings to export per sonar tile.  This can be any value but all testing has been performed on chunk sizes of 500.
```
nchunk = 500
```


- Option to export unknown ping metadata fields:
```
exportUnknown = True
```

- Option to locate missing pings and fill with NoData. See [Issue #33](https://github.com/CameronBodine/PINGMapper/issues/33) and [this](https://cameronbodine.github.io/PINGMapper/docs/gettingstarted/Exports.html#orig_record_num) for more information:
```
fixNoDat = True
```

- Specify maximum number of threads to use during processing:
    - `threadCnt = 0`: Use all available threads.
    - `threadCnt > 0`: Use specified number of threads.
    - `threadCnt < 0`: Use total number of threads minus `threadCnt`.

- Specify sonogram tile file type (".png" or ".jpg")
```
tileFile = ".jpg"
```


- Export un-rectified sonar tiles with water column present `wcp` (*all sonar channels*) AND/OR water column removed `wcr` (*side scan channels only*):
```
wcp = True
wcr = True
```


- Export images that are speed corrected or stretched along track by some factor. This is used for generating images for substrate labeling but can have other applications:
    - `lbl_set = 0`: Don't export.
    - `lbl_set = 1`: Export images with water column and shadows *present*.
    - `lbl_set = 2`: Export images with water column and shadows *removed*.



- Specify if images should be speed corrected (based on distance traveled) or stretched by a factor:
    - `spdCor = 0`: No speed correction.
    - `spdCor = 1`: Speed correction based on distance traveled.
    - `spdCor != 0 or 1`: Stretch along the track by the specified factor.


- Perform ping-wise (`True`) or maximum range for a chunk as determined by shadow detection (`False`). See [this](https://cameronbodine.github.io/PINGMapper/docs/gettingstarted/Exports.html#speed-corrected) for more information:
```
maxCrop = True
```


- Use GPU (instead of CPU) for automated segmentation procedures (depth, shadow, substrate estimation):
```
USE_GPU = True
```


- Automatically segment and remove shadows from any image exports:
    - `remShadow = 0`: Don't segment or remove shadows.
    - `remShadow = 1`: Remove all shadows.
    - `remShadow = 2`: Remove only those shadows in the far-field. In a river, this is usually caused by the river bank.


- Automatically estimate the depth of water column for each side scan channel:
    - `detectDep = 0`: Don't automatically estimate depth. Use sonar sensor depth instead.
    - `detectDep = 1`: Automatically segment and remove water column with a Residual U-Net, based upon [Zheng et al. 2021](https://www.mdpi.com/2072-4292/13/10/1945).
    - `detectDep = 2`: Automatically segment and remove water column with binary segmentation.


- Smooth the depth data before removing water column.  This may help with any strange issues or noisy depth data.
```
smthDep = True
```


- Additional depth adjustment in number of pixels for water column removal. Positive values increase depth estimate, resulting in a larger proportion of sonar returns being removed during water column removal:
```
adjDep = 0
```


- Plot bedick(s) on non-rectified sonogram for visual inspection:
```
pltBedPick = True
```

- Export georectified sonar imagery (water column present `rect_wcp` AND/OR water column removed/slant range corrected `rect_wcr`) for use in GIS.
```
rect_wcp = True
rect_wcr = True
```


- Option to mosaic georectified sonar imagery (exported from step 12). Options include:
    - `mosaic = 0`: Don't Mosaic
    - `mosaic = 1`: Do Mosaic - GeoTiff
    - `mosaic = 2`: Do Mosaic - VRT (virtual raster)

- Run the program by entering the following in the command prompt:
```
python main.py
```

## Batch process multiple sonar recordings

PING-Mapper includes a script which will find all sonar recordings in a directory (even subdirectories!) and batch process them. This is useful if you have spent a day on the water collecting multiple sonar recordings. Just point this script at the top-most folder, provide an output directory for processed files, and PING-Mapper will do the rest!

- Open the Anaconda Prompt (*Windows users: Anaconda Powershell Prompt is preferred*). Navigate to the `PINGMapper` directory using the `cd` command. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

- Open `main_batchDirectory.py` in a text editor/IDE (I use [Atom](https://atom.io/)). Here is an example of the script:

```
import sys
sys.path.insert(0, 'src')

from funcs_common import *
from main_readFiles import read_master_func
from main_rectify import rectify_master_func

import time
import datetime


inDir = r'./exampleData'
outDir = r'./procData'

#################
# User Parameters
# General Parameters
tempC = 10 #Temperature in Celsius
nchunk = 500 #Number of pings per chunk
exportUnknown = False #Option to export Unknown ping metadata
fixNoDat = True # Locate and flag missing pings; add NoData to exported imagery.
threadCnt = 0 #Number of compute threads to use; 0==All threads; <0==(Total threads + threadCnt); >0==Threads to use up to total threads


# Sonogram Exports
tileFile = '.jpg'
wcp = True #Export tiles with water column present
wcr = True #Export Tiles with water column removed (and slant range corrected)

lbl_set = 0 # Export images for labeling: 0==False; 1==True, keep water column & shadows; 2==True, remove water column & shadows
spdCor = 1 # Speed correction: 0==No Speed Correction; 1==Stretch by GPS distance; !=1 or !=0 == Stretch factor.
maxCrop = True # True==Ping-wise crop; False==Crop tile to max range.


# Segmentation Parameters
USE_GPU = False # Use GPU for predictions
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
            'USE_GPU':USE_GPU,
            'remShadow':remShadow,
            'detectDep':detectDep,
            'smthDep':smthDep,
            'adjDep':adjDep,
            'pltBedPick':pltBedPick,
            'rect_wcp':rect_wcp,
            'rect_wcr':rect_wcr,
            'mosaic':mosaic
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

    except:
        print('Could not process:', datFile)

    gc.collect()
    print("\n\nTotal Processing Time: ",datetime.timedelta(seconds = round(time.time() - start_time, ndigits=0)))
```

- Enter paths to input and output directory:
```
inDir = r'./exampleData'
outDir = r'./procData'
```

- Edit parameters as necessary (*Note: supplied parameters will be applied to all sonar recordings. See section above for description of parameters*).

- Run the program by entering the following in the command prompt:
```
python main_batchDirectory.py
```
