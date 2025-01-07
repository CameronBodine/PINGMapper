

import sys, os, zipfile, requests
sys.path.insert(0, 'src')

from funcs_common import *

gdal.SetConfigOption('GDAL_VRT_ENABLE_PYTHON', 'YES')

###########
# Functions
###########

#============================================

def build_vrt(vrt_path, imgsToMosaic, resampleAlg = "average"):
    # vrt_options = gdal.BuildVRTOptions(resampleAlg=resampleAlg)
    vrt_options = gdal.BuildVRTOptions(resampleAlg=resampleAlg, bandList={1})
    try:
        ds = gdal.BuildVRT(vrt_path, imgsToMosaic, options=vrt_options)
        ds.FlushCache()
        ds = None
    except Exception as e:
        print(f"Error building VRT file: {e}")


def build_gtiff(vrt):
    outTIF = vrt.replace('.vrt', '.tif')

    # Create GeoTiff from vrt
    ds = gdal.Open(vrt)

    kwargs = {
            'format': 'GTiff',
            'creationOptions': ['NUM_THREADS=ALL_CPUS', 'COMPRESS=LZW', 'TILED=YES']
            }

    # Set output pixel resolution
    # xRes = 0.25
    # yRes = 0.25

    # Create geotiff
    # gdal.Translate(outTIF, ds, xRes=xRes, yRes=yRes, **kwargs)
    gdal.Translate(outTIF, ds, **kwargs)

# Pixel functions adapted from:
# https://github.com/aerospaceresearch/DirectDemod/blob/Vladyslav_dev/directdemod/merger.py
def add_pixel_fn(filename: str, resample_name: str) -> None:
    """inserts pixel-function into vrt file named 'filename'
    Args:
        filename (:obj:`string`): name of file, into which the function will be inserted
        resample_name (:obj:`string`): name of resampling method
    """

    header = """  <VRTRasterBand dataType="int16" band="1" subClass="VRTDerivedRasterBand">"""
    contents = """
    <PixelFunctionType>{0}</PixelFunctionType>
    <PixelFunctionLanguage>Python</PixelFunctionLanguage>
    <PixelFunctionCode><![CDATA[{1}]]>
    </PixelFunctionCode>
    """

    lines = open(filename, 'r').readlines()
    lines[3] = header  # FIX ME: 3 is a hand constant
    lines.insert(4, contents.format(resample_name,
                                    get_resample(resample_name)))
    open(filename, 'w').write("".join(lines))


def get_resample(name: str) -> str:
    """retrieves code for resampling method
    Args:
        name (:obj:`string`): name of resampling method
    Returns:
        method :obj:`string`: code of resample method
    """

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
    np.clip(y,0,255, out=out_ar)
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
    np.clip(y,0,255, out=out_ar)
""",
        "max":
        """
import numpy as np
def max(in_ar, out_ar, xoff, yoff, xsize, ysize, raster_xsize,raster_ysize, buf_radius, gt, **kwargs):
    y = np.max(in_ar, axis=0)
    np.clip(y,0,255, out=out_ar)
""",
        "average":
        """
import numpy as np
def average(in_ar, out_ar, xoff, yoff, xsize, ysize, raster_xsize,raster_ysize, buf_radius, gt, **kwargs):
    div = np.zeros(in_ar[0].shape)
    for i in range(len(in_ar)):
        div += (in_ar[i] != 0)
    div[div == 0] = 1

    y = np.sum(in_ar, axis = 0, dtype = 'int16')
    y = y / div

    np.clip(y,-255,255, out = out_ar)
"""}

    if name not in methods:
        raise ValueError(
            "ERROR: Unrecognized resampling method (see documentation): '{}'.".
            format(name))

    return methods[name]


###########
###########


#============================================


# Main

# Get tiffs
dir = '/home/cbodine/PythonRepos/PINGMapper/procData/PINGMapper-Test-Small-DS/substrate/map_logit_raster'
files = glob(os.path.join(dir, '*.tif'))

# Build vrt
outVRT = os.path.join(dir, 'out.vrt')
build_vrt(outVRT, files)

# Add raster function to vrt
pix_fn = 'average'
add_pixel_fn(outVRT, pix_fn)

build_gtiff(outVRT)