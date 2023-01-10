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

Bodine, C. S., Buscombe, D., Best, R. J., Redner, J. A., & Kaeser, A. J. (2022). PING-Mapper: Open-source software for automated benthic imaging and mapping using recreation-grade sonar. Earth and Space Science, 9, e2022EA002469. https://doi.org/10.1029/2022EA002469

PrePrint: [![Earth ArXiv Preprint DOI](https://img.shields.io/badge/%F0%9F%8C%8D%20EarthArXiv%F0%9F%8C%8D-doi.org%2F10.31223%2FX5XP8Q-%23FF7F2A)](https://doi.org/10.31223/X5XP8Q)


### Code that made the paper
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6604785.svg)](https://doi.org/10.5281/zenodo.6604785)

### Overview
Running `main.py` (see [this section](#Running-PING-Mapper-on-your-own-data) for more information) carries out the following procedures:

1. Decode Humminbird&reg; (tested on 1197, 1198, 1199, Helix, Solix, Onix).  If it doesn't work for your Humminbird&reg; recording, submit an [Issue](https://github.com/CameronBodine/PINGMapper/issues).  For more information on Humminbird&reg; recording file formats, [read the docs](../main/docs/BinaryStructure.md).

2. Export all metadata from .DAT and .SON files to .CSV.

3. Automatically detect depth (i.e. [Zheng et al. 2021](https://www.mdpi.com/2072-4292/13/10/1945)) and shadows in side scan channels .

4. Export un-rectified sonar tiles with water column present (WCP) AND/OR export un-rectified sonograms with water column removed (WCR) using Humminbird depth estimates OR automated depth detections.

5. Export speed corrected un-rectified sonograms.

6. Smooth and interpolate GPS track points.

7. Export georectified WCP (spatially inaccurate due to presence of water column) AND/OR WCR sonar imagery for use in GIS w/wo shadows removed.

8. Mosaic georectified sonar imagery.

More information on PING-Mapper exports can be found [here](https://cameronbodine.github.io/PINGMapper/docs/gettingstarted/Exports.html).

### Workflows in the Pipeline
1. Automatic substrate classification
2. GUI front-end, either as standalone software, or QGIS plugin
3. Imagery corrections (radiometric, attenuation, etc.)
4. So much more...

## Installation
To install PING-Mapper, visit the [website](https://cameronbodine.github.io/PINGMapper/docs/gettingstarted/Installation.html).

## Testing PING Mapper
To determine if PING-Mapper is functioning as expected, run the [test scripts](https://cameronbodine.github.io/PINGMapper/docs/gettingstarted/Testing.html) with example recordings shipped with the software.

## Running PING Mapper on your own data
For information on processing your own data with PING-Mapper, see the [website](https://cameronbodine.github.io/PINGMapper/docs/gettingstarted/Running.html).
