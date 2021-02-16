"""
Part of PING Mapper software

Developed by Cameron S. Bodine and Dr. Daniel Buscombe

This software builds upon PyHum software,
originally developed by Dr. Daniel Buscombe

https://github.com/dbuscombe-usgs/PyHum

"""

from common_funcs import *
from pj_readFiles import read_master_func
import shutil

#============================================
if __name__ == "__main__":

    H = []; S = []; P = []

    keep_going = True

    while keep_going is True:

        # Header size is: 72
        # humFile = 'Z:\\toProcess\\bedPicking\\SantaFe\\20170801\\R00014.DAT'
        # sonPath = 'Z:\\toProcess\\bedPicking\\SantaFe\\20170801\\R00014'
        # projDir = 'E:/NAU/Python/PINGMapper/procData/delete'

        # Header size is: 152
        # humFile = 'Z:\\toProcess\\bedPicking\\LakeMarry\\20191106\\Rec00003.DAT'
        # sonPath = 'Z:\\toProcess\\bedPicking\\LakeMarry\\20191106\\Rec00003'
        # projDir = 'E:/NAU/Python/PINGMapper/procData/delete'

        # Header size is: 67
        humFile = 'E:/NAU/Python/Py3Hum/example_raw_data/test.DAT'
        sonPath = 'E:/NAU/Python/Py3Hum/example_raw_data/'
        projDir = 'E:/NAU/Python/PINGMapper/procData/delete'

        # Onix
        # humFile = "G:\\Shared drives\\GulfSturgeonProject_NAU\\data\\ExHumFiles\\Onix_sample\\Rec00019.DAT"
        # sonPath = "G:\\Shared drives\\GulfSturgeonProject_NAU\\data\\ExHumFiles\\Onix_sample\\Rec00019"
        # projDir = 'E:/NAU/Python/PINGMapper/procData/delete'

        direct = os.path.join('proc_data', projDir)
        if os.path.exists(direct):
            shutil.rmtree(direct)

        H.append(humFile)

        sonFiles = sorted(glob(sonPath+os.sep+'*.SON'))
        S.append(sonFiles)
        print(sonFiles)

        P.append(projDir)

        try:
            os.mkdir(projDir)
        except:
            pass

        keep_going = False

    t = 10
    t = float(t)/10
    nchunk = 512

    #==================================================
    print('\n===========================================')
    print('===========================================')
    print('***** READING *****')
    for k in range(len(H)):
        print("working on "+P[k])
        read_master_func(S[k], H[k], P[k], t, nchunk)

    keep_going = False
