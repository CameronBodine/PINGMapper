# PINGMapper
Python interface for reading, processing, and mapping side scan sonar data from Humminbird&reg; sonar systems.  Running `main.py` (see [this section](#Running-PING-Mapper-on-your-own-data) for more information) carries out the following procedures:

1. Decode Humminbird&reg; (tested on 1197, 1198, 1199, Helix, Solix, Onyx).  If it doesn't work for your Humminbird&reg; recording, submit an [Issue](https://github.com/CameronBodine/PINGMapper/issues).  For more information on Humminbird&reg; recording file formats, [read the docs](../main/docs/BinaryStructure.md).

2. Export all metadata from .DAT and .SON files to .CSV.

3. (Optional) Export un-rectified sonar tiles with water column present (wcp) AND/OR export un-rectified sonar tiles with water column removed and slant range corrected (wcr/scr) using Humminbird depth estimates.

4. Smooth and interpolate GPS track points.

5. (Optional) Export georectified WCP (water column present) (spatially inaccurate due to presence of water column) AND/OR SRC (slant range corrected) sonar imagery for use in GIS.

6. (Optional) Mosaic georectified sonar imagery from step 5.

## Workflows in the Pipeline
1. Automatic depth detection (i.e. [Zheng et al. 2021](https://www.mdpi.com/2072-4292/13/10/1945))
2. Imagery corrections (radiometric, attenuation, etc.)
3. Automatic substrate classification
4. GUI front-end, either as standalone software, or QGIS plugin
5. So much more...

## Installation
1. Install [Anaconda](https://www.anaconda.com) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

2. Open Anaconda Prompt and navigate to where you would like to save PING Mapper.

3. Clone the repo:
```
git clone --depth 1 https://github.com/CameronBodine/PINGMapper
```

4. Create a conda environment called `ping` and activate it:
```
conda env create --file conda/PINGMapper.yml
conda activate ping
```

**NOTE** Installation may take some time, please be patient.

## Testing PING Mapper
1. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

2. Enter the following into the prompt and press enter.  Outputs are found in `.\\PINGMapper\\procData\\PINGMapperTest`.
```
python main.py
```

## Running PING Mapper on your own data
1. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

2. Open `main.py` in a text editor/IDE (I use [Atom](https://atom.io/)).

3. Update lines 28-30 with path's to your data and your chosen output directory:
```
humFile = "C:/user/Cam/myHumDat.DAT"
sonPath = "C:/user/Cam/myHumDat"
projDir = "C:/user/Cam/myHumAnswerBox/myHumDat"
```

Windows users: Make sure your filepaths are structured in one of the three following file formats:
- (Double backslashes): `humFile = “C:\\Users\\cam\\Documents\\Programs\\PINGMapper\\Rec00012.DAT”`
- (Path preceded by `r`): `humFile = r“C:\Users\cam\Documents\Programs\PINGMapper\Rec00012.DAT”`
- (Single forward slash): `humFile = “C:/Users/dwhealdo/Documents/Programs/PINGMapper/Rec00012.DAT”`

4. Line 32: Update temperature `t=10` with average temperature during scan.

5. Line 33: Choose the number of pings to export per sonar tile.  This can be any value but all testing has been performed on chunk sizes of 500.

6. Line 34: Option to export unknown sonar record metadata fields.

7. Line 35-36: Export un-rectified sonar tiles with water column present AND/OR water column removed.

8. Line 37: Option to use Humminbird depth (`detectDepth=0`), automatically detect depth through thresholding (`detectDepth=1`), automatically detect depth with Residual U-Net (`detectDepth=2`), or do both automatic depth picking methods (`detectDepth=3`).  NOTE: this will soon be updated with a new method, stay tuned...

9. Line 39: Smooth the depth data before removing water column.  This may help with any strange issues or noisy depth data.

10. Line 40: Additional depth adjustment in number of pixels for water column removal.

11. Line 41: Plot bedick(s) on non-rectified sonogram for visual inspection.

12. Line 43-44: Export georectified sonar imagery (water-column-present AND/OR water-column-removed/slant-range-corrected) for use in GIS.

13. Line 46: Option to mosaic georectified sonar imagery (exported from step 12).

14. Save the file.

15. Run PING Mapper:
```
python main.py
```
