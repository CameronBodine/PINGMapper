
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
        self.headBytes = None
        self.datLen = None
        self.isOnix = None
        self.tempC = tempC       # Water temperature
        self.nchunk = nchunk     # Pings per chunk
        # List/Dictionary
        self.headIdx = None
        self.pingCnt = None
        self.pingMax = None
        self.nchunk = nchunk
        self.humDatStruct = None
        self.humDat = None

        return

    # =========================================================
    def _fread(self, infile, num, typ):
        dat = arr(typ)
        dat.fromfile(infile, num)
        return(list(dat))

    #===========================================
    def _getHumDatStruct(self):
        """
        determines .DAT file structure then
        gets the data from .DAT using getHumdat()
        or decode_onix()
        """
        # Returns dictionary with dat structure
        # Format: name : [byteIndex, offset, dataLen, data]
        # name = name of attribute
        # byteIndex = Index indicating position of name
        # offset = Byte offset for the actual data
        # dataLen = number of bytes for data (i.e. utm_x is 4 bytes long)
        # data = actual value of the attribute

        humFile = self.humFile
        datLen = self.datLen
        nchunk = self.nchunk

        #1199, Helix
        if datLen == 64:
            self.isOnix = 0
            humdic = {
            'endianness':'>i', #>=big endian; I=unsigned Int
            'SP1':[0, 0, 1, -1], #Unknown (spacer)
            'water_code':[1, 0, 1, -1], #Water code: 0=fresh,1=deep salt, 2=shallow salt
            'SP2':[2, 0, 1, -1], #Unknown (spacer)
            'unknown_1':[3, 0, 1, -1], #Unknown (gps flag?)
            'sonar_name':[4, 0, 4, -1], #Sonar name
            'unknown_2':[8, 0, 4, -1], #Unknown
            'unknown_3':[12, 0, 4, -1], #Unknown
            'unknown_4':[16, 0, 4, -1], #Unknown
            'unix_time':[20, 0, 4, -1], #Unix Time
            'utm_x':[24, 0, 4, -1], #UTM X
            'utm_y':[28, 0, 4, -1], #UTM Y
            'filename':[32, 0, 10, -1], #Recording name
            'unknown_5':[42, 0, 2, -1], #Unknown
            'numrecords':[44, 0, 4, -1], #Number of records
            'recordlens_ms':[48, 0, 4, -1], #Recording length milliseconds
            'linesize':[52, 0, 4, -1], #Line Size (?)
            'unknown_6':[56, 0, 4, -1], #Unknown
            'unknown_7':[60, 0, 4, -1], #Unknown
            }

        #Solix (Little Endian)
        elif datLen == 96:
            self.isOnix = 0
            humdic = {
            'endianness':'<i', #<=little endian; I=unsigned Int
            'SP1':[0, 0, 1, -1], #Unknown (spacer)
            'water_code':[1, 0, 1, -1], #Need to check if consistent with other models (1=fresh?)
            'SP2':[2, 0, 1, -1], #Unknown (spacer)
            'unknown_1':[3, 0, 1, -1], #Unknown (gps flag?)
            'sonar_name':[4, 0, 4, -1], #Sonar name
            'unknown_2':[8, 0, 4, -1], #Unknown
            'unknown_3':[12, 0, 4, -1], #Unknown
            'unknown_4':[16, 0, 4, -1], #Unknown
            'unix_time':[20, 0, 4, -1], #Unix Time
            'utm_x':[24, 0, 4, -1], #UTM X
            'utm_y':[28, 0, 4, -1], #UTM Y
            'filename':[32, 0, 12, -1], #Recording name
            'numrecords':[44, 0, 4, -1], #Number of records
            'recordlens_ms':[48, 0, 4, -1], #Recording length milliseconds
            'linesize':[52, 0, 4, -1], #Line Size (?)
            'unknown_5':[56, 0, 4, -1], #Unknown
            'unknown_6':[60, 0, 4, -1], #Unknown
            'unknown_7':[64, 0, 4, -1], #Unknown
            'unknown_8':[68, 0, 4, -1], #Unknown
            'unknown_9':[72, 0, 4, -1], #Unknown
            'unknown_10':[76, 0, 4, -1], #Unknown
            'unknown_11':[80, 0, 4, -1], #Unknown
            'unknown_12':[84, 0, 4, -1], #Unknown
            'unknown_13':[88, 0, 4, -1], #Unknown
            'unknown_14':[92, 0, 4, -1]
            }

        #Onix
        else:
            self.isOnix = 1

        self.humDatStruct = humdic
        return

#===========================================
    def _getHumdat(self):
        """
        returns data from .DAT file
        """
        humdic = self.humDatStruct
        humFile = self.humFile
        datLen = self.datLen
        t = self.tempC

        humDat = {}
        endian = humdic['endianness']
        file = open(humFile, 'rb')
        for key, val in humdic.items():
            # print(key,":",val)
            if key == 'endianness':
                pass
            else:
                file.seek(val[0])
                if val[2] == 4:
                    byte = struct.unpack(endian, arr('B', self._fread(file, val[2], 'B')).tobytes())[0]
                elif val[2] < 4:
                    byte = self._fread(file, val[2], 'B')[0]
                elif val[2] > 4:
                    byte = arr('B', self._fread(file, val[2], 'B')).tobytes().decode()
                else:
                    byte = -9999
                humDat[key] = byte

        file.close()

        waterCode = humDat['water_code']
        if datLen == 64:
            if waterCode == 0:
                humDat['water_type'] = 'fresh'
                S = 1
            elif waterCode == 1:
                humDat['water_type'] = 'deep salt'
                S = 35
            elif waterCode == 2:
                humDat['water_type'] = 'shallow salt'
                S = 30
            else:
                humDat['water_type'] = 'unknown'
        #Need to figure out water code for solix
        elif datLen == 96:
            if waterCode == 1:
                humDat['water_type'] = 'fresh'
                S = 1
            else:
                humDat['water_type'] = 'unknown'
                c = 1475

        c = 1449.05 + 45.7*t - 5.21*t**2 + 0.23*t**3 + (1.333 - 0.126*t + 0.009*t**2)*(S - 35)

        tvg = ((8.5*10**-5)+(3/76923)+((8.5*10**-5)/4))*c
        humDat['tvg'] = tvg
        humDat['nchunk'] = self.nchunk

        self.humDat = humDat

        return

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
