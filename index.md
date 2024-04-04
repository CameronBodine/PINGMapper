---
layout: default
title: Home
nav_order: 1
description: "PING-Mapper is an open-source software for recreationg-grade sonar"
---

# PING-Mapper
{: .fs-9 }

Open-source interface for processing recreation-grade side scan sonar datasets and reproducibly mapping benthic habitat
{: .fs-6 .fw-300 }

[Get started now](./docs/gettingstarted/gettingstarted.md){: .btn .btn-primary .fs-5 .mb-4 .mb-md-0 .mr-2 } [View it on GitHub](https://github.com/CameronBodine/PINGMapper){: .btn .fs-5 .mb-4 .mb-md-0 }

---

`PING-Mapper` transforms recreation-grade sonar systems into scientific data collectors, allowing researchers and citizens alike to reproducibly map their aquatic system with minimal expertise in data processing.

## Overview

### Key Functionality

- Decode Humminbird&reg; (tested on 1197, 1198, 1199, Helix, Solix, Onix).  If it doesn't work for your Humminbird&reg; recording, submit an [Issue](https://github.com/CameronBodine/PINGMapper/issues).  For more information on Humminbird&reg; recording file formats, [read the docs](./docs/advanced/HumFileStructure.html).

- Export all metadata from .DAT and .SON files to .CSV.

- Automatically detect depth (i.e. [Zheng et al. 2021](https://www.mdpi.com/2072-4292/13/10/1945)) and shadows in side scan channels .

- Correct sonar backscatter with Empiracle Gain Normalization.

- Export un-rectified sonar tiles with water column present (WCP) AND/OR export un-rectified sonograms with water column removed (WCR) using Humminbird depth estimates OR automated depth detections.

- Export speed corrected un-rectified sonograms.

- Smooth and interpolate GPS track points.

- Export georectified WCP (spatially inaccurate due to presence of water column) AND/OR WCR sonar imagery for use in GIS w/wo shadows removed.

- Mosaic georectified sonar imagery.

- Automatically segment and classify substrate patches.

More information on PING-Mapper exports can be found [here](./docs/gettingstarted/Exports.html).

### Compatible Humminbird&reg; Systems

`PING-Mapper` is currently compatible with Humminbird&reg; side imaging sonar systems. The software has been designed to work with any model, but has been specifically tested with the following models:

- 998
- 1198
- 1199
- Helix
- Solix
- Onix

If `PING-Mapper` doesn't work for your Humminbird&reg; recording, submit an [Issue](https://github.com/CameronBodine/PINGMapper/issues).



### Examples

`PING-Mapper` is designed to **decode sonar recordings** from a Humminbird&reg; like this:

<img src="./assets/Suwa_Son.gif" width="800"/>

*Video made with [HumViewer](https://humviewer.cm-johansen.dk/)*

Export **ping attributes** from each sonar channel including sonar depth, latitude, longitude, vessel speed & heading, etc., to file for further analysis:

<img src="./assets/PingAttribute.png" width="800"/>

And **export georectified mosaics** of the sonar imagery and **automatically generate substrate maps**:

<img src="./assets/GithubMap.png" width="800"/>



## Find out more!

There are several ways you can find out more about `PING-Mapper`. The first of which is this website! You can also check out the manuscripts and Zenodo archives below. If you use `PING-Mapper` for your work, please cite the journal articles below.


### PING-Mapper v2.0.0
The second version of PING-Mapper is available now. Scientific articles documenting the new functionality will be posted here when available. Check the [release notes](https://github.com/CameronBodine/PINGMapper/releases/tag/v2.0.0) for more information.

#### Preprint
[![Earth ArXiv Preprint DOI](https://img.shields.io/badge/%F0%9F%8C%8D%20EarthArXiv%F0%9F%8C%8D-doi.org%2F10.31223%2FX5K402-%23FF7F2A)](https://doi.org/10.31223/X5K402)

#### Code
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.10120054.svg)](https://doi.org/10.5281/zenodo.10120054)

#### Segmentation models
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.10093642.svg)](https://doi.org/10.5281/zenodo.10093642)

#### Segmentation model training datasets
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.10119320.svg)](https://doi.org/10.5281/zenodo.10119320)


### PING-Mapper v1.0.0
An overview of `PING-Mapper` v1.0.0 functionality and justification are published in AGU's Earth and Space Science scientific journal. If you use `PING-Mapper` for your work, please cite the article!

#### Journal Article
Bodine, C. S., Buscombe, D., Best, R. J., Redner, J. A., & Kaeser, A. J. (2022). PING-Mapper: Open-source software for automated benthic imaging and mapping using recreation-grade sonar. Earth and Space Science, 9, e2022EA002469. [https://doi.org/10.1029/2022EA002469](https://doi.org/10.1029/2022EA002469)

#### Preprint
[![Earth ArXiv Preprint DOI](https://img.shields.io/badge/%F0%9F%8C%8D%20EarthArXiv%F0%9F%8C%8D-doi.org%2F10.31223%2FX5XP8Q-%23FF7F2A)](https://doi.org/10.31223/X5XP8Q)

#### Code
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6604785.svg)](https://doi.org/10.5281/zenodo.6604785)

## Ready to get started?

Follow the installation and testing instructions to [Get Started!](./docs/gettingstarted/gettingstarted.md)

# Acknowledgements

*This study was made possible by a partnership between the U.S. Fish and Wildlife Service and Northern Arizona University. Funding for this work was provided by the Open Ocean Trustee Implementation Group to restore natural resources injured by the 2010 Deepwater Horizon oil spill in the Gulf of Mexico. The contents of this website are those of the authors and do not necessarily represent the views of the U.S. Fish and Wildlife Service or Northern Arizona University.*

**Primary Developer:** [Cameron S. Bodine](https://github.com/CameronBodine)

**Co-Developer:** [Daniel Buscombe](https://github.com/dbuscombe-usgs)

Thanks to project collaborators Adam Kaeser (USFWS), Channing St. Aubin (USFWS), Mike Andres (USM), Kasea Price (USM), Alyssa Pagel (USM), Eric Haffey (USM), and Katherine Wright (USM).

A special thanks to advocates and early-adoptors including, but not limited to, Jennylyn Redner, Adrian Pinchbeck, Art Trembanis, Dan Carlson, Alan Ryon, Mirko Denecke, Dan Haught, Dan Hamill, Mark Lundine, Elizabeth Greenheck, Hendra Kurnia Febriawan, Bryan Bozeman, Paul Grams, Matt Kaplinski, Jess Kozarek, Chris Milliren, Brett Connell and James Parham.

Cameron wishes to thank his PhD dissertation committee: Toby Hocking, Co-Chair; advisor Dan Buscombe, Co-Chair; Rebecca Best; and Adam Kaeser.

## PING-Mapper is part of the Doodleverse!
![153729377-e16d0679-ca0d-4d0d-a9f9-90306ba2f871](https://github.com/CameronBodine/PINGMapper/assets/54146655/54df6fdd-26a6-4c26-9cab-9fc834e60ed1)

The Doodleverse is an opinionated collection of Python packages designed for geoscientific image segmentation. Find out more on [GitHub](https://github.com/Doodleverse).







<!-- ## Welcome to GitHub Pages

You can use the [editor on GitHub](https://github.com/CameronBodine/PINGMapper/edit/gh-pages/index.md) to maintain and preview the content for your website in Markdown files.

Whenever you commit to this repository, GitHub Pages will run [Jekyll](https://jekyllrb.com/) to rebuild the pages in your site, from the content in your Markdown files.

### Markdown

Markdown is a lightweight and easy-to-use syntax for styling your writing. It includes conventions for

```markdown
Syntax highlighted code block

# Header 1
## Header 2
### Header 3

- Bulleted
- List

1. Numbered
2. List

**Bold** and _Italic_ and `Code` text

[Link](url) and ![Image](src)
```

For more details see [Basic writing and formatting syntax](https://docs.github.com/en/github/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax).

### Jekyll Themes

Your Pages site will use the layout and styles from the Jekyll theme you have selected in your [repository settings](https://github.com/CameronBodine/PINGMapper/settings/pages). The name of this theme is saved in the Jekyll `_config.yml` configuration file.

### Support or Contact

Having trouble with Pages? Check out our [documentation](https://docs.github.com/categories/github-pages-basics/) or [contact support](https://support.github.com/contact) and we’ll help you sort it out.
 -->
