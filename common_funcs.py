"""
Part of PyHum software

INFO:


Author:    Daniel Buscombe
           Northern Arizona University
           Flagstaff, AZ 86011
           daniel.buscombe@nau.edu
"""

import os, sys, struct, gc
from joblib import Parallel, delayed, cpu_count
from glob import glob
import dask.array as da
import dask.delayed as dd
import numpy as np
from array import array as arr

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

from tkinter import simpledialog
from tkinter import Tk
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter import messagebox
import tkinter.filedialog as filedialog

import pyproj
import imageio
from numpy.lib.stride_tricks import as_strided as ast
from numpy.matlib import repmat
import pandas as pd
import pydensecrf.densecrf as dcrf
from pydensecrf.utils import create_pairwise_gaussian, create_pairwise_bilateral, unary_from_labels
from skimage.morphology import binary_opening, disk

from collections import defaultdict
from copy import deepcopy
import pickle

#===========================================
def read_arrays(filename_pattern, shape, dtype):
    """
    This function reads files matching a pattern into 'lazy' dask arrays
    """
    lazy_arrays = [dd(imageio.imread)(fn) for fn in sorted(glob(filename_pattern))]
    lazy_arrays = [da.from_delayed(x, shape=shape, dtype=dtype) for x in lazy_arrays]
    return da.stack(lazy_arrays) #we stack the array to make it 4d (2d x depth) rather than default

# =========================================================
def norm_shape(shap):
   '''
   Normalize numpy array shapes so they're always expressed as a tuple,
   even for one-dimensional shapes.
   '''
   try:
      i = int(shap)
      return (i,)
   except TypeError:
      # shape was not a number
      pass

   try:
      t = tuple(shap)
      return t
   except TypeError:
      # shape was not iterable
      pass

   raise TypeError('shape must be an int, or a tuple of ints')

# =========================================================
def sliding_window(a,ws,ss = None,flatten = True):
    '''
    Return a sliding window over a in any number of dimensions
    '''
    if None is ss:
        # ss was not provided. the windows will not overlap in any direction.
        ss = ws
    ws = norm_shape(ws)
    ss = norm_shape(ss)
    # convert ws, ss, and a.shape to numpy arrays
    ws = np.array(ws)
    ss = np.array(ss)
    shap = np.array(a.shape)
    # ensure that ws, ss, and a.shape all have the same number of dimensions
    ls = [len(shap),len(ws),len(ss)]
    if 1 != len(set(ls)):
        raise ValueError(\
        'a.shape, ws and ss must all have the same length. They were %s' % str(ls))

    # ensure that ws is smaller than a in every dimension
    if np.any(ws > shap):
        raise ValueError(\
        'ws cannot be larger than a in any dimension.\
 a.shape was %s and ws was %s' % (str(a.shape),str(ws)))
    # how many slices will there be in each dimension?
    newshape = norm_shape(((shap - ws) // ss) + 1)
    # the shape of the strided array will be the number of slices in each dimension
    # plus the shape of the window (tuple addition)
    newshape += norm_shape(ws)
    # the strides tuple will be the array's strides multiplied by step size, plus
    # the array's strides (tuple addition)
    newstrides = norm_shape(np.array(a.strides) * ss) + a.strides
    a = ast(a,shape = newshape,strides = newstrides)
    if not flatten:
        return a
    # Collapse strided so that it has one more dimension than the window.  I.e.,
    # the new array is a flat list of slices.
    meat = len(ws) if ws.shape else 0
    firstdim = (np.product(newshape[:-meat]),) if ws.shape else ()
    dim = firstdim + (newshape[-meat:])
    # remove any dimensions with size 1
    #dim = filter(lambda i : i != 1,dim)

    return a.reshape(dim), newshape

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
def nan_helper(y):
   '''
   function to help manage indices of nans
   '''
   return np.isnan(y), lambda z: z.nonzero()[0]

# =========================================================
def rm_spikes(dat,numstds):
   """
   remove spikes in dat
   """
   ht = np.mean(dat) + numstds*np.std(dat)
   lt = np.argmax(np.mean(dat) - numstds*np.std(dat),0)

   index = np.where(dat>ht);
   if index:
      dat[index] = np.nan

   index = np.where(dat<lt);
   if index:
      dat[index] = np.nan

   # fill nans using linear interpolation
   nans, y= nan_helper(dat)
   dat[nans]= np.interp(y(nans), y(~nans), dat[~nans])
   return dat

# =========================================================
def ascol( arr ):
   '''
   reshapes row matrix to be a column matrix (N,1).
   '''
   if len( arr.shape ) == 1: arr = arr.reshape( ( arr.shape[0], 1 ) )
   return arr

# =========================================================
def set_unary_from_labels(fp, lp, prob, labels):
   """
   This function sets unary potentials according to the label matrix
   """
   H = fp.shape[0]
   W = fp.shape[1]

   d = dcrf.DenseCRF2D(H, W, len(labels)) # +1)
   U = unary_from_labels(lp.astype('int'), len(labels), gt_prob= prob)

   d.setUnaryEnergy(U)

   return d, H, W

# =========================================================
def runningMeanFast(x, N):
   '''
   flawed but fast running mean
   '''
   x = np.convolve(x, np.ones((N,))/N)[(N-1):]
   # the last N values will be crap, so they're set to the global mean
   x[-N:] = x[-N]
   return x
