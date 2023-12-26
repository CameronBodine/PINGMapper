---
layout: default
title: Vision
nav_exclude: true
---

# A vision for the future

Hi! My name is [Cameron Bodine](https://cameronbodine.github.io/) and I am the primary developer of `PING-Mapper`. `PING-Mapper` has been the focus of my PhD dissertation research in Ecological Informatics at Northern Arizona University. I have wanted to build something like `PING-Mapper` ever since I started manually mapping substrates following the Kaeser and Litts ([2010](https://doi.org/10.1577/1548-8446-35.4.163); [2013](https://doi.org/10.1002/rra.2556)) method and discovered that there was a possibility of automating many, if not all, of the workflows as demonstrated by [Dan Buscombe](https://www.mardascience.com/docs/intro#dr-dan-buscombe) with his work on PyHum ([Buscombe et al., 2016](https://doi.org/10.1016/j.envsoft.2016.12.003); [Buscombe, 2017](https://doi.org/10.1016/j.envsoft.2016.12.003)). 

Here are some of the features of `PING-Mapper`. The core functionality is the ability to automatically generate georectified sonar mosaics. While this is available in many third-party software packages, it has never been done so efficiently with an open-source tool. A major improvement to the quality of the imagery is now possible by applying an Empirical Gain Normalization correction to the imagery. This helps to balance the sonar intensity across the image and increase contrast. The most exciting feature of the tool is the ability to automatically generate substrate maps. Deep learning algorithms have been trained to segment and classify substrate patches in a reproducible workflow resulting in significant time savings in map production. You can learn more about these features in Bodine et al. ([2022](https://doi.org/10.1029/2022EA002469); [2023](https://doi.org/10.31223/X5K402)) and in the 15 minute presentation I gave at the 2023 American Fisheries Society annual meeting linked below.

<iframe width="560" height="315" src="https://www.youtube.com/embed/AlebxkKn83c?si=dOVicn8zDsRSHXyP" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

With my nearly five year tenure as a graduate student coming to a close in May 2024, I am proud to provide an open-source tool to the community to enable efficient imaging and mapping of aquatic systems. In fact, several researchers who are not direct collaborators with this project are already using `PING-Mapper`. This is largely due to the fact that the tools are easy to use and require little manual intervention. Additionally, the workflows are completely transparent because the code are housed in a public repository, allowing anyone with Python experience to evaluate and prototype new functionality. While these are important improvements to generating benthic datasets from recreation fish finders, we are just scratching the surface as there is much more that can be done. 


## Support for other sonar systems

`PING-Mapper` currently supports sonar recordings collected with Humminbird&reg; side imaging systems.

## Improving automated mapping


## Mapping other classes


## Locating targets


## Finding PING-Mapper's new home

## References

Bodine, C. S., Buscombe, D., Best, R. J., Redner, J. A., & Kaeser, A. J. (2022). PING‐Mapper: Open‐Source Software for Automated Benthic Imaging and Mapping Using Recreation‐Grade Sonar. Earth and Space Science, 9(9). https://doi.org/10.1029/2022EA002469

Bodine, C. S., Buscombe, D., Hocking, T. D. (2023). Open-source approach for reproducible substrate mapping using semenatic segmentation on recreation-grade side scan sonar datasets. EarthArXiv. https://doi.org/10.31223/X5K402

Buscombe, D., Grams, P. E., & Smith, S. M. C. (2016). Automated Riverbed Sediment Classification Using Low-Cost Sidescan Sonar. Journal of Hydraulic Engineering, 142(2), 06015019. https://doi.org/10.1061/(ASCE)HY.1943-7900.0001079

Buscombe, D. (2017). Shallow water benthic imaging and substrate characterization using recreational-grade sidescan-sonar. Environmental Modelling & Software, 89, 1–18. https://doi.org/10.1016/j.envsoft.2016.12.003

Kaeser, A. J., & Litts, T. L. (2010). A Novel Technique for Mapping Habitat in Navigable Streams Using Low‐cost Side Scan Sonar. Fisheries, 35(4), 163–174. https://doi.org/10.1577/1548-8446-35.4.163

Kaeser, A. J., Litts, T. L., & Tracy, T. W. (2013). Using Low‐Cost Side‐Scan Sonar for Benthic Mapping Throughout the Lower Flint River, Georgia, USA. River Research and Applications, 29(5), 634–644. https://doi.org/10.1002/rra.2556