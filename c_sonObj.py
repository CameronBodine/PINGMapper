
from common_funcs import *

class pyread:
    def __init__(self, son, datMeta, sonMeta, headbytes, outPath, maxRange):
        # Create necessary attributes
        # Path
        self.projDir = projDir   # Project directory
        self.humFile = humFile   # DAT file path
        self.outPath = outPath # Location where outputs are saved
        self.sonFile = son # SON file path
        # Number
        self.headbytes = headbytes
        # List
        self.headIdx = sonMeta['index'].astype(int)
        self.pingCnt = sonMeta['ping_cnt'].astype(int)
        self.pingMax = maxRange.astype(int)
        self.nchunk = datMeta['chunk_size'][0]

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
