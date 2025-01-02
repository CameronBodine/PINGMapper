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



'''
'''

#########
# Imports
import sys, os
sys.path.insert(0, 'src')

from funcs_common import *
from class_sonObj import sonObj
from class_rectObj import rectObj
from class_portstarObj import portstarObj

import time
import datetime
from glob import glob
from osgeo import gdal, ogr, osr
from rasterio.enums import Resampling
import rasterio
from rasterio.merge import merge

# Get processing script's dir so we can save it to file
scriptDir = os.getcwd()
# generate filename with timestring
copied_script_name = os.path.basename(__file__)+'_'+time.strftime("%Y-%m-%d_%H%M")+'.py'
script = os.path.join(scriptDir, os.path.basename(__file__))

threadCnt=cpu_count()


#============================================

#################
# User Parameters
#################

# Directory and Project Name
transectDir = r'./procData/test'
projName = 'test'


# Rectification Parameters
rect_wcp = False #Export rectified tiles with water column present
rect_wcr = False #Export rectified tiles with water column removed/slant range corrected


# Mosaic Parameters
mosaic_transect = 1 #Export rectified tile mosaic; 0==Don't Mosaic; 1==Do Mosaic - GTiff; 2==Do Mosaic - VRT
mosaic_all_transects = False # True: Mosaic transects into one; False: Don't Mosaic
resampleAlg = 'cubic' # mode, average, gauss, lanczos, bilinear, cubic, cubicspline, nearest
pix_fn = 'average'
overview = True
son_colorMap = 'Greys_r'

#################
#################


#============================================


###########
# Functions
###########

def smoothTrackline(sons):

    filter = int(sons[0].nchunk*0.1) #Filters trackline coordinates for smoothing
    filterRange = filter #int(nchunk*0.05) #Filters range extent coordinates for smoothing

    # As side scan beams use same transducer/gps coords, we will smooth one
    ## beam's trackline and use for both. Use the beam with the most sonar records.
    maxRec = 0 # Stores index of recording w/ most sonar records.
    maxLen = 0 # Stores length of ping
    for i, son in enumerate(sons):
        son._loadSonMeta() # Load ping metadata
        sonLen = len(son.sonMetaDF) # Number of sonar records
        if sonLen > maxLen:
            maxLen = sonLen
            maxRec = i

    # Now we will smooth using sonar beam w/ most records.
    son0 = sons[maxRec]
    sonDF = son0.sonMetaDF # Get ping metadata
    sDF = son._interpTrack(df=sonDF, dropDup=True, filt=filter, deg=3) # Smooth trackline and reinterpolate trackpoints along spline
    del sonDF

    ####################################
    ####################################
    # To remove gap between sonar tiles:
    # For chunk > 0, use coords from previous chunks second to last ping
    # and assign as current chunk's first ping coords
    chunks = pd.unique(sDF['chunk_id'])

    i = 1
    while i <= max(chunks):
        # Get second to last row of previous chunk
        lastRow = sDF[sDF['chunk_id'] == i-1].iloc[[-2]]
        # Get index of first row of current chunk
        curRow = sDF[sDF['chunk_id'] == i].iloc[[0]]
        curRow = curRow.index[0]
        # Update current chunks first row from lastRow
        sDF.at[curRow, "lons"] = lastRow["lons"]
        sDF.at[curRow, "lats"] = lastRow["lats"]
        sDF.at[curRow, "utm_es"] = lastRow["utm_es"]
        sDF.at[curRow, "utm_ns"] = lastRow["utm_ns"]
        sDF.at[curRow, "cog"] = lastRow["cog"]

        i+=1
    del lastRow, curRow, i

    son0.smthTrk = sDF # Store smoothed trackline coordinates in rectObj.

    # Update other channel with smoothed coordinates
    # Determine which rectObj we need to update
    for i, son in enumerate(sons):
        if i != maxRec:
            son1 = son # rectObj to update

    sDF = son0.smthTrk.copy() # Make copy of smoothed trackline coordinates
    # Update with correct record_num
    son1._loadSonMeta() # Load ping metadata
    df = son1.sonMetaDF
    sDF['chunk_id'] = df['chunk_id'] # Update chunk_id for smoothed coordinates
    sDF['record_num'] = df['record_num'] # Update record_num for smoothed coordinates
    son1.smthTrk = sDF # Store smoothed trackline coordinates in rectObj

    del sDF, df, son0, son1

    # Save smoothed trackline coordinates to file
    for son in sons:
        outCSV = os.path.join(son.metaDir, "Trackline_Smth_"+son.beamName+".csv")
        son.smthTrk.to_csv(outCSV, index=False, float_format='%.14f')
        son.smthTrkFile = outCSV
        son._cleanup()
    del son, outCSV

    return


