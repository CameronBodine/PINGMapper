# Part of PING-Mapper software
#
# Co-Developed by Cameron S. Bodine and Dr. Daniel Buscombe
#
# Inspired by PyHum: https://github.com/dbuscombe-usgs/PyHum
#
# MIT License
#
# Copyright (c) 2022-23 Cameron S. Bodine
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os, sys, struct, gc
from joblib import Parallel, delayed, cpu_count
from glob import glob
import requests, zipfile

################################################################################
import warnings
warnings.simplefilter("ignore")
################################################################################

import numpy as np
from array import array as arr

from osgeo import gdal
import pyproj
import rasterio
from rasterio.enums import Resampling
from numpy.lib.stride_tricks import as_strided as ast

import pandas as pd
import math

from collections import defaultdict
from copy import deepcopy
import pickle
import shutil

import time
import datetime

# from skimage.filters import median
# from skimage.morphology import square
from skimage.io import imsave, imread
from skimage.measure import label, regionprops
from skimage.segmentation import watershed
from skimage.transform import resize
from skimage.filters import threshold_otsu, gaussian
from skimage.morphology import remove_small_holes, remove_small_objects

import psutil
import json

import logging

# from funcs_pyhum_correct import doPyhumCorrections


# =========================================================
def rescale( dat,
             mn,
             mx):
    '''
    rescales an input dat between mn and mx
    '''
    m = min(dat.flatten())
    M = max(dat.flatten())
    return (mx-mn)*(dat-m)/(M-m)+mn

# =========================================================
def convert_wgs_to_utm(lon, lat):
    """
    This function estimates UTM zone from geographic coordinates
    see https://stackoverflow.com/questions/40132542/get-a-cartesian-projection-accurate-around-a-lat-lng-pair
    """
    utm_band = str((np.floor((lon + 180) / 6 ) % 60) + 1)
    if len(utm_band) == 1:
        utm_band = '0'+utm_band
    if lat >= 0:
        epsg_code = '326' + utm_band
    else:
        epsg_code = '327' + utm_band
    return epsg_code

# =========================================================
def printUsage():
    '''
    Show computing resources used
    '''
    cpuPercent = round(psutil.cpu_percent(0.5), 1)
    ramPercent = round(psutil.virtual_memory()[2], 1)
    ramUsed = round(psutil.virtual_memory()[3]/1000000000, 1)

    print('\n\nCurrent CPU/RAM Usage:')
    print('________________________')
    print('{:<5s} | {:<5s} | {:<5s}'.format('CPU %', 'RAM %', 'RAM [GB]'))
    print('________________________')

    print('{:<5s} | {:<5s} | {:<5s}'.format(str(cpuPercent), str(ramPercent), str(ramUsed)))
    print('________________________\n\n')


    return

# =========================================================
def printProjectMode(p):
    if p == 0:
        print("\nPROJECT MODE {}: Creating new project.".format(str(p)))
    elif p == 1:
        print("\nPROJECT MODE {}: Deleting existing project (if it exists) and creating new project.".format(str(p)))
    elif p == 2:
        print("\nPROJECT MODE {}: Updating project (Any existing dataset flagged for export will be overwritten).".format(str(p)))
    
    else:
        print("\nABORTING: Invalid Project Mode!")
        print("Specify a valid project mode:")
        print("\tproject_mode = 0: Create new project (exits if project already exists).")
        print("\tproject_mode = 1: Deleting existing project (if it exists).")
        # print("\tproject_mode = 1: Update existing project (Any existing dataset flagged for export will be overwritten).")
        # print("\tproject_mode = 2: Mayhem mode - throw caution to the wind, delete existing project (if it exists) and carry on.\n\n")
        sys.exit()

# =========================================================
def projectMode_1_inval():
    print("\nABORTING: Project Already Exists!")
    print("\nEither select a different project name, or select from one of the following:")
    print("\tproject_mode = 1: Deleting existing project (if it exists).")
    # print("\tproject_mode = 1: Update existing project (Any existing dataset flagged for export will be overwritten).")
    # print("\tproject_mode = 2: Mayhem mode - throw caution to the wind, delete existing project (if it exists) and carry on.\n\n")
    sys.exit()

