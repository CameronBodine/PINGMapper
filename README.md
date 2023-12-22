# PING-Mapper v2.0.0
PING-Mapper is a Python interface for reading, processing, and mapping side scan sonar data from Humminbird&reg; sonar systems.

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

<img src="../main/docs/attach/GithubMap.png" width="800"/>

# Overview
Running `main.py` (see [this section](#Running-PING-Mapper-on-your-own-data) for more information) carries out the following procedures:

1. Decode Humminbird&reg; (tested on 1197, 1198, 1199, Helix, Solix, Onix).  If it doesn't work for your Humminbird&reg; recording, submit an [Issue](https://github.com/CameronBodine/PINGMapper/issues).  For more information on Humminbird&reg; recording file formats, [read the docs](../main/docs/BinaryStructure.md).

2. Export all metadata from .DAT and .SON files to .CSV.

3. Automatically detect depth (i.e. [Zheng et al. 2021](https://www.mdpi.com/2072-4292/13/10/1945)) and shadows in side scan channels .

4. Correct sonar backscatter with Empiracle Gain Normalization.

5. Export un-rectified sonar tiles with water column present (WCP) AND/OR export un-rectified sonograms with water column removed (WCR) using Humminbird depth estimates OR automated depth detections.

6. Export speed corrected un-rectified sonograms.

7. Smooth and interpolate GPS track points.

8. Export georectified WCP (spatially inaccurate due to presence of water column) AND/OR WCR sonar imagery for use in GIS w/wo shadows removed.

9. Mosaic georectified sonar imagery.

10. Automatically segment and classify substrate patches.

More information on PING-Mapper exports can be found [here](https://cameronbodine.github.io/PINGMapper/docs/gettingstarted/Exports.html).


# Software Documentation
## Website
Check out PING-Mapper's [website](https://cameronbodine.github.io/PINGMapper/) for more information.

## PING-Mapper v2.0.0
The second version of PING-Mapper is available now. Scientific articles documenting the new functionality will be posted here when available. Check the [release notes](https://github.com/CameronBodine/PINGMapper/releases/tag/v2.0.0) for more information.

### Preprint
[![Earth ArXiv Preprint DOI](https://img.shields.io/badge/%F0%9F%8C%8D%20EarthArXiv%F0%9F%8C%8D-doi.org%2F10.31223%2FX5K402-%23FF7F2A)](https://doi.org/10.31223/X5K402)

### Code
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.10120054.svg)](https://doi.org/10.5281/zenodo.10120054)

### Segmentation models
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.10093642.svg)](https://doi.org/10.5281/zenodo.10093642)

### Segmentation model training datasets
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.10119320.svg)](https://doi.org/10.5281/zenodo.10119320)


## PING-Mapper v1.0.0
An overview of PING-Mapper v1.0.0 functionality and justification are published in AGU's Earth and Space Science scientific journal. If you use PING-Mapper for your work, please cite the article!

### Journal Article
Bodine, C. S., Buscombe, D., Best, R. J., Redner, J. A., & Kaeser, A. J. (2022). PING-Mapper: Open-source software for automated benthic imaging and mapping using recreation-grade sonar. Earth and Space Science, 9, e2022EA002469. https://doi.org/10.1029/2022EA002469

### Preprint
[![Earth ArXiv Preprint DOI](https://img.shields.io/badge/%F0%9F%8C%8D%20EarthArXiv%F0%9F%8C%8D-doi.org%2F10.31223%2FX5XP8Q-%23FF7F2A)](https://doi.org/10.31223/X5XP8Q)


### Code
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6604785.svg)](https://doi.org/10.5281/zenodo.6604785)


# Getting Started

## Installation
View the [installation instructions](https://cameronbodine.github.io/PINGMapper/docs/gettingstarted/Installation.html).

## Testing PING-Mapper
To determine if PING-Mapper is functioning as expected, run the [test scripts](https://cameronbodine.github.io/PINGMapper/docs/gettingstarted/Testing.html) with example recordings shipped with the software.

## Running PING-Mapper on your own data
Learn how to use PING-Mapper to [process your own data](https://cameronbodine.github.io/PINGMapper/docs/gettingstarted/Running.html).

# PING-Mapper is part of the Doodleverse!
![153729377-e16d0679-ca0d-4d0d-a9f9-90306ba2f871](https://github.com/CameronBodine/PINGMapper/assets/54146655/54df6fdd-26a6-4c26-9cab-9fc834e60ed1)

The Doodleverse is an opinionated collection of Python packages designed for geoscientific image segmentation. Find out more on [GitHub](https://github.com/Doodleverse).


