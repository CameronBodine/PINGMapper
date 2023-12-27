---
layout: default
title: Vision
nav_exclude: true
---

# Vision
{: .no_toc }

An essay on how `PING-Mapper` can improve in the future through partnerships.
{: .fs-6 .fw-300 }

---

{: .summary }
>`PING-Mapper` is an open-source software (that means <u>FREE!</u>) that can *automatically* do a lot of truly impressive things:
> - Process sonar recordings from any Humminbird&reg; side imaging fishfinder
> - Map and classify aquatic substrates
> - Export georeference sonar mosaics
> - Correct sonar intensities
> - Detect depth and shadows from side scan channels
> - Export sonar attributes (i.e., latitude, longitude, vessel heading, etc.) to CSV
> - Export plots and sonograms
>
> This functionality, however, is just scratching the surface on what is possible in order to achieve the full potential of `PING-Mapper`. In order to realize this vision, we need to provide additional functionality, including:
> - Support for a variety of sonar instruments
> - Substrate and habitat mapping across a diversity of aquatic environments
> - Automated identification, mapping, and enumeration of specific features (e.g., fish, ghost crab pots, cultural features, etc.)
> - ...
>
>**Are you interested in partnering to build the future of low-cost aquatic imaging and mapping with PING-Mapper?**
> ---
>
> Do you share this vison? Can you benefit from additional development and application of these tools? Are there other features that I am missing that you would like to see supported? I am interested to hear from you in order to discuss these possibilities. Please read on to find out more!


## Introduction

