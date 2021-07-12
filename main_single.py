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

        # Header size is: 72
        # humFile = 'Z:\\toProcess\\bedPicking\\SantaFe\\20170801\\R00014.DAT'
        # sonPath = 'Z:\\toProcess\\bedPicking\\SantaFe\\20170801\\R00014'
        # projDir = 'E:\\NAU/Python\\PINGMapper\\procData\\SFE_20170801_R00014'

        # Header size is: 152
        # humFile = 'Z:\\toProcess\\bedPicking\\LakeMarry\\20191106\\Rec00003.DAT'
        # sonPath = 'Z:\\toProcess\\bedPicking\\LakeMarry\\20191106\\Rec00003'
        # projDir = 'E:/NAU/Python/PINGMapper/procData/delete'

        # Header size is: 67
        # humFile = 'E:/NAU/Python/Py3Hum/example_raw_data/test.DAT'
        # sonPath = 'E:/NAU/Python/Py3Hum/example_raw_data/'
        # projDir = 'E:/NAU/Python/PINGMapper/procData/delete'

        # Onix
        # humFile = "G:\\Shared drives\\GulfSturgeonProject_NAU\\data\\ExHumFiles\\Onix_sample\\Rec00019.DAT"
        # sonPath = "G:\\Shared drives\\GulfSturgeonProject_NAU\\data\\ExHumFiles\\Onix_sample\\Rec00019"
        # projDir = 'E:/NAU/Python/PINGMapper/procData/delete'

        # Mega
        # humFile = 'Z:\\toProcess\\bedPicking\\LSJ\\20170501\\R00002.DAT'
        # sonPath = 'Z:\\toProcess\\bedPicking\\LSJ\\20170501\\R00002'
        # projDir = 'E:/NAU/Python/PINGMapper/procData/delete'

        # Solix Mega - smooth trackline error - gaps
        # humFile = 'E:\\NAU\\GulfSturgeonProject\\Pearl\\data\\Field_data_Feb2021\\Solix_SSS_data_Feb2021\\SolixA1_ChanOquakwa_Feb2021\\Rec00002.DAT'
        # sonPath = 'E:\\NAU\\GulfSturgeonProject\\Pearl\\data\\Field_data_Feb2021\\Solix_SSS_data_Feb2021\\SolixA1_ChanOquakwa_Feb2021\\Rec00002'
        # projDir = 'E:/NAU/Python/PINGMapper/procData/SolixA1_Chan_REC00002'

        # Solix Mega - smooth trackline error - gaps
        # humFile = 'E:\\NAU\\GulfSturgeonProject\\Pearl\\data\\Field_data_March2021\\Solix_A1_030321\\Rec00003.DAT'
        # sonPath = 'E:\\NAU\\GulfSturgeonProject\\Pearl\\data\\Field_data_March2021\\Solix_A1_030321\\Rec00003'
        # projDir = 'E:/NAU/Python/PINGMapper/procData/SolixA1_Chan_030321_REC00003'

        # Solix Mega
        # humFile = 'E:\\NAU\\GulfSturgeonProject\\SSS_Data\\Pearl\\data\\PRL_Field_data_202102_FWS\\Solix_C1_20210202\\Rec00001.DAT'
        # sonPath = 'E:\\NAU\\GulfSturgeonProject\\SSS_Data\\Pearl\\data\\PRL_Field_data_202102_FWS\\Solix_C1_20210202\\Rec00001'
        # projDir = 'E:/NAU/Python/PINGMapper/procData/SolixC1_Adam_REC00001'

        # Solix Mega - gravel bar
        # humFile = 'E:\\NAU\\GulfSturgeonProject\\Pearl\\data\\Field_data_March2021\\Solix_B1_030321\\Rec00007.DAT'
        # sonPath = 'E:\\NAU\\GulfSturgeonProject\\Pearl\\data\\Field_data_March2021\\Solix_B1_030321\\Rec00007'
        # projDir = 'E:/NAU/Python/PINGMapper/procData/SolixB1_20210303_Rec00007_Gravel'

        # Solix Mega - Bouie
        humFile = 'E:\\NAU\\GulfSturgeonProject\\SSS_Data\\Pascagoula\\Field_data\\Bouie\\20210403_Solix_USM1\\Rec00006.DAT'
        sonPath = 'E:\\NAU\\GulfSturgeonProject\\SSS_Data\\Pascagoula\\Field_data\\Bouie\\20210403_Solix_USM1\\Rec00006'
        projDir = 'E:/NAU/Python/PINGMapper/procData/delete_GapTest1000'

        # humFile = 'Z:\\toProcess\\bedPicking\\Yellow\\20171210\\R00036.DAT'
        # sonPath = 'Z:\\toProcess\\bedPicking\\Yellow\\20171210\\R00036'
        # projDir = 'Z:\\toProcess\\bedPicking\\PINGMapperOut\\YLW20171210R00036'

        # direct = os.path.join('proc_data', projDir)
        # if os.path.exists(direct):
        #     shutil.rmtree(direct)

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
