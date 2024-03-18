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