"""
Part of PING-Mapper software

Co-Developed by Cameron S. Bodine and Dr. Daniel Buscombe

Inspired by PyHum: https://github.com/dbuscombe-usgs/PyHum

"""

import sys, os, zipfile, requests
sys.path.insert(0, 'src')

from funcs_common import *
from main_readFiles import read_master_func
from main_rectify import rectify_master_func

start_time = time.time()

#============================================

if len(sys.argv) == 2:
    ds = int(sys.argv[1])
else:
    print("\n\nERROR: \nPlease enter argument to choose which test file to process:")
    print("1 = Short recording \n2 = Long recording \n\nSYNTAX: python test_PINGMapper.py <1 or 2>\n\n")
    sys.exit()

#################
# User Parameters
#################

if ds == 1:
    # Path to data/output
    humFile = r'./exampleData/Test-Small-DS.DAT'
    sonPath = r'./exampleData/Test-Small-DS'
    projDir = r'./procData/PINGMapper-Test-Small-DS'

if ds == 2:
    # Check if files have already been downloaded
    if os.path.exists('./exampleData/Test-Large-DS') and os.path.exists('./exampleData/Test-Large-DS.DAT'):
        print('Files already downloaded!')

    else:
        print('Need to download large recording dataset...\n')
        url='https://github.com/CameronBodine/PINGMapper/releases/download/data/sample_recording.zip'
        filename = './exampleData/sample_recording.zip'
        r = requests.get(url, allow_redirects=True)
        open(filename, 'wb').write(r.content)

        with zipfile.ZipFile(filename, 'r') as z_fp:
            z_fp.extractall('./exampleData/')
        os.remove(filename)
        print('Downloaded and extracted', filename)

    # Path to data/output
    humFile = r'./exampleData/Test-Large-DS.DAT'
    sonPath = r'./exampleData/Test-Large-DS'
    projDir = r'./procData/PINGMapper-Test-Large-DS'


t = 10 #Temperature in Celsius
nchunk = 500 #Number of pings per chunk
exportUnknown = False #Option to export Unknown ping metadata
wcp = True #Export tiles with water column present
wcr = True #Export Tiles with water column removed (and slant range corrected)
smthDep = True #Smooth depth before water column removal
adjDep = 0 #Aditional depth adjustment (in pixels) for water column removaL
pltBedPick = True #Plot bedpick on sonogram

rect_wcp = True #Export rectified tiles with water column present
rect_wcr = True #Export rectified tiles with water column removed/slant range corrected

mosaic = 1 #Export rectified tile mosaic; 0==Don't Mosaic; 1==Do Mosaic - GTiff; 2==Do Mosaic - VRT

threadCnt = 0 #Number of compute threads to use; 0==All threads; <0==(Total threads + threadCnt); >0==Threads to use up to total threads

#################
#################

#============================================

sonFiles = sorted(glob(sonPath+os.sep+'*.SON'))
print(sonFiles)

#==================================================
print('\n===========================================')
print('===========================================')
print('***** READING *****')
print("working on "+projDir)
read_master_func(sonFiles, humFile, projDir, t, nchunk, exportUnknown, wcp, wcr, 0, smthDep, adjDep, pltBedPick, threadCnt)

#==================================================
if rect_wcp or rect_wcr:
    print('\n===========================================')
    print('===========================================')
    print('***** RECTIFYING *****')
    print("working on "+projDir)
    rectify_master_func(sonFiles, humFile, projDir, nchunk, rect_wcp, rect_wcr, mosaic, threadCnt)

gc.collect()
print("\n\nTotal Processing Time: ",datetime.timedelta(seconds = round(time.time() - start_time, ndigits=0)))
