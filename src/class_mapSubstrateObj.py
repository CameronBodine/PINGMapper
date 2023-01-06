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
    def _detectSubstrate(self,
                         method,
                         i,
                         USE_GPU):
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


        if method == 1:
            # Initialize the model
            if not hasattr(self, 'substrateModel'):
                model = initModel(self.weights, self.configfile, USE_GPU)
                self.substrateModel = model

            # Do prediction
            substratePred, i = self._predSubstrate(i)


        gc.collect()
        return

    #=======================================================================
    def _predSubstrate(self, i, winO=1/3):
        '''
        Predict substrate type from sonogram.

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
        # # Load sonar
        # self._getScanChunkSingle(i)
        #
        # # Get original sonDat dimesions
        # R, W = self.sonDat.shape
        #
        # #################################################
        # # Get depth for water column removal and cropping
        # # Get sonMeta to get depth
        # self._loadSonMeta()
        # df = self.sonMetaDF
        #
        # # Get depth/ pix scaler for given chunk
        # df = df.loc[df['chunk_id'] == i, ['dep_m', 'pix_m']]
        #
        # # Crop water column and crop to min depth
        # sonMinDep = self._WCR_crop(df)
        #
        # #################################################
        # # Crop shadow
        # self._SHW_crop(i, False)
        #
        # ###############
        # # Do prediction
        # # model = self.substrateModel
        # label, prob = doPredict(self.substrateModel, self.sonDat)

        # Get chunk size
        nchunk = self.nchunk

        #################################################
        # Get depth for water column removal and cropping
        # Get sonMeta to get depth
        self._loadSonMeta()

        ############
        # Load Sonar
        # Get current chunk, left & right chunk's sonDat and concatenate
        # Pad is tuple with current chunk H, W and water column pix crop
        son3Chunk, pad = self._getSon3Chunk(i)
        # Get dims
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
        for w in movWinInd:
            # Slice son3Chunk by index
            # Return son slice, begin and end index
            sonWin, wStart, wEnd = self._getSonDatWin(w, son3Chunk)

            # Get the model
            model = self.substrateModel

            # Do prediction, return softmax_score for each class
            softmax_score = doPredict(model, sonWin)

            # Expand softmax_score to son3Chunk dims, filled with nan's
            softmax_score = self._expandWin(H, W, wStart, wEnd, softmax_score)

            # Store expanded softmax_score
            winSoftMax.append(softmax_score)

            del sonWin, wStart, wEnd, softmax_score

        # Take mean across all windows to get one final softmax_score array
        fSoftmax = np.nanmean(np.stack(winSoftMax, axis=0), axis=0)

        # Crop fSoftmax to current chunk
        fSoftmax = fSoftmax[:, nchunk:nchunk+pad[1], :]

        # Recover fSoftmax to original dimensions
        h, w = pad[:-1] # original chunk dimensions
        p = pad[-1] # amount of water column cropped
        sh, sw = fSoftmax.shape[:-1] # softmax dimensions
        c = fSoftmax.shape[-1] # number of classes

        fArr = np.zeros((h, w, c))
        fArr[p:p+sh, :, :] = fSoftmax

        print(fArr.shape, np.min(fArr), np.max(fArr))

        return 1, 2

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
        H, W = arr.shape

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
    def _getSon3Chunk(self, i):
        '''
        Get current (i), left (i-1) & right (i+1) chunk's sonDat.
        Concatenate into one array.
        '''
        nchunk = self.nchunk
        df = self.sonMetaDF

        ######
        # Left
        # Get sonDat
        self._getScanChunkSingle(i-1)

        # Crop shadows first
        self._SHW_crop(i-1, True)

        # Get sonMetaDF
        lMetaDF = df.loc[df['chunk_id'] == i-1, ['dep_m', 'pix_m']].copy()

        # Remove water column and crop
        lMinDep = self._WCR_crop(lMetaDF)

        # Create copy of sonar data
        lSonDat = self.sonDat.copy()
        # print('\n\n\n', lSonDat.shape)

        ########
        # Center
        # Get sonDat
        self._getScanChunkSingle(i)

        # Get dimensions
        H, W = self.sonDat.shape

        # Crop shadows first
        self._SHW_crop(i, True)

        # Get sonMetaDF
        cMetaDF = df.loc[df['chunk_id'] == i, ['dep_m', 'pix_m']].copy()

        # Remove water column and crop
        cMinDep = self._WCR_crop(cMetaDF)

        # Create copy of sonar data
        cSonDat = self.sonDat.copy()
        # print(cSonDat.shape)

        ########
        # Right
        # Get sonDat
        self._getScanChunkSingle(i+1)

        # Crop shadows first
        self._SHW_crop(i+1, True)

        # Get sonMetaDF
        rMetaDF = df.loc[df['chunk_id'] == i+1, ['dep_m', 'pix_m']].copy()

        # Remove water column and crop
        rMinDep = self._WCR_crop(rMetaDF)

        # Create copy of sonar data
        rSonDat = self.sonDat.copy()
        # print(rSonDat.shape)

        #############################
        # Merge left, center, & right

        # Find min depth
        minDep = min(lMinDep, cMinDep, rMinDep)

        # Pad arrays if chunk's minDep > minDep and fill with zero's
        # Left
        if lMinDep > minDep:
            # Get current sonDat shape
            r, c = lSonDat.shape
            # Determine pad size
            pad = lMinDep - minDep

            # Make new zero array w/ pad added in
            newArr = np.zeros((pad+r, c))

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

            # Fill sonDat in appropriate location
            newArr[pad:,:] = cSonDat
            cSonDat = newArr.copy()
            del newArr

        # Right
        if rMinDep > minDep:
            # Get current sonDat shape
            r, c = rSonDat.shape
            # Determine pad size
            pad = rMinDep - minDep

            # Make new zero array w/ pad added in
            newArr = np.zeros((pad+r, c))

            # Fill sonDat in appropriate location
            newArr[pad:,:] = rSonDat
            rSonDat = newArr.copy()
            del newArr

        # Find max rows across each chunk
        maxR = max(lSonDat.shape[0], cSonDat.shape[0], rSonDat.shape[0])

        # Find max cols
        maxC = lSonDat.shape[1] + cSonDat.shape[1] + rSonDat.shape[1]

        # Create final array of appropriate size
        fSonDat = np.zeros((maxR, maxC))

        # Add left sonDat into fSonDat
        fSonDat[:lSonDat.shape[0],:nchunk] = lSonDat

        # Add center sonDat into fSonDat
        fSonDat[:cSonDat.shape[0], nchunk:nchunk*2] = cSonDat

        # Add right sonDat into fSonDat
        fSonDat[:rSonDat.shape[0], nchunk*2:] = rSonDat

        # # Export image check
        # try:
        #     os.mkdir(self.outDir)
        # except:
        #     pass
        # self.sonDat = fSonDat
        # self._writeTiles(i, 'test')

        return fSonDat, (H, W, minDep)



    # #=======================================================================
    # def _predSubstrate(self, i):
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
    #     # Load sonar
    #     self._getScanChunkSingle(i)
    #
    #     # Get original sonDat dimesions
    #     R, W = self.sonDat.shape
    #
    #     #################################################
    #     # Get depth for water column removal and cropping
    #     # Get sonMeta to get depth
    #     self._loadSonMeta()
    #     df = self.sonMetaDF
    #
    #     # Get depth/ pix scaler for given chunk
    #     df = df.loc[df['chunk_id'] == i, ['dep_m', 'pix_m']]
    #
    #     # Crop water column and crop to min depth
    #     sonMinDep = self._WCR_crop(df)
    #
    #     #################################################
    #     # Crop shadow
    #     self._SHW_crop(i, 2)
    #
    #     ###############
    #     # Do prediction
    #     # model = self.substrateModel
    #     label, prob = doPredict(self.substrateModel, self.sonDat)
    #
    #
    #     return 1, 2
