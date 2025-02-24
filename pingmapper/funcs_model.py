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


# Imports
import sys, os

# Add 'pingmapper' to the path, may not need after pypi package...
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.append(PACKAGE_DIR)

from pingmapper.funcs_common import *
os.environ['TF_CPP_MIN_LOG_LEVEL']='3'
import json
import numpy as np
import tensorflow as tf
import tensorflow.keras.backend as K
from tensorflow.python.client import device_lib

import itertools

from transformers import TFSegformerForSemanticSegmentation
from transformers import logging
logging.set_verbosity_error()

# Fixes depth detection warning
tf.get_logger().setLevel('ERROR')

from doodleverse_utils.imports import *
from doodleverse_utils.model_imports import *
from doodleverse_utils.prediction_imports import *

################################################################################
# model_imports.py from segmentation_gym                                       #
################################################################################
'''
Utilities provided courtesy Dr. Dan Buscombe from segmentation_gym
https://github.com/Doodleverse/segmentation_gym
'''

#=======================================================================
def initModel(weights, configfile, USE_GPU=False):
    '''
    Compiles a Tensorflow model for segmentation. Developed following:
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
    Compiled model.

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

    #suppress tensorflow warnings
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

    # Open model configuration file
    with open(configfile) as f:
        config = json.load(f)
    globals().update(config)


    ########################################################################
    ########################################################################

    # Get model architecture
    if MODEL == 'resunet':
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

    elif MODEL == 'segformer':
        id2label = {}
        for k in range(NCLASSES):
            id2label[k]=str(k)
        model = segformer(id2label,num_classes=NCLASSES)

    model.load_weights(weights)
    # model = compile_models([model[0]], MODEL)

    return model, MODEL, N_DATA_BANDS

################################################
# prediction_imports.py from doodleverse_utils #
################################################

#=======================================================================
def doPredict(model, MODEL, arr, N_DATA_BANDS, NCLASSES, TARGET_SIZE, OTSU_THRESHOLD, shadow=False):

    '''
    '''

    model = compile_models([model[0]], MODEL)

    # Read array into a cropped and resized tensor
    image, w, h, bigimage = seg_file2tensor(arr, N_DATA_BANDS, TARGET_SIZE, MODEL)

    image = standardize(image.numpy()).squeeze()

    # Kludge to fix error noted in Issue #128
    if shadow:
        image = image[:,:,0]
        image = tf.expand_dims(image, 2)

    if NCLASSES == 2:

        E0, E1 = est_label_binary(image, model, MODEL, False, NCLASSES, TARGET_SIZE, w, h)

        e0 = np.average(np.dstack(E0), axis=-1)

        e1 = np.average(np.dstack(E1), axis=-1)

        est_label = (e1 + (1 - e0)) / 2

        softmax_scores = np.dstack((e0,e1))

        if OTSU_THRESHOLD:
            thres = threshold_otsu(est_label)
            est_label = (est_label > thres).astype('uint8')
        else:
            est_label = (est_label > 0.5).astype('uint8')

    else: # NCLASSES>2
        est_label, counter = est_label_multiclass(image, model, MODEL, False, NCLASSES, TARGET_SIZE)

        est_label /= counter + 1
        # est_label cannot be float16 so convert to float32
        est_label = est_label.numpy().astype('float32')

        if MODEL=='segformer':
            est_label = resize(est_label, (1, NCLASSES, TARGET_SIZE[0],TARGET_SIZE[1]), preserve_range=True, clip=True).squeeze()
            est_label = np.transpose(est_label, (1,2,0))
            est_label = resize(est_label, (w, h))
        else:
            est_label = resize(est_label, (w, h))

        softmax_scores = est_label.copy()

        est_label = np.argmax(softmax_scores, -1)


    return est_label, softmax_scores


#=======================================================================
def seg_file2tensor(bigimage, N_DATA_BANDS, TARGET_SIZE, MODEL):#, resize):
    """
    "seg_file2tensor(f)"
    This function reads a jpeg image from file into a cropped and resized tensor,
    for use in prediction with a trained segmentation model
    INPUTS:
        * f [string] file name of jpeg
    OPTIONAL INPUTS: None
    OUTPUTS:
        * image [tensor array]: unstandardized image
    GLOBAL INPUTS: TARGET_SIZE
    """

    image = resize(bigimage,(TARGET_SIZE[0], TARGET_SIZE[1]), preserve_range=True, clip=True)
    image = np.array(image)
    image = tf.cast(image, tf.uint8)

    w = tf.shape(bigimage)[0]
    h = tf.shape(bigimage)[1]

    if MODEL=='segformer':
        if np.ndim(image)==2:
            image = np.dstack((image, image, image))
        image = tf.transpose(image, (2, 0, 1))

    return image, w, h, bigimage


