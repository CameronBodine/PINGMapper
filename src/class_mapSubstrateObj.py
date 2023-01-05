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
                         i):
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
            substratePred, i = self._predSubstrate(i)


        gc.collect()
        return

    #=======================================================================
    def _predSubstrate(self,
                       i):
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
        # Load sonar
        self._getScanChunkSingle(i)

        # Get original sonDat dimesions
        R, W = self.sonDat.shape

        #################################################
        # Get depth for water column removal and cropping

        # Get sonMeta to get depth
        self._loadSonMeta()
        df = self.sonMetaDF

        # Get depth/ pix scaler for given chunk
        df = df.loc[df['chunk_id'] == i, ['dep_m', 'pix_m']]

        # Crop water column and crop to min depth
        sonMinDep = self._WCR_crop(df)

        #################################################
        # Crop shadow
        self._SHW_crop(i, 2)

        ###############
        # Do prediction


        return 1, 2