# =========================================================
def projectMode_2_inval():
    print("\nABORTING: Project Does Not Exist!")
    print("Set project mode to:")
    print("\tproject_mode = 0: Create new project.\n\n")
    sys.exit()

# =========================================================
def projectMode_2a_inval():
    print("\nABORTING: No Son Meta objects exist, unable to update project.")
    print("Specify a new project name (or delete existing project) and set project mode to:")
    print("\tproject_mode = 0: Create new project.\n\n")
    sys.exit()

# =========================================================
def error_noSubNpz():
    print("\nABORTING: No existing substrate npz files.")
    print("\tSet: pred_sub = 1\n\n")
    sys.exit()

# =========================================================
def error_noSubMap_poly():
    print("\nABORTING: No existing substrate map rasters.")
    print("\tUnable to export substrate map to shapefile.")
    print("\tSet: map_sub = True\n\n")
    sys.exit()

# =========================================================
def error_noSubMap_mosaic():
    print("\nABORTING: No existing substrate map rasters.")
    print("\tUnable to mosaic substrate maps.")
    print("\tSet: map_sub = True")
    print("\tOR")
    print("\tSet: map_mosaic = 0\n\n")
    sys.exit()

# =========================================================
class Logger(object):
    def __init__(self, logfilename):
        self.terminal = sys.stdout
        self.log = open(logfilename, "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        pass

# =========================================================
def downloadSegmentationModelsv1_0(modelDir):

    # Create directories
    if not os.path.exists(modelDir):
        os.makedirs(modelDir)

    # Download
    url = 'https://zenodo.org/records/10093642/files/PINGMapperv2.0_SegmentationModelsv1.0.zip?download=1'
    print('\n\nDownloading segmentation models (v1.0):\nhttps://zenodo.org/records/10092289/files/PINGMapperv2.0_SegmentationModelsv1.0.zip?download=1')

    filename = modelDir+'.zip'
    r = requests.get(url, allow_redirects=True)
    open(filename, 'wb').write(r.content)

    with zipfile.ZipFile(filename, 'r') as z_fp:
        z_fp.extractall(modelDir)
    os.remove(filename)

    print('Model download success!')
    
    return


# =========================================================
def saveDefaultParams(values):
    
    params = {
        'project_mode':int(values[3]),
        'tempC':float(values[5]),
        'nchunk':int(values[6]),
        'cropRange':float(values[7]),
        'exportUnknown':values[8],
        'fixNoDat':values[9],
        'threadCnt':int(values[10]),
        'x_offset':float(values[12]),
        'y_offset':float(values[14]),
        'egn':values[16],
        'egn_stretch':values[17],
        'egn_stretch_factor':float(values[19]),
        'wcp':values[21],
        'wcr':values[22],
        'tileFile':values[23],
        'lbl_set':values[25],
        'spdCor':float(values[26]),
        'maxCrop':values[28],
        'remShadow':values[30],
        'detectDep':values[31],
        'smthDep':values[33],
        'adjDep':float(values[35]),
        'pltBedPick':values[37],
        'rect_wcp':values[39],
        'rect_wcr':values[40],
        'son_colorMap':values[41],
        'pred_sub':values[43],
        'pltSubClass':values[45],
        'map_sub':values[46],
        'export_poly':values[48],
        'map_class_method':values[50],
        'pix_res':float(values[52]),
        'mosaic_nchunk':int(values[54]),
        'mosaic':values[55],
        'map_mosaic':values[57],
        'banklines':values[59]
    }

    json_object = json.dumps(params, indent=4)

    with open("./user_params.json", "w") as f:
        f.write(json_object)

    
# =========================================================
def unableToProcessError(logfilename):
    
    errorfilename = logfilename.replace('log_', 'error_')

    error_logger = logging.getLogger('error_logger')
    myhandler = logging.FileHandler(errorfilename)
    myhandler.setLevel(logging.DEBUG)
    error_logger.addHandler(myhandler)
    error_logger.exception("Error Thrown:")

    print("\n\n!!!!!!!!!!!!!!!!!\nAn Error Occured.\n\nPlease consult the logfile at:\n", errorfilename)
    
    handlers = error_logger.handlers[:]
    for handler in handlers:
        error_logger.removeHandler(handler)
        handler.close()

