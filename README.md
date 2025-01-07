# PING-Mapper
[![PyPI - Version](https://img.shields.io/pypi/v/pingmapper?style=flat-square&label=Latest%20Version%20(PyPi))](https://pypi.org/project/pingmapper/)
<!-- ![PING-Mapper](./docs/attach/PINGMapper_Logo.png) -->
![PINGMapper_Logo](https://github.com/CameronBodine/PINGMapper/blob/main/docs/attach/PINGMapper_Logo.png?raw=true)

[![GitHub last commit](https://img.shields.io/github/last-commit/CameronBodine/PINGMapper)](https://github.com/CameronBodine/PINGMapper/commits)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/CameronBodine/PINGMapper)](https://github.com/CameronBodine/PINGMapper/commits)
[![GitHub](https://img.shields.io/github/license/CameronBodine/PINGMapper)](https://github.com/CameronBodine/PINGMapper/blob/main/LICENSE)

[![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)](https://www.python.org/)
[![Anaconda](https://img.shields.io/badge/conda-342B029.svg?&style=for-the-badge&logo=anaconda&logoColor=white)](https://www.anaconda.com/)
[![Numpy](https://img.shields.io/badge/Numpy-791a9d?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2C2D72?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Tensorflow](https://img.shields.io/badge/TensorFlow-FF6F00?style=for-the-badge&logo=TensorFlow&logoColor=white)](https://www.tensorflow.org/)

## 

**Transform recordings from recreation-grade side scan sonar systems...**

<!-- <img src="../main/docs/attach/Suwa_Son.gif" width="800"/> -->

![PINGMapper_Logo](https://github.com/CameronBodine/PINGMapper/blob/main/docs/attach/Suwa_Son.gif?raw=true)

*Video made with [HumViewer](https://humviewer.cm-johansen.dk/)*

**...into scientific datasets!**

<!-- <img src="../main/docs/attach/GithubMap.png" width="800"/> -->

![GithubMap](https://github.com/CameronBodine/PINGMapper/blob/main/docs/attach/GithubMap.png?raw=true)

# Overview

`PINGMapper` is an open-source Python interface for reading and processing side scan sonar datasets and reproducibly mapping benthic habitat features. `PINGMapper` transforms recreation-grade sonar systems (i.e. fishfinders) into scientific data collectors, allowing researchers and citizens alike to reproducibly map their aquatic system with minimal expertise in data processing.


### New Functionality & Bug Fixes (January 6, 2025)
- PINGMapper is a PyPi package
  - [![PyPI - Version](https://img.shields.io/pypi/v/pingmapper?style=flat-square&label=Latest%20Version%20(PyPi))](https://pypi.org/project/pingmapper/)
- [PINGInstaller](https://github.com/CameronBodine/PINGInstaller) - Light-weight application for installing PING ecosystem (PINGMapper, etc.)
    - [![PyPI - Version](https://img.shields.io/pypi/v/pinginstaller?style=flat-square&label=Latest%20Version%20(PyPi))](https://pypi.org/project/pinginstaller/)
- [PINGWizard](https://github.com/CameronBodine/PINGWizard) - Light-weight interface for running PING ecosystem (PINGMapper, etc.)
    - [![PyPI - Version](https://img.shields.io/pypi/v/pingwizard?style=flat-square&label=Latest%20Version%20(PyPi))](https://pypi.org/project/pingwizard/)

### New Functionality & Bug Fixes (December 28, 2024)
- [PINGVerter](https://github.com/CameronBodine/PINGVerter) - A Python-based convertor for sonar logs collected with consumer-grade fishfinders.
  - Support for Lowrance&reg; *.sl2 and *.sl3 files!
  - Improved mechanism for reading sonar logs, inspired by [sonarlight](https://github.com/KennethTM/sonarlight), resulting in **~1.3x speedup** when running the [Small Dataset Test](https://cameronbodine.github.io/PINGMapper/docs/gettingstarted/Testing.html#small-dataset-test).
- [Sonar log filtering](https://github.com/CameronBodine/PINGMapper/releases/tag/v2.1.0) based on heading deviation, speed, and Area of Interest (AOI) shapefile.
- Export coverage and trackline shapefiles.
- Fix [bankline export](https://github.com/CameronBodine/PINGMapper/releases/tag/v2.1.0).

See the [v3.0.0 release notes](https://github.com/CameronBodine/PINGMapper/releases/tag/v3.0.0) for more information

### Key Functionality
- [PINGVerter](https://github.com/CameronBodine/PINGVerter) - A Python-based convertor for sonar logs collected with consumer-grade fishfinders.
  - [![PyPI - Version](https://img.shields.io/pypi/v/pingverter?style=flat-square&label=Latest%20Version%20(PyPi))](https://pypi.org/project/pingverter/)
  - Decode Humminbird&reg; sonar recordings.  For more information on Humminbird&reg; recording file formats, [read the docs](https://cameronbodine.github.io/PINGMapper/docs/advanced/HumFileStructure.html).

  - Decode Lowrance&reg; *.sl2 and *.sl3 files. Lowrance&reg; support made possible by open-source projects including [SL3Reader](https://github.com/halmaia/SL3Reader), [sonarlight](https://github.com/KennethTM/sonarlight), and [Navico (Lowrance, Simrad, B&G) Sonar Log File Format](https://www.memotech.franken.de/FileFormats/Navico_SLG_Format.pdf).

  - If it doesn't work for your Humminbird&reg; or Lowrance&reg; recording, submit an [Issue](https://github.com/CameronBodine/PINGMapper/issues).

- Export all metadata from .DAT, .SON, .sl2, and .sl3 files to .CSV.

- Automatically detect depth (i.e. [Zheng et al. 2021](https://www.mdpi.com/2072-4292/13/10/1945)) and shadows in side scan channels .

- Correct sonar backscatter with Empiracle Gain Normalization.

- Export un-rectified sonar tiles with water column present (WCP) AND/OR export un-rectified sonograms with water column removed (WCR) using Humminbird depth estimates OR automated depth detections.

- Export speed corrected un-rectified sonograms.

- Smooth and interpolate GPS track points.

- Export georectified WCP (spatially inaccurate due to presence of water column) AND/OR WCR sonar imagery for use in GIS w/wo shadows removed.

- Mosaic georectified sonar imagery.

- Automatically segment and classify substrate patches.

More information on PING-Mapper exports can be found [here](https://cameronbodine.github.io/PINGMapper/docs/gettingstarted/Exports.html).

## Compatible Sonar Systems

`PING-Mapper` is currently compatible with Humminbird&reg; and Lowrance&reg; side imaging sonar systems. The software has been tested with:

### Humminbird&reg; Models:
- 998
- 1198
- 1199
- Helix
- Solix
- Onix
- Apex

### Lowrance&reg; File Formats:
- sl2
- sl3

If `PING-Mapper` doesn't work for your Humminbird&reg; or Lowrance&reg; sonar system, submit an [Issue](https://github.com/CameronBodine/PINGMapper/issues).


# Software Documentation
There are several ways you can find out more about `PING-Mapper`. Check out the website, manuscripts, and Zenodo archives below. If you use `PING-Mapper` for your work, please cite the journal articles below.

## Website
Check out PING-Mapper's [website](https://cameronbodine.github.io/PINGMapper/) for more information.

## PING-Mapper v2.0.0
The second version of PING-Mapper is available now. Check the [release notes](https://github.com/CameronBodine/PINGMapper/releases/tag/v2.0.0) for more information.

#### Journal Article
 Bodine, C. S., Buscombe, D., & Hocking, T. D. (2024). Automated river substrate mapping from sonar imagery with machine learning. Journal of Geophysical Research: Machine Learning and Computation, 1, e2024JH000135. [https://doi.org/10.1029/2024JH000135](https://doi.org/10.1029/2024JH000135) 

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


# Ready to get started?

Follow the installation and testing instructions to [Get Started!](https://cameronbodine.github.io/PINGMapper/docs/gettingstarted)

# Acknowledgements

*This study was made possible by a partnership between the U.S. Fish and Wildlife Service and Northern Arizona University. Funding for this work was provided by the Open Ocean Trustee Implementation Group to restore natural resources injured by the 2010 Deepwater Horizon oil spill in the Gulf of Mexico. The contents of this website are those of the authors and do not necessarily represent the views of the U.S. Fish and Wildlife Service or Northern Arizona University.*

**Primary Developer:** [Cameron S. Bodine](https://github.com/CameronBodine)

**Co-Developer:** [Daniel Buscombe](https://github.com/dbuscombe-usgs)

Thanks to project collaborators Adam Kaeser (USFWS), Channing St. Aubin (USFWS), Mike Andres (USM), Kasea Price (USM), Alyssa Pagel (USM), Eric Haffey (USM), and Katherine Wright (USM).

A special thanks to advocates and early-adoptors including, but not limited to, Jennylyn Redner, Adrian Pinchbeck, Art Trembanis, Dan Carlson, Alan Ryon, Mirko Denecke, Dan Haught, Dan Hamill, Mark Lundine, Elizabeth Greenheck, Hendra Kurnia Febriawan, Bryan Bozeman, Paul Grams, Matt Kaplinski, Jess Kozarek, Chris Milliren, Brett Connell, James Parham and Vincent Capone.

Cameron wishes to thank his PhD dissertation committee chair Toby Hocking, co-chair and advisor Dan Buscombe, Rebecca Best, and Adam Kaeser.

## Future Development, Collaborations, & Partnerships

If you are interested in partnering on future developments, please reach out to [Cameron Bodine](https://cameronbodine.github.io/).

# PING-Mapper is part of the Doodleverse!
![153729377-e16d0679-ca0d-4d0d-a9f9-90306ba2f871](https://github.com/CameronBodine/PINGMapper/assets/54146655/54df6fdd-26a6-4c26-9cab-9fc834e60ed1)

The Doodleverse is an opinionated collection of Python packages designed for geoscientific image segmentation. Find out more on [GitHub](https://github.com/Doodleverse).


