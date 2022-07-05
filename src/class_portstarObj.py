# Part of PING-Mapper software
#
# Co-Developed by Cameron S. Bodine and Dr. Daniel Buscombe
#
# Inspired by PyHum: https://github.com/dbuscombe-usgs/PyHum
#
# MIT License
#
# Copyright (c) 2022 Cameron S. Bodine
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


from funcs_common import *
from funcs_bedpick import *

import gdal
from scipy.signal import savgol_filter

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

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
        self.port._getScanChunkSingle(i)
        self.star._getScanChunkSingle(i)

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
        return self

    ############################################################################
    # Mosaic                                                                   #
    ############################################################################

    #=======================================================================
    def _createMosaic(self,
                      mosaic=1,
                      overview=True):
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
        maxChunk = 100 # Max chunks per mosaic. Limits each mosaic file size.
        self.imgsToMosaic = [] # List to store files to mosaic.

        if self.port.rect_wcp: # Moscaic wcp sonograms if previousl exported
            # Locate port files
            portPath = os.path.join(self.port.outDir, 'rect_wcp')
            port = sorted(glob(os.path.join(portPath, '*.tif')))

            # Locate starboard files
            starPath = os.path.join(self.star.outDir, 'rect_wcp')
            star = sorted(glob(os.path.join(starPath, '*.tif')))

            # Make multiple mosaics if number of input sonograms is greater than maxChunk
            if len(port) > maxChunk:
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
            if len(port) > maxChunk:
                port = [port[i:i+maxChunk] for i in range(0, len(port), maxChunk)]
                star = [star[i:i+maxChunk] for i in range(0, len(star), maxChunk)]
                srcToMosaic = [list(itertools.chain(*i)) for i in zip(port, star)]
            else:
                srcToMosaic = [port + star]

        # Create geotiff
        if mosaic == 1:
            if self.port.rect_wcp:
                self._mosaicGtiff(wcpToMosaic, overview)
            if self.port.rect_wcr:
                self._mosaicGtiff(srcToMosaic, overview)
        # Create vrt
        elif mosaic == 2:
            if self.port.rect_wcp:
                self._mosaicVRT(wcpToMosaic, overview)
            if self.port.rect_wcr:
                self._mosaicVRT(srcToMosaic, overview)
        return self


    #=======================================================================
    def _mosaicGtiff(self,
                     imgsToMosaic,
                     overview=True):
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
        i = 0 # Mosaic number
        # Iterate each sublist of images
        for imgs in imgsToMosaic:

            # Set output file names
            filePrefix = os.path.split(self.port.projDir)[-1]
            fileSuffix = os.path.split(os.path.dirname(imgs[0]))[-1] + '_mosaic_'+str(i)+'.vrt'
            outVRT = os.path.join(self.port.projDir, filePrefix+'_'+fileSuffix)
            outTIF = outVRT.replace('.vrt', '.tif')

            # First built a vrt
            vrt_options = gdal.BuildVRTOptions(resampleAlg='nearest')
            gdal.BuildVRT(outVRT, imgs, options=vrt_options)

            # Create GeoTiff from vrt
            ds = gdal.Open(outVRT)

            kwargs = {'format': 'GTiff',
                      'creationOptions': ['NUM_THREADS=ALL_CPUS', 'COMPRESS=LZW']
                      }
            gdal.Translate(outTIF, ds, **kwargs)

            # Generate overviews
            if overview:
                dest = gdal.Open(outTIF, 1)
                gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
                dest.BuildOverviews('nearest', [2 ** j for j in range(1,10)])

            os.remove(outVRT) # Remove vrt
            i+=1 # Iterate mosaic number

        return self

    #=======================================================================
    def _mosaicVRT(self,
                   imgsToMosaic,
                   overview=True):
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
        i = 0 # Mosaic number
        # Iterate each sublist of images
        for imgs in imgsToMosaic:

            # Set output file names
            filePrefix = os.path.split(self.port.projDir)[-1]
            fileSuffix = os.path.split(os.path.dirname(imgs[0]))[-1] + '_mosaic_'+str(i)+'.vrt'
            outFile = os.path.join(self.port.projDir, filePrefix+'_'+fileSuffix)

            # Build VRT
            vrt_options = gdal.BuildVRTOptions(resampleAlg='nearest')
            gdal.BuildVRT(outFile, imgs, options=vrt_options)

            # Generate overviews
            if overview:
                dest = gdal.Open(outFile)
                gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
                dest.BuildOverviews('nearest', [2 ** j for j in range(1,10)])
            i+=1
        return self

    ############################################################################
    # Bedpicking                                                               #
    ############################################################################

    #=======================================================================
    def _detectDepth(self,
                     method,
                     i,
                     USE_GPU):
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

        if method == 1:
            if not hasattr(self, 'bedpickModel'):
                self._initModel(USE_GPU)
            portDepPixCrop, starDepPixCrop, i = self._depthZheng(i)
        elif method == 2:
            self.port._loadSonMeta()
            self.star._loadSonMeta()
            portDepPixCrop, starDepPixCrop, i = self._depthThreshold(i)

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
    def _initModel(self,
                   USE_GPU=False):
        '''
        Compiles a Tensorflow model for bedpicking. Developed following:
        https://github.com/Doodleverse/segmentation_gym

        ----------
        Parameters
        ----------
        None

        ----------------------------
        Required Pre-processing step
        ----------------------------
        self.__init__()

        -------
        Returns
        -------
        self.bedpickModel containing compiled model.

        --------------------
        Next Processing Step
        --------------------
        self._detectDepth()
        '''
        SEED=42
        np.random.seed(SEED)
        AUTO = tf.data.experimental.AUTOTUNE # used in tf.data.Dataset API

        tf.random.set_seed(SEED)

        if USE_GPU == True:
            os.environ['CUDA_VISIBLE_DEVICES'] = '0' # Use GPU
        else:

            os.environ['CUDA_VISIBLE_DEVICES'] = '-1' # Use CPU

        #suppress tensorflow warnings
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

        # Open model configuration file
        with open(self.configfile) as f:
            config = json.load(f)

        globals().update(config)

        model =  custom_resunet((TARGET_SIZE[0], TARGET_SIZE[1], N_DATA_BANDS),
                        FILTERS,
                        nclasses=[NCLASSES+1 if NCLASSES==1 else NCLASSES][0],
                        kernel_size=(KERNEL,KERNEL),
                        strides=STRIDE,
                        dropout=DROPOUT,#0.1,
                        dropout_change_per_layer=DROPOUT_CHANGE_PER_LAYER,#0.0,
                        dropout_type=DROPOUT_TYPE,#"standard",
                        use_dropout_on_upsampling=USE_DROPOUT_ON_UPSAMPLING,#False,
                        )

        model.compile(optimizer = 'adam', loss = dice_coef_loss, metrics = [mean_iou, dice_coef])
        model.load_weights(self.weights)

        self.bedpickModel = model

        return self

    #=======================================================================
    def _doPredict(self,
                   model,
                   arr):
        '''
        Predict the bed location from an input array of sonogram pixels. Workflow
        follows prediction routine from https://github.com/Doodleverse/segmentation_gym.

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
            image, w, h, bigimage = seg_file2tensor_3band(arr, TARGET_SIZE)

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
        del e0, e1

        # Ping by ping thresholding
        # for p in range(w):
        #     thres = threshold_otsu(est_label[p,:])
        #     est_label[p,:] = (est_label[p,:]>thres).astype('uint8')

        # Threshold entire label
        thres = threshold_otsu(est_label)

        est_prob = est_label.copy()
        est_label = (est_label>thres).astype('uint8')

        return est_label, est_prob

    #=======================================================================
    def _filtPredict(self,
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
    # Really really good, but maybe do better????
    def _depthZheng_OrthodoxCrop(self,i):
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
        plotInitPicks = True

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
        del mergeSon

        # Stack the bands
        son3bnd = np.dstack((b1, b2, b3)).astype(np.uint8)
        del b1, b2, b3

        N = son3bnd.shape[1] # Number of samples per ping (width of non-resized sonogram)
        W = TARGET_SIZE[1] # Width of model output prediction
        C = int(N/2) # Center of sonogram

        ##########################################
        # Do initial prediction on entire sonogram
        init_label, init_prob = self._doPredict(model, son3bnd)

        ######################################
        # Filters for removing small artifacts
        if doFilt:
            init_label = self._filtPredict(init_label, N)

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

        # # Find ping-wise water column width from avg depth prediction
        # Wp = avgDepths*2

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
        # Ws = int( C - (Wwc/2) - (maxDep/2) - WsBuf)
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
        # crop_label = self._doPredict(model, sonCrop)
        crop_label, crop_prob = self._doPredict(model, sonCrop)

        ######################################
        # Filters for removing small artifacts
        if doFilt:
            crop_label = self._filtPredict(crop_label, N)

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

                else: # Final pick ok
                    star.append(sdc)


            # # Interpolation????
            # bed = np.array(bed).astype(np.float32)
            #
            # # Interpolate over nan's
            # nans, x = np.isnan(bed), lambda z: z.nonzero()[0]
            # bed[nans] = np.interp(x(nans), x(~nans), bed[~nans])
            # bed = bed.astype(int)

            portDepPixFinal = port
            starDepPixFinal = star

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
            imsave(os.path.join(self.port.projDir, str(i)+"_initLabel_"+str(i)+".png"), (color_label).astype(np.uint8), check_contrast=False)
            imsave(os.path.join(self.port.projDir, str(i)+"_initImg_"+str(i)+".png"), (son3bnd).astype(np.uint8), check_contrast=False)

            # Cropped
            color_label = label_to_colors(crop_label, sonCrop[:,:,0]==0, alpha=128, colormap=class_label_colormap, color_class_offset=0, do_alpha=False)
            imsave(os.path.join(self.port.projDir, str(i)+"_cropLabel_"+str(i)+".png"), (color_label).astype(np.uint8), check_contrast=False)
            imsave(os.path.join(self.port.projDir, str(i)+"_cropImg_"+str(i)+".png"), (sonCrop).astype(np.uint8), check_contrast=False)


        del son3bnd, init_label, crop_label, sonCrop
        # return self
        return portDepPixFinal, starDepPixFinal, i


    # Really really good, but maybe do better????
    def _depthZheng(self,i):
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
        del mergeSon

        # Stack the bands
        son3bnd = np.dstack((b1, b2, b3)).astype(np.uint8)
        del b1, b2, b3

        N = son3bnd.shape[1] # Number of samples per ping (width of non-resized sonogram)
        W = TARGET_SIZE[1] # Width of model output prediction
        C = int(N/2) # Center of sonogram

        ##########################################
        # Do initial prediction on entire sonogram
        init_label, init_prob = self._doPredict(model, son3bnd)

        ######################################
        # Filters for removing small artifacts
        if doFilt:
            init_label = self._filtPredict(init_label, N)

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

        # # Find ping-wise water column width from avg depth prediction
        # Wp = avgDepths*2

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
        # crop_label = self._doPredict(model, sonCrop)
        crop_label, crop_prob = self._doPredict(model, sonCrop)

        ######################################
        # Filters for removing small artifacts
        if doFilt:
            crop_label = self._filtPredict(crop_label, N)

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

                else: # Final pick ok
                    star.append(sdc)


            # # Interpolation????
            # bed = np.array(bed).astype(np.float32)
            #
            # # Interpolate over nan's
            # nans, x = np.isnan(bed), lambda z: z.nonzero()[0]
            # bed[nans] = np.interp(x(nans), x(~nans), bed[~nans])
            # bed = bed.astype(int)

            portDepPixFinal = port
            starDepPixFinal = star

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
            imsave(os.path.join(self.port.projDir, str(i)+"_initLabel_"+str(i)+".png"), (color_label).astype(np.uint8), check_contrast=False)
            imsave(os.path.join(self.port.projDir, str(i)+"_initImg_"+str(i)+".png"), (son3bnd).astype(np.uint8), check_contrast=False)

            # Cropped
            color_label = label_to_colors(crop_label, sonCrop[:,:,0]==0, alpha=128, colormap=class_label_colormap, color_class_offset=0, do_alpha=False)
            imsave(os.path.join(self.port.projDir, str(i)+"_cropLabel_"+str(i)+".png"), (color_label).astype(np.uint8), check_contrast=False)
            imsave(os.path.join(self.port.projDir, str(i)+"_cropImg_"+str(i)+".png"), (sonCrop).astype(np.uint8), check_contrast=False)


        del son3bnd, init_label, crop_label, sonCrop
        # return self
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
            acousticBed = round(sonMeta['inst_dep_m'] / sonMeta['pix_m'], 0).astype(int)

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

        # return self
        return portDepPixCrop, starDepPixCrop, chunk

    #=======================================================================
    def _saveDepth(self,
                   chunks,
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

        if detectDep == 0:
            portInstDepth = portDF['inst_dep_m']
            starInstDepth = starDF['inst_dep_m']

            if smthDep:
                # print("\nSmoothing depth values...")
                portInstDepth = savgol_filter(portInstDepth, 51, 3)
                starInstDepth = savgol_filter(starInstDepth, 51, 3)

            if adjDep != 0:
                # print("\tIncreasing/Decreasing depth values by {} meters...".format(adjBy))
                adjBy = portDF['pix_m'][0]*adjDep
                portInstDepth += adjBy
                starInstDepth += adjBy

            portDF['dep_m'] = portInstDepth
            starDF['dep_m'] = starInstDepth

            portDF['dep_m_Method'] = 'Instrument Depth'
            starDF['dep_m_Method'] = 'Instrument Depth'

            portDF['dep_m_smth'] = smthDep
            starDF['dep_m_smth'] = smthDep

            portDF['dep_m_adjBy'] = str(adjDep) + ' pixels'
            starDF['dep_m_adjBy'] = str(adjDep) + ' pixels'

        elif detectDep > 0:
            # Prepare depth detection dictionaries
            portFinal = []
            starFinal = []
            for i in sorted(chunks):
                portDep = self.portDepDetect[i]
                starDep = self.starDepDetect[i]

                portFinal.extend(portDep)
                starFinal.extend(starDep)

            # Check shapes to ensure they are same length.  If not, slice off extra.
            if len(portFinal) > portDF.shape[0]:
                lenDif = portDF.shape[0] - len(portFinal)
                portFinal = portFinal[:lenDif]

            if len(starFinal) > starDF.shape[0]:
                lenDif = starDF.shape[0] - len(starFinal)
                starFinal = starFinal[:lenDif]

            # # Check for bad picks (i.e. depth==0) for each sonar channel. If one
            # ## channel is 0 and other is non-zero, use non-zero estimate for both.
            # for i, ps in enumerate(zip(portFinal, starFinal)):
            #     pValid = False
            #     sValid = False
            #     if ps[0] > 0:
            #         pValid = True
            #     if ps[1] > 0:
            #         sValid = True
            #
            #     # Both > 0
            #     if pValid and sValid:
            #         pass
            #     # Both <= 0
            #     elif not pValid and not sValid:
            #         portFinal[i]=np.nan
            #         starFinal[i]=np.nan
            #     # Port > 0, update star
            #     elif pValid:
            #         starFinal[i] = portFinal[i]
            #     # Star > 0, update port
            #     else:
            #         portFinal[i] = starFinal[i]


            if smthDep:
                portFinal = savgol_filter(portFinal, 51, 3)
                starFinal = savgol_filter(starFinal, 51, 3)

            portDF['dep_m'] = portFinal * portDF['pix_m']
            starDF['dep_m'] = starFinal * starDF['pix_m']

            if adjDep != 0:
                adjBy = portDF['pix_m'][0]*adjDep
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

            portDF['dep_m_adjBy'] = str(adjDep) + ' pixels'
            starDF['dep_m_adjBy'] = str(adjDep) + ' pixels'

        # Export to csv
        portDF.to_csv(self.port.sonMetaFile, index=False, float_format='%.14f')
        starDF.to_csv(self.star.sonMetaFile, index=False, float_format='%.14f')

        del portDF, starDF
        return self

    #=======================================================================
    def _plotBedPick(self,
                     i,
                     acousticBed=True,
                     autoBed = True):

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
        portDF = portDF.loc[portDF['chunk_id'] == i, ['inst_dep_m', 'dep_m', 'pix_m']]

        self.star._loadSonMeta()
        starDF = self.star.sonMetaDF
        starDF = starDF.loc[starDF['chunk_id'] == i, ['inst_dep_m', 'dep_m', 'pix_m']]

        # Convert depth in meters to pixels
        portInst = (portDF['inst_dep_m'] / portDF['pix_m']).to_numpy(dtype=np.int, copy=True)
        portAuto = (portDF['dep_m'] / portDF['pix_m']).to_numpy(dtype=np.int, copy=True)

        starInst = (starDF['inst_dep_m'] / starDF['pix_m']).to_numpy(dtype=np.int, copy=True)
        starAuto = (starDF['dep_m'] / starDF['pix_m']).to_numpy(dtype=np.int, copy=True)

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
            # os.mkdir(os.path.join(outDir, '00_Bad'))
        except:
            pass

        # projName = os.path.split(outDir)[-1]
        projName = os.path.split(self.port.projDir)[-1]
        outFile = os.path.join(outDir, projName+'_Bedpick_'+addZero+str(i)+'.png')

        plt.imshow(mergeSon, cmap='gray')
        if acousticBed:
            plt.plot(portInst, y, 'y-.', lw=1, label='Acoustic Depth')
            plt.plot(starInst, y, 'y-.', lw=1)
        if autoBed:
            plt.plot(portAuto, y, 'b-.', lw=1, label='Auto Depth')
            plt.plot(starAuto, y, 'b-.', lw=1)

        plt.legend(loc = 'lower right', prop={'size':4}) # create the plot legend
        plt.savefig(outFile, dpi=300, bbox_inches='tight')
        plt.close()

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

        return self
