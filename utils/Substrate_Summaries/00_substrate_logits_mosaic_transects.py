# Part of PING-Mapper software
#
# Co-Developed by Cameron S. Bodine and Dr. Daniel Buscombe
#
# Inspired by PyHum: https://github.com/dbuscombe-usgs/PyHum
#
# MIT License
#
# Copyright (c) 2022-24 Cameron S. Bodine
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

'''
WARNING: This is terribly inefficient on large areas.
Ubuntu: gdal_calc doesn't run

This script will mosaic substrate prediction maps from overlapping transects:
    1) Create a VRT for a rivers substrate predictions maps (logits)
    2) Apply a pixel function (average, min, max, etc.) to handle overlapping pixels
    3) Export to GeoTiff (NBAND raster) of model predictions for each class
    4) Create VRT to argmax the model predictions to get a classification
    5) Export classification to GeoTiff
'''

#============================================

#########
# Imports
#########

import sys, os
from osgeo import gdal
sys.path.insert(0, 'src')

from funcs_common import *

import time
from glob import glob
import pandas as pd
import numpy as np

import tensorflow as tf


# Get processing script's dir so we can save it to file
scriptDir = os.getcwd()
# generate filename with timestring
copied_script_name = os.path.basename(__file__)+'_'+time.strftime("%Y-%m-%d_%H%M")+'.py'
script = os.path.join(scriptDir, os.path.basename(__file__))

# Enable python functions in VRT
gdal.SetConfigOption('GDAL_VRT_ENABLE_PYTHON', 'YES')


#============================================

#################
# User Parameters
#################

# Directory and Project Name
transectDir = r'/mnt/md0/SynologyDrive/GulfSturgeonProject/SSS_Data_Processed/EGN_Test_Substrate_Mosaic'
projName = 'Test_Transect_Mosaic'
pix_fn = 'average'

# scriptFile = r"C:\Users\csb67\AppData\Local\miniconda3\envs\ping\Scripts\gdal_calc.py"
scriptFile = "/home/cbodine/miniconda3/envs/ping/bin/gdal_calc.py"



#################
#################

#============================================

###########
# Functions
###########

def get_river_code(row):
    project = row.proj
    river_code = project.split('_')[0]
    
    if river_code == 'PRL':
        river = 'Pearl'
    elif river_code == 'BCH':
        river = 'Bogue Chitto'
    elif river_code == 'CHI':
        river = 'Chickasawhay'
    elif river_code == 'CHU':
        river = 'Chunky'
    elif river_code == 'LEA':
        river = 'Leaf'
    elif river_code == 'BOU':
        river = 'Bouie'
    elif river_code == 'PAS':
        river = 'Pascagoula'
    # For testing
    elif river_code == 'RIV':
        river = 'River'
    else:
        print('No River Code:', river_code)
        sys.exit()

    return river, river_code


def getTiffAttributes(tif):

    # Open tif
    t = gdal.Open(tif)

    # Get Attributes
    bandCount = t.RasterCount

    band = t.GetRasterBand(1)
    bandDtype = gdal.GetDataTypeName(band.DataType)

    return bandCount, bandDtype


def build_vrt(vrt_path, imgsToMosaic, resampleAlg = "nearest"):
    vrt_options = gdal.BuildVRTOptions(resampleAlg=resampleAlg)
    try:
        ds = gdal.BuildVRT(vrt_path, imgsToMosaic, options=vrt_options)
        ds.FlushCache()
        ds = None
    except Exception as e:
        print(f"Error building VRT file: {e}")


def findHeadIDX(f, d, b):

    lines = open(f, 'r').readlines()

    # Format header to search for (needed '\n' newline character)
    header = """  <VRTRasterBand dataType="{0}" band="{1}">\n""".format(d, b)
    idx = lines.index(header)

    return idx


def getRange(bandDtype):

    if bandDtype == 'Int8':
        i = np.iinfo(np.int8)
    elif bandDtype == 'Int16':
        i = np.iinfo(np.int16)
    elif bandDtype == 'Int32':
        i = np.iinfo(np.int32)
    elif bandDtype == 'Int64':
        i = np.iinfo(np.int64)

    elif bandDtype == 'UInt8':
        i = np.iinfo(np.uint8)
    elif bandDtype == 'UInt16':
        i = np.iinfo(np.uint16)
    elif bandDtype == 'UInt32':
        i = np.iinfo(np.uint32)
    elif bandDtype == 'UInt64':
        i = np.iinfo(np.uint64)

    elif bandDtype == 'Float32':
        i = np.iinfo(np.float32)
    elif bandDtype == 'Float64':
        i = np.iinfo(np.float64)

    min, max, bdtype = i.min, i.max, i.dtype

    return min, max, bdtype


