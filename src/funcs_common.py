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

import os, sys, struct, gc
from joblib import Parallel, delayed, cpu_count
from glob import glob

################################################################################
import warnings
warnings.simplefilter("ignore")
################################################################################

import numpy as np
from array import array as arr

import pyproj
import rasterio
from numpy.lib.stride_tricks import as_strided as ast

import pandas as pd

from collections import defaultdict
from copy import deepcopy
import pickle
import shutil

import time
import datetime

# from skimage.filters import median
# from skimage.morphology import square
from skimage.io import imsave
from skimage.transform import resize
from skimage.measure import label, regionprops
from skimage.segmentation import watershed

import psutil

# # =========================================================
# # Keep
# def norm_shape(shap):
#    '''
#    Normalize numpy array shapes so they're always expressed as a tuple,
#    even for one-dimensional shapes.
#    '''
#    try:
#       i = int(shap)
#       return (i,)
#    except TypeError:
#       # shape was not a number
#       pass
#
#    try:
#       t = tuple(shap)
#       return t
#    except TypeError:
#       # shape was not iterable
#       pass
#
#    raise TypeError('shape must be an int, or a tuple of ints')

# # =========================================================
# # Keep
# def sliding_window(a,ws,ss = None,flatten = True):
#     '''
#     Return a sliding window over a in any number of dimensions
#     '''
#     if None is ss:
#         # ss was not provided. the windows will not overlap in any direction.
#         ss = ws
#     ws = norm_shape(ws)
#     ss = norm_shape(ss)
#     # convert ws, ss, and a.shape to numpy arrays
#     ws = np.array(ws)
#     ss = np.array(ss)
#     shap = np.array(a.shape)
#     # ensure that ws, ss, and a.shape all have the same number of dimensions
#     ls = [len(shap),len(ws),len(ss)]
#     if 1 != len(set(ls)):
#         raise ValueError(\
#         'a.shape, ws and ss must all have the same length. They were %s' % str(ls))
#
#     # ensure that ws is smaller than a in every dimension
#     if np.any(ws > shap):
#         raise ValueError(\
#         'ws cannot be larger than a in any dimension.\
#          a.shape was %s and ws was %s' % (str(a.shape),str(ws)))
#     # how many slices will there be in each dimension?
#     newshape = norm_shape(((shap - ws) // ss) + 1)
#     # the shape of the strided array will be the number of slices in each dimension
#     # plus the shape of the window (tuple addition)
#     newshape += norm_shape(ws)
#     # the strides tuple will be the array's strides multiplied by step size, plus
#     # the array's strides (tuple addition)
#     newstrides = norm_shape(np.array(a.strides) * ss) + a.strides
#     a = ast(a,shape = newshape,strides = newstrides)
#     if not flatten:
#         return a
#     # Collapse strided so that it has one more dimension than the window.  I.e.,
#     # the new array is a flat list of slices.
#     meat = len(ws) if ws.shape else 0
#     firstdim = (np.product(newshape[:-meat]),) if ws.shape else ()
#     dim = firstdim + (newshape[-meat:])
#     # remove any dimensions with size 1
#     #dim = filter(lambda i : i != 1,dim)
#
#     return a.reshape(dim), newshape

# =========================================================
def convert_wgs_to_utm(lon, lat):
    """
    This function estimates UTM zone from geographic coordinates
    see https://stackoverflow.com/questions/40132542/get-a-cartesian-projection-accurate-around-a-lat-lng-pair
    """
    utm_band = str((np.floor((lon + 180) / 6 ) % 60) + 1)
    if len(utm_band) == 1:
        utm_band = '0'+utm_band
    if lat >= 0:
        epsg_code = '326' + utm_band
    else:
        epsg_code = '327' + utm_band
    return epsg_code

# =========================================================
def printUsage():
    '''
    Show computing resources used
    '''
    cpuPercent = round(psutil.cpu_percent(0.5), 1)
    ramPercent = round(psutil.virtual_memory()[2], 1)
    ramUsed = round(psutil.virtual_memory()[3]/1000000000, 1)

    print('\n\nCurrent CPU/RAM Usage:')
    print('________________________')
    print('{:<5s} | {:<5s} | {:<5s}'.format('CPU %', 'RAM %', 'RAM [GB]'))
    print('________________________')

    print('{:<5s} | {:<5s} | {:<5s}'.format(str(cpuPercent), str(ramPercent), str(ramUsed)))
    print('________________________\n\n')


    return
