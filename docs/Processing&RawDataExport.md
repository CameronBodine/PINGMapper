# Humminbird Recording: DAT & SON Processing & Raw Data Export
By Cameron S. Bodine

## Introduction


## DAT and SON Reading & Processing

Two scripts, modeled after PyHum, have been developed to read in and decode DAT and SON files, export sonar record metadata, and export un-rectified imagery of the sonar echogram.  The first script `pj_readFiles.py` handles the creation and manipulation of a `class sonObj` instance. The `class sonObj` is contained in `c_sonObj.py` which holds the attributes and functions for reading, decoding, and fetching data from DAT and SON files. These two scripts work in tandem to retrieve data from DAT and SON files.  The `class sonObj` in `c_sonObj.py` will first be described, then `pj_readFiles.py` will be described to show how it interacts with the class.

### `pj_readFiles.py`
