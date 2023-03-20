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
from funcs_model import *
from class_rectObj import rectObj
from mpl_toolkits.axes_grid1 import make_axes_locatable

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

from skimage.filters import threshold_otsu
from osgeo import gdal, ogr, osr

class mapSubObj(rectObj):

    '''

    '''

    ############################################################################
    # Create mapObj() instance from previously created rectObj() instance      #
    ############################################################################

    #=======================================================================
    def __init__(self,
                 metaFile):

        rectObj.__init__(self, metaFile)

        return

    ############################################################################
    # Substrate Prediction                                                     #
    ############################################################################

    #=======================================================================
    def _detectSubstrate(self, i, USE_GPU):

        '''
        Main function to automatically predict substrate.

        ----------
        Parameters
        ----------

        ----------------------------
        Required Pre-processing step
        ----------------------------

        -------
        Returns
        -------

        --------------------
        Next Processing Step
        --------------------
        '''


        # Initialize the model
        if not hasattr(self, 'substrateModel'):
            model, model_name, n_data_bands = initModel(self.weights, self.configfile, USE_GPU)
            self.substrateModel = model

        # Open model configuration file
        with open(self.configfile) as f:
            config = json.load(f)
        globals().update(config)

        # Do prediction
        substratePred = self._predSubstrate(i, model_name, n_data_bands)

        # Save predictions to npz
        self._saveSubstrateNpz(substratePred, i, MY_CLASS_NAMES)

        del self.substrateModel, substratePred
        gc.collect()

        return


    #=======================================================================
    def _predSubstrate(self, i, model_name, n_data_bands, winO=1/3):
        '''
        '''

        #################################################
        # Get depth for water column removal and cropping
        # Get sonMeta to get depth
        self._loadSonMeta()

        ############
        # Load Sonar
        # Get current chunk, left & right chunk's sonDat and concatenate
        # Pad is tuple with current chunk H, W and water column pix crop
        son3Chunk, origDims, lOff, tOff = self._getSon3Chunk(i)

        # Get dims of concatenated sonDats
        H, W = son3Chunk.shape

        ###########################
        # Get moving window indices
        movWinInd = self._getMovWinInd(winO, son3Chunk)

        #################################
        # Make prediction for each window
        # Expand softmax_score to dims of son3Chunk filled with nan's
        # Ensure softmax_score in correct location (win offset) in larger array
        # store each softmax in a list labels=[]
        # np.nanmean(labels, axis=2)

        # Store each window's softmax
        winSoftMax = []
        # Iterate each window
        for m in movWinInd:
            # Slice son3Chunk by index
            # Return son slice, begin and end index
            sonWin, wStart, wEnd = self._getSonDatWin(m, son3Chunk)

            # Get the model
            model = self.substrateModel

            # Do prediction, return softmax_score for each class
            softmax_score = doPredict(model, MODEL, sonWin, N_DATA_BANDS, NCLASSES, TARGET_SIZE)

            # Expand softmax_score to son3Chunk dims, filled with nan's
            softmax_score = self._expandWin(H, W, wStart, wEnd, softmax_score)
            # print('softmax_score', softmax_score.shape)

            # Store expanded softmax_score
            winSoftMax.append(softmax_score)

            del sonWin, wStart, wEnd, softmax_score

        # Take mean across all windows to get one final softmax_score array
        fSoftmax = np.nanmean(np.stack(winSoftMax, axis=0), axis=0)

        # Crop center chunk predictions and recover original dims
        h, w = origDims # Center chunks original dims
        lO, rO = lOff # Left and right offset for center chunk
        tO = tOff # Top offset for center chunk

        # Crop left and right
        fSoftmax = fSoftmax[:, lO:rO, :]
        sh, sw, c = fSoftmax.shape

        # Create final array to store prediction at original dims and offsets
        fArr = np.zeros((h, w, c))
        # Fill with nan to prevent so 0's don't affect final prediction
        fArr.fill(np.nan)

        # Need to determine if final array or softmax need to be sliced
        # bOff < 0: slice fArr to fit smaller fSoftmax
        # bOff > 0: slice softmax to fit small fArr
        # bOff == 0: no slicing necessary
        bOff = sh - (h - tO)

        if bOff < 0:
            bOff = fArr.shape[0] + bOff
            fArr[tO:bOff, :, :] = fSoftmax

            # # Set definate shadows to 1.0
            # # Shadow second to last class
            # fArr[bOff:, :, -2] = 10.0

        elif bOff > 0:
            bOff = fArr.shape[0] - tO
            fArr[tO:, :, :] = fSoftmax[:bOff, :, :]

        else:
            fArr[tO:, :, :] = fSoftmax

        # # Make sure softmax is 1.0 for areas definately water
        # # Water last class
        # fArr[:tO, :, -1] = 10.0

        # print(fArr.shape, np.min(fArr), np.max(fArr))
        del fSoftmax, son3Chunk
        gc.collect()

        return fArr

    #=======================================================================
    def _getSon3Chunk(self, i):
        '''
        '''

        # Get sonMeta df
        df = self.sonMetaDF

        # Get sonar chunks, remove shadows and crop, remove water column and crop
        ######
        # Left
        # if i==0, use i for left also
        if i == 0:
            l = i
        else:
            l = i-1

        # Get sonDat
        self._getScanChunkSingle(l)

        # Store left offset for left corner of center chunk, i.e. width of first chunk
        lOffL = self.sonDat.shape[1]

        # Crop shadows
        _ = self._SHW_crop(l, False)

        # Get sonMetaDF
        lMetaDF = df.loc[df['chunk_id'] == l, ['dep_m']].copy()

        # Remove water column and crop
        lMinDep = self._WCR_crop(lMetaDF)

        # Create copy of sonar data
        lSonDat = self.sonDat.copy()

        # If using first chunk, flip horizontally
        if l == 0:
            lSonDat = np.fliplr(lSonDat)

        ########
        # Center
        # Get sonDat
        self._getScanChunkSingle(i)

        # Original image dimensions
        H, W = self.sonDat.shape

        # Store left offset for right corner of center chunk, i.e. width of both chunks
        lOffR = lOffL + self.sonDat.shape[1]

        # Crop shadows first
        _ = self._SHW_crop(i, False)

        # Get sonMetaDF
        cMetaDF = df.loc[df['chunk_id'] == i, ['dep_m']].copy()

        # Remove water column and crop
        cMinDep = self._WCR_crop(cMetaDF)

        # Create copy of sonar data
        cSonDat = self.sonDat.copy()

        ########
        # Right
        # if i is last chunk, use i for right also
        if i == self.chunkMax:
            r = i
        else:
            r = i+1
        # Get sonDat
        self._getScanChunkSingle(r)

        # Crop shadows first
        _ = self._SHW_crop(r, False)

        # Get sonMetaDF
        rMetaDF = df.loc[df['chunk_id'] == r, ['dep_m']].copy()

        # Remove water column and crop
        rMinDep = self._WCR_crop(rMetaDF)

        # Create copy of sonar data
        rSonDat = self.sonDat.copy()

        # If using first chunk, flip horizontally
        if r == self.pingMax:
            rSonDat = np.fliplr(rSonDat)

        del self.sonDat

        #############################
        # Merge left, center, & right

        # Align arrays based on wc_crops

        # Find min depth
        minDep = min(lMinDep, cMinDep, rMinDep)

        # Pad arrays if chunk's minDep > minDep and fill with zero's
        # Left
        if lMinDep > minDep:
            # Get current sonDat shape
            r, c = lSonDat.shape

            # Determine pad size (actual offset from top)
            pad = lMinDep - minDep

            # Make new zero array w/ pad added in
            newArr = np.zeros((pad+r, c))
            # Fill with nan to prevent unneeded prediction
            newArr.fill(np.nan)

            # Fill sonDat in appropriate location
            newArr[pad:,:] = lSonDat
            lSonDat = newArr.copy()
            del newArr

        # Center
        if cMinDep > minDep:
            # Get current sonDat shape
            r, c = cSonDat.shape

            # Determine pad size
            pad = cMinDep - minDep

            # Make new zero array w/ pad added in
            newArr = np.zeros((pad+r, c))
            # Fill with nan to prevent unneeded prediction
            newArr.fill(np.nan)

            # Fill sonDat in appropriate location
            newArr[pad:,:] = cSonDat
            cSonDat = newArr.copy()
            del newArr

            # Return cpad to recover original dims
            cpad = pad
        else:
            cpad = cMinDep

        # Right
        if rMinDep > minDep:
            # Get current sonDat shape
            r, c = rSonDat.shape
            # Determine pad size
            pad = rMinDep - minDep

            # Make new zero array w/ pad added in
            newArr = np.zeros((pad+r, c))
            # Fill with nan to prevent unneeded prediction
            newArr.fill(np.nan)

            # Fill sonDat in appropriate location
            newArr[pad:,:] = rSonDat
            rSonDat = newArr.copy()
            del newArr

        ####
        # Arrays are now aligned along the water bed interface.
        # Last step is to create output array large enough to store all data.

        # Find max rows across each chunk
        maxR = max(lSonDat.shape[0], cSonDat.shape[0], rSonDat.shape[0])

        # Find max cols
        maxC = lSonDat.shape[1] + cSonDat.shape[1] + rSonDat.shape[1]

        # Create final array of appropriate size
        fSonDat = np.zeros((maxR, maxC))
        # Fill with nan to prevent unneeded prediction
        fSonDat.fill(np.nan)

        ####
        # Add each chunk to final array

        # Insert left chunk
        fSonDat[:lSonDat.shape[0], :lOffL] = lSonDat

        # Insert center chunk
        fSonDat[:cSonDat.shape[0], lOffL:lOffR] = cSonDat

        # Insert right chunk
        fSonDat[:rSonDat.shape[0], lOffR:] = rSonDat

        # # For Troubleshooting
        # # Export image check
        # try:
        #     os.mkdir(self.outDir)
        # except:
        #     pass
        # self.sonDat = fSonDat
        # self._writeTiles(i, 'test')

        # Prepare necessary params for rebuilding orig dims and offsets
        origDims = [H, W] # Original dims of center chunk
        lOff = [lOffL, lOffR] # Left/right offset of center chunk
        tOff = cpad # Offset from top


        return fSonDat, origDims, lOff, tOff


    #=======================================================================
    def _expandWin(self, H, W, w1, w2, arr):

        '''
        Generate new array of size (H, W, arr.shape[2]) filled with nan's. Place
        arr in new arr at index [:, w1:w2]
        '''

        # Number of classes
        nclass = arr.shape[2]

        # Create new array filled with nan's
        a = np.zeros((H, W, nclass))
        a.fill(np.nan)

        # Insert arr into a
        a[:, w1:w2, :] = arr

        return a

    #=======================================================================
    def _getSonDatWin(self, w, arr):

        '''
        Get slice of son3Chunk using index (w) and nchunk
        '''
        # Chunk size
        nchunk = self.nchunk

        # End index
        e = w+nchunk

        # Slice by columns
        son = arr[:, w:e]

        return son, w, e

    #=======================================================================
    def _getMovWinInd(self, o, arr):

        '''
        Get moving window indices based on window overlap (o) and arr size
        '''

        # Get array dims
        H, W = arr.shape[:2]

        # Chunk size
        c = self.nchunk

        # Calculate stride
        s = c * o

        # Calculate total windows
        tWin = (int(1 / o)*2) - 1

        # Calculate first window index
        i = (c + s) - c

        # Get all indices
        winInd = np.arange(i,W,s, dtype=int)

        # Only need tWin values
        winInd = winInd[:tWin]

        return winInd

    #=======================================================================
    def _saveSubstrateNpz(self, arr, k, classes):
        '''
        Save substrate prediction to npz
        '''

        ###################
        # Prepare File Name
        # File name zero padding
        if k < 10:
            addZero = '0000'
        elif k < 100:
            addZero = '000'
        elif k < 1000:
            addZero = '00'
        elif k < 10000:
            addZero = '0'
        else:
            addZero = ''

        # Out directory
        outDir = self.outDir
        # outDir = os.path.join(self.substrateDir, 'predict_npz')
        # if not os.path.exists(outDir):
        #     os.mkdir(outDir)

        #projName_substrate_beam_chunk.npz
        channel = self.beamName #ss_port, ss_star, etc.
        projName = os.path.split(self.projDir)[-1] #to append project name to filename

        # Prepare file name
        f = projName+'_'+'substrateSoftmax'+'_'+channel+'_'+addZero+str(k)+'.npz'
        f = os.path.join(outDir, f)

        # Create dict to store output
        datadict = dict()
        datadict['substrate'] = arr

        datadict['classes'] = list(classes.values())

        # Save compressed npz
        np.savez_compressed(f, **datadict)

        # # Save non_compressed npz
        # f = projName+'_'+'substrateSoftmax'+'_'+channel+'_'+addZero+str(k)+'_noncompress.npz'
        # f = os.path.join(outDir, f)
        # np.savez(f, arr)

        del arr
        return

    ############################################################################
    # Plot Substrate Classification                                            #
    ############################################################################

    #=======================================================================
    def _pltSubClass(self, map_class_method, chunk, npz, spdCor=1, maxCrop=0):

        '''
        '''

        ###################
        # Prepare File Name
        # File name zero padding
        k = chunk
        if k < 10:
            addZero = '0000'
        elif k < 100:
            addZero = '000'
        elif k < 1000:
            addZero = '00'
        elif k < 10000:
            addZero = '0'
        else:
            addZero = ''

        # Out directory
        outDir = self.outDir
        # outDir = os.path.join(self.substrateDir, 'plots')
        # if not os.path.exists(outDir):
        #     os.mkdir(outDir)

        #projName_substrate_beam_chunk.npz
        channel = self.beamName #ss_port, ss_star, etc.
        projName = os.path.split(self.projDir)[-1] #to append project name to filename

        # Load sonDat
        self._getScanChunkSingle(chunk)
        son = self.sonDat

        # Speed correct son
        if spdCor>0:
            # Do sonar first
            self._doSpdCor(chunk, spdCor=spdCor, maxCrop=maxCrop)
            son = self.sonDat.copy()

        # Open substrate softmax scores
        npz = np.load(npz)
        softmax = npz['substrate'].astype('float32')

        # Get classes
        classes = npz['classes']


        #####################
        # Plot Classification

        # Get final classification
        label = self._classifySoftmax(chunk, softmax, map_class_method, mask_wc=True, mask_shw=True)
        # label = self._classifySoftmax(chunk, softmax, map_class_method, mask_wc=True, mask_shw=True, do_filt=False)

        # Do speed correction
        if spdCor>0:
            # Now do label
            self.sonDat = label
            self._doSpdCor(chunk, spdCor=spdCor, maxCrop=maxCrop, son=False)
            label = self.sonDat.copy()

            # Store sonar back in sonDat just in case
            self.sonDat = son

        # Prepare plt file name/path
        f = projName+'_'+'pltSub_'+'classified_'+map_class_method+'_'+channel+'_'+addZero+str(k)+'.png'
        f = os.path.join(outDir, f)

        # Set colormap
        class_label_colormap = ['#3366CC','#DC3912', '#FF9900', '#109618', '#990099', '#0099C6', '#DD4477', '#66AA00', '#B82E2E', '#316395', '#000000']

        # Convert labels to colors
        color_label = label_to_colors(label, son[:,:]==0, alpha=128, colormap=class_label_colormap, color_class_offset=0, do_alpha=False)

        # Do plot`
        fig = plt.figure()
        ax = plt.subplot(111)

        # Plot overlay
        ax.imshow(son, cmap='gray')
        ax.imshow(color_label, alpha=0.5)
        ax.axis('off')

        # Shrink plot
        box = ax.get_position()
        ax.set_position([box.x0, box.y0 + box.height * 0.1, box.width, box.height * 0.9])

        # Legend
        colors = class_label_colormap[:len(classes)]
        l=dict()
        for i, (n, c) in enumerate(zip(classes,colors)):
            l[str(i)+' '+n]=c

        markers = [plt.Line2D([0,0],[0,0],color=color, marker='o', linestyle='') for color in l.values()]
        ax.legend(markers, l.keys(), numpoints=1, ncol=int(len(colors)/3),
                  markerscale=0.5, prop={'size': 5}, loc='upper center',
                  bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True,
                  columnspacing=0.75, handletextpad=0.25)

        plt.savefig(f, dpi=200, bbox_inches='tight')
        plt.close()


        ##############
        # Plot Softmax

        probs = False # True=Plot Probabilities, False=Plot Logits

        if probs:
            sigma = 1 # Number of standard deviations to plot
        else:
            sigma = 2

        # Number of rows
        rows=len(classes)

        # Convert to probabilities????
        if probs:
            softmax = tf.nn.softmax(softmax).numpy()

        # Calculate stats and prepare labels
        meanSoft = round(np.nanmean(softmax), 1)
        stdSoft = np.nanstd(softmax)
        minSoft = round(meanSoft-(sigma*stdSoft), 1)
        maxSoft = round(meanSoft+(sigma*stdSoft), 1)

        # Prepare subtitle
        meanL = '$\mu$' +' ('+str(meanSoft)+')'
        if probs:
            if minSoft < 0:
                minSoft = 0
                minL = '('+str(minSoft)+')'
            else:
                minL = '-'+str(sigma)+'$\sigma$'+' ('+str(minSoft)+')'

            if maxSoft > 1:
                maxSoft = 1
                maxL = '('+str(maxSoft)+')'
            else:
                maxL = str(sigma)+'$\sigma$'+' ('+str(maxSoft)+')'

        else:
            minL = '-'+str(sigma)+'$\sigma$'+' ('+str(minSoft)+')'
            meanL = '$\mu$' +' ('+str(meanSoft)+')'
            maxL = str(sigma)+'$\sigma$'+' ('+str(maxSoft)+')'

        # Create subplots
        plt.figure(figsize=(16,12))
        plt.subplots_adjust(hspace=0.25)
        nrows = 3
        ncols = int(np.ceil((softmax.shape[-1]+2)/nrows))

        # Prepare Title
        if probs:
            title = 'Substrate Probabilities\n'
        else:
            title = 'Substrate Logits\n'
        title = title+minL + '$\leq$' + meanL + '$\leq$' + maxL
        plt.suptitle(title, fontsize=18, y=0.95)

        # Plot substrate in first position
        ax = plt.subplot(nrows, ncols, 1)
        ax.set_title('Sonar')
        ax.imshow(son, cmap='gray')
        ax.axis('off')

        # Plot classification in second position
        ax = plt.subplot(nrows, ncols, 2)
        ax.set_title('Classification: '+ map_class_method)
        # Plot overlay
        ax.imshow(son, cmap='gray')
        ax.imshow(color_label, alpha=0.5)
        ax.axis('off')

        # Loop through axes
        for i in range(softmax.shape[-1]):

            # Get class
            cname=classes[i]
            c = softmax[:,:,i]

            # Do speed correction
            if spdCor>0:
                # Now do label
                self.sonDat = c
                self._doSpdCor(chunk, spdCor=spdCor, maxCrop=maxCrop, son=False, integer=False)
                c = self.sonDat.copy()

                # Store sonar back in sonDat just in case
                self.sonDat = son

            # Do plot
            ax = plt.subplot(nrows, ncols, i+3)
            ax.set_title(cname, backgroundcolor=class_label_colormap[i], color='white')

            ax.imshow(son, cmap='gray')

            # Prepare color map
            color_map = plt.cm.get_cmap('viridis')
            # color_map = color_map.reversed()

            im = ax.imshow(c, cmap=color_map, alpha=0.5, vmin=minSoft, vmax=maxSoft)
            # im = ax.imshow(c, cmap='magma', alpha=0.5)
            ax.axis('off')

            # Legend
            # box = ax.get_position()
            # ax.set_position([box.x0, box.y0, box.width * 0.9, box.height])
            # ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

            divider = make_axes_locatable(ax)
            cax = divider.append_axes('right', size='5%', pad=0.05)
            cbar = plt.colorbar(im, ticks=[minSoft, meanSoft, maxSoft], cax=cax)
            # minL = '-2$\sigma$'+' ('+str(minSoft)+')'
            # meanL = '$\mu$' +' ('+str(meanSoft)+')'
            # maxL = '2$\sigma$'+' ('+str(maxSoft)+')'
            # minL = '-2$\sigma$'
            # meanL = '$\mu$'
            # maxL = str(sigma)+'$\sigma$'

            # Prepare colorbar labels
            meanL = '$\mu$'
            if probs:
                if minSoft == 0:
                    minL = str(minSoft)
                else:
                    minL = '-'+str(sigma)+'$\sigma$'

                if maxSoft == 1:
                    maxL = str(maxSoft)
                else:
                    maxL = str(sigma)+'$\sigma$'

            else:
                minL = '-'+str(sigma)+'$\sigma$'
                meanL = '$\mu$'
                maxL = str(sigma)+'$\sigma$'

            cbar.ax.set_yticklabels([minL, meanL, maxL])

        if probs:
            f = f.replace('classified_'+map_class_method, 'probability')
        else:
            f = f.replace('classified_'+map_class_method, 'logits')
        plt.savefig(f, dpi=200, bbox_inches='tight')
        plt.close()


    ############################################################################
    # Substrate Mapping                                                        #
    ############################################################################

    #=======================================================================
    def _classifySoftmax(self, i, arr, map_class_method='max', mask_wc=True, mask_shw=True, do_filt=True):
        '''
        Classify pixels from softmax values
        '''

        #################################
        # Classify substrate from softmax

        # Take max logit as class
        if map_class_method == 'max':
            label = np.argmax(arr, -1)
            # label = np.nanargmax(arr, -1)
            label += 1

        elif map_class_method == 'thresh':
            # Class: ProbThresh 1==no thresh
            thresh = {0: 1,
                      1: 1,
                      2: 1,
                      3: .075,
                      4: .075,
                      5: 1,
                      6: 1,
                      7: 1}

            # Least to most important
            class_order = [0, 6, 7, 5, 1, 4, 3, 2]

            # Convert logits to probability
            arr = tf.nn.softmax(arr).numpy()

            # # Iterate classes least to most important
            # for k, t in thresh.items():
            #
            #     # If t == 1, use softmax directly
            #     # Else t<1, set prob > t to 1
            #     if t < 1:
            #         s = softmax[:,:,k]
            #         s = np.where(s>t, 1, s)
            #
            #         # Update softmax
            #         softmax[:,:,k] = s

            # Zero array to store label
            label = np.zeros((arr.shape[0], arr.shape[1]))
            for k in class_order:
                # # Convert to probability
                # # https://stackoverflow.com/questions/46416984/how-to-convert-logits-to-probability-in-binary-classification-in-tensorflow
                # p = tf.round(tf.nn.sigmoid(arr[:,:,k]))

                # Get threshold
                t = thresh[k]

                # IF t==1, use otsu to set threshold
                if t==1:
                    t = threshold_otsu(arr[:,:,k])
                    # t = threshold_otsu(p)

                label[arr[:,:,k]>t]=k
                # label[p>t]=k

            label += 1

        elif map_class_method == 'pref':
            # Class: pref 1==give pref, 0==don't
            pref = {0: 0,
                    1: 0,
                    2: 1,
                    3: 1,
                    4: 1,
                    5: 0,
                    6: 0,
                    7: 0}

            # Least to most important
            class_order = [0, 6, 7, 5, 1, 2, 4, 3]

            # First get label the normal way
            label = np.argmax(arr, -1)

            # Now iterate each class, if pref==1, do binary class, then mask
            ## label with updated class
            for k in class_order:
                if pref[k] == 1:
                    # Get binary classification
                    p = tf.round(tf.nn.sigmoid(arr[:,:,k]))
                    # Update label
                    label[p==1]=k
            label += 1


        # elif map_class_method == 'thresh':
        #     thresh = {0: 1,
        #               1: 1,
        #               2: 1,
        #               3: 0.15,
        #               4: 0.15,
        #               5: 1,
        #               6: 1}
        #
        #     for c, t in thresh.items():
        #         # Get logits
        #         s = arr[:,:,c]
        #
        #         # Convert to probability
        #         # https://stackoverflow.com/questions/46416984/how-to-convert-logits-to-probability-in-binary-classification-in-tensorflow
        #         p = tf.round(tf.nn.sigmoid(s))
        #
        #         # Set softmax to w if > t
        #         w = 100
        #         p = np.where(p>t, True, False)
        #
        #         # Add weight to logit value
        #         s[p] = w
        #         # s = np.where(s[p==1], s+w, s)
        #
        #         # Update softmax
        #         arr[:,:,c] = s
        #
        #     label = np.argmax(arr, -1)
        #     label += 1

        else:
            print('Invalid map_class_method provided:', map_class_method)
            sys.exit()

        ##################
        # Mask predictions

        # Mask Water column
        if mask_wc:
            self._WC_mask(i)
            wc_mask = self.wcMask

            label = (label*wc_mask).astype('uint8') # Zero-out water column
            wc_mask = np.where(wc_mask==0,9,wc_mask) # Set water column mask value to 8
            wc_mask = np.where(wc_mask==1,0,wc_mask) # Set non-water column mask value to 0
            label = (label+wc_mask).astype('uint8') # Add mask to label to get water column classified in plt

        # Mask Shadows
        if mask_shw:
            self._SHW_mask(i, son=False)
            shw_mask = self.shadowMask

            label = (label*shw_mask).astype('uint8')
            shw_mask = np.where(shw_mask==0,8,shw_mask) # Set water column mask value to 7
            shw_mask = np.where(shw_mask==1,0,shw_mask) # Set non-water column mask value to 0
            label = (label+shw_mask).astype('uint8') # Add mask to label to get water column classified in plt

        label -= 1
        # Filter small regions
        if do_filt:
            # Set minimum patch size (in meters)
            min_size = 28

            # Filter small regions and holes
            label = self._filterLabel(label, min_size)


        return label


    ############################################################################
    # General mapSubObj Utilities                                              #
    ############################################################################

    #=======================================================================
    def _getSubstrateNpz(self):
        '''
        Locate previously saved substrate npz files and return dictionary:
        npzs = {chunkID:NPZFilePath}
        '''

        # Get npz dir
        npzDir = os.path.join(self.substrateDir, 'predict_npz')

        # Get npz files belonging to current son
        npzs = sorted(glob(os.path.join(npzDir, '*'+self.beamName+'*.npz')))

        # Dictionary to store {chunkID:NPZFilePath}
        toMap = defaultdict()

        # Extract chunkID from filename and store in dict
        for n in npzs:
            c = os.path.basename(n)
            c = c.split('.')[0]
            c = int(c.split('_')[-1])
            toMap[c] = n

        del npzDir, npzs, n, c
        return toMap


    #=======================================================================
    def _filterLabel(self, l, min_size):
        '''
        '''
        # Get pixel size (in meters)
        pix_m = self.pixM

        # Convert min size to pixels
        min_size = int(min_size/pix_m)

        # Set nan's to zero
        l = np.nan_to_num(l, nan=0).astype('uint8')

        # Label all regions
        lbl = label(l)

        # First set small objects to background value (0)
        noSmall = remove_small_objects(lbl, min_size)

        # Punch holes in original label
        holes = ~(noSmall==0)

        l = l*holes

        # Remove small holes
        # Convert l to binary
        binary_objects = l.astype(bool)
        # Remove the holes
        binary_filled = remove_small_holes(binary_objects, min_size)
        # Recover classification with holes filled
        objects_filled = watershed(binary_filled, l, mask=binary_filled)

        # Get rid of 0's
        # Iterate each ping

        for p in range(l.shape[1]):
            # Get depth
            d = self.bedPick[p]

            # Get ping returns
            ping = objects_filled[:, p]

            # Get water column
            wc = ping[:d]

            # Remove water column
            ping = ping[d:]

            ##############
            # Remove zeros
            # Find zeros. Should be grouped in contiguous arrays (array[0, 1, 2], array[100, 101, 102], ...
            zero = np.where(ping==0)[0]

            if len(zero) > 0:
                # Group sequential zeros [array([0, 1, 2, 3, ..]), array([1100, 1101, 1102, ..])]
                zero = np.split(zero, np.where(np.diff(zero) != 1)[0]+1)

                # Iterate each zero sequence
                for z in zero:
                    # Get index of first and last zero
                    f, l = z[0], z[-1]

                    # If len(zero) not entire ping AND not 1
                    if len(z) < ping.shape[0] and len(z)>1:
                        # if f at top (ie == 0)
                        if f == 0:
                            # Set c to l+1
                            c = ping[l+1]
                        # if l at bottom (ie == ping.shape[0]-1 -> so we don't go off edge)
                        elif l == ping.shape[0]:
                            # Set c to f-1
                            c = ping[f-1]
                        # zero region somewhere in the middle
                        else:
                            # Set to f-1
                            c = ping[f-1]

                        # Fill zero recion with c
                        ping[f:l+1] = c

                    # Only one zero
                    elif len(z)==1:
                        # Get index
                        f = z[0]

                        # Get next value
                        try:
                            c = ping[f+1]
                        # at end of array, get previous value
                        except:
                            c = ping[f-1]

                        # Fill zero with c
                        ping[f] = c

                    # Else len(zero) entire ping
                    else:
                        break

                # Add water column back in
                ping = list(wc)+list(ping)

                # Update objects filled with ping
                objects_filled[:, p] = ping

        return objects_filled










