
from common_funcs import *

class sonObj(object):
    def __init__(self, sonFile, humFile, projDir, tempC=0.1, nchunk=500):
        # Create necessary attributes
        # Path
        self.projDir = projDir      # Project directory
        self.outDir = None          # Location where outputs are saved
        self.humFile = humFile      # DAT file path
        self.sonFile = None         # SON file path
        self.sonIdxFile = None      # IDX file path
        self.metaDir = None         # Metadata file directory
        self.datMetaFile = None     # DAT metadata file path (csv)
        self.sonMetaFile = None     # SON metadata file path (csv)
        self.sonMetaPickle = None   # SON metadata pickle path

        # String
        self.beamName = None        # Name of sonar beam
        # Number
        self.headBytes = None       # Number of header bytes for a sonar return
        self.datLen = None          # Length in bytes of DAT file
        self.tempC = tempC          # Water temperature
        self.nchunk = nchunk        # Pings per chunk
        self.pingMax = None         # Stores highest pingCnt value (highest range)
        self.nchunk = nchunk        # Number of sonar records per chunk
        # Boolean
        self.isOnix = None          # Flag indicating if files from ONIX
        self.headValid = None       # Flag indicating if SON header structure is correct
        # List/Dictionary
        self.headIdx = None         # List to hold byte index of each sonar record
        self.pingCnt = None         # Number of ping returns for each sonar record
        self.humDatStruct = None    # Dictionary holding DAT file structure
        self.humDat = None          # Dictionary holding DAT file contents
        self.headStruct = None      # Dictionary holding sonar record header structure
        # Function
        self.trans = None           # Function to convert utm to lat/lon
        # DataFrame
        self.sonMetaDF = None       # Pandas df to hold son metadata

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
    def _getHumDatStruct(self):
        """
        Determines .DAT file structure then
        gets the data from .DAT using _getHumdat()
        or _decode_onix()
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
            humdic = {}
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

        humDat = defaultdict(dict)
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
    def _decodeOnix(self):
        """
        returns data from Onix .DAT file
        """
        fid2 = open(self.humFile, 'rb')

        dumpstr = fid2.read()
        fid2.close()

        if sys.version.startswith('3'):
          dumpstr = ''.join(map(chr, dumpstr))

        humdat = {}
        hd = dumpstr.split('<')[0]
        tmp = ''.join(dumpstr.split('<')[1:])
        humdat['NumberOfPings'] = int(tmp.split('NumberOfPings=')[1].split('>')[0])
        humdat['TotalTimeMs'] = int(tmp.split('TotalTimeMs=')[1].split('>')[0])
        humdat['linesize'] = int(tmp.split('PingSizeBytes=')[1].split('>')[0])
        humdat['FirstPingPeriodMs'] = int(tmp.split('FirstPingPeriodMs=')[1].split('>')[0])
        humdat['BeamMask'] = int(tmp.split('BeamMask=')[1].split('>')[0])
        humdat['Chirp1StartFrequency'] = int(tmp.split('Chirp1StartFrequency=')[1].split('>')[0])
        humdat['Chirp1EndFrequency'] = int(tmp.split('Chirp1EndFrequency=')[1].split('>')[0])
        humdat['Chirp2StartFrequency'] = int(tmp.split('Chirp2StartFrequency=')[1].split('>')[0])
        humdat['Chirp2EndFrequency'] = int(tmp.split('Chirp2EndFrequency=')[1].split('>')[0])
        humdat['Chirp3StartFrequency'] = int(tmp.split('Chirp3StartFrequency=')[1].split('>')[0])
        humdat['Chirp3EndFrequency'] = int(tmp.split('Chirp3EndFrequency=')[1].split('>')[0])
        humdat['SourceDeviceModelId2D'] = int(tmp.split('SourceDeviceModelId2D=')[1].split('>')[0])
        humdat['SourceDeviceModelIdSI'] = int(tmp.split('SourceDeviceModelIdSI=')[1].split('>')[0])
        humdat['SourceDeviceModelIdDI'] = int(tmp.split('SourceDeviceModelIdDI=')[1].split('>')[0])
        self.humDat = humdat
        return

    # =========================================================
    def _getEPSG(self):
        """
        Determines appropriate UTM zone based on location
        """
        if self.isOnix == 0:
            utm_x = self.humDat['utm_x']
            utm_y = self.humDat['utm_y']
        else:
            try:
                pass
            except:
                pass

        lat = np.arctan(np.tan(np.arctan(np.exp(utm_y/ 6378388.0)) * 2.0 - 1.570796326794897) * 1.0067642927) * 57.295779513082302
        lon = (utm_x * 57.295779513082302) / 6378388.0

        self.humDat['epsg'] = "epsg:"+str(int(float(convert_wgs_to_utm(lon, lat))))
        self.humDat['wgs'] = "epsg:4326"

        self.trans = pyproj.Proj(self.humDat['epsg'])
        # try:
        #     self.trans = pyproj.Proj(init=self.humDat['epsg'])
        # except:
        #     self.trans = pyproj.Proj(self.humDat['epsg'].lstrip(), inverse=True)

        return

    # =========================================================
    def _cntHead(self):
        """
        Determine SON sonar return header length
        """
        file = open(self.sonFile, 'rb')
        i = 0
        foundEnd = False
        while foundEnd is False and i < 200:
            lastPos = file.tell() # Get current position in file
            byte = self._fread(file, 1, 'B')
            # print("Val: {} Pos: {}".format(byte, lastPos))
            if byte[0] == 33 and lastPos > 3:
                # Double check we found the actual end
                file.seek(-6, 1)
                byte = self._fread(file, 1, 'B')
                if byte[0] == 160:
                    foundEnd = True
                else:
                    # Didn't find the end of header
                    # Move cursor back to lastPos
                    file.seek(lastPos)
            else:
                # Haven't found the end
                pass
            i+=1

        # i reaches 200, then we have exceeded known Humminbird header length
        if i == 200:
            i = 0

        file.close()
        self.headBytes = i
        return i

    # =========================================================
    def _getHeadStruct(self):
        """
        Returns dictionary with header structure
        Format: byteVal : [byteIndex, offset, dataLen, name]
        byteVal = Spacer value (integer) preceding attribute values (i.e. depth)
        byteIndex = Index indicating position of byteVal
        offset = Byte offset for the actual data
        dataLen = number of bytes for data (i.e. utm_x is 4 bytes long)
        name = name of attribute
        """

        headBytes = self.headBytes

        if headBytes == 67:
            headStruct = {
            128:[4, 1, 4, 'record_num'], #Record Number (Unique for each ping)
            129:[9, 1, 4, 'time_s'], #Time Elapsed milliseconds
            130:[14, 1, 4, 'utm_x'], #UTM X
            131:[19, 1, 4, 'utm_y'], #UTM Y
            132.1:[24, 1, 2, 'gps1'], #GPS quality flag (?)
            132.2:[24, 3, 2, 'instr_heading'], #Heading
            133.1:[29, 1, 2, 'gps2'], #GPS quality flag (?)
            133.2:[29, 3, 2, 'speed_ms'], #Speed in meters/second
            135:[34, 1, 4, 'inst_dep_m'], #Depth in centimeters, then converted to meters
            80:[39, 1, 1, 'beam'], #Beam number: 0 (50 or 83 kHz), 1 (200 kHz), 2 (SI Poort), 3 (SI Starboard)
            81:[41, 1, 1, 'volt_scale'], #Volt Scale (?)
            146:[43, 1, 4, 'f'], #Frequency of beam in hertz
            83:[48, 1, 1, "unknown_83"], #Unknown (number of satellites???)
            84:[50, 1, 1, "unknown_84"], #Unknown
            149:[52, 1, 4, "unknown_149"], #Unknown (magnetic deviation???)
            86:[57, 1, 1, 'unknown_86'], #Unknown (+-X error)
            87:[59, 1, 1, 'unknown_87'], #Unknown (+-Y error)
            160:[61, 1, 4, 'ping_cnt'] #Number of ping values (in bytes)
            }

        # 1199 and Helix
        elif headBytes == 72:
            headStruct = {
            128:[4, 1, 4, 'record_num'], #Record Number (Unique for each ping)
            129:[9, 1, 4, 'time_s'], #Time Elapsed milliseconds
            130:[14, 1, 4, 'utm_x'], #UTM X
            131:[19, 1, 4, 'utm_y'], #UTM Y
            132.1:[24, 1, 2, 'gps1'], #GPS quality flag (?)
            132.2:[24, 3, 2, 'instr_heading'], #Heading
            133.1:[29, 1, 2, 'gps2'], #GPS quality flag (?)
            133.2:[29, 3, 2, 'speed_ms'], #Speed in meters/second
            134:[34, 1, 4, 'unknown_134'], #Unknown
            135:[39, 1, 4, 'inst_dep_m'], #Depth in centimeters, then converted to meters
            80:[44, 1, 1, 'beam'], #Beam number: 0 (50 or 83 kHz), 1 (200 kHz), 2 (SI Poort), 3 (SI Starboard)
            81:[46, 1, 1, 'volt_scale'], #Volt Scale (?)
            146:[48, 1, 4, 'f'], #Frequency of beam in hertz
            83:[53, 1, 1, "unknown_83"], #Unknown (number of satellites???)
            84:[55, 1, 1, "unknown_84"], #Unknown
            149:[57, 1, 4, "unknown_149"], #Unknown (magnetic deviation???)
            86:[62, 1, 1, 'unknown_86'], #Unknown (+-X error)
            87:[64, 1, 1, 'unknown_87'], #Unknown (+-Y error)
            160:[66, 1, 4, 'ping_cnt'] #Number of ping values (in bytes)
            }

        # Solix
        elif headBytes == 152:
            headStruct = {
            128:[4, 1, 4, 'record_num'], #Record Number (Unique for each ping)
            129:[9, 1, 4, 'time_s'], #Time Elapsed milliseconds
            130:[14, 1, 4, 'utm_x'], #UTM X
            131:[19, 1, 4, 'utm_y'], #UTM Y
            132.1:[24, 1, 2, 'gps1'], #GPS quality flag (?)
            132.2:[24, 3, 2, 'instr_heading'], #Heading
            133.1:[29, 1, 2, 'gps2'], #GPS quality flag (?)
            133.2:[29, 3, 2, 'speed_ms'], #Speed in meters/second
            134:[34, 1, 4, 'unknown_134'], #Unknown
            135:[39, 1, 4, 'inst_dep_m'], #Depth in centimeters, then converted to meters
            136:[44, 1, 4, 'unknown_136'], #Unknown
            137:[49, 1, 4, 'unknown_137'], #Unknown
            138:[54, 1, 4, 'unknown_138'], #Unknown
            139:[59, 1, 4, 'unknown_139'], #Unkown
            140:[64, 1, 4, 'unknown_140'], #Unknown
            141:[69, 1, 4, 'unknown_141'], #Unknown
            142:[74, 1, 4, 'unknown_142'], #Unknown
            143:[79, 1, 4, 'unknown_143'], #Unknown
            80:[84, 1, 1, 'beam'], #Beam number: 0 (50 or 83 kHz), 1 (200 kHz), 2 (SI Poort), 3 (SI Starboard)
            81:[86, 1, 1, 'volt_scale'], #Volt Scale (?)
            146:[88, 1, 4, 'f'], #Frequency of beam in hertz
            83:[93, 1, 1, "unknown_83"], #Unknown (number of satellites???)
            84:[95, 1, 1, "unknown_84"], #Unknown
            149:[97, 1, 4, "unknown_149"], #Unknown (magnetic deviation???)
            86:[102, 1, 1, 'unknown_86'], #Unknown (+-X error)
            87:[104, 1, 1, 'unknown_87'], #Unknown (+-Y error)
            152:[106, 1, 4, 'unknown_152'], #Unknown
            153:[111, 1, 4, 'f_min'], #Frequency Range (min)
            154:[116, 1, 4, 'f_max'], #Frequency Range (max)
            155:[121, 1, 4, 'unknown_155'], #Unknown
            156:[126, 1, 4, 'unknown_156'], #Unknown
            157:[131, 1, 4, 'unknown_157'], #Unknown
            158:[136, 1, 4, 'unknown_158'], #Unknown
            159:[141, 1, 4, 'unknown_159'], #Unknown
            160:[146, 1, 4, 'ping_cnt'] #Number of ping values (in bytes)
            }
        else:
            headStruct = {}

        self.headStruct = headStruct
        return

    # =========================================================
    def _checkHeadStruct(self):
        """
        Check to make sure sonar return header
        structure determined appropriately
        """
        headStruct = self.headStruct
        if len(headStruct) > 0:
            file = open(self.sonFile, 'rb')

            for key, val in headStruct.items():
                file.seek(val[0])
                byte = self._fread(file, 1, 'B')[0]
                # print(val[3], "::", key, ":", byte)
                if np.floor(key) == byte:
                    headValid = [True]
                else:
                    headValid = [False, key, val, byte]
                    break
            file.close()
        else:
            headValid = [-1]
        self.headValid = headValid
        return

    # =========================================================
    def _decodeHeadStruct(self):
        """
        If sonar return header structure not
        previously known, attempt to automatically
        decode.
        """
        headBytes = self.headBytes
        headStruct = {}
        toCheck = {
            128:[-1, 1, 4, 'record_num'], #Record Number (Unique for each ping)
            129:[-1, 1, 4, 'time_s'], #Time Elapsed milliseconds
            130:[-1, 1, 4, 'utm_x'], #UTM X
            131:[-1, 1, 4, 'utm_y'], #UTM Y
            132.1:[-1, 1, 2, 'gps1'], #GPS quality flag (?)
            132.2:[-1, 3, 2, 'instr_heading'], #Heading
            133.1:[-1, 1, 2, 'gps2'], #GPS quality flag (?)
            133.2:[-1, 3, 2, 'speed_ms'], #Speed in meters/second
            134:[-1, 1, 4, 'unknown_134'], #Unknown
            135:[-1, 1, 4, 'inst_dep_m'], #Depth in centimeters, then converted to meters
            136:[-1, 1, 4, 'unknown_136'], #Unknown
            137:[-1, 1, 4, 'unknown_137'], #Unknown
            138:[-1, 1, 4, 'unknown_138'], #Unknown
            139:[-1, 1, 4, 'unknown_139'], #Unkown
            140:[-1, 1, 4, 'unknown_140'], #Unknown
            141:[-1, 1, 4, 'unknown_141'], #Unknown
            142:[-1, 1, 4, 'unknown_142'], #Unknown
            143:[-1, 1, 4, 'unknown_143'], #Unknown
            80:[-1, 1, 1, 'beam'], #Beam number: 0 (50 or 83 kHz), 1 (200 kHz), 2 (SI Poort), 3 (SI Starboard)
            81:[-1, 1, 1, 'volt_scale'], #Volt Scale (?)
            146:[-1, 1, 4, 'f'], #Frequency of beam in hertz
            83:[-1, 1, 1, "unknown_83"], #Unknown (number of satellites???)
            84:[-1, 1, 1, "unknown_84"], #Unknown
            149:[-1, 1, 4, "unknown_149"], #Unknown (magnetic deviation???)
            86:[-1, 1, 1, 'unknown_86'], #Unknown (+-X error)
            87:[-1, 1, 1, 'unknown_87'], #Unknown (+-Y error)
            152:[-1, 1, 4, 'unknown_152'], #Unknown
            153:[-1, 1, 4, 'unknown_153'], #Unknown
            154:[-1, 1, 4, 'unknown_154'], #Unknown
            155:[-1, 1, 4, 'unknown_155'], #Unknown
            156:[-1, 1, 4, 'unknown_156'], #Unknown
            157:[-1, 1, 4, 'unknown_157'], #Unknown
            158:[-1, 1, 4, 'unknown_158'], #Unknown
            159:[-1, 1, 4, 'unknown_159'], #Unknown
            160:[-1, 1, 4, 'ping_cnt'] #Number of ping values (in bytes)
            }

        file = open(self.sonFile, 'rb')
        lastPos = 0
        head = self._fread(file, 4,'B')

        if head[0] == 192 and head[1] == 222 and head[2] == 171 and head[3] == 33:
            while lastPos < headBytes - 1:
                lastPos = file.tell() # Get current position in file
                byte = self._fread(file, 1, 'B')[0]
                # print("B: ", byte, " I: ", lastPos, " H: ", headBytes-1)
                if byte != 132 and byte != 133:
                    meta = toCheck[byte]
                    meta[0] = lastPos
                    headStruct[byte] = meta
                    file.seek(meta[0]+meta[1]+meta[2])
                else:
                    byte = byte + 0.1
                    meta0_1 = toCheck[byte]
                    meta0_1[0] = lastPos
                    headStruct[byte] = meta0_1
                    byte = byte + 0.1
                    meta0_2 = toCheck[byte]
                    meta0_2[0] = lastPos
                    headStruct[byte] = meta0_2
                    file.seek(meta0_2[0]+meta0_2[1]+meta0_2[2])
                lastPos = file.tell()

        file.close()

        self.headStruct = headStruct
        return

    # =========================================================
    def _getSonMeta(self):
        """
        Use idx file to find every sonar record in son file.
        If idx file is not present, automatically determine
        sonar record return location in bytes.
        Then call _getHead() to decode sonar return header.
        """

        headStruct = self.headStruct
        nchunk = self.nchunk
        idxFile = self.sonIdxFile
        head = defaultdict(list)
        for key, val in headStruct.items():
            head[val[-1]] = []

        # First check if .idx file exists and get that data
        idx = {'record_num': [],
               'time_s': [],
               'index': [],
               'chunk_id': []}

        # idxFile = self.sonFile.replace(".SON", ".IDX")
        if idxFile != "NA":
            self.sonIdxFile = idxFile
            idxLen = os.path.getsize(idxFile)
            idxFile = open(idxFile, 'rb')
            i = j = chunk = 0
            while i < idxLen:
                idx['time_s'].append(struct.unpack('>I', arr('B', self._fread(idxFile, 4, 'B')).tobytes())[0])
                sonIndex = struct.unpack('>I', arr('B', self._fread(idxFile, 4, 'B')).tobytes())[0]
                idx['index'].append(sonIndex)
                idx['chunk_id'].append(chunk)

                head['index'].append(sonIndex)
                head['chunk_id'].append(chunk)
                headerDat = self._getHead(sonIndex)
                for key, val in headerDat.items():
                    head[key].append(val)
                idx['record_num'].append(headerDat['record_num'])
                i+=8
                j+=1
                if j == nchunk:
                    j=0
                    chunk+=1
                # print("\n\n", idx, "\n\n")
        else:
            # sys.exit("idx missing.  need to figure this out")
            print("\n\n{} is missing.  Automatically decoding SON file...".format(idxFile))
            sonFile = self.sonFile
            fileLen = os.path.getsize(sonFile)
            file = open(sonFile, 'rb')
            i = j = chunk = 0
            while i < fileLen:
                file.seek(i)
                headStart = struct.unpack('>I', arr('B', self._fread(file, 4, 'B')).tobytes())[0]
                if headStart == 3235818273: # We are at the beginning of a sonar record
                    head['index'].append(i)
                    head['chunk_id'].append(chunk)
                else:
                    sys.exit("Not at head of sonar record")

                headerDat = self._getHead(i)
                for key, val in headerDat.items():
                    head[key].append(val)
                i = i + self.headBytes + headerDat['ping_cnt']
                j+=1
                if j == nchunk:
                    j=0
                    chunk+=1

        # print(head,"\n\n\n")
        # print(idx)
        sonMetaAll = pd.DataFrame.from_dict(head, orient="index").T
        idxDF = pd.DataFrame.from_dict(idx, orient="index").T

        # Write data to csv
        outCSV = os.path.join(self.metaDir, self.beam+"_"+self.beamName+"_meta.csv")
        sonMetaAll.to_csv(outCSV, index=False, float_format='%.14f')
        # self.sonMetaFile = outCSV

        # outCSV = os.path.join(self.metaDir, self.beam+"_"+self.beamName+"_idx.csv")
        # idxDF.to_csv(outCSV, index=False, float_format='%.14f')

    # =========================================================
    def _getHead(self, sonIndex):
        """
        Helper function called by _getSonMeta().
        Given a byte index location, grab appropriate
        sonar record metadata.
        """
        headStruct = self.headStruct
        humDat = self.humDat
        nchunk = self.nchunk
        sonHead = {'lat':-1}
        file = open(self.sonFile, 'rb')
        for key, val in headStruct.items():
            index = sonIndex + val[0] + val[1]
            file.seek(index)
            if val[2] == 4:
                byte = struct.unpack('>i', arr('B', self._fread(file, val[2], 'B')).tobytes())[0]
            elif 1 < val[2] <4:
                byte = struct.unpack('>h', arr('b', self._fread(file, val[2],'b')).tobytes() )[0]
            else:
                byte = self._fread(file, val[2], 'b')[0]
            # print(val[-1],":",byte)
            sonHead[val[-1]] = byte

        file.close()

        # Make necessary conversions
        lat = np.arctan(np.tan(np.arctan(np.exp(sonHead['utm_y']/ 6378388.0)) * 2.0 - 1.570796326794897) * 1.0067642927) * 57.295779513082302
        lon = (sonHead['utm_x'] * 57.295779513082302) / 6378388.0

        sonHead['lon'] = lon
        sonHead['lat'] = lat

        lon, lat = self.trans(lon, lat)
        sonHead['e'] = lon
        sonHead['n'] = lat

        sonHead['instr_heading'] = sonHead['instr_heading']/10
        sonHead['speed_ms'] = sonHead['speed_ms']/10
        sonHead['inst_dep_m'] = sonHead['inst_dep_m']/10

        # Add tvg depth correction?
        # tvg = humDat['tvg']
        # dist_tvg = np.squeeze(((np.tan(np.radians(25)))*np.squeeze(humDat['inst_dep_m'].values))-(tvg))
        # sonHead['inst_dep_m_tvg'] = dist_tvg

        sonHead['f'] = sonHead['f']/1000
        sonHead['time_s'] = sonHead['time_s']/1000
        sonHead['tempC'] = self.tempC*10
        # Can we figure out a way to base transducer length on where we think the recording came from?
        # I can't see anywhere where this value is used.
        sonHead['t'] = 0.108
        try:
            starttime = float(humDat['unix_time'])
            sonHead['caltime'] = starttime + sonHead['time_s']
        except :
            sonHead['caltime'] = 0

        # if sonHead['beam']==3 or sonHead['beam']==2:
        #     dist = ((np.tan(25*0.0174532925))*sonHead['inst_dep_m']) +(tvg)
        #     bearing = 0.0174532925*sonHead['instr_heading'] - (pi/2)
        #     bearing = bearing % 360
        #     sonHead['heading'] = bearing
        # print("\n\n", sonHead, "\n\n")
        return sonHead

    # =========================================================
    def _getScansChunk(self):
        """
        Main function to read sonar record ping return values.
        Stores the number of pings per chunk, chunk id, and
        byte index location in son file, then calls
        _loadSonChunk() to read the data, then calls
        _writeTiles to save an unrectified image.
        """
        sonMetaAll = pd.read_csv(self.sonMetaFile)

        totalChunk = sonMetaAll['chunk_id'].max() #Total chunks to process
        # self.pingMax = sonMetaAll['ping_cnt'].max().astype(int)
        i = 0 #Chunk index
        while i <= totalChunk:
            isChunk = sonMetaAll['chunk_id']==i
            sonMeta = sonMetaAll[isChunk].reset_index()
            self.pingMax = sonMeta['ping_cnt'].max().astype(int)
            self.headIdx = sonMeta['index'].astype(int)
            self.pingCnt = sonMeta['ping_cnt'].astype(int)
            self._loadSonChunk()
            self._writeTiles(i)
            i+=1

    # =========================================================
    def _loadSonChunk(self):
        """
        Reads in sonar record ping values based on byte
        index location in son file and number of pings
        to return.
        """
        sonDat = np.zeros((self.pingMax, len(self.pingCnt))).astype(int)
        file = open(self.sonFile, 'rb')
        for i in range(len(self.headIdx)):
            # print("index",i)
            headIdx = self.headIdx[i]
            pingCnt = self.pingCnt[i]
            # print("Ping Count", pingCnt)
            pingIdx = headIdx + self.headBytes
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

    # =========================================================
    def _writeTiles(self, k):
        """
        Using currently saved sonar record ping returns
        in self.sonDAT, saves an unrectified image of the
        sonar echogram.
        """
        data = self.sonDat
        nx, ny = np.shape(data)
        Z, ind = sliding_window(data, (nx, ny))
        if k < 10:
            addZero = '0000'
        elif k < 100:
            addZero = '000'
        elif k < 1000:
            addZero = '00'
        elif k < 10000:
            addZero = '0'
        else:
            addZero = ''
        Z = Z[0].astype('uint8')
        imageio.imwrite(os.path.join(self.outDir, 'image-'+addZero+str(k)+'.png'), Z)

    # =========================================================
    def _loadSonMeta(self):
        """
        Load sonar metadata from csv to pandas df
        """
        meta = pd.read_csv(self.sonMetaFile)
        self.sonMetaDF = meta
        return

    # =========================================================
    def __str__(self):
        """
        Generic print function to print contenst of sonObj.
        """
        output = "sonObj Contents"
        output += '\n\t'
        output += self.__repr__()
        temp = vars(self)
        for item in temp:
            output += '\n\t'
            output += "{} : {}".format(item, temp[item])
        return output
