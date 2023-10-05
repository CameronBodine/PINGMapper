---
layout: default
title: Running PING-Mapper
nav_order: 5
parent: Getting Started

nav_exclude: false

---

# Running `PING-Mapper`

After you have [tested](./Testing.md) `PING-Mapper` on the sample datasets, you are ready to process your own sonar recordings! Two scripts have been included with `PING-Mapper` and are found in the top-level directory. The first is `main.py` which allows you to process a single sonar recording. It is recommended that you start with this script when first processing sonar recordings with the software. A second script called `main_batchDirectory.py` provides an example of how to batch process many sonar recordings at once. Both approaches are covered below.

## Process single sonar recording

### Step 1
1. Open the Anaconda Prompt (*Windows users: Anaconda Powershell Prompt is preferred*). Navigate to the `PINGMapper` directory using the `cd` command. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory. For example:
```
cd C:\users\Cam\MyPythonRepos\PINGMapper
```

2. Activate the `ping` virtual environment:
```
conda activate ping
```

You should see something similar to the following in the command prompt following by a flashing cursor:
```
(ping) PS C:\users\Cam\Python\PINGMapper>
```

### Step 2
In the File Explorer, navigate to the PINGMapper folder. You should see a file named `main.py`. Right-click the file and there should be an option to edit the script with IDLE, or select your preferred text editor like Notepad. Don't use a word processor like Microsoft Word.

We are going to update this script with new parameters that we define, specifically this chunk of code:

```
#######################
# Start User Parameters
#######################

# Path to data/output

humFile = "/mnt/md0/SynologyDrive/GulfSturgeonProject/SSS_Data/Pascagoula/Bouie/BOU_20210402_USM1/030_023_Rec00003.DAT" # Path to sonar recording .DAT file
projDir = "/home/cbodine/Desktop/test" # Directory where you want to export files

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
egn_stretch = 1 # 0==Min-Max; 1==% Clip; 2==Standard deviation
egn_stretch_factor = 0.5 # If % Clip, the percent of histogram tails to clip (1.0 == 1%);
                         ## If std, the number of standard deviations to retain


# Sonogram Exports
tileFile = '.jpg' # Img format for plots and sonogram exports
wcp = True #Export tiles with water column present: 0==False; 1==True, side scan channels only; 2==True, all available channels.
wcr = True #Export Tiles with water column removed (and slant range corrected): 0==False; 1==True, side scan channels only; 2==True, all available channels.


# Speed corrected sonogram Exports
lbl_set = 2 # Export images for labeling: 0==False; 1==True, keep water column & shadows; 2==True, remove water column & shadows (based on maxCrop)
spdCor = 1 # Speed correction: 0==No Speed Correction; 1==Stretch by GPS distance; !=1 or !=0 == Stretch factor.
maxCrop = False # True==Ping-wise crop; False==Crop tile to max range.


# Depth Detection and Shadow Removal Parameters
remShadow = 2 # 0==Leave Shadows; 1==Remove all shadows; 2==Remove only bank shadows
detectDep = 1 # 0==Use Humminbird depth; 1==Auto detect depth w/ Zheng et al. 2021;
## 2==Auto detect depth w/ Thresholding

smthDep = True #Smooth depth before water column removal
adjDep = 0 #Aditional depth adjustment (in pixels) for water column removaL
pltBedPick = True #Plot bedpick on sonogram


# Rectification Sonar Map Exports
rect_wcp = True #Export rectified tiles with water column present
rect_wcr = True #Export rectified tiles with water column removed/slant range corrected
son_colorMap = 'Greys_r' # Specify colorramp for rectified imagery. '_r'==reverse the ramp: https://matplotlib.org/stable/tutorials/colors/colormaps.html


# Substrate Mapping
pred_sub = 1 # Automatically predict substrates and save to npz: 0==False; 1==True, SegFormer Model
pltSubClass = True # Export plots of substrate classification and predictions
map_sub = True # Export substrate maps (as rasters). Requires substrate predictions saved to npz.
export_poly = True # Convert substrate maps to shapefile: map_sub must be > 0 or raster maps previously exported
map_class_method = 'max' # 'max' only current option. Take argmax of substrate predictions to get final classification.


# Mosaic Exports
pix_res = 0 # Pixel resolution [meters]: 0 = Default (~0.02 m). ONLY APPLIES TO MOSAICS
mosaic_nchunk = 0 # Number of chunks per mosaic: 0=All chunks. Specifying a value >0 generates multiple mosaics if number of chunks exceeds mosaic_nchunk.
mosaic = 1 #Export sonar mosaic; 0==Don't Mosaic; 1==Do Mosaic - GTiff; 2==Do Mosaic - VRT
map_mosaic = 1 #Export substrate mosaic; 0==Don't Mosaic; 1==Do Mosaic - GTiff; 2==Do Mosaic - VRT

#####################
# End User Parameters
#####################
```

