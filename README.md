# PING-Mapper
{PING-Mapper is a Python interface for reading, processing, and mapping side scan sonar data from Humminbird&reg; sonar systems.}

[![GitHub last commit](https://img.shields.io/github/last-commit/CameronBodine/PINGMapper)](https://github.com/CameronBodine/PINGMapper/commits)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/CameronBodine/PINGMapper)](https://github.com/CameronBodine/PINGMapper/commits)
[![GitHub](https://img.shields.io/github/license/CameronBodine/PINGMapper)](https://github.com/CameronBodine/PINGMapper/blob/main/LICENSE)

[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org/)
[![Anaconda](https://img.shields.io/badge/conda-342B029.svg?&style=for-the-badge&logo=anaconda&logoColor=white)](https://www.anaconda.com/)
[![Numpy](https://img.shields.io/badge/Numpy-791a9d?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2C2D72?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
<!-- [![Tensorflow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=TensorFlow&logoColor=white)](https://www.tensorflow.org/) -->


![PING-Mapper](./docs/attach/PINGMapper_Logo.png)

##
`Transform sonar recordings...`

<img src="../main/docs/attach/Suwa_Son.gif" width="800"/>

*Video made with [HumViewer](https://humviewer.cm-johansen.dk/)*

`...into scientific datasets!`

<img src="../main/docs/attach/GeorectifiedSon.PNG" width="800"/>

## Documentation
### Website 
Check out PING-Mapper's [website!](https://cameronbodine.github.io/PINGMapper/)

### Paper
[![Earth ArXiv Preprint DOI](https://img.shields.io/badge/%F0%9F%8C%8D%20EarthArXiv%F0%9F%8C%8D-doi.org%2F10.31223%2FX5XP8Q-%23FF7F2A)](https://doi.org/10.31223/X5XP8Q)

Peer Reviewed: Forthcoming...

### Code that made the paper
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6604785.svg)](https://doi.org/10.5281/zenodo.6604785)

### Overview
Running `main.py` (see [this section](#Running-PING-Mapper-on-your-own-data) for more information) carries out the following procedures:

1. Decode Humminbird&reg; (tested on 1197, 1198, 1199, Helix, Solix, Onix).  If it doesn't work for your Humminbird&reg; recording, submit an [Issue](https://github.com/CameronBodine/PINGMapper/issues).  For more information on Humminbird&reg; recording file formats, [read the docs](../main/docs/BinaryStructure.md).

2. Export all metadata from .DAT and .SON files to .CSV.

3. (Optional) Export un-rectified sonar tiles with water column present (WCP) AND/OR export un-rectified sonar tiles with water column removed (WCR) using Humminbird depth estimates.

4. Smooth and interpolate GPS track points.

5. (Optional) Export georectified WCP (spatially inaccurate due to presence of water column) AND/OR WCR sonar imagery for use in GIS.

6. (Optional) Mosaic georectified sonar imagery from step 5.

### Workflows in the Pipeline
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

**NOTE:** *Installation may take some time, please be patient.*

## Testing PING Mapper (small dataset)
A quick test can be made to ensure PING-Mapper is working properly.
1. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

2. Enter the following into the prompt:  
```
python test_PINGMapper.py 1
```

Outputs are found in `.\\PINGMapper\\procData\\PINGMapper-Test-Small-DS`.

## Testing PING Mapper (large dataset)
A test on a large (~0.5 GB; 1:00:06 duration) dataset can also be made.
1. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

2. Enter the following into the prompt:  
```
python test_PINGMapper.py 2
```

Outputs are found in `.\\PINGMapper\\procData\\PINGMapper-Test-Large-DS`.

## Running PING Mapper on your own data
1. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

2. Open `main.py` in a text editor/IDE (I use [Atom](https://atom.io/)).

3. Enter paths to DAT, SON, and output directory:

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L45-L48

Windows users: Make sure your filepaths are structured in one of the three following file formats:
- (Double backslashes): `humFile = “C:\\Users\\cam\\Documents\\Programs\\PINGMapper\\Rec00012.DAT”`
- (Path preceded by `r`): `humFile = r“C:\Users\cam\Documents\Programs\PINGMapper\Rec00012.DAT”`
- (Single forward slash): `humFile = “C:/Users/cam/Documents/Programs/PINGMapper/Rec00012.DAT”`

4. Update temperature `t=10` with average temperature during scan.

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L50

5. Choose the number of pings to export per sonar tile.  This can be any value but all testing has been performed on chunk sizes of 500.

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L51

6. Option to export unknown ping metadata fields.

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L52

7. Export un-rectified sonar tiles with water column present AND/OR water column removed.

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L53-L54

<!-- 8. Line 37: Option to use Humminbird depth (`detectDepth=0`), automatically detect depth through thresholding (`detectDepth=1`), automatically detect depth with Residual U-Net (`detectDepth=2`), or do both automatic depth picking methods (`detectDepth=3`).  NOTE: this will soon be updated with a new method, stay tuned... -->

8. Smooth the depth data before removing water column.  This may help with any strange issues or noisy depth data.

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L55

9. Additional depth adjustment in number of pixels for water column removal.

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L56

10. Plot bedick(s) on non-rectified sonogram for visual inspection.

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L57

11. Export georectified sonar imagery (water-column-present AND/OR water-column-removed/slant-range-corrected) for use in GIS.

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L59-L60

12. Option to mosaic georectified sonar imagery (exported from step 12).

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L62

13. Number of compute threads to use for processing in parallel.

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L64

14. Run the program by entering the following in the command prompt:
```
python main.py
```

## Batch process multiple sonar recordings

PING-Mapper includes a script which will find all sonar recordings in a directory (even subdirectories!) and batch process them. This is useful if you have spent a day on the water collecting multiple sonar recordings. Just point this script at the top-most folder, provide an output directory for processed files, and PING-Mapper will do the rest!

1. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

2. Open `main_batchDirectory.py` in a text editor/IDE (I use [Atom](https://atom.io/)).

3. Enter paths to input and output directory:

https://github.com/CameronBodine/PINGMapper/blob/ab77cdf0a5a4fc06d3833700e638777a0b1ec7fa/main_batchDirectory.py#L39-L40

4. Edit parameters as necessary (Note: supplied parameters will be applied to all sonar recordings):

https://github.com/CameronBodine/PINGMapper/blob/dd74f508e689ace132bdf304e28e8561cb0e100f/main_batchDirectory.py#L42-L58

5. Run the program by entering the following in the command prompt:
```
python main_batchDirectory.py
```

