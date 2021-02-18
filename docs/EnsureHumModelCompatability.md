
# Developing and documenting pj_readFiles.py and c_sonObj.py functionality
By Cameron S. Bodine

## Introduction
PyHum (citation) is an open-source python framework for reading and processing from a low-cost Humminbird sidescan sonar system.  Originally developed for Python 2, it can read in Humminbird DAT and SON files, export the data, process radiometric corrections, classify bed texture, and produce maps.  Since its release, additional and enhanced functionality has been identified by the software authors and end-users, including Python 3 compatibility.  This report documents new workflows for decoding Humminbird binary sonar recordings that will work on sonar recordings from any Humminbird model with any firmware version.  The goal and objectives for this effort are as follows:

1. Ensure functionality with all current Humminbird models.
    a. Collect and catalog sonar recordings from various Humminibrd models (in progress)
    b. Develop workflows to test PyHum on sonar recording catalog. (in progress)
    c. Identify and implement alternative workflows for decoding binary sonar recordings. (in progress)

This report documents a new workflow for decoding and loading sonar recordings, and exporting non-rectified imagery.  First, new findings concerning the DAT and SON binary file structure will be discussed.  Next, two new Python scripts for processing these files will be discussed.  Finally, these new workflows will be tested against a variety of Humminbird sonar recordings to determine if they can successfully decode the binary structure and export relevant data.

## DAT and SON Binary Structure
The initial release of PyHum documented the known binary structure of Humminbird sonar files (https://github.com/dbuscombe-usgs/PyHum/blob/master/docs/data_formats.rst).  Using this as a guide, DAT and SON files were further explored using a program called Hexinator (https://hexinator.com/).  Hexinator interface allows you to quickly view binary data in hexidecimal format.  It has a tool that allows you to annotate the file with known structures and elements, known as a grammer, which can be applied to any open binary file which aides in seeing differences in the binary structure.
