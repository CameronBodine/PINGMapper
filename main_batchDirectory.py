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

import sys
sys.path.insert(0, 'src')

from funcs_common import *
from main_readFiles import read_master_func
from main_rectify import rectify_master_func

import time
import datetime

inDir = r'E:\NAU\GulfSturgeonProject\SSS_Data'
outDir = r'E:\NAU\GulfSturgeonProject\SSS_Data_BedpickTest_FixImplement'

#################
# User Parameters
t = 10 #Temperature in Celsius
nchunk = 500 #Number of pings per chunk
exportUnknown = False #Option to export Unknown ping metadata
wcp = False #Export tiles with water column present
wcr = False #Export Tiles with water column removed (and slant range corrected)
detectDepth = 1 #0==Use Humminbird depth; 1==Auto detect depth w/ Zheng et al. 2021;
## 2==Auto detect depth w/ Thresholding
smthDep = False #Smooth depth before water column removal
adjDep = 0 #Aditional depth adjustment (in pixels) for water column removaL
pltBedPick = True #Plot bedpick on sonogram

rect_wcp = False #Export rectified tiles with water column present
rect_wcr = False #Export rectified tiles with water column removed/slant range corrected

mosaic = 1 #Export rectified tile mosaic; 0==Don't Mosaic; 1==Do Mosaic - GTiff; 2==Do Mosaic - VRT

threadCnt = 0 #Number of compute threads to use; 0==All threads; <0==(Total threads + threadCnt); >0==Threads to use up to total threads

# Find all DAT and SON files in all subdirectories of inDir
# inFiles=[]
# for root, dirs, files in os.walk(inDir):
#     for file in files:
#         if file.endswith('.DAT'):
#             inFiles.append(os.path.join(root, file))

inFiles=[]
for root, dirs, files in os.walk(inDir):
    for file in files:
        if file.endswith('.DAT') and ('EggSites' not in root):
            inFiles.append(os.path.join(root, file))

for datFile in inFiles:
    try:
        start_time = time.time()

        # inPath = os.path.dirname(datFile)
        # humFile = datFile
        # recName = os.path.basename(humFile).split('.')[0]
        # sonPath = os.path.join(inDir, recName)
        # sonFiles = sorted(glob(sonPath+os.sep+'*.SON'))
        #
        # projDir = os.path.join(outDir, recName)

        humFile = datFile
        sonPath = datFile.split('.')[0]
        sonFiles = sorted(glob(sonPath+os.sep+'*.SON'))

        recName = os.path.basename(humFile).split('.')[0]
        dateBoat = os.path.dirname(humFile).split(os.sep)[-1]
        river = os.path.dirname(humFile).split(os.sep)[-2]
        projName = river+'_'+dateBoat+'_'+recName

        projDir = os.path.join(outDir, projName)


        print('sonPath',sonPath)
        print('\n\n\n+++++++++++++++++++++++++++++++++++++++++++')
        print('+++++++++++++++++++++++++++++++++++++++++++')
        print('***** Working On *****')
        print(humFile)
        print('Start Time: ', datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))

        print('\n===========================================')
        print('===========================================')
        print('***** READING *****')
        read_master_func(sonFiles, humFile, projDir, t, nchunk, exportUnknown, wcp, wcr, detectDepth, smthDep, adjDep, pltBedPick)

        if rect_wcp or rect_wcr:
            print('\n===========================================')
            print('===========================================')
            print('***** RECTIFYING *****')
            rectify_master_func(sonFiles, humFile, projDir, nchunk, rect_wcp, rect_wcr, adjDep, mosaic)

    except:
        print('Could not process:', datFile)

    gc.collect()
    print("\n\nTotal Processing Time: ",datetime.timedelta(seconds = round(time.time() - start_time, ndigits=0)))