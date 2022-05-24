![GitHub last commit](https://img.shields.io/github/last-commit/CameronBodine/PINGMapper)
![GitHub commit activity](https://img.shields.io/github/commit-activity/m/CameronBodine/PINGMapper)
![GitHub](https://img.shields.io/github/license/CameronBodine/PINGMapper)

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Anaconda](https://img.shields.io/badge/conda-342B029.svg?&style=for-the-badge&logo=anaconda&logoColor=white)
![Numpy](https://img.shields.io/badge/Numpy-791a9d?style=for-the-badge&logo=numpy&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2C2D72?style=for-the-badge&logo=pandas&logoColor=white)
![Tensorflow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=TensorFlow&logoColor=white)

![PING-Mapper](./docs/attach/PINGMapper_Logo.png)


Python interface for reading, processing, and mapping side scan sonar data from Humminbird&reg; sonar systems.  Running `main.py` (see [this section](#Running-PING-Mapper-on-your-own-data) for more information) carries out the following procedures:

1. Decode Humminbird&reg; (tested on 1197, 1198, 1199, Helix, Solix, Onyx).  If it doesn't work for your Humminbird&reg; recording, submit an [Issue](https://github.com/CameronBodine/PINGMapper/issues).  For more information on Humminbird&reg; recording file formats, [read the docs](../main/docs/BinaryStructure.md).

2. Export all metadata from .DAT and .SON files to .CSV.

3. (Optional) Export un-rectified sonar tiles with water column present (WCP) AND/OR export un-rectified sonar tiles with water column removed (WCR) using Humminbird depth estimates.

4. Smooth and interpolate GPS track points.

5. (Optional) Export georectified WCP (spatially inaccurate due to presence of water column) AND/OR WCR sonar imagery for use in GIS.

6. (Optional) Mosaic georectified sonar imagery from step 5.

## Workflows in the Pipeline
1. Automatic depth detection (i.e. [Zheng et al. 2021](https://www.mdpi.com/2072-4292/13/10/1945))
2. Imagery corrections (radiometric, attenuation, etc.)
3. Automatic substrate classification
4. GUI front-end, either as standalone software, or QGIS plugin
5. So much more...

## Installation
1. Install [Anaconda](https://www.anaconda.com) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

2. Open Anaconda Prompt and navigate to where you would like to save PING Mapper:
```
cd C:\users\Cam\MyPythonRepos
```

3. Clone the repo:
```
git clone --depth 1 https://github.com/CameronBodine/PINGMapper
```

4. Change directory into PINGMapper folder:
```
cd PINGMapper
```

5. Create a conda environment called `ping` and activate it:
```
conda env create --file conda/PINGMapper.yml
conda activate ping
```

**NOTE** Installation may take some time, please be patient.

## Testing PING Mapper
1. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

2. Enter the following into the prompt:  
```
python main.py
```

Outputs are found in `.\\PINGMapper\\procData\\PINGMapperTest`.

## Running PING Mapper on your own data
1. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

2. Open `main.py` in a text editor/IDE (I use [Atom](https://atom.io/)).

3. Update lines 28-30 with path's to your data and your chosen output directory:
```
humFile = "C:/user/cam/myHumDat.DAT"
sonPath = "C:/user/cam/myHumDat"
projDir = "C:/user/cam/myHumAnswerBox/myHumDat"
```

Windows users: Make sure your filepaths are structured in one of the three following file formats:
- (Double backslashes): `humFile = “C:\\Users\\cam\\Documents\\Programs\\PINGMapper\\Rec00012.DAT”`
- (Path preceded by `r`): `humFile = r“C:\Users\cam\Documents\Programs\PINGMapper\Rec00012.DAT”`
- (Single forward slash): `humFile = “C:/Users/cam/Documents/Programs/PINGMapper/Rec00012.DAT”`

4. Line 32: Update temperature `t=10` with average temperature during scan.

5. Line 33: Choose the number of pings to export per sonar tile.  This can be any value but all testing has been performed on chunk sizes of 500.

6. Line 34: Option to export unknown ping metadata fields.

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
