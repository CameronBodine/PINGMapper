"""
Part of PING Mapper software

Co-Developed by Cameron S. Bodine and Dr. Daniel Buscombe

This software builds upon PyHum software,
originally developed by Dr. Daniel Buscombe

https://github.com/dbuscombe-usgs/PyHum

"""

from common_funcs import *
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

        direct = os.path.join('proc_data', projDir)
        if os.path.exists(direct):
            shutil.rmtree(direct)

        H.append(humFile)

        sonFiles = sorted(glob(sonPath+os.sep+'*.SON'))
        S.append(sonFiles)
        print(sonFiles)

        P.append(projDir)

        keep_going = False

    t = 10
    t = float(t)/10
    nchunk = 500

    #==================================================
    print('\n===========================================')
    print('===========================================')
    print('***** READING *****')
    for k in range(len(H)):
        print("working on "+P[k])
        read_master_func(S[k], H[k], P[k], t, nchunk)

    #==================================================
    print('\n===========================================')
    print('===========================================')
    print('***** RECTIFYING *****')
    for k in range(len(H)):
        print("working on "+P[k])
        rectify_master_func(S[k], H[k], P[k], nchunk)

    keep_going = False
print(round((time.time() - start_time),ndigits=2))
