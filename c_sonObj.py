
from common_funcs import *

class sonObj:
    def __init__(self, sonFile, humFile, projDir, tempC, nchunk):
        # Create necessary attributes
        # Path
        self.projDir = projDir   # Project directory
        self.humFile = humFile   # DAT file path
        self.outPath = -1 # Location where outputs are saved
        self.sonFile = -1 # SON file path
        # Number
        self.headbytes = -1
        # List
        self.headIdx = -1
        self.pingCnt = -1
        self.pingMax = -1
        self.nchunk = -1

        return

    # =========================================================
    def _fread(self, infile, num, typ):
    #def _fread(self, object infile, int num, str typ):
       dat = arr(typ)
       dat.fromfile(infile, num)
       return(list(dat))

    # =========================================================
    def _loadSon(self):
        sonDat = np.zeros((self.pingMax, self.nchunk)).astype(int)
        file = open(self.sonFile, 'rb')
        for i in range(len(self.headIdx)):
            # print("index",i)
            headIdx = self.headIdx[i]
            pingCnt = self.pingCnt[i]
            # print("Ping Count", pingCnt)
            pingIdx = headIdx + self.headbytes
            file.seek(pingIdx)
            k = 0
            while k < pingCnt:
                byte = self._fread(file, 1, 'B')[0]
                sonDat[k,i] = byte
                # print(k,":",byte)
                k+=1
        # print(sonDat)
        # print(sonDat.shape)
        file.close()
        self.sonDat = sonDat


    # =
    def __str__(self):
        return "Test"
