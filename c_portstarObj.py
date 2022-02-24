from funcs_common import *
from funcs_bedpick import *
# from rasterio.merge import merge
# from rasterio.enums import Resampling
import gdal

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

class portstarObj(object):
    '''

    '''
    #=======================================================================
    def __init__(self, objs):
        '''
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
    def _getPortStarScanChunk(self, i):
        # Load sonar intensity into memory
        self.port._getScanChunkSingle(i)
        self.star._getScanChunkSingle(i)

        # Rotate and merge arrays into one
        # Rotate
        portSon = np.rot90(self.port.sonDat, k=1, axes=(1,0))
        portSon = np.flipud(portSon)
        starSon = np.rot90(self.star.sonDat, k=1, axes=(0,1))

        # Concatenate arrays column-wise
        mergeSon = np.concatenate((portSon, starSon), axis = 1)
        del self.port.sonDat, self.star.sonDat

        self.mergeSon = mergeSon
        return self

    ############################################################################
    # Mosaic                                                                   #
    ############################################################################

    #=======================================================================
    def _createMosaic(self, mosaic, overview):
        self.imgsToMosaic = []
        imgDirs = [self.port.outDir, self.star.outDir]

        if self.port.rect_wcp:
            wrcToMosaic = []
            for path in imgDirs:
                path = os.path.join(path, 'rect_wcp')
                imgs = glob(os.path.join(path, '*.tif'))
                for img in imgs:
                    wrcToMosaic.append(img)
            self.imgsToMosaic.append(wrcToMosaic)

        if self.port.rect_src:
            srcToMosaic = []
            for path in imgDirs:
                path = os.path.join(path, 'rect_src')
                imgs = glob(os.path.join(path, '*.tif'))
                for img in imgs:
                    srcToMosaic.append(img)
            self.imgsToMosaic.append(srcToMosaic)

        if mosaic == 1:
            self._mosaicGtiff(overview)
        elif mosaic == 2:
            self._mosaicVRT(overview)


    #=======================================================================
    def _mosaicGtiff(self, overview):
        for imgs in self.imgsToMosaic:

            filePrefix = os.path.split(self.port.projDir)[-1]
            fileSuffix = os.path.split(os.path.dirname(imgs[0]))[-1] + '_mosaic.vrt'
            outVRT = os.path.join(self.port.projDir, filePrefix+'_'+fileSuffix)
            outTIF = outVRT.replace('.vrt', '.tif')

            vrt_options = gdal.BuildVRTOptions(resampleAlg='nearest')
            gdal.BuildVRT(outVRT, imgs, options=vrt_options)

            ds = gdal.Open(outVRT)

            kwargs = {'format': 'GTiff',
                      'creationOptions': ['NUM_THREADS=ALL_CPUS', 'COMPRESS=LZW']
                      }
            gdal.Translate(outTIF, ds, **kwargs)
            if overview:
                dest = gdal.Open(outTIF, 1)
                gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
                dest.BuildOverviews('nearest', [2 ** j for j in range(1,10)])

            os.remove(outVRT)

        return self

    #=======================================================================
    def _mosaicVRT(self, overview):
        for imgs in self.imgsToMosaic:

            filePrefix = os.path.split(self.port.projDir)[-1]
            fileSuffix = os.path.split(os.path.dirname(imgs[0]))[-1] + '_mosaic.vrt'
            outFile = os.path.join(self.port.projDir, filePrefix+'_'+fileSuffix)

            vrt_options = gdal.BuildVRTOptions(resampleAlg='nearest')
            gdal.BuildVRT(outFile, imgs, options=vrt_options)

            if overview:
                dest = gdal.Open(outFile)
                gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
                dest.BuildOverviews('nearest', [2 ** j for j in range(1,10)])

    ############################################################################
    # Bedpicking                                                               #
    ############################################################################

    #=======================================================================
    def _findBed(self, segArr):
        '''
        Find bed location in pixels
        '''
        # Find center of array
        H, W = segArr.shape[0], segArr.shape[1] # height (row), width (column)
        C = int(W/2) # center of array

        # Find bed location
        portBed = []
        starBed = []
        for k in range(H):
            pB = np.where(segArr[k, 0:C]==1)[0][-1]
            # pB = np.min(np.where(segArr[k, 0:C]==0)[0])
            portBed.append(C-pB)

            sB = np.where(segArr[k, C:]==1)[0][0]
            # sB = np.max(np.where(segArr[k, C:]==0)[0])
            starBed.append(sB)

        # print(portBed)
        return portBed, starBed

    #=======================================================================
    def _initModel(self):
        '''

        '''
        # Dictionary to store chunk : np.array(depth estimate)
        self.portDepDetect = {}
        self.starDepDetect = {}

        # SEED=42
        # np.random.seed(SEED)
        # AUTO = tf.data.experimental.AUTOTUNE # used in tf.data.Dataset API
        #
        # tf.random.set_seed(SEED)
        #
        # print("Version: ", tf.__version__)
        # print("Eager mode: ", tf.executing_eagerly())
        # print('GPU name: ', tf.config.experimental.list_physical_devices('GPU'))
        # print("Num GPUs Available: ", len(tf.config.experimental.list_physical_devices('GPU')))

        USE_GPU = True

        if USE_GPU == True:
           ##use the first available GPU
           os.environ['CUDA_VISIBLE_DEVICES'] = '0' #'1'
        else:
           ## to use the CPU (not recommended):
           os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

        #suppress tensorflow warnings
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

        # Open model configuration file
        with open(self.configfile) as f:
            config = json.load(f)

        globals().update(config)

        # for k in config.keys():
        #     exec(k+'=config["'+k+'"]')

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
    def _detectDepth(self, method, i):
        '''
        '''
        # # Load sonar intensity into memory
        # self.port._getScanChunkSingle(i)
        # self.star._getScanChunkSingle(i)

        if method == 1:
            self._depthZheng(i)

    #=======================================================================
    def _doPredict(self, model, arr):
        # Read array into a cropped and resized tensor
        ## Compression step from Zheng et al. 2021
        if N_DATA_BANDS<=3:
            image, w, h, bigimage = seg_file2tensor_3band(arr, TARGET_SIZE)
        # else:
        #     image, w, h, bigimage = seg_file2tensor_ND(f, TARGET_SIZE)

        # Standardize
        image = standardize(image.numpy()).squeeze()

        # Do segmentation on compressed sonogram
        est_label = model.predict(tf.expand_dims(image, 0), batch_size=1).squeeze()

        # Up-sample / rescale to original dimensions
        ## Store prediction for water and bed classes after resize
        E0 = []; E1 = [];

        E0.append(resize(est_label[:,:,0],(w,h), preserve_range=True, clip=True))
        E1.append(resize(est_label[:,:,1],(w,h), preserve_range=True, clip=True))
        del est_label

        e0 = np.average(np.dstack(E0), axis=-1)
        e1 = np.average(np.dstack(E1), axis=-1)
        del E0, E1

        est_label = (e1+(1-e0))/2
        del e0, e1

        thres = threshold_otsu(est_label)

        est_label = (est_label>thres).astype('uint8')

        return est_label

    #=======================================================================
    def _depthZheng(self, i):
        doFilt = False
        model = self.bedpickModel
        print("Chunk:",i)

        ###########################
        # Prepare sonar intensities

        # # Rotate and merge arrays into one
        # # Rotate
        # portSon = np.rot90(self.port.sonDat, k=1, axes=(1,0))
        # portSon = np.flipud(portSon)
        # starSon = np.rot90(self.star.sonDat, k=1, axes=(0,1))
        #
        # # Concatenate arrays column-wise
        # mergeSon = np.concatenate((portSon, starSon), axis = 1)
        # del self.port.sonDat, self.star.sonDat

        self._getPortStarScanChunk(i)
        mergeSon = self.mergeSon
        # Make 3-band array
        b1 = mergeSon.copy()
        b2 = np.fliplr(b1.copy())
        b3 = np.mean([b1,b2], axis=0)
        # b3 = (b1+b2)/2 # Had strange results when making 3-band from existing rasters
        del mergeSon

        son3bnd = np.dstack((b1, b2, b3)).astype(np.uint8)
        del b1, b2, b3

        ##########################################
        # Do initial prediction on entire sonogram
        init_label = self._doPredict(model, son3bnd)

        ############################
        # Find pixel location of bed
        portDepPix, starDepPix = self._findBed(init_label)

        ##################################
        # Crop image using initial bedpick
        ## Zheng et al. 2021 method
        ## Once cropped, sonogram is closer in size to model TARGET_SIZE, so
        ## any errors introduced after rescaling prediction will be minimized.

        N = son3bnd.shape[1] # Number of samples per ping (width of non-resized sonogram)
        W = TARGET_SIZE[1] # Width of model output prediction
        Wp = np.add(portDepPix, starDepPix) # Width of water column estimate

        # Determine amount of WC to crop (Wwc)
        if (W < (np.max(Wp)+np.min(Wp)) ):
            Wwc = int( (np.max(Wp)+np.min(Wp)-W) / 2 )
        else:
            Wwc = 0

        # Determine amount of bed to crop (Ws)
        if (W > (np.max(Wp)-np.min(Wp)) ):
            Ws = int( (N/2) - (np.max(Wp)+np.min(Wp)+W)/2 )
        else:
            Ws = 0
        # print('Wwc:', Wwc, 'Ws:', Ws)

        # Crop the original sonogram
        C = int(N/2) # Center of sonogram

        ## Port crop
        lC = Ws # Left side crop
        rC = int(C - (Wwc/2)) # Right side crop
        portCrop = son3bnd[:, lC:rC,:]
        # print('port', lC, rC)
        # print(portCrop, '\n', portCrop.shape)

        ## Starboard crop
        lC = int(C + (Wwc/2)) # Left side crop
        rC = int(N-Ws) # Right side crop
        starCrop = son3bnd[:, lC:rC, :]
        # print('star', lC, rC)
        # print(starCrop, '\n', starCrop.shape)

        ## Concatenate port & star crop
        sonCrop = np.concatenate((portCrop, starCrop), axis = 1)
        sonCrop = sonCrop.astype(np.uint8)

        #######################
        # Segment cropped image
        crop_label = self._doPredict(model, sonCrop)

        ###################################################
        # Potential filters for removing small artifacts???
        if doFilt:
            crop_label = remove_small_holes(crop_label, 2*N)#2*self.port.nchunk)
            crop_label = remove_small_objects(crop_label, 2*N)#2*self.port.nchunk)
            # # There should be three total regions: port bed, wc, star bed
            # ## These should also be the largest 3 regions
            # regions, num = label(crop_label, return_num=True)
            # if num > 3:
            #     for region in regionprops(regions):
            #         print(region.area)

        #########
        # Recover
        portDepPixCrop, starDepPixCrop = self._findBed(crop_label) # get pixel location of bed

        # add Wwc/2 to get final estimate at original sonogram dimensions
        portDepPixCrop = np.flip( np.asarray(portDepPixCrop) + int(Wwc/2) )
        starDepPixCrop = np.flip( np.asarray(starDepPixCrop) + int(Wwc/2) )

        ########################
        # Store depth detections
        self.portDepDetect[i] = portDepPixCrop
        self.starDepDetect[i] = starDepPixCrop


        #*#*#*#*#*#*#*#
        # Plot
        # color map
        class_label_colormap = ['#3366CC','#DC3912']

        # color_label = label_to_colors(init_label, son3bnd[:,:,0]==0, alpha=128, colormap=class_label_colormap, color_class_offset=0, do_alpha=False)
        # imsave(os.path.join(self.port.projDir, str(i)+"initLabel_"+str(i)+".png"), (color_label).astype(np.uint8), check_contrast=False)
        # imsave(os.path.join(self.port.projDir, str(i)+"son3bnd_"+str(i)+".png"), (son3bnd).astype(np.uint8), check_contrast=False)
        imsave(os.path.join(self.port.projDir, str(i)+"cropImg_"+str(i)+".png"), (sonCrop).astype(np.uint8), check_contrast=False)

        color_label = label_to_colors(crop_label, sonCrop[:,:,0]==0, alpha=128, colormap=class_label_colormap, color_class_offset=0, do_alpha=False)
        imsave(os.path.join(self.port.projDir, str(i)+"cropLabel_"+str(i)+".png"), (color_label).astype(np.uint8), check_contrast=False)




        return self

    #=======================================================================
    def _saveDepth(self, chunks):
        # Load sonar metadata file
        self.port._loadSonMeta()
        portDF = self.port.sonMetaDF
        self.star._loadSonMeta()
        starDF = self.star.sonMetaDF

        # Prepare depth detection dictionaries
        portFinal = []
        starFinal = []
        for i in sorted(chunks):
            portDep = self.portDepDetect[i]
            starDep = self.starDepDetect[i]

            portFinal.extend(portDep)
            starFinal.extend(starDep)

        portDF['auto_dep_m'] = portFinal * portDF['pix_m']
        starDF['auto_dep_m'] = starFinal * starDF['pix_m']

        # Export to csv
        portDF.to_csv(self.port.sonMetaFile, index=False, float_format='%.14f')
        starDF.to_csv(self.star.sonMetaFile, index=False, float_format='%.14f')

        del portDF, starDF
        return self

    #=======================================================================
    def _plotBedPick(self, i, acousticBed = True, autoBed = True):

        # Load sonar intensity into memory
        self._getPortStarScanChunk(i)
        mergeSon = self.mergeSon

        ####################
        # Prepare depth data
        # Load sonar metadata file
        self.port._loadSonMeta()
        portDF = self.port.sonMetaDF
        portDF = portDF.loc[portDF['chunk_id'] == i, ['inst_dep_m', 'auto_dep_m', 'pix_m']]

        self.star._loadSonMeta()
        starDF = self.star.sonMetaDF
        starDF = starDF.loc[starDF['chunk_id'] == i, ['inst_dep_m', 'auto_dep_m', 'pix_m']]

        # Convert depth in meters to pixels
        portInst = (portDF['inst_dep_m'] / portDF['pix_m']).to_numpy(dtype=np.int, copy=True)
        portAuto = (portDF['auto_dep_m'] / portDF['pix_m']).to_numpy(dtype=np.int, copy=True)

        starInst = (starDF['inst_dep_m'] / starDF['pix_m']).to_numpy(dtype=np.int, copy=True)
        starAuto = (starDF['auto_dep_m'] / starDF['pix_m']).to_numpy(dtype=np.int, copy=True)

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

        projName = os.path.split(outDir)[-1]
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


    # # Old bedpicking workflow from pj_readFiles.py
    # #####################################
    # # Determine which sonObj is port/star
    # portstarObjs = []
    # for son in sonObjs:
    #     beam = son.beamName
    #     if beam == "ss_port" or beam == "ss_star":
    #         portstarObjs.append(son)
    #
    # if detectDep == 0 and pltBedPick:
    #     print("\nUsing Humminbird's depth estimate and plotting...")
    #     Parallel(n_jobs= np.min([len(portstarObjs), cpu_count()]), verbose=10)(delayed(son._detectDepth)(detectDep, pltBedPick) for son in portstarObjs)
    #     depFieldIn = 'inst_dep_m'
    # elif detectDep > 0:
    #     print("\nAutomatically estimating depth...")
    #     depFieldIn = 'dep_m'
    #     # Parallel(n_jobs= np.min([len(sonObjs), cpu_count()]), verbose=10)(delayed(son._detectDepth)(detectDep, pltBedPick) for son in sonObjs)
    #     Parallel(n_jobs= np.min([len(portstarObjs), cpu_count()]), verbose=10)(delayed(son._detectDepth)(detectDep, pltBedPick) for son in portstarObjs)
    #     # portstarObjs[0]._detectDepth(detectDep, pltBedPick)
    # else:
    #     print("\nUsing Humminbird's depth estimate...")
    #     depFieldIn = 'inst_dep_m'
    # print("Done!")
    #
    # # Load sonar metadata.
    # for son in portstarObjs:
    #     son._loadSonMeta()
    #
    # # Get depth values for both beams
    # dep0 = portstarObjs[0].sonMetaDF[depFieldIn].values
    # dep1 = portstarObjs[1].sonMetaDF[depFieldIn].values
    #
    # # # Try removing outliers
    # # dep0 = np.where(abs(dep0 - np.mean(dep0)) < 2 * np.std(dep0), dep0, 0)
    # # dep1 = np.where(abs(dep1 - np.mean(dep1)) < 2 * np.std(dep1), dep1, 0)
    #
    # # Determine which beam has more records, and temporarily store beam's depth
    # ## values in maxDep.  We have to do this since zip function (below) truncates
    # ## longest list to shortest list.
    # if len(dep0) > len(dep1):
    #     maxDep = dep0
    # else:
    #     maxDep = dep1
    #
    # # Now enumerate both beam's depth values and store only the largest.
    # for i, val in enumerate(zip(dep0, dep1)):
    #     # print(i, val)
    #     val = max(val)
    #     maxDep[i] = max(val, maxDep[i])
    #
    # # Do final outlier removal per chunk ?????
    # i = 0
    # while i <= (len(maxDep)-nchunk):
    #     # print('\n\n',maxDep[i:i+nchunk])
    #     depSub = maxDep[i:i+nchunk]
    #     depSub = np.where(abs(depSub - np.median(depSub)) < 2 * np.std(depSub), depSub, 0)
    #     maxDep[i:i+nchunk] = depSub
    #     # print(depSub)
    #     i+=nchunk
    #
    # # If we have too many consecutive zero's, bedbick was likely unsuccesfull.
    # ## Replace those depth values with acoustic pick
    # maxConsecZero = 50
    # zeros = np.where(maxDep==0)[0] # Find zero depths
    # consecZeros = np.split(zeros, np.where(np.diff(zeros) != 1)[0]+1) # Subset consecutive zeros in their own arrays
    # acousticBed = portstarObjs[0].sonMetaDF['inst_dep_m'].values
    # for consecZero in consecZeros: # Iterate consective zero arrays
    #     if len(consecZero) > maxConsecZero: # Check how many consecutive zeros
    #         for i in consecZero:
    #             maxDep[i] = acousticBed[i]
    #
    # # Set remaining 0's to nan and interpolate over them
    # if np.sum(maxDep) > 0:
    #     # Remove bedpick==0 and Interpolate
    #     maxDep[maxDep==0] = np.nan
    #     # Interpolate over nan's
    #     nans, x = np.isnan(maxDep), lambda z: z.nonzero()[0]
    #     maxDep[nans] = np.interp(x(nans), x(~nans), maxDep[~nans])
    #
    # # Smooth depth values
    # if smthDep:
    #     print("\nSmoothing depth values...")
    #     print(maxDep)
    #     maxDep = savgol_filter(maxDep, 51, 3)
    #     greaterThan0 = (maxDep >= 0)
    #     maxDep = maxDep * greaterThan0
    #     print("Done!")
    #
    # # Adjust depth by user-provided offset
    # if adjDep != 0:
    #     adjBy = portstarObjs[0].sonMetaDF['pix_m'][0] * adjDep
    #     print("\tIncreasing/Decreasing depth values by {} meters...".format(adjBy))
    #     maxDep += adjBy
    #     print("Done!")
    #
    # # Update df's w/ max depth and save to csv
    # for son in portstarObjs:
    #     depCopy = maxDep.copy()
    #     lengthDif = len(maxDep) - len(son.sonMetaDF)
    #     if lengthDif > 0:
    #         depCopy = depCopy[:-(lengthDif)]
    #     elif lengthDif < 0:
    #         print('Dataframe is longer then Depth vector, need to troubleshoot.\n\
    #                Please Report.')
    #     else:
    #         pass
    #     son.sonMetaDF['dep_m'] = depCopy
    #     son.sonMetaDF.to_csv(son.sonMetaFile, index=False, float_format='%.14f')
    #
    # # Export final picks
    # if pltBedPick:
    #     print('\nExporting final bedpicks...')
    #     Parallel(n_jobs= np.min([len(sonObjs), cpu_count()]), verbose=10)(delayed(son._writeFinalBedPick)() for son in portstarObjs)
    #     print("Done!")

    # Old bedpick functions from c_sonObj
    ############################################################################
    # For Automatic Depth Detection                                            #
    ############################################################################

    # # ======================================================================
    # def _detectDepth(self,
    #                  detectDepth=1,
    #                  pltBedPick=False):
    #     '''
    #     Main function for depth detection.
    #     '''
    #     self._loadSonMeta() # Load sonar record metadata into memory
    #     sonMetaAll = self.sonMetaDF
    #
    #     totalChunk = sonMetaAll['chunk_id'].max() #Total chunks to process
    #     i = 0 # Chunk index counter
    #
    #     while i <= totalChunk:
    #         print("\t{}: {} of {}".format(self.beamName, i, int(totalChunk)))
    #         # Filter df by chunk
    #         isChunk = sonMetaAll['chunk_id']==i
    #         sonMeta = sonMetaAll[isChunk].reset_index()
    #         # Update class attributes based on current chunk
    #         self.pingMax = sonMeta['ping_cnt'].astype(int).max() # store to determine max range per chunk
    #         self.headIdx = sonMeta['index'].astype(int) # store byte offset per sonar record
    #         self.pingCnt = sonMeta['ping_cnt'].astype(int) # store ping count per sonar record
    #         # Load chunk's sonar data into memory
    #         self._loadSonChunk()
    #
    #         if detectDepth==0:
    #             acousticBed = round(sonMeta['inst_dep_m'] / sonMeta['pix_m'], 0).astype(int)
    #             bedPick1 = None
    #             bedPick2 = None
    #             bedPick = acousticBed
    #
    #         elif detectDepth==1:
    #             acousticBed = round(sonMeta['inst_dep_m'] / sonMeta['pix_m'], 0).astype(int)
    #             bedPick1 = self._detectDepth_BinaryThresh(acousticBed)
    #             bedPick2 = None
    #             bedPick = bedPick1
    #
    #         elif detectDepth==2:
    #             acousticBed = round(sonMeta['inst_dep_m'] / sonMeta['pix_m'], 0).astype(int)
    #             bedPick1 = None
    #             bedPick2 = self._detectDepth_segZoo_ResU_Net(acousticBed, doThresh=True)
    #             bedPick = bedPick2
    #
    #         elif detectDepth==3:
    #             acousticBed = round(sonMeta['inst_dep_m'] / sonMeta['pix_m'], 0).astype(int)
    #             bedPick1 = self._detectDepth_BinaryThresh(acousticBed)
    #             bedPick2 = self._detectDepth_segZoo_ResU_Net(acousticBed, doThresh=True)
    #             bedPick = bedPick2
    #
    #         elif detectDepth==4:
    #             acousticBed = None
    #             bedPick1 = None
    #             bedPick2 = self._detectDepth_segZoo_ResU_Net_Rescale()
    #             bedPick = bedPick2
    #
    #         if pltBedPick:
    #             self._writeBedPick(i, acousticBed, bedPick1, bedPick2)
    #
    #         sonMetaAll.loc[sonMetaAll['chunk_id']==i, 'dep_m'] = sonMeta['pix_m'].values * bedPick
    #         i+=1
    #
    #     # Write output's to .CSV
    #     sonMetaAll.to_csv(self.sonMetaFile, index=False, float_format='%.14f')
    #
    #     return self
    #
    # # ======================================================================
    # def _detectDepth_BinaryThresh(self,
    #                               acousticBed):
    #     '''
    #     Automatically determine depth from rules-based thresholding method.
    #
    #     ----------------------------
    #     Required Pre-processing step
    #     ----------------------------
    #     Called from self._remWater()
    #
    #     -------
    #     Returns
    #     -------
    #     A list with depth estimate for each ping.
    #
    #     --------------------
    #     Next Processing Step
    #     --------------------
    #     Returns depth estimate to self._remWater()
    #     '''
    #     # Parameters
    #     window = 10 # For peak removal in bed pick: moving window size
    #     max_dev = 5 # For peak removal in bed pick: maximum standard deviation
    #     pix_buf = 50 # Buffer size around min/max Humminbird depth
    #
    #     img = self.sonDat # Get sonar intensities
    #     img = standardize(img)[:,:,0].squeeze() # Standardize and rescale
    #     W, H = img.shape[1], img.shape[0] # Determine array dimensions
    #
    #     ##################################
    #     # Step 1 : Acoustic Bedpick Filter
    #     # Use acoustic bed pick to crop image
    #     bedMin = max(min(acousticBed)-50, 0)
    #     bedMax = max(acousticBed)+pix_buf
    #
    #     cropMask = np.ones((H, W)).astype(int)
    #     cropMask[:bedMin,:] = 0
    #     cropMask[bedMax:,:] = 0
    #
    #     # Mask the image with bed_mask
    #     imgMasked = img*cropMask
    #
    #     ###########################
    #     # Step 2 - Threshold Filter
    #     # Binary threshold masked image
    #     imgMasked = gaussian(imgMasked, 3, preserve_range=True) # Do a gaussian blur
    #     imgMasked[imgMasked==0]=np.nan # Set zero's to nan
    #
    #     imgBinaryMask = np.zeros((H, W)).astype(bool) # Create array to store thresholded sonar img
    #     # Iterate over each sonar record
    #     for i in range(W):
    #         thresh = max(np.nanmedian(imgMasked[:,i]), np.nanmean(imgMasked[:,i])) # Determine threshold value
    #         # stdev = np.nanstd(imgMasked[:,i])
    #         imgBinaryMask[:,i] = imgMasked[:,i] > thresh # Keep only intensities greater than threshold
    #
    #     # Clean up image binary mask
    #     imgBinaryMask = remove_small_objects(imgBinaryMask, 2*H)
    #     imgBinaryMask = remove_small_holes(imgBinaryMask, 2*H)
    #     imgBinaryMask = np.squeeze(imgBinaryMask[:H,:W])
    #
    #     ########################################
    #     # Step 3 - Non-Contiguous region removal
    #     # Make sure we didn't accidently zero out the last row, which should be bed.
    #     # If we did, we will fill it back in
    #     # Try filtering image_binary_mask through labeling regions
    #     labelImage, num = label(imgBinaryMask, return_num=True)
    #     allRegions = []
    #
    #     # Find the lowest/deepest region (this is the bed pixels)
    #     max_row = 0
    #     finalRegion = 0
    #     for region in regionprops(labelImage):
    #         allRegions.append(region.label)
    #         minr, minc, maxr, maxc = region.bbox
    #         # if (maxr > max_row) and (maxc > max_col):
    #         if (maxr > max_row):
    #             max_row = maxr
    #             finalRegion = region.label
    #
    #     # If finalRegion is 0, there is only one region
    #     if finalRegion == 0:
    #         finalRegion = 1
    #
    #     # Zero out undesired regions
    #     for regionLabel in allRegions:
    #         if regionLabel != finalRegion:
    #             labelImage[labelImage==regionLabel] = 0
    #
    #     imgBinaryMask = labelImage # Update thresholded image
    #     imgBinaryMask[imgBinaryMask>0] = 1 # Now set all val's greater than 0 to 1 to create the mask
    #
    #     # Now fill in above last row filled to make sure no gaps in bed pixels
    #     lastRow = bedMax
    #     imgBinaryMask[lastRow] = True
    #     for i in range(W):
    #         if imgBinaryMask[lastRow-1,i] == 0:
    #             gaps = np.where(imgBinaryMask[:lastRow,i]==0)[0]
    #             # Split each gap cluster into it's own array, subset the last one,
    #             ## and take top value
    #             topOfGap = np.split(gaps, np.where(np.diff(gaps) != 1)[0]+1)[-1][0]
    #             imgBinaryMask[topOfGap:lastRow,i] = 1
    #
    #     # Clean up image binary mask
    #     imgBinaryMask = imgBinaryMask.astype(bool)
    #     imgBinaryMask = remove_small_objects(imgBinaryMask, 2*H)
    #     imgBinaryMask = remove_small_holes(imgBinaryMask, 2*H)
    #     imgBinaryMask = np.squeeze(imgBinaryMask[:H,:W])
    #
    #     #############################
    #     # Step 4 - Water Below Filter
    #     # Iterate each ping and determine if there is water under the bed.
    #     # If there is, zero out everything except for the lowest region.
    #     # Iterate each sonar record
    #     for i in range(W):
    #         labelPing, num = label(imgBinaryMask[:,i], return_num=True)
    #         if num > 1:
    #             labelPing[labelPing!=num] = 0
    #             labelPing[labelPing>0] = 1
    #         imgBinaryMask[:,i] = labelPing
    #
    #     ###################################################
    #     # Step 5 - Final Bedpick: Locate Bed & Remove Peaks
    #     # Now relocate bed from image_binary_mask
    #     bed = []
    #     for k in range(W):
    #         try:
    #             b = np.where(imgBinaryMask[:,k]==1)[0][0]
    #         except:
    #             b=0
    #         bed.append(b)
    #     bed = np.array(bed).astype(np.float32)
    #
    #     # Interpolate over nan's
    #     nans, x = np.isnan(bed), lambda z: z.nonzero()[0]
    #     bed[nans] = np.interp(x(nans), x(~nans), bed[~nans])
    #
    #     return bed
    #
    # # ======================================================================
    # def _detectDepth_segZoo_ResU_Net(self,
    #                                  acousticBed,
    #                                  doThresh=False):
    #     # Trained w/ Segmentation Zoo: https://github.com/dbuscombe-usgs/segmentation_zoo
    #     '''
    #     '''
    #     # Parameters
    #     USE_GPU = False
    #     weights = r'.\models\bedpick\bedpick_ModelWeights.h5'
    #     win_overlap_r = 0.5
    #     win_overlap_c = 0.5
    #
    #     configfile = weights.replace('.h5','.json').replace('weights', 'config')
    #
    #     with open(configfile) as f:
    #         config = json.load(f)
    #
    #     globals().update(config)
    #
    #     # Initialize the model
    #     model = res_unet((TARGET_SIZE[0], TARGET_SIZE[1], N_DATA_BANDS), BATCH_SIZE, NCLASSES)
    #     model.compile(optimizer = 'adam', loss = 'categorical_crossentropy', metrics = [mean_iou, dice_coef])
    #     model.load_weights(weights)
    #
    #     # Convert array to tensor
    #     image, w, h, bigimage = seg_file2tensor_3band(self.sonDat, TARGET_SIZE, resize=True)
    #     if image is None:
    #         image = bigimage#/255
    #     w = image.shape[0]; h = image.shape[1] #Model target size shape
    #     W_orig = bigimage.shape[0]; H_orig = bigimage.shape[1] #Original image shape
    #
    #     image = standardize(image.numpy()).squeeze()
    #     bigimage = standardize(bigimage.numpy()).squeeze()
    #
    #     if doThresh:
    #         ##############
    #         # Testing binary threshold filter
    #         threshBed = self._detectDepth_BinaryThresh(acousticBed).astype(int)
    #
    #         # Create a mask from rules-based threshold bedpick
    #         msk = np.ones((W_orig, H_orig)).astype(int)
    #         for i, bed in enumerate(threshBed):
    #             msk[:bed,i] = 0
    #
    #         imgBed = bigimage*msk # Mask out the water, leaving only bed pix
    #         imgWat = bigimage*(~msk) # Mask out the bed, leaving only water pix
    #
    #         # Find standard deviations for bed and water
    #         bedStdv = np.nanstd(imgBed)
    #         watStdv = np.nanstd(imgWat)
    #
    #         # Subtract a standard deviation from 'water' region
    #         imgWat[imgWat>0] = imgWat[imgWat>0]-(watStdv)
    #         imgWat[imgWat<0] = 0.05
    #         imgWat[imgWat>1] = 1
    #
    #         bigimage = imgBed + imgWat
    #
    #         ######################
    #         # End threshold filter
    #         ######################
    #
    #     # Determine window indecies ensuring complete coverage
    #     row_i, stride_r = getWindowIndices(W_orig, w, win_overlap_r)
    #     col_i, stride_c = getWindowIndices(H_orig, h, win_overlap_c)
    #
    #     # Predict over a moving window
    #     for win_r in row_i:
    #         for win_c in col_i:
    #             winImage = bigimage[win_r:win_r+w, win_c:win_c+h]
    #
    #             E = []; W = []
    #             E.append(model.predict(tf.expand_dims(winImage, 0) , batch_size=1).squeeze())
    #             W.append(1)
    #
    #             K.clear_session()
    #
    #             est_label = np.average(np.dstack(E), axis=-1, weights=np.array(W))
    #             est_label /= est_label.max()
    #
    #             # if np.max(est_label)-np.min(est_label) > .5:
    #             #     thres = threshold_otsu(est_label)
    #             #     print("Threshold: %f" % (thres))
    #             # else:
    #             #     thres = .9
    #             #     print("Default threshold: %f" % (thres))
    #             thres = 0.90
    #
    #             var = np.std(np.dstack(E), axis=-1)
    #
    #             conf = 1-est_label
    #             conf[est_label<thres] = est_label[est_label<thres]
    #             conf = 1-conf
    #
    #             conf[np.isnan(conf)] = 0
    #             conf[np.isinf(conf)] = 0
    #
    #             model_conf = np.sum(conf)/np.prod(conf.shape)
    #
    #             est_label[est_label<thres] = 0
    #             est_label[est_label>thres] = 1
    #             est_label = remove_small_holes(est_label.astype(bool), 2*w)
    #             est_label = remove_small_objects(est_label, 2*w)
    #             est_label[est_label<thres] = 0
    #             est_label[est_label>thres] = 1
    #             est_label = np.squeeze(est_label[:w,:h])
    #
    #             ## Add results to predictStack
    #             # First determine row/col offset so predictions population at appropriate index
    #             row_off = win_r
    #             col_off = win_c
    #
    #             # Create nan array of original size to store results
    #             winPredict = np.zeros((W_orig, H_orig))
    #             winPredict[:,:] = np.nan
    #
    #             # Store results
    #             winPredict[row_off:row_off+w, col_off:col_off+h] = est_label
    #
    #             # Stack results
    #             if row_off==0 and col_off==0:
    #                 predictStack = winPredict.copy()
    #             else:
    #                 predictStack = np.dstack((predictStack, winPredict))
    #             del winPredict
    #
    #     # Now we have all our results
    #     # Find the mean of the stack
    #     predictStack = np.nanmean(predictStack, axis=-1)
    #
    #     # Threshold predictions
    #     predictStack = np.nan_to_num(predictStack, nan=1)
    #     predictStack[predictStack>=0.5] = 1
    #     predictStack[predictStack<0.5] = 0
    #
    #     ###########################
    #     # Post-prediction filtering
    #     # 1) Remove bed floating on water
    #     # Determine if more then one water region
    #     waterRegions = predictStack.copy()
    #     waterRegions[waterRegions==0] = 2 # Change water pix values to 2
    #     waterRegions[waterRegions==1] = 0
    #
    #     labelImage, num = label(waterRegions, return_num=True)
    #
    #     pingsFiltered = np.zeros((H_orig)).astype(bool)
    #     if num > 1:
    #         for i in range(H_orig):
    #             gaps = np.where(predictStack[:,i]==0)[0]
    #             # Split each gap cluster into it's own array, subset the last one,
    #             ## and take top value
    #             if len(gaps) > 1:
    #                 topOfGap = np.split(gaps, np.where(np.diff(gaps) != 1)[0]+1)[-1][0]
    #                 if topOfGap > 0:
    #                     predictStack[:topOfGap,i] = 0
    #                     pingsFiltered[i] = True
    #
    #     # Locate the bed
    #     bed = []
    #     for k in range(H_orig):
    #         try:
    #             b = np.where(predictStack[:,k]==1)[0][0]
    #         except:
    #             b=0
    #         bed.append(b)
    #
    #     bed = np.array(bed).astype(np.float32)
    #
    #     # Set outliers to zero.  We will interpolate over them during final bedpick
    #     bed = np.where(abs(bed - np.median(bed)) < 2 * np.std(bed), bed, 0)
    #
    #     return bed.astype(int)
    #
    # # ======================================================================
    # def _detectDepth_segZoo_ResU_Net_Rescale(self):
    #     # Trained w/ Segmentation Zoo: https://github.com/dbuscombe-usgs/segmentation_zoo
    #     '''
    #     '''
    #     # Parameters
    #     USE_GPU = False
    #     weights = r'.\models\bedpick\bedpick_ModelWeights.h5'
    #
    #     configfile = weights.replace('.h5','.json').replace('weights', 'config')
    #
    #     with open(configfile) as f:
    #         config = json.load(f)
    #
    #     globals().update(config)
    #
    #     # Initialize the model
    #     model = res_unet((TARGET_SIZE[0], TARGET_SIZE[1], N_DATA_BANDS), BATCH_SIZE, NCLASSES)
    #     model.compile(optimizer = 'adam', loss = 'categorical_crossentropy', metrics = [mean_iou, dice_coef])
    #     model.load_weights(weights)
    #
    #     # Convert array to tensor
    #     image, w, h, bigimage = seg_file2tensor_3band(self.sonDat, TARGET_SIZE, resize=True)
    #     if image is None:
    #         image = bigimage#/255
    #     w = image.shape[0]; h = image.shape[1] #Model target size shape
    #     W_orig = bigimage.shape[0]; H_orig = bigimage.shape[1] #Original image shape
    #
    #     # Standardize
    #     image = standardize(image.numpy()).squeeze()
    #     bigimage = standardize(bigimage.numpy()).squeeze()
    #
    #     #################################
    #     # Do prediction on rescaled image
    #     E = []; W = []
    #     E.append(model.predict(tf.expand_dims(image, 0) , batch_size=1).squeeze())
    #     W.append(1)
    #
    #     K.clear_session()
    #
    #     est_label = np.average(np.dstack(E), axis=-1, weights=np.array(W))
    #     est_label /= est_label.max()
    #
    #     if np.max(est_label)-np.min(est_label) > .5:
    #         thres = threshold_otsu(est_label)
    #         print("Threshold: %f" % (thres))
    #     else:
    #         thres = .9
    #         print("Default threshold: %f" % (thres))
    #
    #     var = np.std(np.dstack(E), axis=-1)
    #
    #     conf = 1-est_label
    #     conf[est_label<thres] = est_label[est_label<thres]
    #     conf = 1-conf
    #
    #     conf[np.isnan(conf)] = 0
    #     conf[np.isinf(conf)] = 0
    #
    #     model_conf = np.sum(conf)/np.prod(conf.shape)
    #
    #     est_label[est_label<thres] = 0
    #     est_label[est_label>thres] = 1
    #     est_label = remove_small_holes(est_label.astype(bool), 2*w)
    #     est_label = remove_small_objects(est_label, 2*w)
    #     est_label[est_label<thres] = 0
    #     est_label[est_label>thres] = 1
    #     est_label = np.squeeze(est_label[:w,:h])
    #
    #     # Locate the bed
    #     bed = []
    #     for k in range(H_orig):
    #         try:
    #             b = np.where(est_label[:,k]==1)[0][0]
    #         except:
    #             b=0
    #         bed.append(b)
    #
    #     bed = np.array(bed).astype(np.float32)
    #
    # # ======================================================================
    # def _writeBedPick(self,
    #                   k,
    #                   acousticBed = None,
    #                   bed1 = None,
    #                   bed2 = None,
    #                   finalBed = None,
    #                   imgOutPrefix = 'bedpick'):
    #
    #     '''
    #     Exports a plot of a bedpick on a non-rectified sonogram.
    #
    #     ----------------------------
    #     Required Pre-processing step
    #     ----------------------------
    #     Called from self._detectDepth() or self._writeFinalBedPick()
    #
    #     -------
    #     Returns
    #     -------
    #     A .png in projDir/*sonar_channel*/bedpick showing bedpick overlain on a
    #     sonogram.
    #     '''
    #     data = self.sonDat # Get the sonar data
    #
    #     # File name zero padding
    #     if k < 10:
    #         addZero = '0000'
    #     elif k < 100:
    #         addZero = '000'
    #     elif k < 1000:
    #         addZero = '00'
    #     elif k < 10000:
    #         addZero = '0'
    #     else:
    #         addZero = ''
    #
    #     # Prepare output directory if it doesn't already exist
    #     outDir = os.path.join(self.outDir, imgOutPrefix)
    #     try:
    #         os.mkdir(outDir)
    #     except:
    #         pass
    #
    #     channel = os.path.split(self.outDir)[-1] #ss_port, ss_star, etc.
    #     projName = os.path.split(self.projDir)[-1] #to append project name to filename
    #     outFile = os.path.join(outDir, projName+'_'+imgOutPrefix+'_'+channel+'_'+addZero+str(k)+'.png') #prepare file name
    #
    #     plt.imshow(data, cmap='gray') # create Matlab plt object
    #     if acousticBed is not None: # plot acoustic bedpick in yellow
    #         plt.plot(acousticBed, 'y-.', lw=1, label='Acoustic Depth')
    #     if bed1 is not None: # plot binary threshold bedpick in magenta
    #         plt.plot(bed1, 'm-.', lw=1, label='Auto Depth 1')
    #     if bed2 is not None: # plot residual u-net bedpick in red
    #         plt.plot(bed2, 'r-.', lw=1, label='Auto Depth 2')
    #     if finalBed is not None: # plot final bedpick in blue
    #         plt.plot(finalBed, 'b-.', lw=1, label='Auto Depth Final')
    #     plt.legend(loc = 'lower right', prop={'size':4}) # create the plot legend
    #     plt.savefig(outFile, dpi=300, bbox_inches='tight') # save the plot
    #     plt.close()
    #
    # # ======================================================================
    # def _writeFinalBedPick(self):
    #     '''
    #     '''
    #     self._loadSonMeta() # Load sonar record metadata into memory
    #     sonMetaAll = self.sonMetaDF
    #
    #     totalChunk = sonMetaAll['chunk_id'].max() #Total chunks to process
    #     i = 0 # Chunk index counter
    #
    #     while i <= totalChunk:
    #         # Filter df by chunk
    #         isChunk = sonMetaAll['chunk_id']==i
    #         sonMeta = sonMetaAll[isChunk].reset_index()
    #         # Update class attributes based on current chunk
    #         self.pingMax = sonMeta['ping_cnt'].astype(int).max() # store to determine max range per chunk
    #         self.headIdx = sonMeta['index'].astype(int) # store byte offset per sonar record
    #         self.pingCnt = sonMeta['ping_cnt'].astype(int) # store ping count per sonar record
    #         # Load chunk's sonar data into memory
    #         self._loadSonChunk()
    #         acousticBed = round(sonMeta['inst_dep_m'] / sonMeta['pix_m'], 0).astype(int)
    #         finalBed = round(sonMeta['dep_m'] / sonMeta['pix_m'], 0).astype(int)
    #         self._writeBedPick(i, acousticBed, finalBed = finalBed, imgOutPrefix = 'bedpick_final')
    #         i+=1
