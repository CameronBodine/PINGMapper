# Humminbird Recording: DAT/SON Processing & Raw Data Export
By Cameron S. Bodine

## Introduction

This report documents new workflows for decoding Humminbird binary sonar recordings that will process recordings from any Humminbird model with any firmware version (see [Humminbird Recording: DAT & SON Binary Structure](../docs/BinaryStructure.md) for more information).  The workflow includes procedures for loading DAT/SON files, exporting associated metadata, and exporting raw un-rectified imagery.

Two scripts, modeled after PyHum [[1]](#1) [[2]](#2), have been developed to read in and decode DAT and SON files, export sonar record metadata, and export un-rectified imagery of the sonar echogram.  The first script **pj_readFiles.py** handles the creation and manipulation of a `class sonObj()` instance. The `class sonObj()` is contained in **c_sonObj.py** which holds the attributes and functions for reading, decoding, and fetching data from DAT and SON files. These two scripts work in tandem to retrieve data from DAT and SON files.  **pj_readFiles.py** will be described to show how it interacts with the class.

## Decode DAT File

The script **pj_readFiles.py** contains a single function `read_master_func()` which is called from **main_single.py**.  The parameters passed to `read_master_func()` are as follows:

##### Parameters
*sonFiles : str*
- SON file path

*humFile : str*
- DAT file path

*projDir : str*
- Project directory

*tempC : float [Default=0.1]*
- Water temperature (Celcius) / 10

*nchunk : int [Default=500]*
- Number of sonar records per chunk

Using the above parameters, a single `sonObj()` instance is then generated called `son`.  The structure of the DAT file is determined by calling `son._getHumDatStruct()`.  The length of the DAT file, in bytes, is used to create a dictionary (`son.humDatStruct`) to store the byte index, offset from byte index where the data is stored, data length (in bytes), and data for each of the known and unknown elements in the DAT file.  For example, a recording generated from a 1100 series Humminbird will store the Unix date/time when the recording began at byte index `20`, with a `0` offset (DAT file attributes are not preceded by a tag, as is the case with SON files), with a length of `4` (32 bit integer).  See [DAT File Structure](../docs/BinaryStructure.md#21-DAT-File-Structure) for more information.  Once the DAT structure is determined, the contents of the DAT file are stored in `son.humDatStruct` by calling `son._getHumdat()`.  




## 3) References

<a id="1">[1]</a> Buscombe, D., Grams, P. E., & Smith, S. M. C. (2015). Automated Riverbed Sediment Classification Using Low-Cost Sidescan Sonar. Journal of Hydraulic Engineering, 142(2), 06015019. https://doi.org/10.1061/(ASCE)HY.1943-7900.0001079

<a id="2">[2]</a> Buscombe, D. (2017). Shallow water benthic imaging and substrate characterization using recreational-grade sidescan-sonar. Environmental Modelling and Software, 89, 1–18. https://doi.org/10.1016/j.envsoft.2016.12.003