Hi! My name is [Cameron Bodine](https://cameronbodine.github.io/) and I am the primary developer of `PING-Mapper`. `PING-Mapper` has been the focus of my PhD dissertation research in Ecological Informatics at Northern Arizona University. I have wanted to build something like `PING-Mapper` ever since I started manually mapping substrates following the Kaeser and Litts ([2010](https://doi.org/10.1577/1548-8446-35.4.163); [2013](https://doi.org/10.1002/rra.2556)) method and discovered that there was a possibility of automating many, if not all, of the workflows as demonstrated by [Dan Buscombe](https://www.mardascience.com/docs/intro#dr-dan-buscombe) with his work on PyHum ([Buscombe et al., 2016](https://doi.org/10.1016/j.envsoft.2016.12.003); [Buscombe, 2017](https://doi.org/10.1016/j.envsoft.2016.12.003)). 

Let's examine a few of the features provided by `PING-Mapper`. The core functionality of the software is the ability to automatically generate georectified sonar mosaics. While this is available in many third-party software packages, it has never been done so efficiently with an open-source tool. A major improvement to the quality of the imagery is now possible by applying an Empirical Gain Normalization correction to the imagery. This helps to balance the sonar intensity across the image and increase contrast. The most exciting feature of the tool is the ability to automatically generate substrate maps. Deep learning algorithms have been trained to segment and classify substrate patches in a reproducible workflow resulting in significant time savings in map production. You can learn more about these features in Bodine et al. ([2022](https://doi.org/10.1029/2022EA002469); [2023](https://doi.org/10.31223/X5K402)) and in the 15 minute presentation I gave at the 2023 American Fisheries Society annual meeting linked below.

<iframe width="560" height="315" src="https://www.youtube.com/embed/AlebxkKn83c?si=dOVicn8zDsRSHXyP" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

With my nearly five-year tenure as a graduate student coming to a close in May 2024, I am proud to provide an open-source tool to the community to enable efficient imaging and mapping of aquatic systems. In fact, several researchers who are not direct collaborators with this project are already using `PING-Mapper`. This is largely due to the fact that the tools are easy to use and require little manual intervention. Additionally, the workflows are completely transparent because the code are housed in a public repository, allowing anyone with Python experience to evaluate and prototype new functionality. While these methods are important improvements to generating benthic datasets from recreation fish finders, we are just scratching the surface as there is much more that can be done. The following sections describe a vision of some of the improvements that can be developed, given interest and financial investment by potential collaborators and sponsors.


## Support for other sonar systems

`PING-Mapper` currently supports sonar recordings collected with Humminbird&reg; side imaging systems. Humminbird&reg; is only one of several recreation-grade sonar systems used in aquatic studies. The other two major brands are Lowrance&reg; and Garmin&reg;. Future development of `PING-Mapper` could focus on adding support for these brands. For example, Lowrance&reg; has a style of interferometric sonar which enables collecting depth across the swath of the side-scan channels ([Halmai, 2020](https://doi.org/10.3390/ijgi9030149)). Support for a wide range of sonar instruments and brands would increase versitility of the software and provide more options for end-users.

## Improving automated mapping

In version 2.0 of `PING-Mapper`, a function to reproducibly map substrates automatically was added to the software and is detailed in a preprint ([Bodine et al., 2023](https://doi.org/10.31223/X5K402)). This is the first example of such a workflow specifically made for recreation-grade sonar datasets, that I know of. 
This was accomplished by training deep learning models to learn to map substrates the same way that I do manually. I took a bunch of sonar images collected on the Pearl and Pascagoula river systems in Mississippi which I then delineated and classified different types of substrates with a program called [Doodler](https://github.com/Doodleverse/dash_doodler) ([Buscombe et al., 2023](https://doi.org/10.1029/2021EA002085)). The sonar images and maps (e.g., labels) where then used to train deep learning models using workflows available in [Segmentation Gym](https://github.com/Doodleverse/segmentation_gym) ([Buscombe and Goldstein, 2022](https://doi.org/10.1029/2022EA002332)). The trained models were then integrated into a function in `PING-Mapper`, allowing for the automatic generation of substrate maps from any sonar recording.

But how accurate are these models and resulting maps?? Well, one measure I made is holding out a portion of the training data, or test set, during model training which I used to evaluate the model's performance. This can tell us how good the models are at learning how to map like me. It turns out the models classified 78% of the test pixels with the same classification I assigned. It appears that the models are able to learn to map like me and could likely improve with more consistency in the training set, additional training image-label pairs, image-label pairs developed by other people on other systems, and providing more examples for less frequent substrate classes.

Another measure is how well do these maps reflect true conditions in the field, which is the accuracy we actually care about. `PING-Mapper` collaborators in the [Estuarine and Movement Ecology Lab](https://www.andreslab.net/) at the University of Southern Mississippi are visiting random locations throughout the study systems to determine the true substrate type. This will serve two purposes. First, I will be able to assign an accuracy to these maps. These numbers may be misleading as change could have occured due to high-flow events between data collection and field validation, which will be 1-3 years depending on location. Second, these data will help me validate my interpretation of features in the sonar images, which will lead to improved and more accurate training sets.

## Mapping other substrate and habitat classes

The substrate classes available in the map are based on the classes that were visible in the sonar imagery. Some classes which are common to other large river systems in the Southeastern United States simply weren't present. For example, there was little to no aquatic vegetation in these systems at the time of data collection. There was also relatively small proportion cobble and boulder substrate patches. Data collection on a wide range of river systems with a variety of substrate classes would allow the creation of training sets and models that encompass that breadth of substrate and habitat types. There would even be an opportunity to train models specific to a region or class of aquatic system.


## Locating and enumerating targets

One of the primary uses of side-scan sonar systems is to locate and identify different types of targets (i.e., fish, archeology sites, hazards). Side-scan sonar imagery is particularly conducive to this task due to the clarity of the imagery. A class of deep learning models which detect objects exists which could be trained to automatically locate and enumerate these targets. For example, the [Trembanis Lab](https://www.udel.edu/academics/colleges/ceoe/departments/smsp/faculty/arthur-trembanis/) at the University of Delaware are crowd-sourcing a vast catalog of imagery in search of [ghost crab pots](https://www.udel.edu/udaily/2019/may/Ghost-crab-pots-Delaware-Inland-Bays/) and are using object detection models to identify these biological hazards. These types of models could also be integrated into `PING-Mapper`, providing a rapid method of identifying and enumerating these targets. Similarly, models could be trained to locate different species of fish or other types of targets.

## Centralized aquatic data and processing center

Imagine you are interested in conducting a study on a new aquatic system and you want to get an idea of what conditions are like. You navigate a web browser to the AquaDatStor (or similar), find your area of interest, download existing sonar mosaics and maps, and load them into GIS. You didn't have to collect the data or process anything yet you are off to the races in understanding conditions of this system. Or maybe you just returned from a day of scanning in the field and want to see what you scanned and generate some maps. This is all possible by creating a centralized data and processing center in the cloud. Through a crowd-sourcing model, researchers could upload their own data, access data collected by other community members, and benefit from analysis ready data products generated by remote servers.

## Finding PING-Mapper's new home

As I mentioned at the beginning of this long-winded and meandering essay, I will be ending my tenure as a graduate student in May 2024. I will be moving on to the next thing, which, at this point, is unknown. If afforded the opportunity, I would love to keep working on `PING-Mapper` and continuing to develop the software along the directions I have outlined above. If you or your organization are interested in partnering on this, please reach out to me at csb67@nau.edu.

## References

Bodine, C. S., Buscombe, D., Best, R. J., Redner, J. A., & Kaeser, A. J. (2022). PING‐Mapper: Open‐Source Software for Automated Benthic Imaging and Mapping Using Recreation‐Grade Sonar. Earth and Space Science, 9(9). [https://doi.org/10.1029/2022EA002469](https://doi.org/10.1029/2022EA002469)

Bodine, C. S., Buscombe, D., Hocking, T. D. (2023). Open-source approach for reproducible substrate mapping using semenatic segmentation on recreation-grade side scan sonar datasets. EarthArXiv. [https://doi.org/10.31223/X5K402](https://doi.org/10.31223/X5K402)

Buscombe, D., Grams, P. E., & Smith, S. M. C. (2016). Automated Riverbed Sediment Classification Using Low-Cost Sidescan Sonar. Journal of Hydraulic Engineering, 142(2), 06015019. [https://doi.org/10.1061/(ASCE)HY.1943-7900.0001079](https://doi.org/10.1061/(ASCE)HY.1943-7900.0001079)

Buscombe, D. (2017). Shallow water benthic imaging and substrate characterization using recreational-grade sidescan-sonar. Environmental Modelling & Software, 89, 1–18. [https://doi.org/10.1016/j.envsoft.2016.12.003](https://doi.org/10.1016/j.envsoft.2016.12.003)

Buscombe, D., & Goldstein, E. B. (2022). A Reproducible and Reusable Pipeline for Segmentation of Geoscientific Imagery. Earth and Space Science, 9(9). [https://doi.org/10.1029/2022EA002332](https://doi.org/10.1029/2022EA002332)

Buscombe, D., Goldstein, E. B., Sherwood, C. R., Bodine, C. S., Brown, J. A., Favela, J., … Wernette, P. (2022). Human‐in‐the‐Loop Segmentation of Earth Surface Imagery. Earth and Space Science, 9(3), e2021EA002085. [https://doi.org/10.1029/2021EA002085](https://doi.org/10.1029/2021EA002085)

Halmai, Á., Gradwohl–Valkay, A., Czigány, S., Ficsor, J., Liptay, Z. Á., Kiss, K., … Pirkhoffer, E. (2020). Applicability of a Recreational-Grade Interferometric Sonar for the Bathymetric Survey and Monitoring of the Drava River. ISPRS International Journal of Geo-Information, 9(3), 149. https://doi.org/10.3390/ijgi9030149

Kaeser, A. J., & Litts, T. L. (2010). A Novel Technique for Mapping Habitat in Navigable Streams Using Low‐cost Side Scan Sonar. Fisheries, 35(4), 163–174. [https://doi.org/10.1577/1548-8446-35.4.163](https://doi.org/10.1577/1548-8446-35.4.163)

Kaeser, A. J., Litts, T. L., & Tracy, T. W. (2013). Using Low‐Cost Side‐Scan Sonar for Benthic Mapping Throughout the Lower Flint River, Georgia, USA. River Research and Applications, 29(5), 634–644. [https://doi.org/10.1002/rra.2556](https://doi.org/10.1002/rra.2556)