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

1. Open the Anaconda Prompt (*Windows users: Anaconda Powershell Prompt is preferred*). Navigate to the `PINGMapper` directory using the `cd` command. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

2. Open `main.py` in a text editor/IDE (I use [Atom](https://atom.io/)). Here is an example of the script:

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

t = 10                     #Temperature (C)
nchunk = 500               #Pings per chunk
exportUnknown = True       #Export unknown ping attributes
wcp = True                 #Export water column present tiles
wcr = True                 #Export water column removed tiles
smthDep = True             #Smooth depth
adjDep = 0                 #Depth adjustment (in pixels)
pltBedPick = True          #Export bedpick plots

rect_wcp = True            #Export georectified wcp
rect_wcr = True            #Export rectified wcr

mosaic = 1                 #Export georectified mosaic

threadCnt = 0              #Thread count

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
read_master_func(sonFiles, humFile, projDir, t, nchunk, exportUnknown, wcp, wcr, 0, smthDep, adjDep, pltBedPick, threadCnt)

#==================================================
if rect_wcp or rect_wcr:
    print('\n===========================================')
    print('===========================================')
    print('***** RECTIFYING *****')
    print("working on "+projDir)
    rectify_master_func(sonFiles, humFile, projDir, nchunk, rect_wcp, rect_wcr, mosaic, threadCnt)

gc.collect()
print("\n\nTotal Processing Time: ",datetime.timedelta(seconds = round(time.time() - start_time, ndigits=0)))
```

We are going to update this script with new parameters that we define, specifically this chunk of code:

```
#################
# User Parameters
#################

# Path to data/output
humFile = r'./exampleData/Test-Small-DS.DAT'
sonPath = r'./exampleData/Test-Small-DS'
projDir = r'./procData/PINGMapper-Test-Small-DS'

t = 10                     #Temperature (C)
nchunk = 500               #Pings per chunk
exportUnknown = True       #Export unknown ping attributes
wcp = True                 #Export water column present tiles
wcr = True                 #Export water column removed tiles
smthDep = True             #Smooth depth
adjDep = 0                 #Depth adjustment (in pixels)
pltBedPick = True          #Export bedpick plots

rect_wcp = True            #Export georectified wcp
rect_wcr = True            #Export rectified wcr

mosaic = 1                 #Export georectified mosaic

threadCnt = 0              #Thread count

#################
#################
```

3. Enter paths to DAT, SON, and output directory:

```
humFile = "C:/user/cam/myHumDat.DAT"
sonPath = "C:/user/cam/myHumDat"
projDir = "C:/user/cam/myHumAnswerBox/myHumDat"
```

Windows users: Make sure your filepaths are structured in one of the three following file formats:
- (Double backslashes): `humFile = “C:\\Users\\cam\\Documents\\Programs\\PINGMapper\\Rec00012.DAT”`
- (Path preceded by `r`): `humFile = r“C:\Users\cam\Documents\Programs\PINGMapper\Rec00012.DAT”`
- (Single forward slash): `humFile = “C:/Users/cam/Documents/Programs/PINGMapper/Rec00012.DAT”`

4. `t=10`: Update temperature with average temperature during scan.


5. `nchunk = 500`: Choose the number of pings to export per sonar tile.  This can be any value but all testing has been performed on chunk sizes of 500.


6. `exportUnknown = True`: Option to export unknown ping metadata fields.


7. `wcp = True` & `wcr = True`: Export un-rectified sonar tiles with water column present `wcp` AND/OR water column removed `wcr`.

<!-- 8. Line 37: Option to use Humminbird depth (`detectDepth=0`), automatically detect depth through thresholding (`detectDepth=1`), automatically detect depth with Residual U-Net (`detectDepth=2`), or do both automatic depth picking methods (`detectDepth=3`).  NOTE: this will soon be updated with a new method, stay tuned... -->

8. `smthDep = True`: Smooth the depth data before removing water column.  This may help with any strange issues or noisy depth data.


9. `adjDep = 0`: Additional depth adjustment in number of pixels for water column removal. Positive values increase depth estimate, resulting in a larger proportion of sonar returns being removed during water column removal.


10. `pltBedPick = True`: Plot bedick(s) on non-rectified sonogram for visual inspection.


11. `rect_wcp = True` & `rect_wcr = True`: Export georectified sonar imagery (water column present `rect_wcp` AND/OR water column removed/slant range corrected `rect_wcr`) for use in GIS.


12. `mosaic = 1`: Option to mosaic georectified sonar imagery (exported from step 12). Options include:

- `mosaic = 0`: Don't Mosaic
- `mosaic = 1`: Do Mosaic - GeoTiff
- `mosaic = 2`: Do Mosaic - VRT (virtual raster)


13. `threadCnt = 0`: Number of compute threads to use for processing in parallel. Options include:

- `threadCnt = 0`: Use all available threads
- Positive values: Only use specified number of threads
- Negative values: Use all but specified number of threads

14. Run the program by entering the following in the command prompt:
```
python main.py
```

## Batch process multiple sonar recordings

PING-Mapper includes a script which will find all sonar recordings in a directory (even subdirectories!) and batch process them. This is useful if you have spent a day on the water collecting multiple sonar recordings. Just point this script at the top-most folder, provide an output directory for processed files, and PING-Mapper will do the rest!

1. Open the Anaconda Prompt (*Windows users: Anaconda Powershell Prompt is preferred*). Navigate to the `PINGMapper` directory using the `cd` command. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

2. Open `main_batchDirectory.py` in a text editor/IDE (I use [Atom](https://atom.io/)). Here is an example of the script:

```
import sys
sys.path.insert(0, 'src')


from funcs_common import *
from main_readFiles import read_master_func
from main_rectify import rectify_master_func


import time
import datetime

#################
# User Parameters
#################

inDir = r'./exampleData'
outDir = r'./procData'


t = 10                     #Temperature (C)
nchunk = 500               #Pings per chunk
exportUnknown = True       #Export unknown ping attributes
wcp = True                 #Export water column present tiles
wcr = True                 #Export water column removed tiles
smthDep = True             #Smooth depth
adjDep = 0                 #Depth adjustment (in pixels)
pltBedPick = True          #Export bedpick plots

rect_wcp = True            #Export georectified wcp
rect_wcr = True            #Export rectified wcr

mosaic = 1                 #Export georectified mosaic

threadCnt = 0              #Thread count

#################
#################

# Find all DAT and SON files in all subdirectories of inDir
inFiles=[]
for root, dirs, files in os.walk(inDir):
    for file in files:
        if file.endswith('.DAT'):
            inFiles.append(os.path.join(root, file))


for datFile in inFiles:
    try:
        start_time = time.time()


        inPath = os.path.dirname(datFile)
        humFile = datFile
        recName = os.path.basename(humFile).split('.')[0]
        sonPath = os.path.join(inDir, recName)
        sonFiles = sorted(glob(sonPath+os.sep+'*.SON'))


        projDir = os.path.join(outDir, recName)


        print('sonPath',sonPath)
        print('\n\n\n+++++++++++++++++++++++++++++++++++++++++++')
        print('+++++++++++++++++++++++++++++++++++++++++++')
        print('***** Working On *****')
        print(humFile)
        print('Start Time: ', datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))


        print('\n===========================================')
        print('===========================================')
        print('***** READING *****')
        read_master_func(sonFiles, humFile, projDir, t, nchunk, exportUnknown, wcp, wcr, detectDepth, smthDep, adjDep, pltBedPick)


        if rect_wcp or rect_wcr:
            print('\n===========================================')
            print('===========================================')
            print('***** RECTIFYING *****')
            rectify_master_func(sonFiles, humFile, projDir, nchunk, rect_wcp, rect_wcr, adjDep, mosaic)


    except:
        print('Could not process:', datFile)


    gc.collect()
    print("\n\nTotal Processing Time: ",datetime.timedelta(seconds = round(time.time() - start_time, ndigits=0)))
```

3. Enter paths to input and output directory:

```
inDir = r'./exampleData'
outDir = r'./procData'
```

4. Edit parameters as necessary (*Note: supplied parameters will be applied to all sonar recordings. See section above for description of parameters*):

```
t = 10                     #Temperature (C)
nchunk = 500               #Pings per chunk
exportUnknown = True       #Export unknown ping attributes
wcp = True                 #Export water column present tiles
wcr = True                 #Export water column removed tiles
smthDep = True             #Smooth depth
adjDep = 0                 #Depth adjustment (in pixels)
pltBedPick = True          #Export bedpick plots

rect_wcp = True            #Export georectified wcp
rect_wcr = True            #Export rectified wcr

mosaic = 1                 #Export georectified mosaic

threadCnt = 0              #Thread count
```

5. Run the program by entering the following in the command prompt:
```
python main_batchDirectory.py
```
