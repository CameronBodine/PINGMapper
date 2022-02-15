#
# import os, time
# import json
# import tensorflow as tf
# import numpy as np
#
# from skimage.morphology import remove_small_holes, remove_small_objects
# from skimage.transform import resize
# from skimage.filters import threshold_otsu
# from skimage.measure import label, regionprops
#
# import tensorflow.keras.backend as K
#
# #suppress tensorflow warnings
# os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
#
# #===============================================================================
# def standardize(img, mn, mx, stack1d=False):
#     '''
#     Helper function to standardize an image
#     '''
#     #standardization using adjusted standard deviation
#     N = np.shape(img)[0] * np.shape(img)[1]
#     s = np.maximum(np.std(img), 1.0/np.sqrt(N))
#     m = np.mean(img)
#     img = (img - m) / s
#     img = rescale(img, mn, mx)
#     del m, s, N
#
#     if (np.ndim(img)!=3) & stack1d:
#         img = np.dstack((img,img,img))
#
#     return img
#
# #===============================================================================
# def rescale( dat,
#              mn,
#              mx):
#     '''
#     rescales an input dat between mn and mx
#     '''
#     m = min(dat.flatten())
#     M = max(dat.flatten())
#     return (mx-mn)*(dat-m)/(M-m)+mn
#
# #===============================================================================
# def mean_iou(y_true, y_pred):
#     """
#     mean_iou(y_true, y_pred)
#     This function computes the mean IoU between `y_true` and `y_pred`: this version is tensorflow (not numpy) and is used by tensorflow training and evaluation functions
#
#     INPUTS:
#         * y_true: true masks, one-hot encoded.
#             * Inputs are B*W*H*N tensors, with
#                 B = batch size,
#                 W = width,
#                 H = height,
#                 N = number of classes
#         * y_pred: predicted masks, either softmax outputs, or one-hot encoded.
#             * Inputs are B*W*H*N tensors, with
#                 B = batch size,
#                 W = width,
#                 H = height,
#                 N = number of classes
#     OPTIONAL INPUTS: None
#     GLOBAL INPUTS: None
#     OUTPUTS:
#         * IoU score [tensor]
#     """
#     yt0 = y_true[:,:,:,0]
#     yp0 = tf.keras.backend.cast(y_pred[:,:,:,0] > 0.5, 'float32')
#     inter = tf.math.count_nonzero(tf.logical_and(tf.equal(yt0, 1), tf.equal(yp0, 1)))
#     union = tf.math.count_nonzero(tf.add(yt0, yp0))
#     iou = tf.where(tf.equal(union, 0), 1., tf.cast(inter/union, 'float32'))
#     return iou
#
# #===============================================================================
# def dice_coef(y_true, y_pred):
#     """
#     dice_coef(y_true, y_pred)
#
#     This function computes the mean Dice coefficient between `y_true` and `y_pred`: this version is tensorflow (not numpy) and is used by tensorflow training and evaluation functions
#
#     INPUTS:
#         * y_true: true masks, one-hot encoded.
#             * Inputs are B*W*H*N tensors, with
#                 B = batch size,
#                 W = width,
#                 H = height,
#                 N = number of classes
#         * y_pred: predicted masks, either softmax outputs, or one-hot encoded.
#             * Inputs are B*W*H*N tensors, with
#                 B = batch size,
#                 W = width,
#                 H = height,
#                 N = number of classes
#     OPTIONAL INPUTS: None
#     GLOBAL INPUTS: None
#     OUTPUTS:
#         * Dice score [tensor]
#     """
#     smooth = 1.
#     y_true_f = tf.reshape(tf.dtypes.cast(y_true, tf.float32), [-1])
#     y_pred_f = tf.reshape(tf.dtypes.cast(y_pred, tf.float32), [-1])
#     intersection = tf.reduce_sum(y_true_f * y_pred_f)
#     return (2. * intersection + smooth) / (tf.reduce_sum(y_true_f) + tf.reduce_sum(y_pred_f) + smooth)
#
# # =========================================================
# def getWindowIndices(val, win, overlap):
#     stride = win
#
#     if overlap > 0:
#         win_cnt = np.ceil(val / (win*overlap))
#     else:
#         win_cnt = np.ceil(val / win)
#     stride = np.floor(val/win_cnt).astype(int)
#
#     win_i = [0]
#     i = 1
#     offset = stride
#     while i < win_cnt:
#         if (offset + win) <= val:
#             win_i.append(offset)
#         else:
#             win_i.append(val-win)
#         offset += stride
#         i+=1
#
#     win_i = sorted(list(set(win_i)))
#     return win_i, stride
#
# ################################################################################
# ### MODEL FUNCTIONS
# ################################################################################
# #-----------------------------------
# def batchnorm_act(x):
#     """
#     batchnorm_act(x)
#     This function applies batch normalization to a keras model layer, `x`, then a relu activation function
#     INPUTS:
#         * `z` : keras model layer (should be the output of a convolution or an input layer)
#     OPTIONAL INPUTS: None
#     GLOBAL INPUTS: None
#     OUTPUTS:
#         * batch normalized and relu-activated `x`
#     """
#     x = tf.keras.layers.BatchNormalization()(x)
#     return tf.keras.layers.Activation("relu")(x)
#
# #-----------------------------------
# def conv_block(x, filters, kernel_size = (7,7), padding="same", strides=1):
#     """
#     conv_block(x, filters, kernel_size = (7,7), padding="same", strides=1)
#     This function applies batch normalization to an input layer, then convolves with a 2D convol layer
#     The two actions combined is called a convolutional block
#
#     INPUTS:
#         * `filters`: number of filters in the convolutional block
#         * `x`:input keras layer to be convolved by the block
#     OPTIONAL INPUTS:
#         * `kernel_size`=(3, 3): tuple of kernel size (x, y) - this is the size in pixels of the kernel to be convolved with the image
#         * `padding`="same":  see tf.keras.layers.Conv2D
#         * `strides`=1: see tf.keras.layers.Conv2D
#     GLOBAL INPUTS: None
#     OUTPUTS:
#         * keras layer, output of the batch normalized convolution
#     """
#     conv = batchnorm_act(x)
#     return tf.keras.layers.Conv2D(filters, kernel_size, padding=padding, strides=strides)(conv)
#
# #-----------------------------------
# def bottleneck_block(x, filters, kernel_size = (7,7), padding="same", strides=1):
#     """
#     bottleneck_block(x, filters, kernel_size = (7,7), padding="same", strides=1)
#
#     This function creates a bottleneck block layer, which is the addition of a convolution block and a batch normalized/activated block
#     INPUTS:
#         * `filters`: number of filters in the convolutional block
#         * `x`: input keras layer
#     OPTIONAL INPUTS:
#         * `kernel_size`=(3, 3): tuple of kernel size (x, y) - this is the size in pixels of the kernel to be convolved with the image
#         * `padding`="same":  see tf.keras.layers.Conv2D
#         * `strides`=1: see tf.keras.layers.Conv2D
#     GLOBAL INPUTS: None
#     OUTPUTS:
#         * keras layer, output of the addition between convolutional and bottleneck layers
#     """
#     conv = tf.keras.layers.Conv2D(filters, kernel_size, padding=padding, strides=strides)(x)
#     conv = conv_block(conv, filters, kernel_size=kernel_size, padding=padding, strides=strides)
#
#     bottleneck = tf.keras.layers.Conv2D(filters, kernel_size=(1, 1), padding=padding, strides=strides)(x)
#     bottleneck = batchnorm_act(bottleneck)
#
#     return tf.keras.layers.Add()([conv, bottleneck])
#
# #-----------------------------------
# def res_block(x, filters, kernel_size = (7,7), padding="same", strides=1):
#     """
#     res_block(x, filters, kernel_size = (7,7), padding="same", strides=1)
#
#     This function creates a residual block layer, which is the addition of a residual convolution block and a batch normalized/activated block
#     INPUTS:
#         * `filters`: number of filters in the convolutional block
#         * `x`: input keras layer
#     OPTIONAL INPUTS:
#         * `kernel_size`=(3, 3): tuple of kernel size (x, y) - this is the size in pixels of the kernel to be convolved with the image
#         * `padding`="same":  see tf.keras.layers.Conv2D
#         * `strides`=1: see tf.keras.layers.Conv2D
#     GLOBAL INPUTS: None
#     OUTPUTS:
#         * keras layer, output of the addition between residual convolutional and bottleneck layers
#     """
#     res = conv_block(x, filters, kernel_size=kernel_size, padding=padding, strides=strides)
#     res = conv_block(res, filters, kernel_size=kernel_size, padding=padding, strides=1)
#
#     bottleneck = tf.keras.layers.Conv2D(filters, kernel_size=(1, 1), padding=padding, strides=strides)(x)
#     bottleneck = batchnorm_act(bottleneck)
#
#     return tf.keras.layers.Add()([bottleneck, res])
#
# #-----------------------------------
# def upsamp_concat_block(x, xskip):
#     """
#     upsamp_concat_block(x, xskip)
#     This function takes an input layer and creates a concatenation of an upsampled version and a residual or 'skip' connection
#     INPUTS:
#         * `xskip`: input keras layer (skip connection)
#         * `x`: input keras layer
#     OPTIONAL INPUTS: None
#     GLOBAL INPUTS: None
#     OUTPUTS:
#         * keras layer, output of the addition between residual convolutional and bottleneck layers
#     """
#     u = tf.keras.layers.UpSampling2D((2, 2))(x)
#     return tf.keras.layers.Concatenate()([u, xskip])
#
# #-----------------------------------
# def res_unet(sz, f, nclasses=1):
#     """
#     res_unet(sz, f, nclasses=1)
#     This function creates a custom residual U-Net model for image segmentation
#     INPUTS:
#         * `sz`: [tuple] size of input image
#         * `f`: [int] number of filters in the convolutional block
#         * flag: [string] if 'binary', the model will expect 2D masks and uses sigmoid. If 'multiclass', the model will expect 3D masks and uses softmax
#         * nclasses [int]: number of classes
#     OPTIONAL INPUTS:
#         * `kernel_size`=(3, 3): tuple of kernel size (x, y) - this is the size in pixels of the kernel to be convolved with the image
#         * `padding`="same":  see tf.keras.layers.Conv2D
#         * `strides`=1: see tf.keras.layers.Conv2D
#     GLOBAL INPUTS: None
#     OUTPUTS:
#         * keras model
#     """
#     inputs = tf.keras.layers.Input(sz)
#
#     ## downsample
#     e1 = bottleneck_block(inputs, f); f = int(f*2)
#     e2 = res_block(e1, f, strides=2); f = int(f*2)
#     e3 = res_block(e2, f, strides=2); f = int(f*2)
#     e4 = res_block(e3, f, strides=2); f = int(f*2)
#     _ = res_block(e4, f, strides=2)
#
#     ## bottleneck
#     b0 = conv_block(_, f, strides=1)
#     _ = conv_block(b0, f, strides=1)
#
#     ## upsample
#     _ = upsamp_concat_block(_, e4)
#     _ = res_block(_, f); f = int(f/2)
#
#     _ = upsamp_concat_block(_, e3)
#     _ = res_block(_, f); f = int(f/2)
#
#     _ = upsamp_concat_block(_, e2)
#     _ = res_block(_, f); f = int(f/2)
#
#     _ = upsamp_concat_block(_, e1)
#     _ = res_block(_, f)
#
#     ## classify
#     if nclasses==1:
#         outputs = tf.keras.layers.Conv2D(nclasses, (1, 1), padding="same", activation="sigmoid")(_)
#     else:
#         outputs = tf.keras.layers.Conv2D(nclasses, (1, 1), padding="same", activation="softmax")(_)
#
#     #model creation
#     model = tf.keras.models.Model(inputs=[inputs], outputs=[outputs])
#     return model
#
# #-----------------------------------
# def seg_file2tensor_3band(f, TARGET_SIZE, resize):
#     """
#     "seg_file2tensor(f)"
#     This function reads a jpeg image from file into a cropped and resized tensor,
#     for use in prediction with a trained segmentation model
#     INPUTS:
#         * f [string] file name of jpeg
#     OPTIONAL INPUTS: None
#     OUTPUTS:
#         * image [tensor array]: unstandardized image
#     GLOBAL INPUTS: TARGET_SIZE
#     """
#     # bits = tf.io.read_file(f)
#     # if 'jpg' in f:
#     #     bigimage = tf.image.decode_jpeg(bits)
#     # elif 'png' in f:
#     #     bigimage = tf.image.decode_png(bits)
#     f = np.expand_dims(f, axis=2)
#     bigimage = tf.convert_to_tensor(f, dtype=tf.uint8)
#
#     # if USE_LOCATION:
#     #     gx,gy = np.meshgrid(np.arange(bigimage.shape[1]), np.arange(bigimage.shape[0]))
#     #     loc = np.sqrt(gx**2 + gy**2)
#     #     loc /= loc.max()
#     #     loc = (255*loc).astype('uint8')
#     #     bigimage = np.dstack((bigimage, loc))
#
#     w = tf.shape(bigimage)[0]
#     h = tf.shape(bigimage)[1]
#
#     if resize:
#
#         tw = TARGET_SIZE[0]
#         th = TARGET_SIZE[1]
#         resize_crit = (w * th) / (h * tw)
#         image = tf.cond(resize_crit < 1,
#                       lambda: tf.image.resize(bigimage, [w*tw/w, h*tw/w]), # if true
#                       lambda: tf.image.resize(bigimage, [w*th/h, h*th/h])  # if false
#                      )
#
#         nw = tf.shape(image)[0]
#         nh = tf.shape(image)[1]
#         image = tf.image.crop_to_bounding_box(image, (nw - tw) // 2, (nh - th) // 2, tw, th)
#         # image = tf.cast(image, tf.uint8) #/ 255.0
#
#
#
#         return image, w, h, bigimage
#
#     else:
#         return None, w, h, bigimage