# Pixel functions adapted from:
# https://github.com/aerospaceresearch/DirectDemod/blob/Vladyslav_dev/directdemod/merger.py
def add_pixel_fn(filename: str, resample_name: str, band: str, bandCount: int, bandDtype: str) -> None:
    """inserts pixel-function into vrt file named 'filename'
    Args:
        filename (:obj:`string`): name of file, into which the function will be inserted
        resample_name (:obj:`string`): name of resampling method
    """

    # Find index of appropriate header
    headerIDX = findHeadIDX(filename, bandDtype, band)    

    # header = """  <VRTRasterBand dataType="int16" band="1" subClass="VRTDerivedRasterBand">"""
    header = """  <VRTRasterBand dataType="{0}" band="{1}" subClass="VRTDerivedRasterBand">"""
    header = header.format(bandDtype, band)

    contents = """
    <PixelFunctionType>{0}</PixelFunctionType>
    <PixelFunctionLanguage>Python</PixelFunctionLanguage>
    <PixelFunctionCode><![CDATA[{1}]]>
    </PixelFunctionCode>
    """

    # Format contents
    contents = contents.format(resample_name, get_resample(resample_name, bandDtype))

    # Add contents
    lines = open(filename, 'r').readlines()
    lines[headerIDX] = header # Replace header at appropriate location
    # Insert
    lines.insert(headerIDX+1, contents)
    open(filename, 'w').write("".join(lines))

    # lines = open(filename, 'r').readlines()
    # lines[3] = header  # FIX ME: 3 is a hand constant
    # lines.insert(4, contents.format(resample_name,
    #                                 get_resample(resample_name, bandDtype)))
    # open(filename, 'w').write("".join(lines))


def get_resample(name: str, bandDtype: str) -> None:
    """retrieves code for resampling method
    Args:
        name (:obj:`string`): name of resampling method
    Returns:
        method :obj:`string`: code of resample method
    """

    # Get valid clip range
    min, max, bDtype = getRange(bandDtype)

    methods = {
        "first":
        """
import numpy as np
def first(in_ar, out_ar, xoff, yoff, xsize, ysize, raster_xsize,raster_ysize, buf_radius, gt, **kwargs):
    y = np.ones(in_ar[0].shape)
    for i in reversed(range(len(in_ar))):
        mask = in_ar[i] == 0
        y *= mask
        y += in_ar[i]
    np.clip(y,{0},{1}, out=out_ar)
""",
        "last":
        """
import numpy as np
def last(in_ar, out_ar, xoff, yoff, xsize, ysize, raster_xsize,raster_ysize, buf_radius, gt, **kwargs):
    y = np.ones(in_ar[0].shape)
    for i in range(len(in_ar)):
        mask = in_ar[i] == 0
        y *= mask
        y += in_ar[i]
    np.clip(y,{0}, {1}, out=out_ar)
""",
        "max":
        """
import numpy as np
def max(in_ar, out_ar, xoff, yoff, xsize, ysize, raster_xsize,raster_ysize, buf_radius, gt, **kwargs):
    y = np.max(in_ar, axis=0)
    np.clip(y,{0}, {1}, out=out_ar)
""",
        "average":
        """
import numpy as np
def average(in_ar, out_ar, xoff, yoff, xsize, ysize, raster_xsize,raster_ysize, buf_radius, gt, **kwargs):
    div = np.zeros(in_ar[0].shape)
    for i in range(len(in_ar)):
        div += (in_ar[i] != 0)
    div[div == 0] = 1

    y = np.sum(in_ar, axis = 0, dtype = '{2}')
    y = (y / div).astype(np.{2})

    np.clip(y,{0}, {1}, out = out_ar)
""",
        "sum":
        """
import numpy as np
def sum(in_ar, out_ar, xoff, yoff, xsize, ysize, raster_xsize,raster_ysize, buf_radius, gt, **kwargs):
    y = np.sum(in_ar, axis=0)
    np.clip(y, {0}, {1}, out=out_ar)
""",
        "classify":
        """
import numpy as np
def classify(in_ar, out_ar, xoff, yoff, xsize, ysize, raster_xsize,raster_ysize, buf_radius, gt, **kwargs):
    y = np.argmax(in_ar, axis=0)
    np.clip(y, {0}, {1}, out=out_ar)
"""}

    if name not in methods:
        raise ValueError(
            "ERROR: Unrecognized resampling method (see documentation): '{}'.".
            format(name))

    return methods[name].format(min, max, bDtype)