def rangeCoordinates(sons):

    flip = False #Flip port/star
    filter = int(sons[0].nchunk*0.1) #Filters trackline coordinates for smoothing
    filterRange = filter #int(nchunk*0.05) #Filters range extent coordinates for smoothing

    for son in sons:
        son._getRangeCoords(flip, filterRange)


# Pixel functions from:
# https://github.com/aerospaceresearch/DirectDemod/blob/Vladyslav_dev/directdemod/merger.py
def add_pixel_fn(filename: str, resample_name: str) -> None:
    """inserts pixel-function into vrt file named 'filename'
    Args:
        filename (:obj:`string`): name of file, into which the function will be inserted
        resample_name (:obj:`string`): name of resampling method
    """

    header = """  <VRTRasterBand dataType="Byte" band="1" subClass="VRTDerivedRasterBand">"""
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

    y = np.sum(in_ar, axis = 0, dtype = 'uint16')
    y = y / div

    np.clip(y,0,255, out = out_ar)
"""}

    if name not in methods:
        raise ValueError(
            "ERROR: Unrecognized resampling method (see documentation): '{}'.".
            format(name))

    return methods[name]


###########
###########


#============================================

# Prepare directories
transectDir = os.path.normpath(transectDir)
projDir = os.path.join(transectDir, projName)

if not os.path.exists(projDir):
    os.mkdir(projDir)

# Get star and port pickle files for each transect
sonMetasPort = glob(os.path.join(transectDir, '**', '*ss_port_meta.meta'), recursive=True)
sonMetasStar = glob(os.path.join(transectDir, '**', '*ss_star_meta.meta'), recursive=True)

sonMetas = sorted(sonMetasPort+sonMetasStar) # Concatenate into single list
del sonMetasPort, sonMetasStar


#============================================

###########################################
# Create rectObj instance from pickle files
rectObjs = []
for m in sonMetas:
    son = rectObj(m) # Initialize object

    son.son_colorMap = son_colorMap

    rectObjs.append(son) # add to rectObjs


#============================================

############################
# Do trackline interpolation

# Group port and star rectObjs for each recording
portstar = []
for i in range(0, len(rectObjs), 2):
    portstar.append([rectObjs[i], rectObjs[i+1]])

# Smooth tracklines
print("\nSmoothing tracklines...")
Parallel(n_jobs= np.min([len(portstar), threadCnt]), verbose=10)(delayed(smoothTrackline)(sons) for sons in portstar)

# Store smthTrkFile in rectObj
for sons in portstar:
    for son in sons:
        son.smthTrkFile = os.path.join(son.metaDir, 'Trackline_Smth_'+son.beamName+'.csv')

# Calculate range extent coordinates
print("\nCalculating, smoothing, and interpolating range extent coordinates...")
Parallel(n_jobs= np.min([len(portstar), threadCnt]), verbose=10)(delayed(rangeCoordinates)(sons) for sons in portstar)

for sons in portstar:
    for son in sons:
        son._cleanup()
        son._pickleSon()


#============================================

##########################################
# Create and populate dict with egn values
egn_vals = defaultdict()

# Get egn keys from first sonObj
son = rectObjs[0]
temp = vars(son)
for item in temp:
    print(item)
    if 'egn_' in item:
        egn_vals[item] = []
del son

print(egn_vals)

# Populate egn_vals with each sonObj
for son in rectObjs:
    temp = vars(son)
    for item in temp:
        if 'egn_' in item:
            egn_vals[item].append(temp[item])

# for k, v in egn_vals.items():
#     print(k)


if egn_vals:
    #============================================

    ###########################
    # Calculate global egn vals


    #####################
    ### egn_bed_means ###
    egn_val = 'egn_bed_means'
    # Find longest vector
    lv = 0
    for v in egn_vals[egn_val]:
        if len(v) > lv:
            lv = len(v)

    # Create nan array
    egn_bed_means = np.empty((lv, len(egn_vals[egn_val])))
    egn_bed_means[:] = np.nan

    # Stack arrays
    for i, v in enumerate(egn_vals[egn_val]):
        egn_bed_means[:len(v), i] = v

    # Calculate mean
    egn_bed_means = np.nanmean(egn_bed_means, axis=1)

    # Update dictionary
    egn_vals[egn_val] = egn_bed_means
    del egn_bed_means
    # print('\n\n'+egn_val, egn_vals[egn_val])


    # ####################
    # ### egn_wc_means ###
    # egn_val = 'egn_wc_means'
    # # Find longest vector
    # lv = 0
    # for v in egn_vals[egn_val]:
    #     if len(v) > lv:
    #         lv = len(v)
    #
    # # Create nan array
    # egn_wc_means = np.empty((lv, len(egn_vals[egn_val])))
    # egn_wc_means[:] = np.nan
    #
    # # Stack arrays
    # for i, v in enumerate(egn_vals[egn_val]):
    #     egn_wc_means[:len(v), i] = v
    #
    # # Calculate mean
    # egn_wc_means = np.nanmean(egn_wc_means, axis=1)
    #
    # # Update dictionary
    # egn_vals[egn_val] = egn_wc_means
    # del egn_wc_means
    # # print('\n\n'+egn_val, egn_vals[egn_val])


    ###################
    ### egn_bed_min ###
    egn_val = 'egn_bed_min'

    # Calculate min
    egn_bed_min = np.nanmin(egn_vals[egn_val])

    # Update dictionary
    egn_vals[egn_val] = egn_bed_min
    del egn_bed_min
    # print('\n\n'+egn_val, egn_vals[egn_val])


    ###################
    ### egn_bed_max ###
    egn_val = 'egn_bed_max'

    # Calculate min
    egn_bed_max = np.nanmax(egn_vals[egn_val])

    # Update dictionary
    egn_vals[egn_val] = egn_bed_max
    del egn_bed_max
    # print('\n\n'+egn_val, egn_vals[egn_val])


    # ##################
    # ### egn_wc_min ###
    # egn_val = 'egn_wc_min'
    #
    # # Calculate min
    # egn_wc_min = np.nanmin(egn_vals[egn_val])
    #
    # # Update dictionary
    # egn_vals[egn_val] = egn_wc_min
    # del egn_wc_min
    # # print('\n\n'+egn_val, egn_vals[egn_val])
    #
    #
    # ##################
    # ### egn_wc_max ###
    # egn_val = 'egn_wc_max'
    #
    # # Calculate min
    # egn_wc_max = np.nanmax(egn_vals[egn_val])
    #
    # # Update dictionary
    # egn_vals[egn_val] = egn_wc_max
    # del egn_wc_max
    # # print('\n\n'+egn_val, egn_vals[egn_val])


    # ####################
    # ### egn_wcp_hist ###
    # egn_val = 'egn_wcp_hist'
    #
    # # Delete because we don't need it
    # del egn_vals[egn_val]


    # ####################
    # ### egn_wcp_hist ###
    # egn_val = 'egn_wcr_hist'
    #
    # # Delete because we don't need it
    # del egn_vals[egn_val]


    # #########################
    # ### egn_wcp_hist_pcnt ###
    # egn_val = 'egn_wcp_hist_pcnt'
    #
    # # Delete because we don't need it
    # del egn_vals[egn_val]


    #########################
    ### egn_wcr_hist_pcnt ###
    egn_val = 'egn_wcr_hist_pcnt'

    # Delete because we don't need it
    del egn_vals[egn_val]


    ###################
    ### egn_stretch ###
    egn_val = 'egn_stretch'

    # Delete because we don't need it
    del egn_vals[egn_val]


    ##########################
    ### egn_stretch_factor ###
    egn_val = 'egn_stretch_factor'

    # Delete because we don't need it
    del egn_vals[egn_val]


    # ###########################
    # ### egn_wcp_stretch_min ###
    # egn_val = 'egn_wcp_stretch_min'
    #
    # # Calculate min
    # egn_wcp_stretch_min = np.nanmin(egn_vals[egn_val])
    #
    # # Update dictionary
    # egn_vals[egn_val] = egn_wcp_stretch_min
    # del egn_wcp_stretch_min
    # # print('\n\n'+egn_val, egn_vals[egn_val])
    #
    #
    # ###########################
    # ### egn_wcp_stretch_max ###
    # egn_val = 'egn_wcp_stretch_max'
    #
    # # Calculate min
    # egn_wcp_stretch_max = np.nanmin(egn_vals[egn_val])
    #
    # # Update dictionary
    # egn_vals[egn_val] = egn_wcp_stretch_max
    # del egn_wcp_stretch_max
    # # print('\n\n'+egn_val, egn_vals[egn_val])


    ###########################
    ### egn_wcr_stretch_min ###
    egn_val = 'egn_wcr_stretch_min'

    # Calculate min
    egn_wcr_stretch_min = np.nanmin(egn_vals[egn_val])

    # Update dictionary
    egn_vals[egn_val] = egn_wcr_stretch_min
    del egn_wcr_stretch_min
    # print('\n\n'+egn_val, egn_vals[egn_val])


    ###########################
    ### egn_wcr_stretch_max ###
    egn_val = 'egn_wcr_stretch_max'

    # Calculate min
    egn_wcr_stretch_max = np.nanmin(egn_vals[egn_val])

    # Update dictionary
    egn_vals[egn_val] = egn_wcr_stretch_max
    del egn_wcr_stretch_max
    # print('\n\n'+egn_val, egn_vals[egn_val])


#============================================

#######################
# Rectify sonar imagery

if rect_wcp or rect_wcr:
    print("\nRectifying and exporting GeoTiffs:\n")
    for sons in portstar:
        print("Working on:", os.path.basename(sons[0].projDir))
        for son in sons:
            filter = int(son.nchunk*0.1) #Filters trackline coordinates for smoothing

            son.outDir = os.path.join(son.projDir, son.beamName)
            if not os.path.exists(son.outDir):
                os.mkdir(son.outDir)

            # # Overwrite local egn settings with global settings
            for k, v in egn_vals.items():
                son.k = v

            # Store rect_wcp and rect_wcr
            son.rect_wcp = rect_wcp
            son.rect_wcr = rect_wcr

            # Get chunk id's
            chunks = son._getChunkID()

            # Load sonMetaDF
            son._loadSonMeta()

            # Get colormap
            son._getSonColorMap(son_colorMap)

            print('\n\tExporting', len(chunks), 'GeoTiffs for', son.beamName)
            Parallel(n_jobs= np.min([len(chunks), threadCnt]), verbose=10)(delayed(son._rectSonParallel)(i, filter, wgs=False) for i in chunks)

            del son.sonMetaDF
            try:
                del son.smthTrk
            except:
                pass
            son._cleanup()
            # son._pickleSon()

#============================================

######################
# Mosaic each transect

if mosaic_transect > 0:
    print("\nMosaicing each transect...")
    for sons in portstar:
        start_time = time.time()
        psObj = portstarObj(sons)
        psObj._createMosaic(mosaic_transect, overview, threadCnt)
        print("Done!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        del psObj
        gc.collect()
        printUsage()



#============================================

##################################
# Create mosaic from all transects

if mosaic_all_transects:
    print("\nMosaicing all transects...")
    # Set output filename
    filename = os.path.join(projDir, projName)

    # Get files
    if rect_wcp:
        wcpToMosaic = sorted(glob(os.path.join(transectDir, '**', 'rect_wcp', '*.tif'), recursive=True))
    if rect_wcr:
        wcrToMosaic = sorted(glob(os.path.join(transectDir, '**', 'rect_wcr', '*.tif'), recursive=True))

    # Export mosaic as gtiff
    if rect_wcp:
        pass
    if rect_wcr:
        start_time = time.time()
        print('\n\tMosaicing sonograms with water column removed (wcr)...')
        outTIF = filename+'_rect_wcr.tif'
        outVRT = filename+'_rect_wcr.vrt'

        print('\tBuilding vrt...')
        vrt_options = gdal.BuildVRTOptions(resampleAlg=resampleAlg, srcNodata=0, VRTNodata=0)
        gdal.BuildVRT(outVRT, wcrToMosaic, options=vrt_options)

        # Create GeoTiff from vrt
        print('\tExporting geotiff...')
        # Add resample function
        add_pixel_fn(outVRT, pix_fn)

        gdal.SetConfigOption('GDAL_VRT_ENABLE_PYTHON', 'YES')
        ds = gdal.Open(outVRT)

        kwargs = {'format': 'GTiff',
                  'creationOptions': ['NUM_THREADS=ALL_CPUS', 'COMPRESS=LZW', 'TILED=YES']
                  }
        gdal.Translate(outTIF, ds, **kwargs)

        gdal.SetConfigOption('GDAL_VRT_ENABLE_PYTHON', None)

        ds = None

        # Generate overviews
        if overview:
            dest = gdal.Open(outTIF, 1)
            gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
            dest.BuildOverviews('nearest', [2 ** j for j in range(1,10)])
            dest = None

        print("Done!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        gc.collect()
        printUsage()












##############################
# Create mosaic from transects

# def max_function(*values):
#     return max(values)
#
# if mosaic > 0:
#     print("\nMosaicing GeoTiffs...")
#     # Set output filename
#     filename = os.path.join(projDir, projName)
#
#     # Set resampling
#     if resampleAlg == 'max':
#         resampleAlg = Resampling.max
#
#
#     # Get files
#     if rect_wcp:
#         wcpToMosaic = sorted(glob(os.path.join(transectDir, '**', 'rect_wcp', '*.tif'), recursive=True))
#     if rect_wcr:
#         wcrToMosaic = sorted(glob(os.path.join(transectDir, '**', 'rect_wcr', '*.tif'), recursive=True))
#
#     # Export mosaic as gtiff
#     if mosaic == 1:
#         if rect_wcp:
#             pass
#         if rect_wcr:
#             outTIF = filename+'_rect_wcr.tif'
#             outVRT = filename+'_rect_wcr.vrt'
#
#             # warp_options = gdal.WarpOptions(
#             #                                 format = 'GTiff',
#             #                                 dstNodata=0,
#             #                                 srcNodata=0,
#             #                                 creationOptions=['COMPRESS=LZW'],
#             #                                 callback=gdal.TermProgress,
#             #                                 transformerOptions=['SRC_METHOD=NO_GEOTRANSFORM'],
#             #                                 resampleAlg='bilinear',  # Set the resampling algorithm
#             #                                 warpOptions=['SKIP_NOSOURCE=YES'],  # Skip missing input datasets
#             #                                 warpMemoryLimit=gdal.GetCacheMax() // 2,  # Set the memory limit
#             #                                 multithread=True,  # Enable multi-threading
#             #                                 dstAlpha=True
#             #                                 )
#             # gdal.Warp(filename, wcrToMosaic, options=warp_options)
#
#             # vrt_options = gdal.BuildVRTOptions(resampleAlg=resampleAlg, srcNodata=0, VRTNodata=0, addAlpha=True)
#             # gdal.BuildVRT(outVRT, wcrToMosaic, options=vrt_options, customSourceToDest=max_function)
#             #
#             # ds = gdal.Open(outVRT)
#             #
#             # kwargs = {'format': 'GTiff',
#             #           'creationOptions': ['NUM_THREADS=ALL_CPUS', 'COMPRESS=LZW']
#             #           }
#             # gdal.Translate(outTIF, ds, **kwargs)
#             #
#             #
#             # output_ds = gdal.Open(outTIF, gdal.GA_Update)
#             # mask_band = output_ds.GetMaskBand()
#             #
#             # for img in wcrToMosaic:
#             #     input_ds = gdal.open(img)
#             #     input_band = input_ds.GetRasterBand(1)
#             #     gdal.ComputeMaskBand(max_function, input_band, mask_band)
#             #
#             # output_ds = None
#             # mask_band = None
#             # input_ds = None
#             # input_band = None
#
#             datasets = []
#             for d in wcrToMosaic:
#                 src = rasterio.open(d)
#                 datasets.append(src)
#
#             mosaic, out_trans = merge(datasets)
#
#             mosaic_data = np.ma.array(mosaic, mask=np.isnan(mosaic))
#             average = np.ma.average(mosaic_data, axis=0)
#
#             mosaic_meta = datasets[0].meta.copy()
#             mosaic_meta.update({'driver': 'GTiff',
#                                 'height': average.shape[0],
#                                 'width': average.shape[1],
#                                 'transform': out_trans})
#
#             with rasterio.open(outTIF, 'w', **mosaic_meta) as dst:
#                 dst.write(average, 1)
#
#
#
#     # Export mosaic as vrt
#     elif mosaic == 2:
#         if rect_wcp:
#             pass
#         if rect_wcr:
#             filename = filename+'_rect_wcr.vrt'
#
#             vrt_options = gdal.BuildVRTOptions(resampleAlg=resampleAlg, srcNodata=0, VRTNodata=0)
#             gdal.BuildVRT(filename, wcrToMosaic, options=vrt_options, customSourceToDest=max_function)
#
#             # Generate overviews
#             if overview:
#                 print('\tBuilding overviews...')
#                 dest = gdal.Open(filename)
#                 gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
#                 dest.BuildOverviews('nearest', [2 ** j for j in range(1,10)])
#
# gc.collect()




# import gdal
#
# # Define a custom function that takes the maximum value of overlapping pixels
# def max_function(*args):
#     return max(args)
#
# # Set the input raster filenames
# input_rasters = ['raster1.tif', 'raster2.tif', 'raster3.tif']
#
# # Set the output VRT filename
# output_vrt = 'output.vrt'
#
# # Create the VRT using the BuildVRT function and the custom function
# vrt = gdal.BuildVRT(output_vrt, input_rasters, srcNodata=0, VRTNodata=0, addAlpha=True, options=['-r', 'average', '-srcnodata', '0', '-vrtnodata', '0'], callback=gdal.TermProgress_nocb, separate=True, resampleAlg=gdal.GRA_NearestNeighbour, transformerOptions=None, warpOptions=None, warpMemoryLimit=None, creationOptions=None, outputBounds=None, outputSRS=None, xRes=None, yRes=None, targetAlignedPixels=None, width=None, height=None, format=None, outputType=None, bandList=None, metadataOptions=None, subClass=None, siblingFiles=None, openOptions=None, colorTableName=None, callback_data=None, customSourceToDest=None, customDestToSrc=None, options=None, **kwargs)
#
# # Save the VRT to disk
# vrt.FlushCache()
