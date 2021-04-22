# Humminbird Recording: Sonar Georectification
By Cameron S. Bodine

## 1) Introduction
This document outlines the workflows for generating georectified side scan sonar imagery.  Georectification is the process of warping sonar tile pixel coordinates to real-world coordinates, enabling end-users to visualize sonar imagery in a GIS in context.  This is the next step in the PING Mapper workflow, following [Humminbird Recording: DAT/SON Processing & Raw Data Export](../docs/Processing&RawDataExport.md).  

Three scripts handle the georectification procedure.  **c_rectObj.py** contains a new class called `class rectObj(sonObj)`.  This class is a child of `class sonObj()`, found in **c_sonObj.py**, giving `rectObj()` access to `sonObj()` attributes and functions.  **py_rectify.py** handles the creation and manipulation of the `rectObj()` instance.  

The workflow begins with loading a previously saved `sonObj` object and creating a new `rectObj()` instance.  A smoothed trackline is then fit to the sonar GPS track points and sonar records (pings) are interpolated along the smoothed trackline.  The port and starboard range extent for each chunk is calculated, following procedures from PyHum [[1]](#1) [[2]](#2).  Finally, previously exported un-rectified sonar tiles are warped and georectified, and a GeoTiff is exported for each chunk.

## 2) Load Sonar Object
The script **pj_rectify.py** contains a single function `rectify_master_func()`, called from **main_single.py**.  The parameters passed to `rectify_master_func()` are as follows:

Parameters
----------
*sonFiles : str*
- SON file path

*humFile : str*
- DAT file path

*projDir : str*
- Project directory

Each of the previously saved sonar objects (`projDir/meta/beamNumber_beamName_meta.meta`) are temporarily loaded and a new `rectObj()` is initialized and all the attributes in the sonar object are loaded into `rectObj()`.  Each sonar channel now has it's own `rectObj()` instance and are stored in the list `rectObjs`.  The objects in `rectObjs` are interrogated to find the port and starboard channels, and are stored in a new list `portstar`.

## 3) Smooth Trackline
Modern Humminbird units have a built-in GPS to store the latitude and longitude for each sonar record.  Ports are available on the control head to connect to external GPS if desired.  Unless a survey grade GPS is used, the resulting trackpoints will exhibit a stepwise behavior, with multiple sonar records sharing the same geographic coordinates.  Ideally, the boat is constantly moving with smooth navigation and consistent speed during a sonar survey in order to generate optimal images of the bed.  The raw trackpoints do not accurately reflect this.  Therefore, additional processing of the trackpoints is needed to create a smooth trackline.






## 7) References

<a id="1">[1]</a> Buscombe, D., Grams, P. E., & Smith, S. M. C. (2015). Automated Riverbed Sediment Classification Using Low-Cost Sidescan Sonar. Journal of Hydraulic Engineering, 142(2), 06015019. https://doi.org/10.1061/(ASCE)HY.1943-7900.0001079

<a id="2">[2]</a> Buscombe, D. (2017). Shallow water benthic imaging and substrate characterization using recreational-grade sidescan-sonar. Environmental Modelling and Software, 89, 1–18. https://doi.org/10.1016/j.envsoft.2016.12.003