### Step 3
Enter paths to .DAT file and output directory:
```
humFile = "C:/user/cam/myHumDat.DAT" # Path to sonar recording .DAT file
projDir = "C:/user/cam/myHumAnswerBox/myHumDat" # Directory where you want to export files
```

{: .warning }
> Windows users: Make sure your filepaths are structured in one of the three following file formats:
> - (Double backslashes): `humFile = “C:\\Users\\cam\\Documents\\Programs\\PINGMapper\\Rec00012.DAT”`
> - (Path preceded by `r`): `humFile = r“C:\Users\cam\Documents\Programs\PINGMapper\Rec00012.DAT”`
> - (Single forward slash): `humFile = “C:/Users/cam/Documents/Programs/PINGMapper/Rec00012.DAT”`

### Step 4
Set whether to overwrite existing projects:

    - `project_mode = 0`: Create a new project. If project exists, program will exit without any changes
    - `project_mode = 1`: Overwrite project, if it exists.

### Step 5
Update general parameters as necessary:

1. Update temperature (in Celcius) with average temperature during scan:
```
tempC=10
```

2. Choose the number of pings to export per sonar tile. This can be any value but all testing has been performed on chunk sizes of 500.
```
nchunk = 500
```

3. Option to crop the max range extent [in meters].
    - `cropRange = 0`: Don't crop range.
    - `cropRange > 0`: Crop sonar returns past this range.

4. Option to export unknown ping metadata fields.
```
exportUnknown = True
```