######
# Begin Old
# #=======================================================================
# def _predSubstrate(self, i, model_name, n_data_bands, winO=1/3):
#     '''
#     Predict substrate type from sonogram.
#
#     ----------
#     Parameters
#     ----------
#
#     ----------------------------
#     Required Pre-processing step
#     ----------------------------
#
#     -------
#     Returns
#     -------
#
#     --------------------
#     Next Processing Step
#     --------------------
#     '''
#
#     # Get chunk size
#     nchunk = self.nchunk
#
#     #################################################
#     # Get depth for water column removal and cropping
#     # Get sonMeta to get depth
#     self._loadSonMeta()
#
#     ############
#     # Load Sonar
#     # Get current chunk, left & right chunk's sonDat and concatenate
#     # Pad is tuple with current chunk H, W and water column pix crop
#     son3Chunk, pad = self._getSon3Chunk(i)
#     # Get dims
#     H, W = son3Chunk.shape
#
#     # #########################
#     # # Convert array to tensor
#     # son3Chunk, w, h, bigimage = seg_file2tensor(son3Chunk, TARGET_SIZE)
#     # son3Chunk = standardize(son3Chunk.numpy()).squeeze()
#     #
#     #
#     # ############################
#     # # For segformer architecture
#     # if model_name == 'segformer':
#     #     if n_data_bands == 1:
#     #         son3Chunk = np.dstack((son3Chunk, son3Chunk, son3Chunk))
#     #     son3Chunk = tf.transpose(son3Chunk, (2, 0, 1))
#
#     ###########################
#     # Get moving window indices
#     movWinInd = self._getMovWinInd(winO, son3Chunk)
#
#     #################################
#     # Make prediction for each window
#     # Expand softmax_score to dims of son3Chunk filled with nan's
#     # Ensure softmax_score in correct location (win offset) in larger array
#     # store each softmax in a list labels=[]
#     # np.nanmean(labels, axis=2)
#
#     # Store each window's softmax
#     winSoftMax = []
#     # Iterate each window
#     for m in movWinInd:
#         # Slice son3Chunk by index
#         # Return son slice, begin and end index
#         sonWin, wStart, wEnd = self._getSonDatWin(m, son3Chunk)
#
#         # Get the model
#         model = self.substrateModel
#
#         # Do prediction, return softmax_score for each class
#         softmax_score = doPredict(model, MODEL, sonWin, N_DATA_BANDS, NCLASSES, TARGET_SIZE)
#
#         # Expand softmax_score to son3Chunk dims, filled with nan's
#         softmax_score = self._expandWin(H, W, wStart, wEnd, softmax_score)
#         # print('softmax_score', softmax_score.shape)
#
#         # Store expanded softmax_score
#         winSoftMax.append(softmax_score)
#
#         del sonWin, wStart, wEnd, softmax_score
#
#     # Take mean across all windows to get one final softmax_score array
#     fSoftmax = np.nanmean(np.stack(winSoftMax, axis=0), axis=0)
#
#     # # Recover fSoftmax to original dimensions
#     # h, w = pad[:-1] # original chunk dimensions
#     # p = pad[-1]-1 # amount of water column cropped
#     # sh, sw = fSoftmax.shape[:-1] # softmax dimensions
#     # c = fSoftmax.shape[-1] # number of classes
#     #
#     # print('Softmax', fSoftmax.shape)
#     # print('Pad', pad)
#     #
#     # if fSoftmax.shape[0] == h:
#     #     fArr = fSoftmax
#     # # elif fSoftmax.shape[0] < h:
#     # #     fArr = np.zeros((h, w, c))
#     # #     fArr[p:p+sh, :, :] = fSoftmax
#     # else:
#     #     fArr = np.zeros((h, w, c))
#     #
#     #     # Check if need to trim softmax
#     #     # if (p+sh) > h:
#     #     # 2091 to 1967
#     #     print(sh, h-p)
#     #     if sh > (h-p):
#     #         fSoftmax = fSoftmax[:-p, :, :]
#     #         sh = fSoftmax.shape[0]
#     #     fArr[p:p+sh, :, :] = fSoftmax
#
#     # Recover fSoftmax to original vertical dimensions
#     h, w = pad[0], pad[1] # original chunk dimensions
#     wc_crop = pad[2] # amount of water column cropped
#     r_crop = pad[3] # amount of range cropped
#     sh, sw = fSoftmax.shape[0], fSoftmax.shape[1] # softmax dimensions
#     c = fSoftmax.shape[2] # number of classes
#
#     print('\n\n\n\nGut Check')
#     print('Orig Dims:', h, w)
#     print('WC cropped:', wc_crop)
#     print('Range Cropped:', r_crop)
#     print('Softmax Shape', fSoftmax.shape)
#
#     # Crop fSoftmax to current chunk
#     # fSoftmax = fSoftmax[:, nchunk:nchunk+pad[1], :]
#     fSoftmax = fSoftmax[:, nchunk:2*nchunk, :]
#     # print('fSoftmax', fSoftmax.shape, nchunk, pad[1])
#
#     fArr = np.zeros((h, w, c))
#
#     # fArr[wc_crop:wc_crop+h, :, :] = fSoftmax[:h, :, :]
#
#     # Determine top offset
#     if wc_crop > 0:
#         topOff = wc_crop
#     else:
#         topOff = 0 # No offset necessary
#
#     # Determine if softmax or fArr needs to be sliced on bottom to get correct dims
#     bottomOff = sh - (fArr.shape[0] - wc_crop)
#
#     # If bottomOff < 0: Need to slice bottom of fArr to fit smaller softmax dims
#     if bottomOff < 0:
#         bottomOff = fArr.shape[0] + bottomOff
#         fArr[wc_crop:bottomOff, :, :] = fSoftmax
#
#         # Set definate shadows to 1.0
#         # Shadow second to last class
#         fArr[bottomOff:, :, -2] = 1.0
#
#     # Need to slice softmax bottom to fit in fArr
#     elif bottomOff > 0:
#         # bottomOff = fSoftmax.shape[0] - bottomOff
#         # fArr[:bottomOff] = fSoftmax[:bottomOff, :, :]
#
#         bottomOff = fArr.shape[0] - wc_crop
#         fArr[wc_crop:, :, :] = fSoftmax[:bottomOff, :, :]
#
#     # No slicing necessary
#     else:
#         fArr = fSoftmax
#
#     # # Determine if softmax bottom needs to be cropped
#     # if (fArr.shape[0] - wc_crop) > sh:
#     #     # fArr with offset larger then softmax
#     #     # Need to slice fArr to compensate
#     #     bottomOff = sh - (fArr.shape[0] - wc_crop) # This should be negative ???
#     #
#     # elif (fArr.shape[0] - wc_crop) < sh:
#     #     # fArr with offset smaller then softmax
#     #     # Need to slice softmax to compensate
#     #     bottomOff = sh - (fArr.shape[0] - wc_crop)
#     #
#     # else:
#     #     bottomOff = 0 # Bottom alread aligned
#
#     # Make sure softmax is 1.0 for areas definately water and shadow
#     # Shadow second to last class
#     # fArr[p+sh, :, -2] = 1.0
#     # fArr[p+sh-1:, :, -2] = 1.0
#
#     # Make sure softmax is 1.0 for areas definately water
#     # Water last class
#     fArr[:wc_crop, :, -1] = 1.0
#
#     # print(fArr.shape, np.min(fArr), np.max(fArr))
#     del fSoftmax, son3Chunk
#     gc.collect()
#
#     return fArr


