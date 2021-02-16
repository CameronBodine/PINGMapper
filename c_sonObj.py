

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

        humfile = self.humFile
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
            humdat = _getHumdat(humdic)

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
            humdat = _getHumdat(humdic)

        #Onix
        else:
            humdic = {}
            fid2 = open(humfile,'rb')
            humdat = _decode_onix(fid2)
            fid2.close()

        humdat['chunk_size'] = nchunk
        self.humDat = humdat
        return