5. Option to locate missing pings and fill with NoData. See [Issue #33](https://github.com/CameronBodine/PINGMapper/issues/33) and [this](https://cameronbodine.github.io/PINGMapper/docs/gettingstarted/Exports.html#orig_record_num) for more information:
```
fixNoDat = True
```

6. Specify maximum number of threads to use during processing:
    - `threadCnt = 0`: Use all available threads.
    - `threadCnt > 0`: Use specified number of threads.
    - `threadCnt < 0`: Use total number of threads minus `threadCnt`.

### Step 6
Provide an x and y offset to account for position offset between the control head (or external GPS) and the transducer.
```
## Origin (0,0) is the location of control head (or external GPS)
## X-axis runs from bow (fore, or front) to stern (aft, or rear) with positive offset towards the bow, negative towards stern
## Y-axis runs from portside (left) to starboard (right), with negative values towards the portside, positive towards starboard
## Z-offsets can be provided with `adjDep` below.
x_offset = 0.0 # [meters]
y_offset = 0.0 # [meters]
```

### Step 7
Sonar intensity corrections:

1. Do Empirical Gain Normalization to correct for sonar attenuation:
```
egn = True
```

2. Specify how to stretch the pixel values after correction:
    - `egn_stretch = 0`: Stretch to min and max value.
    - `egn_stretch = 1`: Do percent clip [Recommended]
    - `egn_stretch = 2`: Standard deviation

3. EGN stretch factor
    - If `egn_stretch == 1`, the value supplied to `egn_stretch_factor` specifies percent of the histogram tails to clip.
    - if `egn_stretch == 2`, the value supplied to `egn_stretch_factor` specifies the number of standard deviations to retain.

### Step 8
Update sonogram export parameters as necessary:

1. Specify sonogram tile file type (".png" or ".jpg"). This applies to sonograms and plots. Note that all mosaics are exported to either GTiff or VRT.
```
tileFile = ".jpg"
```

2. Export un-rectified sonagrams with water column present `wcp` (*all sonar channels*) AND/OR water column removed `wcr` (*side scan channels only*):
```
wcp = True
wcr = True
```

3. Export images that are speed corrected or stretched along track by some factor. This is used for generating images for substrate labeling but can have other applications:
    - `lbl_set = 0`: Don't export.
    - `lbl_set = 1`: Export images with water column and shadows *present*.
    - `lbl_set = 2`: Export images with water column and shadows *removed*.



4. Specify if images should be speed corrected (based on distance traveled) or stretched by a factor:
    - `spdCor = 0`: No speed correction.
    - `spdCor = 1`: Speed correction based on distance traveled.
    - `spdCor != 0 or 1`: Stretch along the track by the specified factor.


5. Perform ping-wise (`True`) or maximum range for a chunk as determined by shadow detection (`False`). See [this](https://cameronbodine.github.io/PINGMapper/docs/gettingstarted/Exports.html#speed-corrected) for more information:
```
maxCrop = True
```

### Step 9
Update depth detection and shadow removal parameters as necessary:

1. Automatically segment and remove shadows from any image exports:
    - `remShadow = 0`: Don't segment or remove shadows.
    - `remShadow = 1`: Remove all shadows.
    - `remShadow = 2`: Remove only those shadows in the far-field. In a river, this is usually caused by the river bank.


2. Automatically estimate the depth of water column for each side scan channel:
    - `detectDep = 0`: Don't automatically estimate depth. Use sonar sensor depth instead.
    - `detectDep = 1`: Automatically segment and remove water column with a Residual U-Net, based upon [Zheng et al. 2021](https://www.mdpi.com/2072-4292/13/10/1945).
    - `detectDep = 2`: Automatically segment and remove water column with binary segmentation.


3. Smooth the depth data before removing water column.  This may help with any strange issues or noisy depth data.
```
smthDep = True
```


4. Additional depth adjustment in number of pixels for water column removal. Positive values increase depth estimate, resulting in a larger proportion of sonar returns being removed during water column removal:
```
adjDep = 0
```


5. Plot bedpick(s) on non-rectified sonogram for visual inspection:
```
pltBedPick = True
```
### Step 10
Update georectification parameters as necessary:

1. Export georectified sonar imagery (water column present `rect_wcp` AND/OR water column removed/slant range corrected `rect_wcr`) for use in GIS.
```
rect_wcp = True
rect_wcr = True
```

2. Apply colormap to rectified imagery. Any [Matplotlib colormap](https://matplotlib.org/stable/tutorials/colors/colormaps.html) can be used. If the colormap needs to be reversed, append `_r` to the colormap name:
```
son_colorMap = "Greys_r" # Reversed
# OR
son_colorMap = "Greys"
```

### Step 11
Update substrate mapping parameters as necessary:

1. Substrate prediction:
    - `pred_sub = 0`: Don't do prediction
    - `pred_sub = 1`: Use pre-trained SegFormer model to do prediction

2. Export substrate plots:
```
pltSubClass = True
```

3. Export rasster georectified substrate maps:
```
map_sub = True
```

4. Export polygon georectified substrate maps (must set `map_sub = True` also):
```
export_poly
```

5. There is only one substrate classification method:
```
map_class_method = "max"
```

### Step 12
Update mosaic export parameters as necessary:

1. Specify an output pixel resolution [in meters]:
    - `pix_res = 0`: Use default resolution [~0.02 m].
    - `pix_res > 0`: Resize mosaic to output pixel resolution.

2. Optionally limit the number of chunks per mosaic:
    - `mosaic_nchunk = 0`: Mosaic all chunks into single mosaic
    - `mosaic_nchunk > 0`: Maximum number of chunks per mosaic

3. Option to mosaic georectified sonar imagery (exported from step 10). Options include:
    - `mosaic = 0`: Don't Mosaic
    - `mosaic = 1`: Do Mosaic - GeoTiff
    - `mosaic = 2`: Do Mosaic - VRT (virtual raster)

4. Option to mosaic georectified substrate classification rasters (exported from step 11). Options include:
    - `map_mosaic = 0`: Don't Mosaic
    - `map_mosaic = 1`: Do Mosaic - GeoTiff
    - `map_mosaic = 2`: Do Mosaic - VRT (virtual raster)


### Step 13

{: .g2k }
> Don't forget to save the file! You can either save it, or save as a new file inside the PINGMapper directory, i.e. `main_myscript.py`.

Run the program by entering the following in the command prompt:
```
python main.py
```

or if you changed the filename:
```
python main_myscript.py
```

## Batch process multiple sonar recordings

PING-Mapper includes a script which will find all sonar recordings in a directory (even subdirectories!) and batch process them. This is useful if you have spent a day on the water collecting multiple sonar recordings. Just point this script at the top-most folder, provide an output directory for processed files, and PING-Mapper will do the rest!

### Step 1
1. Open the Anaconda Prompt (*Windows users: Anaconda Powershell Prompt is preferred*). Navigate to the `PINGMapper` directory using the `cd` command. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory. For example:
```
cd C:\users\Cam\MyPythonRepos\PINGMapper
```

2. Activate the `ping` virtual environment:
```
conda activate ping
```

You should see something similar to the following in the command prompt following by a flashing cursor:
```
(ping) PS C:\users\Cam\Python\PINGMapper>
```

### Step 2
In the File Explorer, navigate to the PINGMapper folder. You should see a file named `main_batchDirectory.py`. Right-click the file and there should be an option to edit the script with IDLE, or select your preferred text editor like Notepad. Don't use a word processor like Microsoft Word.

We are going to update this script with new parameters that we define, specifically this chunk of code:

```
#######################
# Start User Parameters
#######################

# Path to data/output

humFile = "/mnt/md0/SynologyDrive/GulfSturgeonProject/SSS_Data/Pascagoula/Bouie/BOU_20210402_USM1/030_023_Rec00003.DAT" # Path to sonar recording .DAT file
projDir = "/home/cbodine/Desktop/test" # Directory where you want to export files

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
egn_stretch = 1 # 0==Min-Max; 1==% Clip; 2==Standard deviation
egn_stretch_factor = 0.5 # If % Clip, the percent of histogram tails to clip (1.0 == 1%);
                         ## If std, the number of standard deviations to retain


# Sonogram Exports
tileFile = '.jpg' # Img format for plots and sonogram exports
wcp = True #Export tiles with water column present: 0==False; 1==True, side scan channels only; 2==True, all available channels.
wcr = True #Export Tiles with water column removed (and slant range corrected): 0==False; 1==True, side scan channels only; 2==True, all available channels.


# Speed corrected sonogram Exports
lbl_set = 2 # Export images for labeling: 0==False; 1==True, keep water column & shadows; 2==True, remove water column & shadows (based on maxCrop)
spdCor = 1 # Speed correction: 0==No Speed Correction; 1==Stretch by GPS distance; !=1 or !=0 == Stretch factor.
maxCrop = False # True==Ping-wise crop; False==Crop tile to max range.


# Depth Detection and Shadow Removal Parameters
remShadow = 2 # 0==Leave Shadows; 1==Remove all shadows; 2==Remove only bank shadows
detectDep = 1 # 0==Use Humminbird depth; 1==Auto detect depth w/ Zheng et al. 2021;
## 2==Auto detect depth w/ Thresholding

smthDep = True #Smooth depth before water column removal
adjDep = 0 #Aditional depth adjustment (in pixels) for water column removaL
pltBedPick = True #Plot bedpick on sonogram


# Rectification Sonar Map Exports
rect_wcp = True #Export rectified tiles with water column present
rect_wcr = True #Export rectified tiles with water column removed/slant range corrected
son_colorMap = 'Greys_r' # Specify colorramp for rectified imagery. '_r'==reverse the ramp: https://matplotlib.org/stable/tutorials/colors/colormaps.html


# Substrate Mapping
pred_sub = 1 # Automatically predict substrates and save to npz: 0==False; 1==True, SegFormer Model
pltSubClass = True # Export plots of substrate classification and predictions
map_sub = True # Export substrate maps (as rasters). Requires substrate predictions saved to npz.
export_poly = True # Convert substrate maps to shapefile: map_sub must be > 0 or raster maps previously exported
map_class_method = 'max' # 'max' only current option. Take argmax of substrate predictions to get final classification.


# Mosaic Exports
pix_res = 0 # Pixel resolution [meters]: 0 = Default (~0.02 m). ONLY APPLIES TO MOSAICS
mosaic_nchunk = 0 # Number of chunks per mosaic: 0=All chunks. Specifying a value >0 generates multiple mosaics if number of chunks exceeds mosaic_nchunk.
mosaic = 1 #Export sonar mosaic; 0==Don't Mosaic; 1==Do Mosaic - GTiff; 2==Do Mosaic - VRT
map_mosaic = 1 #Export substrate mosaic; 0==Don't Mosaic; 1==Do Mosaic - GTiff; 2==Do Mosaic - VRT

#####################
# End User Parameters
#####################
```

### Step 3
Enter paths to input and output directory. The `inDir` is the parent folder containing all of the .DAT files and folders containing associated .SON and .IDX files. The `outDir` is the parent folder where all exports from the sonar recordings will be found. `outDir` must exist to export the data. The exports for each recording will share the same name as the Humminbird file, i.e. "Rec00008".
```
inDir = r"C:/user/cam/myHumRecordings"
outDir = r"C:/user/cam/ExportedDatasets"
```

### Step 4
Edit parameters as necessary (*Note: supplied parameters will be applied to all sonar recordings. See section above for description of parameters*).

### Step 5

{: .g2k }
> Don't forget to save the file! You can either save it, or save as a new file inside the PINGMapper directory, i.e. `main_batchDirectory_myscript.py`.

Run the program by entering the following in the command prompt:
```
python main_batchDirectory.py
```

or if you changed the filename:
```
python main_batchDirectory_myscript.py
```
