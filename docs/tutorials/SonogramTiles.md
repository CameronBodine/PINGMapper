---
layout: default
title: Sonogram Tiles
nav_order: 2
parent: Tutorials

nav_exclude: false
---

# Sonogram Tiles Tutorial
{: .no_toc }

Generate a variety of sonogram tiles for various use-cases.
{: .fs-6 .fw-300 }

---

<details open markdown="block">
  <summary>
    Table of contents
  </summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

## Exporting Sonograms

### Raw

<img src="../../assets/sonotiles/SonoTiles_1_Raw.PNG" width="800"/>

#### Mask Shadows

<img src="../../assets/sonotiles/SonoTiles_2_Raw_Shdw.PNG" width="800"/>

#### Mask Shadows - Crop

<img src="../../assets/sonotiles/SonoTiles_3_Raw_ShdwCrop.PNG" width="800"/>

#### Crop - W/ Shadow Model

<img src="../../assets/sonotiles/SonoTiles_4_Raw_CropShdwModel.PNG" width="800"/>

#### Crop - W/o Shadow Model

<img src="../../assets/sonotiles/SonoTiles_5_Raw_Crop.PNG" width="800"/>

### Speed Corrected

<img src="../../assets/sonotiles/SonoTiles_6_Spd.PNG" width="800"/>

#### Mask Shadows

<img src="../../assets/sonotiles/SonoTiles_7_Spd_Shdw.PNG" width="800"/>

#### Mask Shadows - Crop

<img src="../../assets/sonotiles/SonoTiles_8_Spd_ShdwCrop.PNG" width="800"/>

#### Crop - W/ Shadow Model

<img src="../../assets/sonotiles/SonoTiles_9_CropShdwCrop.PNG" width="800"/>

#### Crop - W/o Shadow Model

<img src="../../assets/sonotiles/SonoTiles_10_Crop.PNG" width="800"/>

## Case Studies

*coming soon: show simple case studies that might link to specific tutorials (??)*

### Data Quality Review

*coming soon*

### Target Identification

*coming soon*

#### Crab Pot

*coming soon*

#### Fish Enumeration

*coming soon*

#### SAV

*coming soon*

### Generate AI-Compliant Datasets

*coming soon*

#### Doodler

Sonograms can be labeled using an open-source software called [Doodler](https://github.com/Doodleverse/dash_doodler) (See [companion manuscript](https://doi.org/10.1029/2021EA002085)). Doodler is a "Human-In-The-Loop" machine learning tool for partially supervised image segmentation. 

The image below ([Figure 5 - Bodine, Buscombe, & Hocking (2024)](https://doi.org/10.1029/2024JH000135)) shows how substrates can be labeled on a sonogram tile. The sonogram is loaded into Doodler, classes are visually annotated with doodles, and the doodles are used to train a model to segment the remaining pixels. This is how the datasets used to train the substrate model in `PINGMapper` were generated.

[![Figure 5 - Bodine, Buscombe, & Hocking (2024)](https://agupubs.onlinelibrary.wiley.com/cms/asset/e9804009-6031-4149-892e-083f2e0c0ee8/jgr133-fig-0005-m.png)](https://doi.org/10.1029/2024JH000135)

#### Roboflow

*coming soon*