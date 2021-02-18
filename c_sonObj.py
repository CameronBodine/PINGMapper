
from common_funcs import *

class sonObj:
    def __init__(self, sonFile, humFile, projDir, tempC, nchunk):
        # Create necessary attributes
        # Path
        self.projDir = projDir   # Project directory
        self.humFile = humFile   # DAT file path
        self.outPath = None # Location where outputs are saved
        self.sonFile = None # SON file path
        # Number
        self.headbytes = None
        # List
        self.headIdx = None
        self.pingCnt = None
        self.pingMax = None
        self.nchunk = None

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
        output = "sonObj Contents"
        output += '\n\t'
        output += self.__repr__()
        temp = vars(self)
        for item in temp:
            output += '\n\t'
            output += "{} : {}".format(item, temp[item])
        return output
