"""
Part of PING Mapper software

Co-Developed by Cameron S. Bodine and Dr. Daniel Buscombe

This software builds upon PyHum software,
originally developed by Dr. Daniel Buscombe

https://github.com/dbuscombe-usgs/PyHum

"""

from funcs_common import *
from pj_readFiles import read_master_func
from pj_rectify import rectify_master_func

import time
start_time = time.time()

#============================================
if __name__ == "__main__":

    H = []; S = []; P = []

    keep_going = True

    while keep_going is True:

        # Path to data/output
        humFile = '.\\exampleData\\test.DAT'
        sonPath = '.\\exampleData\\test'
        projDir = '.\\procData\\PINGMapperTest'

        H.append(humFile)

        sonFiles = sorted(glob(sonPath+os.sep+'*.SON'))
        S.append(sonFiles)
        print(sonFiles)

        P.append(projDir)

        keep_going = False

    #################
    # User Parameters
    t = 10 #Temperature in Celsius
    nchunk = 500 #Number of pings per chunk
    exportUnknown = False #Option to export Unknown sonar record metadata
    wcp = False #Export tiles with water column present
    src = False #Export Tiles with water column removed/slant range corrected
    detectDepth = 0 #0==Use Humminbird depth; 1==Auto detect depth w/ binary threshold;
    ## 2==Auto detect depth w/ Res U-Net; 3==Both auto picks
    smthDep = False #Smooth depth before water column removal
    adjDep = 0 #Aditional depth adjustment (in pixels) for water column removaL
    pltBedPick = False

    rect_wcp = False #Export rectified tiles with water column present
    rect_src = False #Export rectified tiles with water column removed/slant range corrected

    #==================================================
    t = float(t)/10
    print('\n===========================================')
    print('===========================================')
    print('***** READING *****')
    for k in range(len(H)):
        print("working on "+P[k])
        read_master_func(S[k], H[k], P[k], t, nchunk, exportUnknown, wcp, src, detectDepth, smthDep, adjDep, pltBedPick)

    #==================================================
    if rect_wcp or rect_src:
        print('\n===========================================')
        print('===========================================')
        print('***** RECTIFYING *****')
        for k in range(len(H)):
            print("working on "+P[k])
            rectify_master_func(S[k], H[k], P[k], nchunk, detectDepth, smthDep, rect_wcp, rect_src, adjDep)

    keep_going = False
print("Total Processing Time: ",round((time.time() - start_time),ndigits=2))
