

from common_funcs import *

class sonObj:
    def __init__(self, sonFile, humFile, projDir, tempC, nchunk):
        # Create necessary attributes
        self.sonFile = sonFile
        self.humFile = humFile
        self.projDir = projDir
        self.tempC = tempC
        self.nchunk = nchunk
        self.datLen = -1

        return

    # =========================================================
    def _fread(self, infile, num, typ):
        """
        This function reads binary data in a file
        """
        dat = arr(typ)
        dat.fromfile(infile, num)
        return(list(dat))

    #===========================================
    def _decodeHumdat(self):
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
        t = self.tempC
        nchunk = self.nchunk

        #1199, Helix
        if datLen == 64:
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
            humDat = self._getHumdat(humdic)

        #Solix (Little Endian)
        elif datLen == 96:
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
            humDat = self._getHumdat(humdic)

        #Onix
        else:
            humdic = {}
            fid2 = open(humFile,'rb')
            # humDat = self._decode_onix(fid2)
            fid2.close()

        humDat['chunk_size'] = nchunk
        self.humDat = humDat
        return

    #===========================================
    def _getHumdat(self, humdic):
        """
        returns data from .DAT file
        """
        humFile = self.humFile
        datLen = self.datLen
        t = self.tempC

        humDat = {}
        endian = humdic['endianness']
        file = open(humFile, 'rb')
        for key, val in humdic.items():
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

        return humDat