def build_gtiff(vrt, outTIF):

    # Create GeoTiff from vrt
    ds = gdal.Open(vrt)

    kwargs = {
            'format': 'GTiff',
            'creationOptions': ['NUM_THREADS=ALL_CPUS', 'COMPRESS=LZW', 'TILED=YES']
            }

    # Set output pixel resolution
    xRes = 0.25
    yRes = 0.25

    # Create geotiff
    gdal.Translate(outTIF, ds, xRes=xRes, yRes=yRes, **kwargs)

###########
###########


#============================================

######
# Main
######

# Prepare directories
transectDir = os.path.abspath(os.path.normpath(transectDir))
projDir = os.path.join(transectDir, projName)

if not os.path.exists(projDir):
    os.mkdir(projDir)

# Get tiffs
tif_dir_pattern = os.path.join(transectDir, '**', 'map_logit_raster', '*.tif')
tif_files = glob(tif_dir_pattern, recursive=True)

# Remove 'Summary' from dirs
tif_files = [f for f in tif_files if projDir not in f]

# Prepare project df
# Store dirs in dataframe
tifDF = pd.DataFrame()
tifDF['tif'] = tif_files

# Add projName to df
tifDF['proj'] = tifDF['tif'].apply(lambda d: os.path.basename(d))

# Add river and code
tifDF[['river', 'river_code']] = tifDF.apply(lambda row: get_river_code(row), axis=1).values.tolist()

# Get RKM
tifDF['up_rkm'] = tifDF['proj'].apply(lambda d: d.split('_')[1]).astype(int)
tifDF['dn_rkm'] = tifDF['proj'].apply(lambda d: d.split('_')[2]).astype(int)

# Sort by river code and up rkm
projDF = tifDF.sort_values(['river_code', 'up_rkm'], ascending=False)

# Create a map based on river
for name, group in tifDF.groupby('river_code'):

    print('\n\nWorking On:', name)

    # Get tif files into a list
    files = group.tif.values.tolist()

    # Get relavent attributes from tif
    bandCount, bandDtype = getTiffAttributes(files[0])

    # Build vrt
    print('Building VRT')
    vrtName = '_'.join([name, 'substrate', 'logit', 'rast', 'transect', 'mosaic']) + '.vrt'
    outVRT_mosaic = os.path.join(projDir, vrtName)
    build_vrt(outVRT_mosaic, files)

    # Iterate each band and add raster function to vrt
    for b in range(1, bandCount+1):
        add_pixel_fn(outVRT_mosaic, pix_fn, b, bandCount, bandDtype)
    
    # Create gtiff mosaic from vrt
    print('Mosaic Logits')
    outTIF_mosaic = outVRT_mosaic.replace('.vrt', '.tif')
    build_gtiff(outVRT_mosaic, outTIF_mosaic)

    # Do classification
    print('Classifying Substrate')
    # https://courses.spatialthoughts.com/gdal-tools.html#calculate-pixel-wise-statistics-over-multiple-rasters
    # https://github.com/Doodleverse/dash_doodler/blob/41ce96b8c341c591bfa1c0d467dc6290b2e31963/website/blog/2020-08-01-blog-post.md
    # https://gis.stackexchange.com/questions/417936/gdal-calc-in-python-without-gdal-path
    # gdal_calc_str = 'python {4} \
    #                 -A {0} --A_band=1 \
    #                 -B {0} --B_band=2 \
    #                 -C {0} --C_band=3 \
    #                 -D {0} --D_band=4 \
    #                 -E {0} --E_band=5 \
    #                 -F {0} --F_band=6 \
    #                 -G {0} --G_band=7 \
    #                 -H {0} --H_band=8 \
    #                 --outfile={1} --calc={2} --type={3} --overwrite'

    # expr = '"numpy.argmax((numpy.dstack((A,B,C,D,E,F,G,H))/100), axis=2)"'
    gdal_calc_str = 'python {4} \
                    -B {0} --B_band=2 \
                    -C {0} --C_band=3 \
                    -D {0} --D_band=4 \
                    -E {0} --E_band=5 \
                    -F {0} --F_band=6 \
                    -G {0} --G_band=7 \
                    -H {0} --H_band=8 \
                    --outfile={1} --calc={2} --type={3} --overwrite'

    expr = '"numpy.argmax((numpy.dstack((B,C,D,E,F,G,H))/100), axis=2)"'
    f = '"Int8"'
    outTIF_class = outTIF_mosaic.replace('.tif', '_class.tif')

    calc_process = gdal_calc_str.format(outTIF_mosaic, outTIF_class, expr, f, scriptFile)

    print(calc_process)

    os.system(calc_process)


    

    

    