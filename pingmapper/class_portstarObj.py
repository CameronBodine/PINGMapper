# Part of PING-Mapper software
#
# GitHub: https://github.com/CameronBodine/PINGMapper
# Website: https://cameronbodine.github.io/PINGMapper/ 
#
# Co-Developed by Cameron S. Bodine and Dr. Daniel Buscombe
#
# Inspired by PyHum: https://github.com/dbuscombe-usgs/PyHum
#
# MIT License
#
# Copyright (c) 2025 Cameron S. Bodine
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


import os, sys

# Add 'pingmapper' to the path, may not need after pypi package...
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.append(PACKAGE_DIR)

from pingmapper.funcs_common import *
from pingmapper.funcs_model import *

# import gdal
from osgeo import gdal, ogr, osr
from scipy.signal import savgol_filter
from scipy import stats
from skimage.transform import PiecewiseAffineTransform, warp
from rasterio.transform import from_origin
# from rasterio.enums import Resampling
from PIL import ImageColor

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

import inspect

from doodleverse_utils.imports import *
from doodleverse_utils.model_imports import *
from doodleverse_utils.prediction_imports import *

import geopandas as gpd

class portstarObj(object):
    '''
    Python class to store port and starboard objects (sonObj() or rectObj()) in
    a single object to facilitate functions which operate on both objects at the
    same time.

    ----------------
    Class Attributes
    ----------------
    * Alphabetical order *
    self.bedpickModel : tf model
        DESCRIPTION - Stores compiled model used for automated depth detection.

    self.configfile : str
        DESCRIPTION - Stores path to depth detection model configuration file.

    self.mergeSon : Numpy array
        DESCRIPTION - Stores a chunk's portside and starboard sonar intensities,
                      flipped and rotated in single array.

    self.port : Object
        DESCRIPTION - Stores either sonObj() or rectObj() instance for portside.

    self.portDepDetect : dictionary
        DESCRIPTION - Dictionary to store automated depth estimates for portside.
                      chunk : np.array(depth estimate)

    self.star : Object
        DESCRIPTION - Stores either sonObj() or rectObj() instance for starboard.

    self.starDepDetect : dictionary
        DESCRIPTION - Dictionary to store automated depth estimates for starboard.
                      chunk : np.array(depth estimate)

    self.weights : str
        DESCRIPTION - Store path to depth detection model weights file.


    '''
    #=======================================================================
    def __init__(self, objs):
        '''
        Initialize a portstarObj instance.

        ----------
        Parameters
        ----------
        objs : list
            DESCRIPTION - Portside and starboard sonObj or rectObj instances stored
                          in a list.
            EXAMPLE -     objs = [portSonObj, starSonObj]

        -------
        Returns
        -------
        portstarObj instance.
        '''
        for obj in objs:
            if obj.beamName == 'ss_port':
                self.port = obj
            elif obj.beamName == 'ss_star':
                self.star = obj
            else:
                print("Object is unknown...")
        return

    ############################################################################
    # Get Port/Star Sonar Intensity and Merge                                  #
    ############################################################################

    #=======================================================================
    def _getPortStarScanChunk(self,
                              i):
        '''
        Reads ping returns for each side scan channel into arrays. Arrays are
        rotated and flipped as necessary to concatenate side scan arrays into a
        merged array.

        ----------
        Parameters
        ----------
        i : int
            DESCRIPTION - The chunk index to load into memory.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        self.__init__()

        -------
        Returns
        -------
        self.mergeSon, a Numpy array with concatenated portside and starboard
        ping returns.

        --------------------
        Next Processing Step
        --------------------
        None
        '''
        # Load sonar intensity into memory
        try:
            self.port._getScanChunkSingle(i)
            portsonDat = True
        except:
            portsonDat = False

        try:
            self.star._getScanChunkSingle(i)
            starsonDat = True
        except:
            starsonDat = False

        if not portsonDat:
            self.port.sonDat = np.zeros(self.star.sonDat.shape)

        if not starsonDat:
            self.star.sonDat = np.zeros(self.port.sonDat.shape)

        del portsonDat, starsonDat


        # Rotate and merge arrays into one
        portSon = np.rot90(self.port.sonDat, k=1, axes=(1,0))
        portSon = np.flipud(portSon)
        starSon = np.rot90(self.star.sonDat, k=1, axes=(0,1))

        # Ensure portSon/starSon same length.
        if (portSon.shape[0] != starSon.shape[0]):
            pL = portSon.shape[0]
            sL = starSon.shape[0]
            # Add rows to shortest array from longest array
            if (pL > sL):
                slice = np.fliplr(portSon[(sL-pL):,:])
                starSon = np.append(starSon, slice, axis=0)

            else:
                slice = np.fliplr(starSon[(pL-sL):, :])
                portSon = np.append(portSon, slice, axis=0)


        # Concatenate arrays column-wise
        mergeSon = np.concatenate((portSon, starSon), axis = 1)
        del self.port.sonDat, self.star.sonDat

        self.mergeSon = mergeSon
        return #self

    ############################################################################
    # Mosaic                                                                   #
    ############################################################################

    #=======================================================================
    def _createMosaic(self,
                      mosaic=1,
                      overview=True,
                      threadCnt=cpu_count(),
                      son=True,
                      maxChunk = 50):
        '''
        Main function to mosaic exported rectified sonograms into a mosaic. If
        overview=True, overviews of the mosaic will be built, enhancing view
        performance in a GIS. Generating overviews will increase mosaic file size.

        ----------
        Parameters
        ----------
        mosaic : int : [Default=1]
            DESCRIPTION - Type of mosaic to create.
                          1 = GeoTiff;
                          2 = VRT (Virtual raster table), an xml that references
                            each individual rectified sonogram chunk and mosaics
                            on the fly.
        overview : bool : [Default=True]
            DESCRIPTION - Flag indicating if mosaic overviews should be generated.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        rectObj._rectSonParallel()

        -------
        Returns
        -------
        Exports mosaics of rectified sonograms.

        --------------------
        Next Processing Step
        --------------------
        Calls self._mosaicGtiff() or self._mosaicVRT() to generate mosaics.
        '''
        # maxChunk = 50 # Max chunks per mosaic. Limits each mosaic file size.
        self.imgsToMosaic = [] # List to store files to mosaic.

        if son:
            if self.port.rect_wcp: # Moscaic wcp sonograms if previousl exported
                # Locate port files
                portPath = os.path.join(self.port.outDir, 'rect_wcp')
                port = sorted(glob(os.path.join(portPath, '*.tif')))

                # Locate starboard files
                starPath = os.path.join(self.star.outDir, 'rect_wcp')
                star = sorted(glob(os.path.join(starPath, '*.tif')))

                # Make multiple mosaics if number of input sonograms is greater than maxChunk
                if (len(port) > maxChunk) and (maxChunk != 0):
                    port = [port[i:i+maxChunk] for i in range(0, len(port), maxChunk)]
                    star = [star[i:i+maxChunk] for i in range(0, len(star), maxChunk)]
                    wcpToMosaic = [list(itertools.chain(*i)) for i in zip(port, star)]
                else:
                    wcpToMosaic = [port + star]

            if self.port.rect_wcr: # Moscaic wcp sonograms if previousl exported
                # Locate port files
                portPath = os.path.join(self.port.outDir, 'rect_wcr')
                port = sorted(glob(os.path.join(portPath, '*.tif')))

                # Locate starboard files
                starPath = os.path.join(self.star.outDir, 'rect_wcr')
                star = sorted(glob(os.path.join(starPath, '*.tif')))

                # Make multiple mosaics if number of input sonograms is greater than maxChunk
                if (len(port) > maxChunk) and (maxChunk != 0):
                    port = [port[i:i+maxChunk] for i in range(0, len(port), maxChunk)]
                    star = [star[i:i+maxChunk] for i in range(0, len(star), maxChunk)]
                    srcToMosaic = [list(itertools.chain(*i)) for i in zip(port, star)]
                else:
                    srcToMosaic = [port + star]

        else:
            if self.port.map_sub:
                # Locate map files
                mapPath = os.path.join(self.port.substrateDir, 'map_substrate_raster')
                map = sorted(glob(os.path.join(mapPath, '*.tif')))

                # Make multiple mosaics if number of input sonograms is greater than maxChunk
                if (len(map) > maxChunk) and (maxChunk != 0):
                    subToMosaic = [map[i:i+maxChunk] for i in range(0, len(map), maxChunk)]
                else:
                    subToMosaic = [map]

            if self.port.map_predict:
                # Locate map files
                if self.port.map_predict == 1:
                    mapPath = os.path.join(self.port.substrateDir, 'map_probability_raster')
                elif self.port.map_predict == 2:
                    mapPath = os.path.join(self.port.substrateDir, 'map_logit_raster')
                map = sorted(glob(os.path.join(mapPath, '*.tif')))

                # Make multiple mosaics if number of input sonograms is greater than maxChunk
                if (len(map) > maxChunk) and (maxChunk != 0):
                    predictToMosaic = [map[i:i+maxChunk] for i in range(0, len(map), maxChunk)]
                else:
                    predictToMosaic = [map]

        # Create geotiff
        if mosaic == 1:
            if son:
                if self.port.rect_wcp:
                    _ = Parallel(n_jobs= np.min([len(wcpToMosaic), threadCnt]), verbose=10)(delayed(self._mosaicGtiff)([wcp], overview, i, son=son) for i, wcp in enumerate(wcpToMosaic))
                if self.port.rect_wcr:
                    _ = Parallel(n_jobs= np.min([len(srcToMosaic), threadCnt]), verbose=10)(delayed(self._mosaicGtiff)([src], overview, i, son=son) for i, src in enumerate(srcToMosaic))
            else:
                if self.port.map_sub:
                    _ = Parallel(n_jobs= np.min([len(subToMosaic), threadCnt]), verbose=10)(delayed(self._mosaicGtiff)([sub], overview=overview, i=i, son=son) for i, sub in enumerate(subToMosaic))

                if self.port.map_predict:
                    # Determine number of bands, i.e. substrate classes
                    bands = self._getBandCount(predictToMosaic[0][0])
                    for i, pred in enumerate(predictToMosaic):
                        _ = Parallel(n_jobs= np.min([bands, threadCnt]), verbose=10)(delayed(self._mosaicGtiff)([pred], overview, i, bands=[c], son=True) for c in range(1,bands+1))

        # Create vrt
        elif mosaic == 2:
            if son:
                if self.port.rect_wcp:
                    _ = Parallel(n_jobs= np.min([len(wcpToMosaic), threadCnt]), verbose=10)(delayed(self._mosaicVRT)([wcp], overview, i, son=son) for i, wcp in enumerate(wcpToMosaic))
                if self.port.rect_wcr:
                    _ = Parallel(n_jobs= np.min([len(srcToMosaic), threadCnt]), verbose=10)(delayed(self._mosaicVRT)([src], overview, i, son=son) for i, src in enumerate(srcToMosaic))
            else:
                if self.port.map_sub:
                    _ = Parallel(n_jobs= np.min([len(subToMosaic), threadCnt]), verbose=10)(delayed(self._mosaicVRT)([sub], overview, i, son=son) for i, sub in enumerate(subToMosaic))

                if self.port.map_predict:
                    # Determine number of bands, i.e. substrate classes
                    bands = self._getBandCount(predictToMosaic[0][0])
                    for i, pred in enumerate(predictToMosaic):
                        _ = Parallel(n_jobs= np.min([bands, threadCnt]), verbose=10)(delayed(self._mosaicVRT)([pred], overview, i, bands=[c], son=True) for c in range(1,bands+1))

        return


    def _createMosaicTransect(self,
                      mosaic=1,
                      overview=True,
                      threadCnt=cpu_count(),
                      son=True,
                      maxChunk = 50,
                      cog=True):
        '''
        Main function to mosaic exported rectified sonograms into a mosaic. If
        overview=True, overviews of the mosaic will be built, enhancing view
        performance in a GIS. Generating overviews will increase mosaic file size.

        ----------
        Parameters
        ----------
        mosaic : int : [Default=1]
            DESCRIPTION - Type of mosaic to create.
                          1 = GeoTiff;
                          2 = VRT (Virtual raster table), an xml that references
                            each individual rectified sonogram chunk and mosaics
                            on the fly.
        overview : bool : [Default=True]
            DESCRIPTION - Flag indicating if mosaic overviews should be generated.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        rectObj._rectSonParallel()

        -------
        Returns
        -------
        Exports mosaics of rectified sonograms.

        --------------------
        Next Processing Step
        --------------------
        Calls self._mosaicGtiff() or self._mosaicVRT() to generate mosaics.
        '''
        # maxChunk = 50 # Max chunks per mosaic. Limits each mosaic file size.
        self.imgsToMosaic = [] # List to store files to mosaic.

        chunkField = 'chunk_id'

        if son:
            if self.port.rect_wcp: # Moscaic wcp sonograms if previousl exported
                self.port._loadSonMeta()
                df = self.port.sonMetaDF

                portPath = os.path.join(self.port.outDir, 'rect_wcp')

                port = []
                for name, group in df.groupby('transect'):
                    chunks = pd.unique(group[chunkField])
                    port_transect = []
                    for chunk in chunks:
                        zero = self.port._addZero(chunk)
                        img_path = os.path.join(portPath, '*_{}{}.tif'.format(zero, chunk))
                        img = glob(img_path)[0]
                        port_transect.append(img)
                    port.append(port_transect)

                self.star._loadSonMeta()
                df = self.star.sonMetaDF

                starPath = os.path.join(self.star.outDir, 'rect_wcp')

                star = []
                for name, group in df.groupby('transect'):
                    chunks = pd.unique(group[chunkField])
                    star_transect = []
                    for chunk in chunks:
                        zero = self.port._addZero(chunk)
                        img_path = os.path.join(starPath, '*_{}{}.tif'.format(zero, chunk))
                        img = glob(img_path)[0]
                        star_transect.append(img)
                    star.append(star_transect)

                wcpToMosaic = [list(itertools.chain(*i)) for i in zip(port, star)]

            if self.port.rect_wcr: # Moscaic wcp sonograms if previousl exported

                self.port._loadSonMeta()
                df = self.port.sonMetaDF

                portPath = os.path.join(self.port.outDir, 'rect_wcr')

                port = []
                for name, group in df.groupby('transect'):
                    chunks = pd.unique(group[chunkField])
                    port_transect = []
                    for chunk in chunks:
                        # try:
                        zero = self.port._addZero(chunk)
                        img_path = os.path.join(portPath, '*_{}{}.tif'.format(zero, chunk))
                        img = glob(img_path)[0]
                        port_transect.append(img)
                        # except:
                        #     pass
                    port.append(port_transect)

                self.star._loadSonMeta()
                df = self.star.sonMetaDF

                starPath = os.path.join(self.star.outDir, 'rect_wcr')

                star = []
                for name, group in df.groupby('transect'):
                    chunks = pd.unique(group[chunkField])
                    star_transect = []
                    for chunk in chunks:
                        # try:
                        zero = self.star._addZero(chunk)
                        img_path = os.path.join(starPath, '*_{}{}.tif'.format(zero, chunk))
                        img = glob(img_path)[0]
                        star_transect.append(img)
                        # except:
                        #     pass
                    star.append(star_transect)

                srcToMosaic = [list(itertools.chain(*i)) for i in zip(port, star)]

        else:
            if self.port.map_sub:
                # # Locate map files
                # mapPath = os.path.join(self.port.substrateDir, 'map_substrate_raster')
                # map = sorted(glob(os.path.join(mapPath, '*.tif')))

                # # Make multiple mosaics if number of input sonograms is greater than maxChunk
                # if (len(map) > maxChunk) and (maxChunk != 0):
                #     subToMosaic = [map[i:i+maxChunk] for i in range(0, len(map), maxChunk)]
                # else:
                #     subToMosaic = [map]

                self.port._loadSonMeta()
                df = self.port.sonMetaDF

                portPath = os.path.join(self.port.substrateDir, 'map_substrate_raster')

                subToMosaic = []
                for name, group in df.groupby('transect'):
                    chunks = pd.unique(group[chunkField])
                    port_transect = []
                    for chunk in chunks:
                        zero = self.port._addZero(chunk)
                        img_path = os.path.join(portPath, '*_{}{}.tif'.format(zero, chunk))
                        img = glob(img_path)[0]
                        port_transect.append(img)
                    subToMosaic.append(port_transect)

            if self.port.map_predict:
                # Locate map files
                if self.port.map_predict == 1:
                    mapPath = os.path.join(self.port.substrateDir, 'map_probability_raster')
                elif self.port.map_predict == 2:
                    mapPath = os.path.join(self.port.substrateDir, 'map_logit_raster')
                map = sorted(glob(os.path.join(mapPath, '*.tif')))

                # Make multiple mosaics if number of input sonograms is greater than maxChunk
                if (len(map) > maxChunk) and (maxChunk != 0):
                    predictToMosaic = [map[i:i+maxChunk] for i in range(0, len(map), maxChunk)]
                else:
                    predictToMosaic = [map]

        # Create geotiff
        if mosaic == 1:
            if son:
                if self.port.rect_wcp:
                    _ = Parallel(n_jobs= np.min([len(wcpToMosaic), threadCnt]), verbose=10)(delayed(self._mosaicGtiff)([wcp], overview, i, son=son) for i, wcp in enumerate(wcpToMosaic))
                if self.port.rect_wcr:
                    _ = Parallel(n_jobs= np.min([len(srcToMosaic), threadCnt]), verbose=10)(delayed(self._mosaicGtiff)([src], overview, i, son=son) for i, src in enumerate(srcToMosaic))
            else:
                if self.port.map_sub:
                    _ = Parallel(n_jobs= np.min([len(subToMosaic), threadCnt]), verbose=10)(delayed(self._mosaicGtiff)([sub], overview=overview, i=i, son=son) for i, sub in enumerate(subToMosaic))

                if self.port.map_predict:
                    # Determine number of bands, i.e. substrate classes
                    bands = self._getBandCount(predictToMosaic[0][0])
                    for i, pred in enumerate(predictToMosaic):
                        _ = Parallel(n_jobs= np.min([bands, threadCnt]), verbose=10)(delayed(self._mosaicGtiff)([pred], overview, i, bands=[c], son=True) for c in range(1,bands+1))

        # Create vrt
        elif mosaic == 2:
            if son:
                if self.port.rect_wcp:
                    _ = Parallel(n_jobs= np.min([len(wcpToMosaic), threadCnt]), verbose=10)(delayed(self._mosaicVRT)([wcp], overview, i, son=son) for i, wcp in enumerate(wcpToMosaic))
                if self.port.rect_wcr:
                    _ = Parallel(n_jobs= np.min([len(srcToMosaic), threadCnt]), verbose=10)(delayed(self._mosaicVRT)([src], overview, i, son=son) for i, src in enumerate(srcToMosaic))
            else:
                if self.port.map_sub:
                    _ = Parallel(n_jobs= np.min([len(subToMosaic), threadCnt]), verbose=10)(delayed(self._mosaicVRT)([sub], overview, i, son=son) for i, sub in enumerate(subToMosaic))

                if self.port.map_predict:
                    # Determine number of bands, i.e. substrate classes
                    bands = self._getBandCount(predictToMosaic[0][0])
                    for i, pred in enumerate(predictToMosaic):
                        _ = Parallel(n_jobs= np.min([bands, threadCnt]), verbose=10)(delayed(self._mosaicVRT)([pred], overview, i, bands=[c], son=True) for c in range(1,bands+1))

        return


    #=======================================================================
    def _mosaicGtiff(self,
                     imgsToMosaic,
                     overview=True,
                     i=0,
                     bands=[1],
                     son=True):
        '''
        Function to mosaic sonograms into a GeoTiff.

        ----------
        Parameters
        ----------
        imgsToMosaic : list of lists
            DESCRIPTION - A list of lists containing file paths of sonograms to
                          mosaic.

        overview : bool : [Default=True]
            DESCRIPTION - Flag indicating if mosaic overviews should be generated.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self._createMosaic()

        -------
        Returns
        -------
        Exports mosaics of rectified sonograms.

        --------------------
        Next Processing Step
        --------------------
        None
        '''
        
        resampleAlg = 'nearest'

        # Iterate each sublist of images
        outMosaic = []
        for imgs in imgsToMosaic:

            # Set output file names
            fileSuffix = os.path.split(os.path.dirname(imgs[0]))[-1] + '_mosaic_'+str(i)+'.vrt'
            filePrefix = os.path.split(self.port.projDir)[-1]
            if 'substrate' in fileSuffix:
                outDir = os.path.join(self.port.substrateDir, 'map_substrate_mosaic')
                outVRT = os.path.join(outDir, filePrefix+'_'+fileSuffix)
            elif 'probability' in fileSuffix:
                outDir = os.path.join(self.port.substrateDir, 'map_probability_mosaic')
                outVRT = os.path.join(outDir, filePrefix+'_'+'class_'+str(bands[0]-1)+'_'+fileSuffix)
            elif 'logit' in fileSuffix:
                outDir = os.path.join(self.port.substrateDir, 'map_logit_mosaic')
                outVRT = os.path.join(outDir, filePrefix+'_'+'class_'+str(bands[0]-1)+'_'+fileSuffix)
            else:
                outDir = os.path.join(self.port.projDir, 'sonar_mosaic')
                outVRT = os.path.join(outDir, filePrefix+'_'+fileSuffix)
            outTIF = outVRT.replace('.vrt', '.tif')

            if not os.path.isdir(outDir):
                try:
                    os.makedirs(outDir)
                except:
                    pass

            # First built a vrt
            vrt_options = gdal.BuildVRTOptions(resampleAlg=resampleAlg, bandList = bands)
            gdal.BuildVRT(outVRT, imgs, options=vrt_options)

            # Create GeoTiff from vrt
            ds = gdal.Open(outVRT)

            kwargs = {'format': 'GTiff',
                      'creationOptions': ['NUM_THREADS=ALL_CPUS', 'COMPRESS=LZW', 'TILED=YES']
                      }

            # # Set output pixel resolution
            # xRes = self.port.pix_res
            # yRes = self.port.pix_res

            # # Create geotiff
            # gdal.Translate(outTIF, ds, xRes=xRes, yRes=yRes, **kwargs)

            # Create geotiff
            gdal.Translate(outTIF, ds, **kwargs)

            # Generate overviews
            if overview:
                dest = gdal.Open(outTIF, 1)
                gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
                dest.BuildOverviews('nearest', [2 ** j for j in range(1,10)])

            os.remove(outVRT) # Remove vrt
            i+=1 # Iterate mosaic number
            outMosaic.append(outTIF)

        gc.collect()
        return outTIF

    #=======================================================================
    def _mosaicVRT(self,
                   imgsToMosaic,
                   overview=True,
                   i=0,
                   bands=[1],
                   son=True):
        '''
        Function to mosaic sonograms into a VRT (virtual raster table, see
        https://gdal.org/drivers/raster/vrt.html for more information).

        ----------
        Parameters
        ----------
        imgsToMosaic : list of lists
            DESCRIPTION - A list of lists containing file paths of sonograms to
                          mosaic.

        overview : bool : [Default=True]
            DESCRIPTION - Flag indicating if mosaic overviews should be generated.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self._createMosaic()

        -------
        Returns
        -------
        Exports mosaics of rectified sonograms.

        --------------------
        Next Processing Step
        --------------------
        None
        '''

        if son:
            resampleAlg='lanczos'
        else:
            resampleAlg='nearest'

        # Iterate each sublist of images
        outMosaic = []
        for imgs in imgsToMosaic:

            # Set output file names
            fileSuffix = os.path.split(os.path.dirname(imgs[0]))[-1] + '_mosaic_'+str(i)+'.vrt'
            filePrefix = os.path.split(self.port.projDir)[-1]
            if 'substrate' in fileSuffix:
                outDir = os.path.join(self.port.substrateDir, 'map_substrate_mosaic')
                outVRT = os.path.join(outDir, filePrefix+'_'+fileSuffix)
            elif 'probablity' in fileSuffix:
                outDir = os.path.join(self.port.substrateDir, 'map_probability_mosaic')
                outVRT = os.path.join(outDir, filePrefix+'_'+'class_'+str(bands[0]-1)+'_'+fileSuffix)
            elif 'logit' in fileSuffix:
                outDir = os.path.join(self.port.substrateDir, 'map_logit_mosaic')
                outVRT = os.path.join(outDir, filePrefix+'_'+'class_'+str(bands[0]-1)+'_'+fileSuffix)
            else:
                outDir = os.path.join(self.port.projDir, 'sonar_mosaic')
                outVRT = os.path.join(outDir, filePrefix+'_'+fileSuffix)

            if not os.path.isdir(outDir):
                try:
                    os.makedirs(outDir)
                except:
                    pass

            # # Set output pixel resolution
            # xRes = self.port.pix_res
            # yRes = self.port.pix_res

            # Build VRT
            # vrt_options = gdal.BuildVRTOptions(resampleAlg=resampleAlg, bandList = bands, xRes=xRes, yRes=yRes)
            vrt_options = gdal.BuildVRTOptions(resampleAlg=resampleAlg, bandList = bands)
            gdal.BuildVRT(outVRT, imgs, options=vrt_options)

            # Generate overviews
            if overview:
                dest = gdal.Open(outVRT)
                gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
                dest.BuildOverviews('nearest', [2 ** j for j in range(1,10)])
            i+=1
            outMosaic.append(outVRT)

        gc.collect()
        return outMosaic

    #=======================================================================
    def _getBandCount(self, img_file):
        '''
        '''
        img = imread(img_file)
        bands = img.shape[2]
        del img
        return bands
    

    #=======================================================================
    def _doPredict(self,
                   model,
                   arr,
                   doCRF=False):
        '''
        Predict the bed location or shadows from an input array of sonogram
        pixels. Workflow follows prediction routine from
        https://github.com/Doodleverse/segmentation_gym.

        ----------
        Parameters
        ----------
        model : Tensorflow model object
            DESCRIPTION - Pre-trained and compiled Tensorflow model to predict
                          bed location.
        arr : Numpy array
            DESCRIPTION - Numpy array of sonar intensities.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self._depthZheng()

        -------
        Returns
        -------
        2D array of water / bed prediction

        --------------------
        Next Processing Step
        --------------------
        Returns prediction to self._depthZheng()
        '''
        # Read array into a cropped and resized tensor
        if N_DATA_BANDS<=3:
            image, w, h, bigimage = seg_file2tensor(arr, TARGET_SIZE)

        # Standardize
        image = standardize(image.numpy()).squeeze()

        # Do segmentation on compressed sonogram
        est_label = model.predict(tf.expand_dims(image, 0), batch_size=1).squeeze()

        # Up-sample / rescale to original dimensions
        ## Store liklihood for water and bed classes after resize
        E0 = [] # Water liklihood
        E1 = [] # Bed liklihood

        E0.append(resize(est_label[:,:,0],(w,h), preserve_range=True, clip=True))
        E1.append(resize(est_label[:,:,1],(w,h), preserve_range=True, clip=True))
        del est_label

        e0 = np.average(np.dstack(E0), axis=-1)
        e1 = np.average(np.dstack(E1), axis=-1)
        del E0, E1

        # Final classification
        est_label = (e1+(1-e0))/2
        softmax_scores = np.dstack((e0,e1))
        del e0, e1

        if doCRF:
            est_label, l_unique = crf_refine(softmax_scores, bigimage, NCLASSES+1, 1, 1, 2)
            est_label = est_label-1
            est_prob = softmax_scores
        else:

            # Threshold entire label
            thres = threshold_otsu(est_label)

            est_prob = est_label.copy()
            est_label = (est_label>thres).astype('uint8')

        return est_label, est_prob

    ############################################################################
    # Bedpicking                                                               #
    ############################################################################

    #=======================================================================
    def _detectDepth(self,
                     method,
                     i,
                     USE_GPU,
                     tileFile):
        '''
        Main function to automatically calculate depth (i.e. bedpick).

        ----------
        Parameters
        ----------
        method : int
            DESCRIPTION - Flag indicating bedpicking method:
                          1 = Zheng et al. 2021 (self._depthZheng);
                          2 = Binary thresholding (self._depthThreshold).
        i : int
            DESCRIPTION - Chunk index.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from main_readFiles.py

        -------
        Returns
        -------
        None

        --------------------
        Next Processing Step
        --------------------
        self._depthZheng() or self._depthThreshold()
        '''

        # Open model configuration file
        with open(self.configfile) as f:
            config = json.load(f)
        globals().update(config)

        if method == 1:
            if not hasattr(self, 'bedpickModel'):
                # model = self._initModel(USE_GPU)
                model = initModel(self.weights, self.configfile, USE_GPU)
                self.bedpickModel = model

            portDepPixCrop, starDepPixCrop, i = self._depthZheng(i, tileFile)

        elif method == 2:
            self.port._loadSonMeta()
            self.star._loadSonMeta()
            portDepPixCrop, starDepPixCrop, i = self._depthThreshold(i, tileFile)

        gc.collect()
        return portDepPixCrop, starDepPixCrop, i

    #=======================================================================
    def _findBed(self,
                 segArr):
        '''
        This function locates the transition from water column to bed in an array
        of one-hot encoded array where water column pixels are coded as 1 and all
        other pixels are 0. The pixel index for each ping is stored in lists for
        the portside and starboard scans.

        ----------
        Parameters
        ----------
        segArr : Numpy array
            DESCRIPTION - 2D array storing one-hot encoded values indicating water
                          column and non-water column pixels. Array is concatenated
                          port and star pixels.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self._depthZheng()

        -------
        Returns
        -------
        Lists for portside and starboard storing pixel index of water / bed
        transition.

        --------------------
        Next Processing Step
        --------------------
        Returns bed location to self._depthZheng()
        '''
        # Find center of array
        H, W = segArr.shape[0], segArr.shape[1] # height (row), width (column)
        C = int(W/2) # center of array

        # Find bed location
        portBed = [] # Store portside bed location
        starBed = [] # Store starboard bed location
        # Iterate each ping
        for k in range(H):
            # Find portside bed location (left half of sonogram)
            pB = np.where(segArr[k, 0:C]!=1)[0]
            pB = np.split(pB, np.where(np.diff(pB) != 1)[0]+1)[0][-1]

            pDep = C-pB-1 # Subtract from center to get depth

            # If depth is zero, store nan
            if pDep == 0:
                pDep = np.nan

            portBed.append(pDep)

            # Find starboard bed location (right half of sonogram)
            sB = np.where(segArr[k, C:]!=1)[0]
            sB = np.split(sB, np.where(np.diff(sB) != 1)[0]+1)[-1][0]

            # If depth is zero, store nan
            if sB == 0:
                sB = np.nan
            starBed.append(sB)

        return portBed, starBed

    #=======================================================================
    def _filtPredictDepth(self,
                     lab,
                     N):

        lab = remove_small_holes(lab.astype(bool), 2*N)#2*self.port.nchunk)
        lab = remove_small_objects(lab, 2*N).astype('int')+1#2*self.port.nchunk)

        C = int(lab.shape[1]/2) # Center of img width

        for row in range(lab.shape[0]):
            # Label port/star regions seperately
            pReg = label(lab[row,:C])
            sReg = label(lab[row,C:])

            # Get region ID for bed on port/star
            pID = pReg[0]
            sID = sReg[-1]

            # Get port & star bed regions seperately
            pReg = (pReg == pID).astype('int')
            sReg = (sReg == sID).astype('int')

            # Concatenate
            psReg = np.concatenate((pReg, sReg))

            # Get bool arrray where the water==True
            regions = (psReg == 0)

            # Update crop_label
            lab[row,:] = regions

        return lab

    #=======================================================================
    def _depthZheng(self,i,tileFile):
        '''
        Automatically estimate the depth following method of Zheng et al. 2021:
        https://doi.org/10.3390/rs13101945. The only difference between this
        implementation and Zheng et al. 2021 is that model architecture and main
        prediction workflow follow: https://github.com/Doodleverse/segmentation_gym.

        ----------
        Parameters
        ----------
        i : int
            DESCRIPTION - Chunk index.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self.detectDep()

        -------
        Returns
        -------
        Estimated depths for each ping store in self.portDepDetect and
        self.starDepDetect.

        --------------------
        Next Processing Step
        --------------------
        self._saveDepth()
        '''
        doFilt = True
        plotInitPicks = False

        # Get the model
        model = self.bedpickModel

        # Load port/star ping returns and merge them
        self._getPortStarScanChunk(i)
        mergeSon = self.mergeSon

        ###################
        # Make 3-band array
        b1 = mergeSon.copy() # Band 1: no change
        b2 = np.fliplr(b1.copy()) # Band 2: flip port and star
        b3 = np.mean([b1,b2], axis=0) # Band 3: mean of band 1 and 2
        del mergeSon, self.mergeSon

        # Stack the bands
        son3bnd = np.dstack((b1, b2, b3)).astype(np.uint8)
        del b1, b2, b3

        N = son3bnd.shape[1] # Number of samples per ping (width of non-resized sonogram)
        W = TARGET_SIZE[1] # Width of model output prediction
        C = int(N/2) # Center of sonogram

        ##########################################
        # Do initial prediction on entire sonogram
        init_label, init_prob = doPredict(model, MODEL, son3bnd, N_DATA_BANDS, NCLASSES, TARGET_SIZE, OTSU_THRESHOLD)

        ######################################
        # Filters for removing small artifacts
        if doFilt:
            init_label = self._filtPredictDepth(init_label, N)

        ############################################
        # Find pixel location of bed from prediction
        portDepPix, starDepPix = self._findBed(init_label)

        ##################################
        # Crop image using initial bedpick
        ## Modified from Zheng et al. 2021 method
        ## Once cropped, sonogram is closer in size to model TARGET_SIZE, so
        ## any errors introduced after rescaling prediction will be minimized.

        # Find ping-wise max, min, and avg depth from port and star
        maxDepths = np.fmax(portDepPix, starDepPix)
        minDepths = np.fmin(portDepPix, starDepPix)
        avgDepths = np.mean([minDepths, maxDepths], axis=0)

        # Find global min and max depth, ignoring nan's
        maxDep = max(np.nanmax(portDepPix), np.nanmax(starDepPix))
        minDep = min(np.nanmin(portDepPix), np.nanmin(starDepPix))

        # If initial pick failed, store 0 for min and max
        if np.isnan(minDep):
            minDep = 0
        if np.isnan(maxDep):
            maxDep = 0

        # Find ping-wise water column width from min and max depth prediction
        Wp = maxDepths+minDepths

        # Try cropping so water column ~1/3 of target size area
        WCProp = 1/3

        # Buffers so we don't crop too much
        WwcBuf = 150
        WsBuf = 150

        # Sum Wp to determine area of water column
        WpArea = np.nansum(Wp)

        # Determine area of target image
        TArea = TARGET_SIZE[0] * TARGET_SIZE[1]

        # Determine area of WC to keep as proportion of target area
        WpTarget = int( WCProp * TArea)

        # Determine width of water column to remove
        Wwc = int( (WpArea - WpTarget) / TARGET_SIZE[1] )

        # Subtract a buffer from crop and set to zero if Wwc-50<0
        Wwc = max( (Wwc - 50), 0)

        # Make sure we didn't crop past min depth
        if Wwc > minDep:
            # Wwc = max( (minDep - WwcBuf), 0)
            Wwc = max(minDep, 0)

        # Determine amount of bed to crop (Ws)
        # Ws = int( C - (Wwc/2) - maxDep - WsBuf)
        Ws = int( C - maxDep - WsBuf)

        # Make sure we didn't crop too much, especially if initial bedpick was
        ## not good.
        if Ws > (C-(Wwc/2)):
            Ws = int( C - (Wwc/2) - (W/2) - WsBuf)

        # Crop the original sonogram
        ## Port Crop
        lC = Ws # left side crop
        rC = int(C - (Wwc/2)) # right side crop
        portCrop = son3bnd[:, lC:rC,:]

        ## Star Crop
        lC = int(C + (Wwc/2)) # left side crop
        rC = int(N - Ws) # right side crop
        starCrop = son3bnd[:, lC:rC, :]


        ## Concatenate port & star crop
        sonCrop = np.concatenate((portCrop, starCrop), axis = 1)
        sonCrop = sonCrop.astype(np.uint8)
        del portCrop, starCrop

        # Add center pixels back in
        ## The depth model was trained using cropped sonograms that always had
        ## the line dividing port from star present. The cropping step in this
        ## implementation can crop that out, which messes up the prediction on
        ## the cropped image. So we will add center line back into cropped image.
        c = int(sonCrop.shape[1]/2)
        if Wwc > 0:
            sonCrop[:, (c-1):(c+1), :] = 1


        #######################
        # Segment cropped image
        crop_label, crop_prob = doPredict(model, MODEL, sonCrop, N_DATA_BANDS, NCLASSES, TARGET_SIZE, OTSU_THRESHOLD)


        ######################################
        # Filters for removing small artifacts
        if doFilt:
            crop_label = self._filtPredictDepth(crop_label, N)

        #########
        # Recover
        # Calculate depth from prediction
        portDepPixCrop, starDepPixCrop = self._findBed(crop_label) # get pixel location of bed

        # add Wwc/2 to get final estimate at original sonogram dimensions
        portDepPixFinal = np.flip( np.asarray(portDepPixCrop) + int(Wwc/2) )
        starDepPixFinal = np.flip( np.asarray(starDepPixCrop) + int(Wwc/2) )

        #############
        # Final Check

        # Check to make sure final bedpick has valid values (ie not nan's).
        ## If final pick is nan, replace with initial pick if not nan.
        ## If initial pick also nan, set bedpick to 0.
        check = True
        if check:
            portDepPix = np.flip( np.asarray(portDepPix) )
            starDepPix = np.flip( np.asarray(starDepPix) )
            # Port
            port = []
            for pdi, pdc in zip(portDepPix, portDepPixFinal):
                if np.isnan(pdc): # Final pick is nan
                    if np.isnan(pdc): # Initial pick is nan
                        port.append(0) # set to 0
                    else: # Initial pick not nan
                        port.append(pdi) # Use initial pick

                elif pdc < 0:
                    port.append(0)

                else: # Final pick is ok
                    port.append(pdc)

            # Star
            star = []
            for sdi, sdc in zip(starDepPix, starDepPixFinal):
                if np.isnan(sdc): # Final pick is nan
                    if np.isnan(sdi): # Initial pick is nan
                        star.append(0) # set to 0
                    else: # Initial pick not nan
                        star.append(sdi) # Use initial pick

                elif sdc < 0:
                    port.append(0)

                else: # Final pick ok
                    star.append(sdc)

            portDepPixFinal = port
            starDepPixFinal = star
            del port, star

        # For debug purposes
        if plotInitPicks:
            # Show centerline on labels for debug
            init_label[:, (C-1):(C+1)] = 2
            crop_label[:, (c-1):(c+1)] = 2

            #*#*#*#*#*#*#*#
            # Plot
            # color map
            class_label_colormap = ['#3366CC','#DC3912', '#000000']

            # Initial
            color_label = label_to_colors(init_label, son3bnd[:,:,0]==0, alpha=128, colormap=class_label_colormap, color_class_offset=0, do_alpha=False)
            imsave(os.path.join(self.port.projDir, str(i)+"_initLabel_"+str(i)+tileFile), (color_label).astype(np.uint8), check_contrast=False)
            imsave(os.path.join(self.port.projDir, str(i)+"_initImg_"+str(i)+tileFile), (son3bnd).astype(np.uint8), check_contrast=False)

            # Cropped
            color_label = label_to_colors(crop_label, sonCrop[:,:,0]==0, alpha=128, colormap=class_label_colormap, color_class_offset=0, do_alpha=False)
            imsave(os.path.join(self.port.projDir, str(i)+"_cropLabel_"+str(i)+tileFile), (color_label).astype(np.uint8), check_contrast=False)
            imsave(os.path.join(self.port.projDir, str(i)+"_cropImg_"+str(i)+tileFile), (sonCrop).astype(np.uint8), check_contrast=False)

        del son3bnd, init_label, init_prob, crop_label, crop_prob, sonCrop
        del maxDepths, minDepths, avgDepths, Wp, portDepPixCrop, starDepPixCrop
        del portDepPix, starDepPix
        del model, self.bedpickModel ######## Not sure about this one...

        # return #self
        return portDepPixFinal, starDepPixFinal, i

    #=======================================================================
    def _depthThreshold(self, chunk):
        '''
        PING-Mapper's rules-based automated depth detection using pixel intensity
        thresholding.

        ----------
        Parameters
        ----------
        chunk : int
            DESCRIPTION - Chunk index.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self._detectDepth()

        -------
        Returns
        -------
        Estimated depths for each ping store in self.portDepDetect and
        self.starDepDetect.

        --------------------
        Next Processing Step
        --------------------
        self._saveDepth()
        '''
        # Parameters
        window = 10 # For peak removal in bed pick: moving window size
        max_dev = 5 # For peak removal in bed pick: maximum standard deviation
        pix_buf = 50 # Buffer size around min/max Humminbird depth

        portstar = [self.port, self.star]
        for son in portstar:
            # Load sonar intensity, standardize & rescale
            son._getScanChunkSingle(chunk)
            img = son.sonDat
            img = standardize(img, 0, 1, True)[:,:,-1].squeeze()
            W, H = img.shape[1], img.shape[0]

            # Get chunks sonar metadata and instrument depth
            isChunk = son.sonMetaDF['chunk_id']==1
            sonMeta = son.sonMetaDF[isChunk].reset_index()
            # acousticBed = round(sonMeta['inst_dep_m'] / sonMeta['pix_m'], 0).astype(int)
            acousticBed = round(sonMeta['inst_dep_m'] / self.pixM, 0).astype(int)

            ##################################
            # Step 1 : Acoustic Bedpick Filter
            # Use acoustic bed pick to crop image
            bedMin = max(min(acousticBed)-50, 0)
            bedMax = max(acousticBed)+pix_buf

            cropMask = np.ones((H, W)).astype(int)
            cropMask[:bedMin,:] = 0
            cropMask[bedMax:,:] = 0

            # Mask the image with bed_mask
            imgMasked = img*cropMask

            ###########################
            # Step 2 - Threshold Filter
            # Binary threshold masked image
            imgMasked = gaussian(imgMasked, 3, preserve_range=True) # Do a gaussian blur
            imgMasked[imgMasked==0]=np.nan # Set zero's to nan

            imgBinaryMask = np.zeros((H, W)).astype(bool) # Create array to store thresholded sonar img
            # Iterate over each ping
            for i in range(W):
                thresh = max(np.nanmedian(imgMasked[:,i]), np.nanmean(imgMasked[:,i])) # Determine threshold value
                # stdev = np.nanstd(imgMasked[:,i])
                imgBinaryMask[:,i] = imgMasked[:,i] > thresh # Keep only intensities greater than threshold

            # Clean up image binary mask
            imgBinaryMask = remove_small_objects(imgBinaryMask, 2*H)
            imgBinaryMask = remove_small_holes(imgBinaryMask, 2*H)
            imgBinaryMask = np.squeeze(imgBinaryMask[:H,:W])

            ########################################
            # Step 3 - Non-Contiguous region removal
            # Make sure we didn't accidently zero out the last row, which should be bed.
            # If we did, we will fill it back in
            # Try filtering image_binary_mask through labeling regions
            labelImage, num = label(imgBinaryMask, return_num=True)
            allRegions = []

            # Find the lowest/deepest region (this is the bed pixels)
            max_row = 0
            finalRegion = 0
            for region in regionprops(labelImage):
                allRegions.append(region.label)
                minr, minc, maxr, maxc = region.bbox
                # if (maxr > max_row) and (maxc > max_col):
                if (maxr > max_row):
                    max_row = maxr
                    finalRegion = region.label

            # If finalRegion is 0, there is only one region
            if finalRegion == 0:
                finalRegion = 1

            # Zero out undesired regions
            for regionLabel in allRegions:
                if regionLabel != finalRegion:
                    labelImage[labelImage==regionLabel] = 0

            imgBinaryMask = labelImage # Update thresholded image
            imgBinaryMask[imgBinaryMask>0] = 1 # Now set all val's greater than 0 to 1 to create the mask

            # Now fill in above last row filled to make sure no gaps in bed pixels
            lastRow = bedMax
            imgBinaryMask[lastRow] = True
            for i in range(W):
                if imgBinaryMask[lastRow-1,i] == 0:
                    gaps = np.where(imgBinaryMask[:lastRow,i]==0)[0]
                    # Split each gap cluster into it's own array, subset the last one,
                    ## and take top value
                    topOfGap = np.split(gaps, np.where(np.diff(gaps) != 1)[0]+1)[-1][0]
                    imgBinaryMask[topOfGap:lastRow,i] = 1

            # Clean up image binary mask
            imgBinaryMask = imgBinaryMask.astype(bool)
            imgBinaryMask = remove_small_objects(imgBinaryMask, 2*H)
            imgBinaryMask = remove_small_holes(imgBinaryMask, 2*H)
            imgBinaryMask = np.squeeze(imgBinaryMask[:H,:W])

            #############################
            # Step 4 - Water Below Filter
            # Iterate each ping and determine if there is water under the bed.
            # If there is, zero out everything except for the lowest region.
            # Iterate each ping
            for i in range(W):
                labelPing, num = label(imgBinaryMask[:,i], return_num=True)
                if num > 1:
                    labelPing[labelPing!=num] = 0
                    labelPing[labelPing>0] = 1
                imgBinaryMask[:,i] = labelPing

            ###################################################
            # Step 5 - Final Bedpick: Locate Bed & Remove Peaks
            # Now relocate bed from image_binary_mask
            bed = []
            for k in range(W):
                try:
                    b = np.where(imgBinaryMask[:,k]==1)[0][0]
                except:
                    b=0
                bed.append(b)
            bed = np.array(bed).astype(np.float32)

            # Interpolate over nan's
            nans, x = np.isnan(bed), lambda z: z.nonzero()[0]
            bed[nans] = np.interp(x(nans), x(~nans), bed[~nans])
            bed = bed.astype(int)

            if son.beamName == 'ss_port':
                # self.portDepDetect[chunk] = bed
                portDepPixCrop = bed
            elif son.beamName == 'ss_star':
                # self.starDepDetect[chunk] = bed
                starDepPixCrop = bed

        # return #self
        return portDepPixCrop, starDepPixCrop, chunk

    #=======================================================================
    def _saveDepth(self,
                   chunksPred,
                   detectDep=0,
                   smthDep=False,
                   adjDep=False):
        '''
        Converts bedpick location (in pixels) to a depth in meters and additionally
        smooth and adjust depth estimate.

        ----------
        Parameters
        ----------
        chunks : list
            DESCRIPTION - List storing chunk indexes.

        detectDep : int : [Default=0]
            DESCRIPTION - Flag indicating bedpicking method:
                          0 = Instrument depth
                          1 = Zheng et al. 2021 (self._depthZheng);
                          2 = Binary thresholding (self._depthThreshold).

        smthDep : bool : [Default=False]
            DESCRIPTION - Apply Savitzky-Golay filter to depth data.  May help smooth
                          noisy depth estimations.  Recommended if using Humminbird
                          depth to remove water column (detectDep=0).
                          True = smooth depth estimate;
                          False = do not smooth depth estimate.

        adjDep : bool : [Default=False]
            DESCRIPTION - Specify additional depth adjustment (in pixels) for water
                          column removal.  Does not affect the depth estimate stored
                          in exported metadata *.CSV files.
                          Integer > 0 = increase depth estimate by x pixels.
                          Integer < 0 = decrease depth estimate by x pixels.
                          0 = use depth estimate with no adjustment.
        '''
        # Load sonar metadata file
        self.port._loadSonMeta()
        portDF = self.port.sonMetaDF
        self.star._loadSonMeta()
        starDF = self.star.sonMetaDF

        # Get all chunks
        chunks = pd.unique(portDF['chunk_id'])

        if detectDep == 0:
            portInstDepth = portDF['inst_dep_m']
            starInstDepth = starDF['inst_dep_m']

            if smthDep:
                # print("\nSmoothing depth values...")
                portInstDepth = savgol_filter(portInstDepth, 51, 3)
                starInstDepth = savgol_filter(starInstDepth, 51, 3)

            if adjDep != 0:
                adjBy = adjDep
                portInstDepth += adjBy
                starInstDepth += adjBy

            # Set negatives to 0
            portInstDepth = np.asarray(portInstDepth)
            starInstDepth = np.asarray(starInstDepth)

            portInstDepth = np.where(portInstDepth<0, 0, portInstDepth)
            starInstDepth = np.where(starInstDepth<0, 0, starInstDepth)

            portInstDepth = portInstDepth.tolist()
            starInstDepth = starInstDepth.tolist()

            # Add depth to df
            portDF['dep_m'] = portInstDepth
            starDF['dep_m'] = starInstDepth

            portDF['dep_m_Method'] = 'Instrument Depth'
            starDF['dep_m_Method'] = 'Instrument Depth'

            portDF['dep_m_smth'] = smthDep
            starDF['dep_m_smth'] = smthDep

            portDF['dep_m_adjBy'] = str(adjDep / self.port.pixM) + ' pixels'
            starDF['dep_m_adjBy'] = str(adjDep / self.port.pixM) + ' pixels'

        elif detectDep > 0:
            # Prepare depth detection dictionaries
            portFinal = []
            starFinal = []
            for i in sorted(chunks):

                if i in self.portDepDetect:
                    portDep = self.portDepDetect[i]
                # For chunks completely filled with NoData
                else:
                    portDep = [0]*self.port.nchunk

                if i in self.starDepDetect:
                    starDep = self.starDepDetect[i]
                # For chunks completely filled with NoData
                else:
                    starDep = [0]*self.star.nchunk

                portFinal.extend(portDep)
                starFinal.extend(starDep)

            # Check shapes to ensure they are same length.  If not, slice off extra.
            ## Port
            if len(portFinal) > portDF.shape[0]:
                # Trim portFinal
                lenDif = portDF.shape[0] - len(portFinal)
                portFinal = portFinal[:lenDif]
            elif len(portFinal) < portDF.shape[0]:
                # Extend portFinal
                t = np.zeros((len(portDF))) # Make array same size as portDF
                t[:len(portFinal)] = portFinal
                portFinal = t
            else:
                pass

            ## Star
            if len(starFinal) > starDF.shape[0]:
                lenDif = starDF.shape[0] - len(starFinal)
                starFinal = starFinal[:lenDif]
            elif len(starFinal) < starDF.shape[0]:
                # Extend starFinal
                t = np.zeros((len(starDF))) # Make array same size as starDF
                t[:len(starFinal)] = starFinal
                starFinal = t

            # Smooth depth
            if smthDep:
                portFinal = savgol_filter(portFinal, 51, 3)
                starFinal = savgol_filter(starFinal, 51, 3)

            # Convert pix to depth [m]
            portFinal = np.asarray(portFinal) * self.port.pixM
            starFinal = np.asarray(starFinal) * self.star.pixM

            # Set negatives to 0
            portFinal = np.where(portFinal<0, 0, portFinal)
            starFinal = np.where(starFinal<0, 0, starFinal)

            portFinal = portFinal.tolist()
            starFinal = starFinal.tolist()

            portDF['dep_m'] = portFinal
            starDF['dep_m'] = starFinal

            if adjDep != 0:
                adjBy = adjDep
                portDF['dep_m'] += adjBy
                starDF['dep_m'] += adjBy

            if detectDep == 1:
                portDF['dep_m_Method'] = 'Zheng et al. 2021'
                starDF['dep_m_Method'] = 'Zheng et al. 2021'
            elif detectDep == 2:
                portDF['dep_m_Method'] = 'Threshold'
                starDF['dep_m_Method'] = 'Threshold'

            portDF['dep_m_smth'] = smthDep
            starDF['dep_m_smth'] = smthDep

            portDF['dep_m_adjBy'] = str(adjDep / self.port.pixM) + ' pixels'
            starDF['dep_m_adjBy'] = str(adjDep / self.port.pixM) + ' pixels'

        # Export to csv
        portDF.to_csv(self.port.sonMetaFile, index=False, float_format='%.14f')
        starDF.to_csv(self.star.sonMetaFile, index=False, float_format='%.14f')

        try:
            # Take average of both estimates to store with downlooking sonar csv
            depDF = pd.DataFrame(columns=['dep_m', 'dep_m_Method', 'dep_m_smth', 'dep_m_adjBy'])
            depDF['dep_m'] = np.nanmean([portDF['dep_m'].to_numpy(), starDF['dep_m'].to_numpy()], axis=0)
            depDF['dep_m_Method'] = portDF['dep_m_Method']
            depDF['dep_m_smth'] = portDF['dep_m_smth']
            depDF['dep_m_adjBy'] = portDF['dep_m_adjBy']
        except:
            # In case port and star are not same length
            depDF = pd.DataFrame(columns=['dep_m', 'dep_m_Method', 'dep_m_smth', 'dep_m_adjBy'])
            depDF['dep_m'] = portDF['dep_m']
            depDF['dep_m_Method'] = portDF['dep_m_Method']
            depDF['dep_m_smth'] = portDF['dep_m_smth']
            depDF['dep_m_adjBy'] = portDF['dep_m_adjBy']

        del portDF, starDF
        gc.collect()
        return depDF

    #=======================================================================
    def _plotBedPick(self,
                     i,
                     acousticBed = True,
                     autoBed = True,
                     autoBank = False,
                     tileFile = '.jpg'):

        '''
        Export a plot of bedpicks on sonogram for a given chunk.

        ----------
        Parameters
        ----------
        i : int
            DESCRIPTION - Chunk index.

        acousticBed : bool : [Default=True]
            DESCRIPTION - Plot the instrument's acoustic bedpick on sonogram.

        autoBed : bool : [Default=True]
            DESCRIPTION - Plot the automated bedpick on sonogram.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        None

        -------
        Returns
        -------
        Plot of bedpicks overlaying sonogram.

        --------------------
        Next Processing Step
        --------------------
        None
        '''

        # Load sonar intensity into memory
        self._getPortStarScanChunk(i)
        mergeSon = self.mergeSon

        ####################
        # Prepare depth data
        # Load sonar metadata file
        self.port._loadSonMeta()
        portDF = self.port.sonMetaDF

        self.star._loadSonMeta()
        starDF = self.star.sonMetaDF

        portDF = portDF.loc[portDF['chunk_id'] == i, ['inst_dep_m', 'dep_m']]
        starDF = starDF.loc[starDF['chunk_id'] == i, ['inst_dep_m', 'dep_m']]

        portInst = (portDF['inst_dep_m'] / self.port.pixM).to_numpy(dtype=int, copy=True)
        portAuto = (portDF['dep_m'] / self.port.pixM).to_numpy(dtype=int, copy=True)

        starInst = (starDF['inst_dep_m'] / self.star.pixM).to_numpy(dtype=int, copy=True)
        starAuto = (starDF['dep_m'] / self.star.pixM).to_numpy(dtype=int, copy=True)

        # Ensure port/star same length
        if (portAuto.shape[0] != starAuto.shape[0]):
            pL = portAuto.shape[0]
            sL = starAuto.shape[0]
            # Add rows to shortest array from longest array
            if (pL > sL):
                starAuto = np.append(starAuto, portAuto[(sL-pL):])
                starInst = np.append(starInst, portInst[(sL-pL):])
            else:
                portAuto = np.append(portAuto, starAuto[(pL-sL):])
                portInst = np.append(portInst, starInst[(pL-sL):])

        # Relocate depths relative to horizontal center of image
        c = int(mergeSon.shape[1]/2)

        portInst = c - portInst
        portAuto = c - portAuto

        starInst = c + starInst
        starAuto = c + starAuto

        # maybe flip???
        portInst = np.flip(portInst)
        portAuto = np.flip(portAuto)

        starInst = np.flip(starInst)
        starAuto = np.flip(starAuto)

        #############
        # Export Plot
        y = np.arange(0, mergeSon.shape[0])
        # File name zero padding
        if i < 10:
            addZero = '0000'
        elif i < 100:
            addZero = '000'
        elif i < 1000:
            addZero = '00'
        elif i < 10000:
            addZero = '0'
        else:
            addZero = ''

        outDir = os.path.join(self.port.projDir, 'Bedpick')
        try:
            os.mkdir(outDir)
        except:
            pass

        projName = os.path.split(self.port.projDir)[-1]
        outFile = os.path.join(outDir, projName+'_Bedpick_'+addZero+str(i)+tileFile)

        plt.imshow(mergeSon, cmap='gray')
        if acousticBed:
            plt.plot(portInst, y, 'r-.', lw=1, label='Acoustic Depth')
            plt.plot(starInst, y, 'r-.', lw=1)
            del portInst, starInst
        if autoBed:
            plt.plot(portAuto, y, 'b-.', lw=1, label='Auto Depth')
            plt.plot(starAuto, y, 'b-.', lw=1)
            del portAuto, starAuto

        plt.legend(loc = 'lower right', prop={'size':4}) # create the plot legend
        plt.savefig(outFile, dpi=300, bbox_inches='tight')
        plt.close()

        del self.mergeSon, self.port.sonMetaDF, self.star.sonMetaDF, y

        gc.collect()
        return #self


    ############################################################################
    # Shadow Removal                                                           #
    ############################################################################

    def _filtShadow(self, lab):
        R = lab.shape[0] # max range
        P = lab.shape[1] # number of pings

        lab = remove_small_holes(lab.astype(bool), 2*R)#2*self.port.nchunk)
        lab = remove_small_objects(lab, 2*R).astype('int')+1#2*self.port.nchunk)

        return lab

    #=======================================================================
    def _getShadowPix(self, lab, remShadow):
        '''
        '''
        R = lab.shape[0] # max range
        P = lab.shape[1] # number of pings

        # Zero out everything except shadows
        lab = np.where(lab==1, lab, 0)

        # Remove only far-field (river bank) shadows
        if remShadow == 2:

            # Label contiguous shadow regions
            reg = label(lab)

            # Get shadow regions which touch far-field boarder (max range)
            ffReg = np.unique(reg[R-1,:])

            # Remove region labeled 0
            ffReg = ffReg[ffReg != 0]

            # Keep only far-field regions
            lab = np.zeros((R, P))
            for r in ffReg:
                l = np.where(reg==r, 1, 0)
                lab += l

        # Iterate pings, get begin, end indices for shadow regions
        pix = defaultdict()
        for p in range(P):
            # Find shadows
            bed = np.where(lab[:,p] == 1)[0]

            # Find contiguous shadows
            bed = np.split(bed, np.where(np.diff(bed)>1)[0]+1)

            pPix = []

            # Store per-ping shadow regions (begin, end)
            if len(bed[0]) > 0:
                for b in bed:
                    pPix.append((b[0], b[-1]))

                pix[p] = pPix

        return pix

    #=======================================================================
    def _detectShadow(self, remShadow, i, USE_GPU, doPlot=True, tileFile='.jpg'):
        '''

        '''
        # Open model configuration file
        with open(self.configfile) as f:
            config = json.load(f)
        globals().update(config)

        # Load the model if necessary
        if not hasattr(self, 'shadowModel'):
            # self.shadowModel = self._initModel(USE_GPU)
            self.shadowModel = initModel(self.weights, self.configfile, USE_GPU)

        self.port._loadSonMeta()
        self.star._loadSonMeta()

        # Get the model
        model = self.shadowModel

        #################################################
        # Get depth for water column removal and cropping
        portDF = self.port.sonMetaDF
        starDF = self.star.sonMetaDF

        # Get depth/ pix scaler for given chunk
        portDF = portDF.loc[portDF['chunk_id'] == i, ['dep_m']].reset_index()
        starDF = starDF.loc[starDF['chunk_id'] == i, ['dep_m']].reset_index()

        # Load sonar
        self.port._getScanChunkSingle(i)
        self.star._getScanChunkSingle(i)

        # Get original sonDat dimensions
        pR, pW = self.port.sonDat.shape
        sR, sW = self.star.sonDat.shape

        # Remove water and crop to min depth
        pMinDep = self.port._WCR_crop(portDF)
        sMinDep = self.star._WCR_crop(starDF)

        ###############
        # Do prediction

        port_label, port_prob = doPredict(model, MODEL, self.port.sonDat, N_DATA_BANDS, NCLASSES, TARGET_SIZE, OTSU_THRESHOLD, shadow=True)
        star_label, star_prob = doPredict(model, MODEL, self.star.sonDat, N_DATA_BANDS, NCLASSES, TARGET_SIZE, OTSU_THRESHOLD, shadow=True)

        # Set shadow to 0, else 1
        port_label = np.where(port_label==0,1,0)
        star_label = np.where(star_label==0,1,0)

        ##############################################
        # Recover original dimensions for shadow label
        pMask = np.ones((pR, pW))
        sMask = np.ones((sR, sW))

        pMask[pMinDep:,] = port_label
        sMask[sMinDep:,] = star_label

        ###########################################
        # Remove shadow predictions in water column
        bedpickPort = round(portDF['dep_m'] / self.port.pixM, 0).astype(int)
        bedpickStar = round(starDF['dep_m'] / self.star.pixM, 0).astype(int)

        for j in range(pMask.shape[1]):
            depth = bedpickPort[j]
            pMask[:depth, j] = 1

        for j in range(sMask.shape[1]):
            depth = bedpickStar[j]
            sMask[:depth, j] = 1

        ####################
        # Filter predictions
        port_label = self._filtShadow(pMask)
        star_label = self._filtShadow(sMask)


        ######
        # Plot
        if doPlot:
            # color map
            class_label_colormap = ['#3366CC', '#D3D3D3']

            # Port            
            for son, lb in zip([self.port, self.star], [port_label, star_label]):
                im = son.sonDat
                plt.imshow(im, cmap='gray')

                color_label = label_to_colors(lb, im[:,:]==0, alpha=128, colormap=class_label_colormap, color_class_offset=0, do_alpha=False)
                plt.imshow(color_label, alpha=0.5)

                plt.axis('off')
                plt.savefig(os.path.join(son.projDir, str(i)+"_shadow_"+son.beamName+tileFile), dpi=200, bbox_inches='tight')
                plt.close('all')

        ###
        # Get Pix Coordinates of shadow regions
        port_pix = self._getShadowPix(port_label, remShadow)
        star_pix = self._getShadowPix(star_label, remShadow)

        del self.shadowModel, model
        gc.collect()
        return i, port_pix, star_pix

    ############################################################################
    # For Substrate & Prediction Mapping                                       #
    ############################################################################

    #=======================================================================
    def _mapSubstrate(self, map_class_method, chunk, npzs):
        '''
        '''
        # Set output directory
        self.outDir = self.port.outDir

        # Load npz's
        # Port is always first
        portSub = np.load(npzs[0])
        starSub = np.load(npzs[1])

        self.port.sonDat = portSub['substrate'].astype('float32')
        self.star.sonDat = starSub['substrate'].astype('float32')

        ####################################
        # Do shadow and water column removal

        # Need to update sonObj attributes based on chunk
        # Store in list to process in for loop
        sonObjs = [self.port, self.star]

        for son in sonObjs:

            # Load sonMetaDF
            if not hasattr(son, 'sonMetaDF'):
                son._loadSonMeta()

            sonMetaAll = son.sonMetaDF
            isChunk = sonMetaAll['chunk_id']==chunk
            sonMeta = sonMetaAll[isChunk].reset_index()

            son.pingMax = np.nanmax(sonMeta['ping_cnt']) # store to determine max range per chunk
            son.headIdx = sonMeta['index'] # store byte offset per ping
            son.pingCnt = sonMeta['ping_cnt'] # store ping count per ping

            # Do classification
            label = son._classifySoftmax(chunk, son.sonDat, map_class_method, mask_wc=True, mask_shw=True)
            del son.sonDat

            # Get rid of zeros along water column area
            for p in range(label.shape[1]):
                # Get depth
                d = son.bedPick[p]

                # Get ping classification
                ping = label[:, p]

                # Get water column
                wc = ping[:d]

                # Remove water column
                ping = ping[d:]

                # If any water column pics remain, set to zero
                ping = np.where(ping==8, 0, ping)

                ##############
                # Remove zeros
                # Find zeros. Should be grouped in contiguous arrays (array[0, 1, 2], array[100, 101, 102], ...
                zero = np.where(ping==0)

                if len(zero[0])>0:
                    for z in zero:
                        # Get index of first and last zero
                        f, l = z[0], z[-1]

                        # Don't fall off edge
                        if l+1 < ping.shape[0]:

                            # Get classification of next pixel
                            c = ping[l+1]

                            # Fill zero region with c
                            ping[f:l+1] = c

                    # Add water column back in
                    ping = list(wc)+list(ping)

                    # Update objects filled with ping
                    label[:, p] = ping

                del ping

            son.sonDat = label

            del label

            # Remove shadows
            # Get mask
            son._SHW_mask(chunk, son=False)

            # Mask out shadows
            son.sonDat = son.sonDat*son.shadowMask
            del son.shadowMask

            # Remove water column
            son._WCR_SRC(sonMeta)

            del son

        del sonObjs

        portSub = self.port.sonDat
        starSub = self.star.sonDat


        ###############################################################
        # Merge arrays

        # Check to see if there is a size mismatch. If so, resize and rectify each individually
        if portSub.shape[1] == starSub.shape[1]:
            portSub = np.rot90(portSub, k=2, axes=(1,0))
            portSub = np.fliplr(portSub)
            mergeSub = np.concatenate((portSub, starSub), axis=0)

            del portSub, starSub

            # Do rectification
            self._rectify(mergeSub, chunk, 'map_substrate')
            del mergeSub

        else:
            # Rectify each individually
            # Port
            self.port.sonDat = portSub
            self.port.rect_wcr = True
            self.port._rectSonRubber(chunk, son=False)

            # Star
            self.star.sonDat = starSub
            self.star.rect_wcr = True
            self.star._rectSonRubber(chunk, son=False)

        gc.collect()

        return


    #=======================================================================
    def _mapPredictions(self, map_predict, imgOutPrefix, chunk, npzs):
        '''
        '''
        # Set pixel size [m]
        pix_res_map = self.port.pix_res_map

        if pix_res_map == 0:
            pix_res_map = 0.25

        # Set output directory
        self.outDir = self.port.outDir

        # Get leading zeros for output name
        addZero = self.port._addZero(chunk)

        # Load npz's
        # Port is always first
        portSub = np.load(npzs[0])
        starSub = np.load(npzs[1])

        self.port.sonDat = portSub['substrate'].astype('float32')
        self.star.sonDat = starSub['substrate'].astype('float32')

        del portSub, starSub

        # For debugging
        # self.port.sonDat = portSub['substrate'].astype('float32')[:,:,1:3]
        # self.star.sonDat = starSub['substrate'].astype('float32')[:,:,1:3]

        # Calculate probability, rescale by constant multiplyer, and change dtype
        if map_predict == 1:
            # Set data type and nodata value
            data_type = 'uint16'
            no_data = 0 # no data value (square area around rect data)

            # Calculate probablity
            port = tf.nn.softmax(self.port.sonDat).numpy()
            star = tf.nn.softmax(self.star.sonDat).numpy()

            # Rescale to digital number
            dn = 10000 # Convert 0.XXXX... to XXXX
            port = port * dn
            star = star * dn

            # Round to whole number
            port = np.around(port, 0)
            star = np.around(star, 0)

            # Convert and store data
            self.port.sonDat = port.astype(data_type)
            self.star.sonDat = star.astype(data_type)

        # Logit: rescale by constant multiplyer, and change dtype
        elif map_predict == 2:
            # Set data type and nodata value
            data_type = 'int16'
            no_data = 0 # no data value (square area around rect data)

            # Rescale to digital number
            dn = 100 # Convert XX.XX... to XXXX
            port = self.port.sonDat * dn
            star = self.star.sonDat * dn

            # Round to whole number
            port = np.around(port, 0)
            star = np.around(star, 0)

            # Convert and store data
            self.port.sonDat = port.astype(data_type)
            self.star.sonDat = star.astype(data_type)

        del port, star

        # Store number of bands, i.e. classes
        classes = self.port.sonDat.shape[2]

        # Need to update sonObj attributes based on chunk
        # Store in list to process in for loop
        sonObjs = [self.port, self.star]

        for son in sonObjs:

            # Load sonMetaDF
            if not hasattr(son, 'sonMetaDF'):
                son._loadSonMeta()

            sonMetaAll = son.sonMetaDF
            isChunk = sonMetaAll['chunk_id']==chunk
            sonMeta = sonMetaAll[isChunk].reset_index()

            son.pingMax = np.nanmax(sonMeta['ping_cnt']) # store to determine max range per chunk
            son.headIdx = sonMeta['index'] # store byte offset per ping
            son.pingCnt = sonMeta['ping_cnt'] # store ping count per ping


            # ####################################
            # # Do shadow and water column removal

            # Store pred stack in variable
            predStack = son.sonDat

            # Iterate each classification layer
            for c in range(classes):
                # Get class prediction
                son.sonDat = predStack[:,:,c]

                # Remove shadows
                # Get mask
                son._SHW_mask(chunk, son=False)

                # Mask out shadows
                son.sonDat = son.sonDat*son.shadowMask

                # Remove Water Column
                son._WCR_SRC(sonMeta, son=False)

                # Update predStack
                predStack[:,:,c] = son.sonDat

                del son.sonDat

            # Store in son.sonDat
            son.sonDat = predStack

        # Iterate each class again and:
        for c in range(classes):

            # Get the pred stack
            port = self.port.sonDat
            star = self.star.sonDat

            # Merge #
            port = np.rot90(port[:,:,c], k=2, axes=(1,0))
            port = np.fliplr(port)
            merge = np.concatenate((port, star[:,:,c]), axis=0)

            del port, star

            # Rectify #
            # Try only passing first class to _rectify() to attempt speedup
            if 'transform' not in locals():
                rect_pred, tform, outShape, epsg, transform = self._rectify(merge, chunk, '', return_rect=True)
            else:
                # Use existing tranformation matrix to rectify remaining classes
                # Warp image from the input shape to output shape
                rect_pred = warp(merge.T,
                                 tform.inverse,
                                 output_shape=(outShape[1], outShape[0]),
                                 mode='constant',
                                 cval=np.nan,
                                 clip=False,
                                 preserve_range=True)

                # Rotate 180 and flip
                # https://stackoverflow.com/questions/47930428/how-to-rotate-an-array-by-%C2%B1-180-in-an-efficient-way
                rect_pred = np.flip(np.flip(np.flip(rect_pred,1),0),1)#.astype('uint8')

            del merge

            # Stack #
            if 'out' not in locals():
                out = rect_pred
            else:
                out = np.dstack((out, rect_pred))

            del rect_pred

        # Reorder so band count is first
        out = np.rollaxis(out, axis=2)

        # Ensure output is right data type and nan's converted to no_data
        out = out.astype(data_type)
        # out = np.nan_to_num(out, nan=no_data)

        #########################
        # Export Rectified Raster
        # Set output name
        projName = os.path.split(self.port.projDir)[-1] # Get project name
        imgName = projName+'_'+imgOutPrefix+'_'+addZero+str(int(chunk))+'.tif'
        gtiff = os.path.join(self.outDir, imgName)

        if pix_res_map != 0:
            gtiff = gtiff.replace('.tif', 'temp.tif')

        # Export georectified image at raw resolution
        with rasterio.open(
            gtiff,
            'w',
            driver='GTiff',
            height=out.shape[1],
            width=out.shape[2],
            count=classes,
            dtype=out.dtype,
            crs=epsg,
            transform=transform,
            compress='lzw'
            ) as dst:
                dst.nodata=no_data
                dst.write(out)
                dst=None

        del out

        # Resize pixels if necessary                
        if pix_res_map != 0:
            self.port._pixresResize(gtiff, son=False)

        return



    #=======================================================================
    def _rectify(self, dat, chunk, imgOutPrefix, filt=50, wgs=False, return_rect=False):
        '''
        '''

        pix_res = self.port.pix_res_map

        # Get trackline/range extent file path
        portTrkMetaFile = os.path.join(self.port.metaDir, "Trackline_Smth_"+self.port.beamName+".csv")
        starTrkMetaFile = os.path.join(self.star.metaDir, "Trackline_Smth_"+self.star.beamName+".csv")

        # What coordinates should be used?
        ## Use WGS 1984 coordinates and set variables as needed
        if wgs is True:
            epsg = self.port.humDat['wgs']
            xRange = 'range_lons'
            yRange = 'range_lats'
            # xTrk = 'trk_lons'
            # yTrk = 'trk_lats'
        ## Use projected coordinates and set variables as needed
        else:
            epsg = self.port.humDat['epsg']
            xRange = 'range_es'
            yRange = 'range_ns'
            # xTrk = 'trk_utm_es'
            # yTrk = 'trk_utm_ns'

        # Determine leading zeros to match naming convention
        addZero = self.port._addZero(chunk)

        #################################
        # Prepare pixel (pix) coordinates
        ## Pix coordinates describe the size of the coordinates in pixels
        ## Coordinate Order
        ## top left of dat == port(range, 0)
        ## bot left of dat == star(range, 0)
        ## top next == port(range, 0+filt)
        ## bottom next == star(range, 0+filt)
        ## ....
        rows, cols = dat.shape # Determine number rows/cols
        pix_cols = np.arange(0, cols) # Create array of column indices
        pix_rows = np.linspace(0, rows, 2).astype('int') # Create array of two row indices (0 for points at ping origin, `rows` for max range)
        pix_rows, pix_cols = np.meshgrid(pix_rows, pix_cols) # Create grid arrays that we can stack together
        pixAll = np.dstack([pix_rows.flat, pix_cols.flat])[0] # Stack arrays to get final map of pix pixel coordinats [[row1, col1], [row2, col1], [row1, col2], [row2, col2]...]

        # Create mask for filtering array. This makes fitting PiecewiseAffineTransform
        ## more efficient
        mask = np.zeros(len(pixAll), dtype=bool) # Create mask same size as pixAll
        mask[0::filt] = 1 # Filter row coordinates
        mask[1::filt] = 1 # Filter column coordinates
        mask[-2], mask[-1] = 1, 1 # Make sure we keep last row/col coordinates

        # Filter pix
        pix = pixAll[mask]

        #######################################
        # Prepare destination (dst) coordinates
        ## Destination coordinates describe the geographic location in lat/lon
        ## or easting/northing that directly map to the pix coordinates.

        ###
        # Get top (port range) coordinates
        trkMeta = pd.read_csv(portTrkMetaFile)
        trkMeta = trkMeta[trkMeta['chunk_id']==chunk].reset_index(drop=False) # Filter df by chunk_id

        # Get range (outer extent) coordinates [xR, yR] to transposed numpy arrays
        xTop, yTop = trkMeta[xRange].to_numpy().T, trkMeta[yRange].to_numpy().T
        xyTop = np.vstack((xTop, yTop)).T # Stack the arrays

        ###
        # Get bottom (star range) coordinates
        trkMeta = pd.read_csv(starTrkMetaFile)
        trkMeta = trkMeta[trkMeta['chunk_id']==chunk].reset_index(drop=False) # Filter df by chunk_id

        # Get range (outer extent) coordinates [xR, yR] to transposed numpy arrays
        xBot, yBot = trkMeta[xRange].to_numpy().T, trkMeta[yRange].to_numpy().T
        xyBot = np.vstack((xBot, yBot)).T # Stack the arrays

        # Stack the coordinates (port[0,0], star[0,0], port[1,1]...) following
        ## pattern of pix coordinates
        dstAll = np.empty([len(xyTop)+len(xyBot), 2]) # Initialize appropriately sized np array
        dstAll[0::2] = xyTop # Add port range coordinates
        dstAll[1::2] = xyBot # Add star range coordinates

        # Filter dst using previously made mask
        dst = dstAll[mask]

        ##################
        ## Before applying a geographic projection to the image, the image
        ## must be warped to conform to the shape specified by the geographic
        ## coordinates.  We don't want to warp the image to real-world dimensions,
        ## so we will normalize and rescale the dst coordinates to give the
        ## top-left coordinate a value of (0,0)

        # Get pixel size
        pix_m = self.port.pixM

        # Determine min/max for rescaling
        xMin, xMax = dst[:,0].min(), dst[:,0].max() # Min/Max of x coordinates
        yMin, yMax = dst[:,1].min(), dst[:,1].max() # Min/Max of y coordinates

        # Determine output shape dimensions
        outShapeM = [xMax-xMin, yMax-yMin] # Calculate range of x,y coordinates
        outShape=[0,0]
        # Divide by pixel size to arrive at output shape of warped image
        outShape[0], outShape[1] = round(outShapeM[0]/pix_m,0), round(outShapeM[1]/pix_m,0)

        # Rescale destination coordinates
        # X values
        xStd = (dst[:,0]-xMin) / (xMax-xMin) # Standardize
        xScaled = xStd * (outShape[0] - 0) + 0 # Rescale to output shape
        dst[:,0] = xScaled # Store rescaled x coordinates

        # Y values
        yStd = (dst[:,1]-yMin) / (yMax-yMin) # Standardize
        yScaled = yStd * (outShape[1] - 0) + 0 # Rescale to output shape
        dst[:,1] = yScaled # Store rescaled y coordinates

        ########################
        # Perform transformation
        # PiecewiseAffineTransform
        # tform = PiecewiseAffineTransform()
        tform = FastPiecewiseAffineTransform()
        tform.estimate(pix, dst) # Calculate H matrix

        ##############
        # Save Geotiff
        ## In order to visualize the warped image in a GIS at the appropriate
        ## spatial extent, the pixel coordinates of the warped image must be
        ## mapped to spatial coordinates. This is accomplished by calculating
        ## the transformation matrix using rasterio.transform.from_origin

        # First get the min/max values for x,y geospatial coordinates
        xMin, xMax = dstAll[:,0].min(), dstAll[:,0].max()
        yMin, yMax = dstAll[:,1].min(), dstAll[:,1].max()

        # Calculate x,y resolution of a single pixel
        xres = (xMax - xMin) / outShape[0]
        yres = (yMax - yMin) / outShape[1]

        # Calculate transformation matrix by providing geographic coordinates
        ## of upper left corner of the image and the pixel size
        transform = from_origin(xMin - xres/2, yMax - yres/2, xres, yres)

        # Potential for warp speedup
        # https://stackoverflow.com/a/49901710
        # Warp image from the input shape to output shape
        out = warp(dat.T,
                   tform.inverse,
                   output_shape=(outShape[1], outShape[0]),
                   mode='constant',
                   cval=np.nan,
                   clip=False,
                   preserve_range=True)

        # Rotate 180 and flip
        # https://stackoverflow.com/questions/47930428/how-to-rotate-an-array-by-%C2%B1-180-in-an-efficient-way
        out = np.flip(np.flip(np.flip(out,1),0),1)#.astype('uint8')

        # Export geotiff or return rectified array
        if return_rect:
            return out, tform, outShape, epsg, transform

        else:

            min_size = int((out.shape[0] + out.shape[1])/2)

            # Set nan's to zero
            out = np.nan_to_num(out, nan=0)#.astype('uint8')

            # Label all regions
            lbl = label(out)

            # First set small objects to background value (0)
            noSmall = remove_small_objects(lbl, min_size)

            # Punch holes in original label
            holes = ~(noSmall==0)

            l = (out*holes).astype('uint8')

            del holes, lbl

            # Remove small holes
            # Convert l to binary
            binary_objects = l.astype(bool)
            # Remove the holes
            binary_filled = remove_small_holes(binary_objects, min_size+100)
            # Recover classification with holes filled
            out = watershed(binary_filled, l, mask=binary_filled)

            out = out.astype('uint8')
            del binary_filled, binary_objects, l

            # Prepare colors
            class_colormap = {0: '#3366CC',
                              1: '#DC3912',
                              2: '#FF9900',
                              3: '#109618',
                              4: '#990099', 
                              5: '#0099C6',
                              6: '#DD4477',
                              7: '#66AA00',
                              8: '#B82E2E'}
            
            for k, v in class_colormap.items():
                rgb = ImageColor.getcolor(v, 'RGB')
                class_colormap[k] = rgb

            #########################
            # Export Rectified Raster
            # Set output name
            projName = os.path.split(self.port.projDir)[-1] # Get project name
            imgName = projName+'_'+imgOutPrefix+'_'+addZero+str(int(chunk))+'.tif'
            gtiff = os.path.join(self.outDir, imgName)

            if pix_res != 0:
                gtiff = gtiff.replace('.tif', 'temp.tif')

            # Export georectified image
            with rasterio.open(
                gtiff,
                'w',
                driver='GTiff',
                height=out.shape[0],
                width=out.shape[1],
                count=1,
                dtype=out.dtype,
                crs=epsg,
                transform=transform,
                compress='lzw'
                ) as dst:
                    dst.nodata=0
                    dst.write(out,1)
                    dst.write_colormap(1, class_colormap)
                    dst=None

            del out

            if pix_res != 0:
                self.port._pixresResize(gtiff, son=False)

            gc.collect()

            return


    #=======================================================================
    def _rasterToPoly(self, mosaic, threadCnt, mosaic_nchunk):
        '''
        '''

        # if mosaic != 2:
        print("\n\tCreating vrt...")
        self._createMosaic(mosaic=2, overview=False, threadCnt=threadCnt, son=False, maxChunk=mosaic_nchunk)

        inDir = os.path.join(self.port.substrateDir, 'map_substrate_mosaic')
        rasterFiles = glob(os.path.join(inDir, '*map_sub*vrt'))

        outDir = os.path.join(self.port.substrateDir, 'map_substrate_polygon')

        if not os.path.exists(outDir):
            os.mkdir(outDir)

        print("\n\tExporting to shapefile...")
        _ = Parallel(n_jobs= np.min([len(rasterFiles), threadCnt]), verbose=10)(delayed(self._createPolygon)(f, outDir) for f in rasterFiles)

        return

    #=======================================================================
    def _createPolygon(self, f, outDir):
        '''
        '''
        # Get class names from json
        # Open model configuration file
        with open(self.port.configfile) as file:
            config = json.load(file)
        globals().update(config)

        # https://gis.stackexchange.com/questions/340284/converting-raster-pixels-to-polygons-with-gdal-python
        # Open raster
        src_ds = gdal.Open(f)


        ####################
        # Polygon Conversion
        # Set spatial reference
        srs = osr.SpatialReference()
        srs.ImportFromWkt(src_ds.GetProjection())

        # Prepare layerfile
        dst_layername = os.path.basename(f).replace('.vrt', '')
        dst_layername = dst_layername.replace('_raster_mosaic', '')
        dst_layername = os.path.join(outDir, dst_layername)

        srcband = src_ds.GetRasterBand(1)
        drv = ogr.GetDriverByName("ESRI Shapefile")
        dst_ds = drv.CreateDataSource(dst_layername+'.shp')
        dst_layer = dst_ds.CreateLayer(dst_layername, srs = srs, geom_type=ogr.wkbMultiPolygon)
        newField = ogr.FieldDefn('Substrate', ogr.OFTReal)
        dst_layer.CreateField(newField)
        gdal.Polygonize(srcband, None, dst_layer, 0, [], callback=None)

        # Set substrate name
        newField = ogr.FieldDefn('Name', ogr.OFTString)
        newField.SetWidth(20)
        dst_layer.CreateField(newField)

        for feature in dst_layer:
            subID = str(int(feature.GetField('Substrate')))
            subName = MY_CLASS_NAMES[subID]
            feature.SetField('Name', subName)
            dst_layer.SetFeature(feature)

        # Calculate Area
        # https://gis.stackexchange.com/questions/169186/calculate-area-of-polygons-using-ogr-in-python-script
        # Create field to store area
        newField = ogr.FieldDefn('Area_m', ogr.OFTReal)
        newField.SetWidth(32)
        newField.SetPrecision(2)
        dst_layer.CreateField(newField)

        # Calculate Area
        for feature in dst_layer:
            geom = feature.GetGeometryRef()
            area = geom.GetArea()
            feature.SetField("Area_m", area)
            dst_layer.SetFeature(feature)

        # Delete NoData Polygon
        # https://gis.stackexchange.com/questions/254444/deleting-selected-features-from-vector-ogr-in-gdal-python
        layer = dst_ds.GetLayer()
        layer.SetAttributeFilter("Substrate = 0")

        for feat in layer:
            layer.DeleteFeature(feat.GetFID())


        dst_ds.SyncToDisk()
        dst_ds=None

        return
    
    #=======================================================================
    def _exportBanklines(self, threadCnt):
        '''
        '''

        # print("\n\tCreating vrt...")
        # self._createMosaic(mosaic=2, overview=False, threadCnt=threadCnt, son=True, maxChunk=mosaic_nchunk)

        # inDir = os.path.join(self.port.projDir, 'sonar_mosaic')
        # rasterFiles = glob(os.path.join(inDir, '*mosaic*tif'))

        if self.port.rect_wcr:
            inDirPort = os.path.join(self.port.projDir, self.port.beamName, 'rect_wcr')
            inDirStar = os.path.join(self.star.projDir, self.star.beamName, 'rect_wcr')
        else:
            inDirPort = os.path.join(self.port.projDir, self.beamName, 'rect_wcp')
            inDirStar = os.path.join(self.star.projDir, self.beamName, 'rect_wcp')

        portFiles = glob(os.path.join(inDirPort, '*.tif'))
        starFiles = glob(os.path.join(inDirStar, '*.tif'))

        rasterFiles = portFiles + starFiles

        outDir = os.path.join(self.port.projDir, 'banklines')

        if not os.path.exists(outDir):
            os.mkdir(outDir)

        print("\n\tExporting to shapefile...")
        # r = Parallel(n_jobs= np.min([len(rasterFiles), threadCnt]), verbose=10)(delayed(self._createBanklinePolygon)(f, outDir) for f in rasterFiles)
        r = []
        for f in rasterFiles:
            ds = self._createBanklinePolygon(f, outDir)
            r.append(ds)


        for ds in r:

            if not 'outDS' in locals():
                outDS = ds
            else:
                outDS = pd.concat([outDS, ds], ignore_index=True)

        # Dissolve
        outDS['geometry'] = outDS.simplify(0.1)
        outDS['geometry'] = outDS.buffer(0.1, join_style=2)
        outDS = outDS.dissolve()
        outDS['geometry'] = outDS.buffer(-0.1, join_style=2)

        # Save
        projName = os.path.split(self.port.projDir)[-1] 
        fileName = projName + '_bankline.shp'
        fileName = os.path.join(outDir, fileName)

        outDS.to_file(fileName, index=False)

        outDS = None

        return



    #=======================================================================
    def _createBanklinePolygon(self, f, outDir):

        # https://gis.stackexchange.com/questions/340284/converting-raster-pixels-to-polygons-with-gdal-python
        # Open raster
        src_ds = gdal.Open(f)

        ####################
        # Polygon Conversion
        # Set spatial reference
        srs = osr.SpatialReference()
        srs.ImportFromWkt(src_ds.GetProjection())

        # Prepare layerfile
        dst_layername = os.path.basename(f).replace('.tif', '')
        # dst_layername = dst_layername.replace('rect_wcr_mosaic', 'bankline')
        dst_layername = dst_layername.replace('rect_wcr', 'bankline')
        dst_layername = os.path.join(outDir, dst_layername)

        # Get raster data and reclass
        srcband = src_ds.GetRasterBand(1)
        # mask = np.where(srcband.ReadAsArray()>0, 254, 0)
        mask = np.where(srcband.ReadAsArray()>0, 1, 0)
        del srcband

        tmp_ds = gdal.GetDriverByName('MEM').CreateCopy('', src_ds, 0)
        tmp_ds.GetRasterBand(1).WriteArray(mask)
        t = tmp_ds.GetRasterBand(1).ReadAsArray()
        temp = os.path.join(os.path.dirname(dst_layername), 'temp.tif')
        dst_ds1 = gdal.GetDriverByName('GTiff').CreateCopy(temp, tmp_ds, 0)
        srcband = dst_ds1.GetRasterBand(1)

        drv = ogr.GetDriverByName("ESRI Shapefile")
        dst_ds = drv.CreateDataSource(dst_layername+'temp.shp')
        dst_layer = dst_ds.CreateLayer(dst_layername, srs = srs, geom_type=ogr.wkbMultiPolygon)

        # Try storing pixel value in field
        fd = ogr.FieldDefn("Value", ogr.OFTInteger)
        dst_layer.CreateField(fd)
        dst_field = dst_layer.GetLayerDefn().GetFieldIndex('Value')

        # Create Polygon
        # gdal.Polygonize(srcband, None, dst_layer, 0, [], callback=None)
        gdal.Polygonize(srcband, None, dst_layer, dst_field, [], callback=None)

        # # Delete NoData poly (last feature)
        # ft_cnt = dst_layer.GetFeatureCount()-1
        # layer = dst_ds.GetLayer()
        # layer.SetAttributeFilter("FID = {}".format(ft_cnt))

        # Delete NoData poly (Value = 0)
        layer = dst_ds.GetLayer()
        layer.SetAttributeFilter("Value = 0")

        for feat in layer:
            layer.DeleteFeature(feat.GetFID())

        dst_ds.SyncToDisk()
        dst_ds=None
        dst_ds1=None
        tmp_ds=None
        src_ds=None
        temp=None

        # Open in geopandas
        ds = gpd.read_file(dst_layername+'temp.shp')
        # Dissolve all polygons
        ds = ds.dissolve()
        # # Save
        # ds.to_file(dst_layername+'.shp', index=False)

        # Delete temp files
        outDir = os.path.join(self.port.projDir, 'banklines')
        tempFiles = glob(os.path.join(outDir, '*temp*'))

        for f in tempFiles:
            try:
                os.remove(f)
            except:
                pass


        return ds


    #=======================================================================
    def _cleanup(self):
        '''
        Clean up any unneeded variables.
        '''
        try:
            del self.bedpickModel
        except:
            pass

        try:
            del self.port.sonDat, self.star.sonDat
        except:
            pass

        try:
            del self.port.sonMetaDF, self.star.sonMetaDF
        except:
            pass

        try:
            del self.starDepDetect, self.portDepDetect
        except:
            pass

        gc.collect()
        return #self

    # ======================================================================
    def __str__(self):
        '''
        Generic print function to print contents of sonObj.
        '''
        output = "portstarObj Contents"
        output += '\n\t'
        output += self.__repr__()
        temp = vars(self)
        for item in temp:
            output += '\n\t'
            output += "{} : {}".format(item, temp[item])
        return output