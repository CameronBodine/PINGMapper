---
layout: default
title: Presentations
nav_order: 7
nav_exclude: false
---

# Presentations
{: .no_toc }

<details open markdown="block">
  <summary>
    Table of contents
  </summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

## Ph.D. Defense: Automated Mapping of Gulf Sturgeon Spawning Habitat in Coastal Plain Rivers

By Cameron S. Bodine<sup>1</sup> (March 29, 2024)

Dissertation Committee:
Toby D. Hocking<sup>1</sup>, Ph.D., Co-Chair
Daniel Buscombe<sup>1,2</sup>, Ph.D., Co-Chair
Rebecca J. Best<sup>2</sup>, Ph.D.
Adam J. Kaeser<sup>3</sup>, Ph.D.

<sup>1</sup>School of Informatics, Computing, and Cyber Systems, Northern Arizona University
<sup>2</sup>School of Earth and Sustainability, Northern Arizona University
<sup>3</sup>Panama City Fish and Wildlife Conservation Office, U.S. Fish and Wildlife Service 

### Abstract
{: .no_toc }

Gulf sturgeon are a threatened anadromous fish species with spawning populations found in seven Gulf of Mexico coastal plain rivers (east to west: Suwannee, Apalachicola, Choctawhatchee, Yellow, Escambia/Conecuh, Pascagoula, and Pearl/Bogue Chitto rivers).  Relatively little is known about spawning habitats located in the Pearl and Pascagoula River Basins as only one confirmed spawning location has been identified. Characterizing, locating, and quantifying existing suitable spawning habitat is critical to species recovery and restoration efforts. While air and space-borne remote sensing provides invaluable insight for mapping terrestrial habitats, these approaches are limited in their application to locating Gulf Sturgeon spawning habitats due to river stage, turbidity, and canopy cover, requiring direct observation of conditions in the field. Recreation-grade side-scan sonar (SSS) instruments have demonstrated their unparalleled value as a low-cost scientific instrument capable of efficient and rapid imaging of the benthic environment. However, existing methods for generating georeferenced datasets from these instruments, especially substrate maps, remains a barrier of adoption for general scientific inquiry due to the high degree of human-intervention and required expertise. To address this short-coming, I introduce PING-Mapper; an open-source and freely available Python-based software for automatically generating geospatial benthic datasets from popular Humminbird instruments reproducibly. The modular software automatically: 1) decodes sonar recordings; 2) exports ping attributes from every sonar channel; 3) uses sonar sensor depth for water column removal; and 4) exports sonogram tiles and georectified mosaics. I further extend functionality of the software by incorporating semantic segmentation with deep neural networks to reproducibly map substrates at large spatial extents. I present a novel approach for generating label-ready sonar datasets, creating label-image training sets, and model training with transfer learning; all with open-source tools. The substrate models achieve an overall accuracy of 78% on six classes and 87% on three classes combined based on experiments on test datasets not used in model training. Additional workflows enable masking sonar shadows, calculating independent bedpicks, and correcting attenuation effects in the imagery to improve interpretability. I use PING-Mapper to map substrate and bedforms across 1,200 river kilometers (RKM) in the Pearl and Pascagoula River Basins for the first time, with no human intervention. Overall fuzzy map accuracies determined from field verification achieve 68.7 to 69.3%. The maps are synthesized to identify potential Gulf Sturgeon spawning habitat which will aid prioritization and evaluation of critical habitat restoration projects. This novel software provides an improved mechanism for automatically mapping substrate distribution from recreation-grade SSS systems, thereby lowering the barrier for inclusion in wider aquatic research.

### Video
{: .no_toc }

<iframe width="560" height="315" src="https://www.youtube.com/embed/KboFOv5ySjQ?si=goAURZB9GIG9Sqfy" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>


## Reproducible Substrate Mapping with Recreation-grade Sonar Systems

By Cameron S. Bodine, Daniel Buscombe, Adam J. Kaeser (August 2023)

Presented at: American Fisheries Society Annual Meeting

### Abstract
{: .no_toc }

Predictive understanding of the variation and distribution of substrates at large spatial extents in aquatic systems is severely lacking. This hampers efforts to numerically predict the occurrence and distribution of specific benthic habitats important to aquatic species, which must be observed in the field. Existing survey methods are limited in scale, require heavy and technically sophisticated survey equipment, or are prohibitively expensive for surveying and mapping. Recreation-grade side scan sonar (SSS) instruments, or fishfinders, have demonstrated their unparalleled value in a lightweight and easily-to-deploy system to image benthic habitats efficiently at the landscape-level. Existing methods for generating geospatial datasets from these sonar systems require a high-level of interaction from the user and are primarily closed-source, limiting opportunities for community-driven enhancements. We introduce PING-Mapper, an open-source and freely available Python-based software for generating geospatial benthic datasets from recreation-grade SSS systems. PING-Mapper is an end-to-end framework for surveying and mapping aquatic systems at large spatial extents reproducibly, with minimal intervention from the user. Version 1.0 of the software (Summer 2022) decodes sonar recordings from any existing Humminbird® side imaging system, export plots of sonar intensities and sensor-derived bedpicks and generates georeferenced mosaics of geometrically corrected sonar imagery. Version 2.0 of the software, to be released Summer 2023, extends PING-Mapper functionality by incorporating deep neural network models that automatically locate and mask sonar shadows, calculate independent bedpicks from both side scan channels, and classify substrates at the pixel level. The widespread availability of substrate information in aquatic systems will inform fish sampling efforts, habitat suitability models, and planning and monitoring habitat restoration.

### Video
{: .no_toc }

<iframe width="560" height="315" src="https://www.youtube.com/embed/AlebxkKn83c?si=hXVNl7mYob8MFbcE" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

## Advancing Freshwater Mussel Conservation via Side Scan Sonar Imaging and Habitat Mapping Automation

By Adam J. Kaeser and Cameron S. Bodine (March 2024)

Presented at: [Freshwater Mollusk Conservation Society 2024 Workshop](https://molluskconservation.org/EVENTS/2024WORKSHOP/2024_FMCS-Workshop.html)

### Abstract
{: .no_toc }

Freshwater mussels are often distributed throughout deep, turbid, and non-wadeable streams of the Southeastern Coastal Plain.  These conditions pose significant challenges to the identification and characterization of mussel habitats, and the development of standardized mussel sampling approaches across landscapes.  Nearly twenty years ago, a type of sonar called side scan sonar (SSS) first appeared on the recreational market, opening the door to underwater investigation via remote sensing to anglers and biologists alike.  Side scan sonar produces a picture-like image of the underwater environment across wide swaths (up to ~90 meters).  Data can be collected relatively quickly (8 km/hr), processed into sonar image mosaics, and then interpreted to produce classified habitat maps.  Until recently map production was a labor intensive step, requiring significant expertise, but newly emerging (and free) software tools based on machine learning make it possible to both process raw data into mosaics and automatically produce classified substrate maps in a fraction of the time.  The utility of these maps for designing sampling approaches, and developing models of the distribution and abundance of mussels via habitat associations is under exploration, and access to these no-cost tools offers the promise of greater rates of adoption and implementation in the future.  Now is the time to harness the power of imaging technology and automation to advance mussel conservation at the landscape scale.

### Video
{: .no_toc }

<iframe width="560" height="315" src="https://www.youtube.com/embed/DgLAVHdXNmM?si=ghJlIL_USq228DjM" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>