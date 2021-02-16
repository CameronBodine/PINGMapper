"""
Part of PING Mapper software

Developed by Cameron S. Bodine and Dr. Daniel Buscombe

This software builds upon PyHum software,
originally developed by Dr. Daniel Buscombe

https://github.com/dbuscombe-usgs/PyHum

"""

from pj_readFiles import read_master_func
import shutil

#============================================
if __name__ == "__main__":

    H = []; S = []; P = []

    keep_going = True

    while keep_going is True:

        # Header size is: 72
        # humfile = 'Z:\\toProcess\\bedPicking\\SantaFe\\20170801\\R00014.DAT'
        # sonpath = 'Z:\\toProcess\\bedPicking\\SantaFe\\20170801\\R00014'
        # proj_name = 'delete'

        # Header size is: 152
        # humfile = 'Z:\\toProcess\\bedPicking\\LakeMarry\\20191106\\Rec00003.DAT'
        # sonpath = 'Z:\\toProcess\\bedPicking\\LakeMarry\\20191106\\Rec00003'
        # proj_name = 'delete'

        # Header size is: 67
        humFile = 'example_raw_data/test.DAT'
        sonPath = 'example_raw_data/'
        projDir = 'E:/NAU/Python/PINGMapper/procData'

        # Onix
        # humfile = "G:\\Shared drives\\GulfSturgeonProject_NAU\\data\\ExHumFiles\\Onix_sample\\Rec00019.DAT"
        # sonpath = "G:\\Shared drives\\GulfSturgeonProject_NAU\\data\\ExHumFiles\\Onix_sample\\Rec00019"
        # proj_name = 'delete'

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