# #=======================================================================
# def _getSon3Chunk(self, i):
#
#     '''
#     Get current (i), left (i-1) & right (i+1) chunk's sonDat.
#     Concatenate into one array.
#     '''
#     nchunk = self.nchunk
#     df = self.sonMetaDF
#
#
#     ######
#     # Left
#     # Get sonDat
#     self._getScanChunkSingle(i-1)
#     # # Image dimensions
#     # h, w = self.sonDat.shape
#     # if h > H:
#     #     H = h
#     #     W = w
#
#     # Crop shadows first
#     _ = self._SHW_crop(i-1, False)
#
#     # Get sonMetaDF
#     lMetaDF = df.loc[df['chunk_id'] == i-1, ['dep_m']].copy()
#
#     # Remove water column and crop
#     lMinDep = self._WCR_crop(lMetaDF)
#
#     # Create copy of sonar data
#     lSonDat = self.sonDat.copy()
#     # print('\n\n\n', lSonDat.shape)
#
#     ########
#     # Center
#     # Get sonDat
#     self._getScanChunkSingle(i)
#
#     # Original image dimensions
#     H, W = self.sonDat.shape
#
#     # Crop shadows first
#     max_r = self._SHW_crop(i, False)
#     print('\n\n\nmax_r', max_r)
#
#     # Get sonMetaDF
#     cMetaDF = df.loc[df['chunk_id'] == i, ['dep_m']].copy()
#
#     # Remove water column and crop
#     cMinDep = self._WCR_crop(cMetaDF)
#
#     # Create copy of sonar data
#     cSonDat = self.sonDat.copy()
#     # print(cSonDat.shape)
#
#     # Cropped dims (??)
#     h, w = cSonDat.shape
#
#     ########
#     # Right
#     # Get sonDat
#     self._getScanChunkSingle(i+1)
#
#     # # Image dimensions
#     # h, w = self.sonDat.shape
#     # if h > H:
#     #     H = h
#     #     W = w
#
#     # Crop shadows first
#     _ = self._SHW_crop(i+1, False)
#
#     # Get sonMetaDF
#     rMetaDF = df.loc[df['chunk_id'] == i+1, ['dep_m']].copy()
#
#     # Remove water column and crop
#     rMinDep = self._WCR_crop(rMetaDF)
#
#     # Create copy of sonar data
#     rSonDat = self.sonDat.copy()
#     # print(rSonDat.shape)
#
#     del self.sonDat
#
#     #############################
#     # Merge left, center, & right
#
#     # Align arrays based on wc_crops
#
#     # Find min depth
#     minDep = min(lMinDep, cMinDep, rMinDep)
#
#     # Pad arrays if chunk's minDep > minDep and fill with zero's
#     # Left
#     if lMinDep > minDep:
#         # Get current sonDat shape
#         r, c = lSonDat.shape
#
#         # Determine pad size (actual offset from top)
#         pad = lMinDep - minDep
#
#         # Make new zero array w/ pad added in
#         newArr = np.zeros((pad+r, c))
#         # Fill with nan to prevent unneeded prediction
#         newArr.fill(np.nan)
#
#         # Fill sonDat in appropriate location
#         newArr[pad:,:] = lSonDat
#         lSonDat = newArr.copy()
#         del newArr
#
#     # Center
#     if cMinDep > minDep:
#         # Get current sonDat shape
#         r, c = cSonDat.shape
#
#         # Determine pad size
#         pad = cMinDep - minDep
#
#         # Make new zero array w/ pad added in
#         newArr = np.zeros((pad+r, c))
#         # Fill with nan to prevent unneeded prediction
#         newArr.fill(np.nan)
#
#         # Fill sonDat in appropriate location
#         newArr[pad:,:] = cSonDat
#         cSonDat = newArr.copy()
#         del newArr
#
#         # Return cpad to recover original dims
#         cpad = pad
#     else:
#         cpad = cMinDep
#
#     # Right
#     if rMinDep > minDep:
#         # Get current sonDat shape
#         r, c = rSonDat.shape
#         # Determine pad size
#         pad = rMinDep - minDep
#
#         # Make new zero array w/ pad added in
#         newArr = np.zeros((pad+r, c))
#         # Fill with nan to prevent unneeded prediction
#         newArr.fill(np.nan)
#
#         # Fill sonDat in appropriate location
#         newArr[pad:,:] = rSonDat
#         rSonDat = newArr.copy()
#         del newArr
#
#     # If range of center chunk < other chunks, slice other chunks
#     if h < lSonDat.shape[0]:
#         lSonDat = lSonDat[:H,:]
#
#     if h < rSonDat.shape[0]:
#         rSonDat = rSonDat[:H,:]
#
#     # Find max rows across each chunk
#     maxR = max(lSonDat.shape[0], cSonDat.shape[0], rSonDat.shape[0])
#
#     # Find max cols
#     maxC = lSonDat.shape[1] + cSonDat.shape[1] + rSonDat.shape[1]
#
#     # Create final array of appropriate size
#     fSonDat = np.zeros((maxR, maxC))
#     # Fill with nan to prevent unneeded prediction
#     fSonDat.fill(np.nan)
#
#     # Add left sonDat into fSonDat
#     fSonDat[:lSonDat.shape[0],:nchunk] = lSonDat
#
#     # Add center sonDat into fSonDat
#     fSonDat[:cSonDat.shape[0], nchunk:nchunk*2] = cSonDat
#
#     # Add right sonDat into fSonDat
#     fSonDat[:rSonDat.shape[0], nchunk*2:] = rSonDat
#
#     # Export image check
#     try:
#         os.mkdir(self.outDir)
#     except:
#         pass
#     self.sonDat = fSonDat
#     self._writeTiles(i, 'test')
#     print(self.outDir)
#
#     # fSonDat = standardize(fSonDat)
#
#     print('fSonDat', fSonDat.shape)
#     print('pad', H, W, cpad)
#
#     # return fSonDat, (H, W, minDep)
#     return fSonDat, (H, W, cpad, max_r)

# End Old
#########
