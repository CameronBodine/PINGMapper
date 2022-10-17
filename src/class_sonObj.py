# Part of PING-Mapper software
#
# Co-Developed by Cameron S. Bodine and Dr. Daniel Buscombe
#
# Inspired by PyHum: https://github.com/dbuscombe-usgs/PyHum
#
# MIT License
#
# Copyright (c) 2022 Cameron S. Bodine
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from funcs_common import *

class sonObj(object):
    '''
    Python class to store everything related to reading and exporting data from
    Humminbird sonar recordings.

    ----------------
    Class Attributes
    ----------------
    * Alphabetical order *
    self.beam : str
        DESCRIPTION - Beam number B***

    self.beamName : str
        DESCRIPTION - Name of sonar beam.

    self.datLen : int
        DESCRIPTION - Number of bytes in DAT file.

    self.datMetaFile : str
        DESCRIPTION - Path to .DAT metadata file (.csv).

    self.headBytes : int
        DESCRIPTION - Number of header bytes for a ping.

    self.headIdx : list
        DESCRIPTION - List to hold byte index (offset) of each ping.

    self.headStruct : dict
        DESCRIPTION - Dictionary to store ping header structure.

    self.headValid : bool
        DESCRIPTION - Flag indicating if SON header structure is correct.

    self.humDat : dict
        DESCRIPTION - Dictionary to store .DAT file contents.

    self.humDatStruct : dict
        DESCRIPTION - Dictionary to store .DAT file structure.

    self.humFile : str
        DESCRIPTION - Path to .DAT file.

    self.isOnix : bool
        DESCRIPTION - Flag indicating if sonar recording from ONIX.

    self.metaDir : str
        DESCRIPTION - Path to metadata directory.

    self.nchunk : int
        DESCRIPTION - Number of pings/sonar records per chunk.

    self.outDir : str
        DESCRIPTION - Path where outputs are saved.

    self.pingCnt : int
        DESCRIPTION - Number of ping returns for each ping.

    self.pingMax : int
        DESCRIPTION - Stores largest pingCnt value (max range) for a currently
                      loaded sonar chunk.

    self.projDir : str
        DESCRIPTION - Path (top level) to output directory.

    self.sonDat : arr
        DESCRIPTION - Array to hold ping ping returns for currently
                      loaded chunk.

    self.sonFile : str
        DESCRIPTION - Path to .SON file.

    self.sonIdxFile : str
        DESCRIPTION - Path to .IDX file.

    self.sonMetaDF : DataFrame
        DESCRIPTION - Pandas dataframe to store .SON metadata.

    self.sonMetaFile : str
        DESCRIPTION - Path to .SON metadata file (.csv).

    self.sonMetaPickle : str
        DESCRIPTION - Path to .SON metadata pickle file (.meta).

    self.wcr : bool
        DESCRIPTION - Flag to export non-rectified sonar tiles w/ water column
                      removed (wcr) & slant range corrected.

    self.tempC : float
        DESCRIPTION - Water temperature (Celcius) during survey divided by 10.

    self.trans : non-class function
        DESCRIPTION - Function to convert utm to lat/lon.

    self.wcp : bool
        DESCRIPTION - Flag to export non-rectified sonar tiles w/ water column
                      present (wcp).
    '''

    #===========================================================================
    def __init__(self,
                 sonFile,
                 humFile,
                 projDir,
                 tempC=0.1,
                 nchunk=500,
                 pH=8.0):
        '''
        Initialize a sonObj instance.

        ----------
        Parameters
        ----------
        sonFile : str
            DESCRIPTION - Path to .SON file.
            EXAMPLE -     sonFile = 'C:/PINGMapper/SonarRecordings/R00001/B002.SON'
        humFile : str
            DESCRIPTION - Path to .DAT file associated w/ .SON directory.
            EXAMPLE -     humFile = 'C:/PINGMapper/SonarRecordings/R00001.DAT'
        projDir : str
            DESCRIPTION - Path to output directory.
            EXAMPLE -     projDir = 'C:/PINGMapper/procData/R00001'
        tempC : float : [Default=0.1]
            DESCRIPTION - Water temperature (Celcius) during survey divided by 10.
            EXAMPLE -     tempC = (20/10)
        nchunk : int : [Default=500]
            DESCRIPTION - Number of pings per chunk.  Chunk size dictates size of
                          sonar tiles (sonograms).  Most testing has been on chunk
                          sizes of 500 (recommended).
            EXAMPLE -     nchunk = 500
        pH : float : [Default=8.0]
            DESCRIPTION - pH of the water during sonar survey. Used in the phase
                          preserving filtering of high dynamic range images.
            EXAMPLE -     pH = 8

        -------
        Returns
        -------
        sonObj instance.
        '''
        # Create necessary attributes
        self.sonFile = sonFile      # SON file path
        self.projDir = projDir      # Project directory
        self.humFile = humFile      # DAT file path
        self.tempC = tempC          # Water temperature
        self.nchunk = nchunk        # Number of sonar records per chunk
        self.pH = pH                # Water pH during survey

        return

    ############################################################################
    # Decode DAT file (varies by model)                                        #
    ############################################################################

    #=======================================================================
    def _getHumDatStruct(self):
        '''
        Determines .DAT file structure for a sonObj instance.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        self.__init__()

        -------
        Returns
        -------
        A dictionary with .DAT file structure stored in self.humDatStruct with
        the following format:

        self.humDatStruct = {name : [byteIndex, offset, dataLen, data],
                             .... : ....} where:
            name == Name of attribute;
            byteIndex == Index indicating position of name;
            offset == Byte offset for the actual data;
            dataLen == number of bytes for data (i.e. utm_e is 4 bytes long);
            data = actual value of the attribute.

        --------------------
        Next Processing Step
        --------------------
        self._getHumDat()
        '''

        # Set variables equal to data stored in sobObj attributes.
        humFile = self.humFile # Path to .DAT file.
        datLen = self.datLen # Number of bytes in DAT file.
        nchunk = self.nchunk # Number of pings/sonar records per chunk.

        # The length (in bytes, `datLen`) of the .DAT file can indicate which
        ## Humminbird model a .DAT file is from.  That means we know where certain
        ## attributes are stored in the .DAT file.
        #1199, Helix
        if datLen == 64:
            self.isOnix = 0
            humDic = {
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
            'utm_e':[24, 0, 4, -1], #UTM X
            'utm_n':[28, 0, 4, -1], #UTM Y
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
            humDic = {
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
            'utm_e':[24, 0, 4, -1], #UTM X
            'utm_n':[28, 0, 4, -1], #UTM Y
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

        #### TESTING ######
        elif datLen == 100:
            self.isOnix = 0
            humDic = {
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
            'utm_e':[24, 0, 4, -1], #UTM X
            'utm_n':[28, 0, 4, -1], #UTM Y
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
            'unknown_14':[92, 0, 4, -1], #Unknown
            'unknown_15':[96, 0, 4, -1]
            }

        #Onix
        else:
            humDic = {}
            self.isOnix = 1

        self.humDatStruct = humDic
        return

    #=======================================================================
    def _getHumdat(self):
        '''
        Decode .DAT file using known DAT file structure.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        self._getHumDatStruct()

        -------
        Returns
        -------
        A dictionary stored in self.humDat containing data from .DAT file.

        --------------------
        Next Processing Step
        --------------------
        self._getEPSG()
        '''
        # Get necessary class attributes
        humDic = self.humDatStruct # Dictionary to store .DAT file structure.
        humFile = self.humFile # Path to .DAT file.
        datLen = self.datLen # Number of bytes in DAT file.
        t = self.tempC # Water temperature (Celcius) during survey divided by 10.

        humDat = defaultdict(dict) # Empty dict to store DAT contents
        endian = humDic['endianness'] # Is data big or little endian?
        file = open(humFile, 'rb') # Open the file

        # Search for humDic items in DAT file
        for key, val in humDic.items(): # Iterate each item in humDic
            if key == 'endianness':
                pass
            else:
                file.seek(val[0]) # Move to correct byte offset
                # If the expected data is 4 bytes long
                if val[2] == 4:
                    byte = struct.unpack(endian, arr('B', self._fread(file, val[2], 'B')).tobytes())[0] # Decode byte
                # If the expected data is less than 4 bytes long
                elif val[2] < 4:
                    byte = self._fread(file, val[2], 'B')[0] # Decode byte
                # If the expected data is greater than 4 bytes long
                elif val[2] > 4:
                    byte = arr('B', self._fread(file, val[2], 'B')).tobytes().decode() # Decode byte
                # Something went wrong...
                else:
                    byte = -9999
                humDat[key] = byte # Store the data

        file.close() # Close the file

        # Determine Humminbird water type setting and update (S)alinity appropriately
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

        ###### TESTING ######
        elif datLen == 100:
            if waterCode == 1:
                humDat['water_type'] = 'fresh'
                S = 1
            else:
                humDat['water_type'] = 'unknown'
                c = 1475

        # Calculate speed of sound based on temp & salinity
        c = 1449.05 + 45.7*t - 5.21*t**2 + 0.23*t**3 + (1.333 - 0.126*t + 0.009*t**2)*(S - 35)

        # Calculate time varying gain
        self.tvg = ((8.5*10**-5)+(3/76923)+((8.5*10**-5)/4))*c
        self.c = c
        self.S = S

        humDat['nchunk'] = self.nchunk
        self.humDat = humDat # Store data in class attribute for later use

        return

    # ======================================================================
    def _decodeOnix(self):
        '''
        Decodes .DAT file from Onix Humminbird models.  Onix has a significantly
        different .DAT file structure compared to other Humminbird models,
        requiring a specific function to decode the file.

        -------
        Returns
        -------
        A dictionary stored in self.humDat containing data from .DAT file.
        '''
        fid2 = open(self.humFile, 'rb') # Open file

        dumpstr = fid2.read() # Store file contents
        fid2.close() # Close the file

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
        humdat['water_type'] = 'fresh' #'shallow salt' #'deep salt'
        self.humDat = humdat # Store data in class attribute for later use
        return

    # ======================================================================
    def _fread(self,
               infile,
               num,
               typ):
        '''
        Helper function that reads binary data in a file.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self._getHumDat(), self._cntHead(), self._decodeHeadStruct(),
        self._getSonMeta(), self._loadSonChunk()

        ----------
        Parameters
        ----------
        infile : file
            DESCRIPTION - A binary file opened in read mode at a pre-specified
                          location.
        num : int
            DESCRIPTION - Number of bytes to read.
        typ : type
            DESCRIPTION - Byte type

        -------
        Returns
        -------
        List of decoded binary data

        --------------------
        Next Processing Step
        --------------------
        Returns list to function it was called from.
        '''
        dat = arr(typ)
        dat.fromfile(infile, num)
        return(list(dat))

    # ======================================================================
    def _getEPSG(self, utm_e=None, utm_n=None):
        '''
        Determines appropriate UTM zone based on location (EPSG 3395 Easting/Northing)
        provided in .DAT file.  This is used to project coordinates from
        EPSG 3395 to local UTM zone.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        self._getHumdat()

        -------
        Returns
        -------
        self.trans which will re-poroject Humminbird easting/northings to local UTM zone.

        --------------------
        Next Processing Step
        --------------------
        self._cntHead()
        '''
        # Check if file from Onix
        if self.isOnix == 0:
            utm_e = self.humDat['utm_e'] # Get easting
            utm_n = self.humDat['utm_n'] # Get northing
        # Need to add routine if Onix is encountered
        else:
            try:
                pass
            except:
                pass

        # Convert easting/northing to latitude/longitude
        lat = np.arctan(np.tan(np.arctan(np.exp(utm_n/ 6378388.0)) * 2.0 - 1.570796326794897) * 1.0067642927) * 57.295779513082302
        lon = (utm_e * 57.295779513082302) / 6378388.0

        # Determine epsg code
        self.humDat['epsg'] = "epsg:"+str(int(float(convert_wgs_to_utm(lon, lat))))
        self.humDat['wgs'] = "epsg:4326"

        # Configure re-projection function
        self.trans = pyproj.Proj(self.humDat['epsg'])

        return

    ############################################################################
    # Determine ping header length (varies by model)                   #
    ############################################################################

    # ======================================================================
    def _cntHead(self):
        '''
        Determine .SON ping header length based on known Humminbird
        .SON file structure.  Humminbird stores sonar records in packets, where
        the first x bytes of the packet contain metadata (record number, northing,
        easting, time elapsed, depth, etc.), proceeded by the sonar/ping returns
        associated with that ping.  This function will search the first
        ping to determine the length of ping header.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        self.__init__()

        -------
        Returns
        -------
        self.headBytes, indicating length, in bytes, of ping header.

        --------------------
        Next Processing Step
        --------------------
        self._getHeadStruct()
        '''
        file = open(self.sonFile, 'rb') # Open sonar file
        i = 0 # Counter to track sonar header length
        foundEnd = False # Flag to track if end of sonar header found
        while foundEnd is False and i < 200:
            lastPos = file.tell() # Get current position in file (byte offset from beginning)
            byte = self._fread(file, 1, 'B') # Decode byte value

            # Check if we found the end of the ping.
            ## A value of 33 **may** indicate end of ping.
            if byte[0] == 33 and lastPos > 3:
                # Double check we found the actual end by moving backward -6 bytes
                ## to see if value is 160 (spacer preceding number of ping records)
                file.seek(-6, 1)
                byte = self._fread(file, 1, 'B')
                if byte[0] == 160:
                    foundEnd = True
                else:
                    # Didn't find the end of header
                    # Move cursor back to lastPos+1
                    file.seek(lastPos+1)
            else:
                # Haven't found the end
                pass
            i+=1

        # i reaches 200, then we have exceeded known Humminbird header length.
        ## Set i to 0, then the next sonFile will be checked.
        if i == 200:
            i = 0

        file.close()
        self.headBytes = i # Store data in class attribute for later use
        return i

    ############################################################################
    # Get the SON header structure and attributes                              #
    ############################################################################

    # ======================================================================
    def _getHeadStruct(self,
                       exportUnknown = False):
        '''
        Determines .SON header structure based on self.headBytes.  The value of
        headBytes indicates the length of the ping header, which determines
        the location of each ping attribute within the sonar header.

        ----------
        Parameters
        ----------
        exportUnknown : bool
            DESCRIPTION - Flag indicating if unknown attributes in ping
                          should be exported or not.  If a user of PING Mapper
                          determines what an unkown attribute actually is, please
                          report using a github issue.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        self._cntHead()

        -------
        Returns
        -------
        A dictionary with .SON file structure stored in self.headStruct with
        the following format:

        self.headStruct = {byteVal : [byteIndex, offset, dataLen, name],
                           ...} where:
            byteVal == Spacer value (integer) preceding attribute values (i.e. depth);
            byteIndex == Index indicating position of byteVal in ping;
            offset == Byte offset from byteIndex for the actual data in ping;
            dataLen == number of bytes for data (i.e. utm_e is 4 bytes long);
            name = name of attribute.

        --------------------
        Next Processing Step
        --------------------
        self._checkHeadStruct()
        '''

        headBytes = self.headBytes

        if headBytes == 67:
            headStruct = {
            128:[4, 1, 4, 'record_num'], #Record Number (Unique for each ping)
            129:[9, 1, 4, 'time_s'], #Time Elapsed milliseconds
            130:[14, 1, 4, 'utm_e'], #UTM X
            131:[19, 1, 4, 'utm_n'], #UTM Y
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
            130:[14, 1, 4, 'utm_e'], #UTM X
            131:[19, 1, 4, 'utm_n'], #UTM Y
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
            130:[14, 1, 4, 'utm_e'], #UTM X
            131:[19, 1, 4, 'utm_n'], #UTM Y
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

        # We will ignore unknown attributes if exportUnknown==False, so we will
        ## remove those from headStruct.  This will make metadata csv file smaller.
        if not exportUnknown:
            toDelete = [] # List to store uknown keys
            for key, value in headStruct.items(): # Iterate each element in headStruct
                attributeName = value[3] # Get attribute name from headStruct element
                if 'unknown' in attributeName: # If attribute name contains 'unknown'
                    toDelete.append(key) # Add key name to toDelete
            for key in toDelete: # Iterate each key in toDelete
                del headStruct[key] # Remove key from headStruct

        self.headStruct = headStruct # Store data in class attribute for later use
        return

    # ======================================================================
    def _checkHeadStruct(self):
        '''
        Check to make sure ping header was structure determined
        appropriately.  The function searches through first ping to make
        sure each of the previously identified metadata attributes are located
        at the appropriate byte offset.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        self._getHeadStruct()

        -------
        Returns
        -------
        A boolean flag stored in self.headValid indicating if the ping
        structure was appropriately determined.

        --------------------
        Next Processing Step
        --------------------
        If self.headValid == False:
            self._decodeHeadStruct
        else:
            self._getSonMeta()
        '''
        headStruct = self.headStruct # Load ping header structure
        if len(headStruct) > 0:
            file = open(self.sonFile, 'rb') # Open son file

            # Iterate through each headStruct item
            for key, val in headStruct.items():
                file.seek(val[0]) # Move to the appropriate byte offset
                byte = self._fread(file, 1, 'B')[0] # Decode byte value

                # If the headStruct key is equal to the byte value,
                ## we are good to go (for now).
                if np.floor(key) == byte:
                    headValid = [True]
                # If not, we are encountering an unknown structure.  Return the
                ## decoded value and expected value for debug.
                else:
                    headValid = [False, key, val, byte]
                    break
            file.close()
        else:
            # We never determined the ping header structure.
            headValid = [-1]
        self.headValid = headValid # Store data in class attribute for later use
        return

    # ======================================================================
    def _decodeHeadStruct(self,
                          exportUnknown = False):
        '''
        This function attempts to automatically decode the sonar return header
        structure if self.headValid == FALSE as determined by self._checkHeadStruct().
        This function will iterate through each byte at the beginning of the
        sonar file, decode the byte, determine if it matches any known or unknown
        spacer value (ping attribute 'name') and if it does, store the
        byte offset.

        ----------
        Parameters
        ----------
        exportUnknown : bool
            DESCRIPTION - Flag indicating if unknown attributes in ping
                          should be exported or not.  If a user of PING Mapper
                          determines what an unkown attribute actually is, please
                          report using a github issue.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        self._cntHead()

        -------
        Returns
        -------
        A dictionary with .SON file structure stored in self.headStruct with
        the following format:

        self.headStruct = {byteVal : [byteIndex, offset, dataLen, name],
                           ...} where:
            byteVal == Spacer value (integer) preceding attribute values (i.e. depth);
            byteIndex == Index indicating position of byteVal;
            offset == Byte offset for the actual data;
            dataLen == number of bytes for data (i.e. utm_e is 4 bytes long);
            name = name of attribute.

        --------------------
        Next Processing Step
        --------------------
        self._checkHeadStruct()
        '''
        headBytes = self.headBytes # Number of header bytes for a ping
        headStruct = {}
        toCheck = {
            128:[-1, 1, 4, 'record_num'], #Record Number (Unique for each ping)
            129:[-1, 1, 4, 'time_s'], #Time Elapsed milliseconds
            130:[-1, 1, 4, 'utm_e'], #UTM X
            131:[-1, 1, 4, 'utm_n'], #UTM Y
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

        file = open(self.sonFile, 'rb') # Open the file
        lastPos = 0 # Track last position in file
        head = self._fread(file, 4,'B') # Get first 4 bytes of file

        # If first four bytes match known Humminbird ping header
        if head[0] == 192 and head[1] == 222 and head[2] == 171 and head[3] == 33:
            while lastPos < headBytes - 1:
                lastPos = file.tell() # Get current position in file
                byte = self._fread(file, 1, 'B')[0] # Decode the spacer byte
                # If spacer byte not equal to 132 or 133
                if byte != 132 and byte != 133:
                    meta = toCheck[byte] # Get associated metadata for known byteVal
                    meta[0] = lastPos # Store the current position
                    headStruct[byte] = meta # Store what was found in headStruct
                    file.seek(meta[0]+meta[1]+meta[2]) # Move to next position in file
                # Spacer 132/133 store two sets of information per spacer, so
                ## we need to handle differently.
                else:
                    # Part 1 (first 2 bytes of 4 byte sequence following spacer)
                    byte = byte + 0.1 # Append .1 to byteVal (i.e. 132.1 or 133.1)
                    meta0_1 = toCheck[byte] # Get associated metadata for known byteVal
                    meta0_1[0] = lastPos # Store the current position
                    headStruct[byte] = meta0_1 # Store what was found in headStruct

                    # Part 2 (second 2 bytes of 4 byte sequence following spacer)
                    byte = byte + 0.1 # Append .1 to byteVal (i.e. 132.2 or 133.3)
                    meta0_2 = toCheck[byte] # Get associated metadata for known byteVal
                    meta0_2[0] = lastPos # Store the current position
                    headStruct[byte] = meta0_2 # Store what was found in headStruct
                    file.seek(meta0_2[0]+meta0_2[1]+meta0_2[2]) # Move to next position in file
                lastPos = file.tell() # Update with current position

        file.close() # Close the file

        # We will ignore unknown attributes if exportUnknown==False, so we will
        ## remove those from headStruct.  This will make metadata csv file smaller.
        if not exportUnknown:
            toDelete = [] # List to store uknown keys
            for key, value in headStruct.items():# Iterate each element in headStruct
                attributeName = value[3] # Get attribute name from headStruct element
                if 'unknown' in attributeName: # If attribute name contains 'unknown'
                    toDelete.append(key) # Add key name to toDelete
            for key in toDelete: # Iterate each key in toDelete
                del headStruct[key] # Remove key from headStruct

        self.headStruct = headStruct # Store data in class attribute for later use
        return

    ############################################################################
    # Get the metadata for each ping                                   #
    ############################################################################

    # ======================================================================
    def _getSonMeta(self):
        '''
        Use .IDX file to find every ping in .SON file. If .IDX file is
        not present, automatically determine each ping location in bytes.
        Then call _getHeader() to decode sonar return header.

        .IDX Structure: Each ping in B***.SON has an 8-byte struct associated
        with it where the first 4-bytes indicate time elapsed since beginning of
        recording and second 4-bytes indicate the byte offset from the beginning
        of the B***.SON file where the ping begins.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        self._getHeadStruct()

        -------
        Returns
        -------
        B00*_**_*****_meta.csv where each row is associated with a ping
        and each column contains a given ping's metadata.

        --------------------
        Next Processing Step
        --------------------
        No additional processing is necessary if only interested in data exported
        to .CSV.  If export of non-rectified imagery is desired, next step is
        self._exportTiles().
        '''

        # Get necessary class attributes
        headStruct = self.headStruct # Dictionary to store ping header structure.
        nchunk = self.nchunk # Number of pings/sonar records per chunk.
        idxFile = self.sonIdxFile # Path to .IDX file.

        # Prepopulate dictionary w/ attribute names stored in headStruct
        head = defaultdict(list)
        for key, val in headStruct.items():
            head[val[-1]] = []

        # First check if .IDX file exists and get that data
        # Create a dictionary to store data from .IDX
        idx = {'record_num': [],
               'time_s': [],
               'index': [],
               'chunk_id': []}

        # If .IDX file exists
        if idxFile:
            idxLen = os.path.getsize(idxFile) # Determine length in bytes
            idxFile = open(idxFile, 'rb') # Open .IDX file
            i = j = chunk = 0 # Set counters
            while i < idxLen:
                # Decode .IDX data and store in IDX dictionary so we can find
                ## the associated ping metadata in B***.SON
                sonTime = struct.unpack('>I', arr('B', self._fread(idxFile, 4, 'B')).tobytes())[0] # Decode ping time offset
                idx['time_s'].append(sonTime) # Store time offset
                sonIndex = struct.unpack('>I', arr('B', self._fread(idxFile, 4, 'B')).tobytes())[0] # Decode ping byte index
                idx['index'].append(sonIndex) # Store byte index
                idx['chunk_id'].append(chunk) # Store chunk id

                # Store needed data in head dict
                head['index'].append(sonIndex) # ping byte index
                head['chunk_id'].append(chunk) # ping chunk id
                headerDat = self._getHeader(sonIndex) # Get and decode header data in .SON file
                for key, val in headerDat.items():
                    head[key].append(val) # Store in dictionary
                idx['record_num'].append(headerDat['record_num']) # Store ping number in idx dictionary
                # Increment counters
                i+=8
                j+=1
                if j == nchunk:
                    j=0
                    chunk+=1

                # Tried variable chunk size for rectification issues, but didn't
                ## fix the problem and introduced new problems
                # if j == 0:
                #     lastPingCnt = curPingCnt = headerDat['ping_cnt']
                # else:
                #     curPingCnt = headerDat['ping_cnt']
                # i+=8
                # j+=1
                # if (j == nchunk) or (lastPingCnt != curPingCnt):
                #     j=0
                #     chunk+=1
                # # else:
                #     # j+=1
                # # print('L: ', lastPingCnt, ' C: ', curPingCnt)
                # idx['chunk_id'].append(chunk) # Store chunk id
                # head['chunk_id'].append(chunk) # ping chunk id
                # lastPingCnt = curPingCnt

        # If .IDX file is missing
        ## Attempt to automatically decode .SON file
        else:
            print("\n\n{} is missing.  Automatically decoding SON file...".format(self.beam+'.IDX'))
            sonFile = self.sonFile # Get .SON file path
            fileLen = os.path.getsize(sonFile) # Determine size of .SON file
            file = open(sonFile, 'rb') # Open .SON file
            i = j = chunk = 0 # Set counters
            while i < fileLen:
                file.seek(i) # Go to appropriate location in file
                headStart = struct.unpack('>I', arr('B', self._fread(file, 4, 'B')).tobytes())[0]
                if headStart == 3235818273: # We are at the beginning of a ping
                    # Store needed data in head dict
                    head['index'].append(i)
                    head['chunk_id'].append(chunk)
                else:
                    sys.exit("Not at head of ping")

                headerDat = self._getHeader(i) # Get and decode header data in .SON file
                for key, val in headerDat.items():
                    head[key].append(val) # Store in dictionary
                # Increment counters
                i = i + self.headBytes + headerDat['ping_cnt'] # Determine location of next ping
                j+=1
                if j == nchunk:
                    j=0
                    chunk+=1

        sonMetaAll = pd.DataFrame.from_dict(head, orient="index").T # Store header metadata in dataframe
        sonMetaAll = self._getPixSize(sonMetaAll) # Calculate pixel size
        # Update last chunk size if last chunk too small (for rectification)
        lastChunk = sonMetaAll[sonMetaAll['chunk_id']==chunk]
        if len(lastChunk) <= (nchunk/2):
            sonMetaAll.loc[sonMetaAll['chunk_id']==chunk, 'chunk_id'] = chunk-1

        # Write metadata to csv
        outCSV = os.path.join(self.metaDir, self.beam+"_"+self.beamName+"_meta.csv")
        sonMetaAll.to_csv(outCSV, index=False, float_format='%.14f')
        self.sonMetaFile = outCSV

    # ======================================================================
    def _getHeader(self,
                   sonIndex):
        '''
        Helper function that, given a byte index location, decodes a sonar
        record's metadata according to known ping header structure.

        ----------
        Parameters
        ----------
        sonIndex : int
            DESCRIPTION - Byte index location of a ping in a .SON file.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called by self._getSonMeta()

        -------
        Returns
        -------
        A dictionary containing current ping's metadata.

        --------------------
        Next Processing Step
        --------------------
        Return metadata to self._getSonMeta()
        '''

        # Get necessary class attributes
        headStruct = self.headStruct # Dictionary to store ping header structure.
        humDat = self.humDat # Dictionary to store .DAT file contents.
        nchunk = self.nchunk # Number of pings/sonar records per chunk.

        sonHead = defaultdict() # Create dictionary to store ping metadata
        file = open(self.sonFile, 'rb') # Open .SON file
        # Traverse .SON file based on known headStruct
        for key, val in headStruct.items():
            byteIndex = val[0] # Offset to ping attribute spacer value
            offset = val[1] # Offset from byteIndex to attribute value
            dataLen = val[2] # Length of data (in bytes)
            index = sonIndex + byteIndex + offset # Location of data measured from beginning of the file
            file.seek(index) # Go to appropriate location
            # Decode data based on expected data byte size
            if dataLen == 4:
                byte = struct.unpack('>i', arr('B', self._fread(file, dataLen, 'B')).tobytes())[0]
            elif 1 < val[2] <4:
                byte = struct.unpack('>h', arr('b', self._fread(file, dataLen,'b')).tobytes() )[0]
            else:
                byte = self._fread(file, dataLen, 'b')[0]

            sonHead[val[-1]] = byte # Store attribute name and data in sonHead

        file.close() # Close .SON file

        if self.isOnix and not hasattr(self, 'trans'):
            # print('\n\n\n\n\n\nONIX\n\n')
            self._getEPSG(sonHead['utm_e'], sonHead['utm_n'])
            # print(self.trans)
            # sys.exit()

        # Make necessary conversions
        # Convert eastings/northings to latitude/longitude
        lat = np.arctan(np.tan(np.arctan(np.exp(sonHead['utm_n']/ 6378388.0)) * 2.0 - 1.570796326794897) * 1.0067642927) * 57.295779513082302
        lon = (sonHead['utm_e'] * 57.295779513082302) / 6378388.0

        sonHead['lon'] = lon
        sonHead['lat'] = lat

        # Reproject latitude/longitude to UTM zone
        lon, lat = self.trans(lon, lat)
        sonHead['e'] = lon
        sonHead['n'] = lat

        # Instrument heading, speed, and depth need to be divided by 10 to be
        ## in appropriate units.
        sonHead['instr_heading'] = sonHead['instr_heading']/10
        sonHead['speed_ms'] = sonHead['speed_ms']/10
        sonHead['inst_dep_m'] = sonHead['inst_dep_m']/10

        # Get units into appropriate format
        sonHead['f'] = sonHead['f']/1000 # Hertz to Kilohertz
        sonHead['time_s'] = sonHead['time_s']/1000 #milliseconds to seconds
        sonHead['tempC'] = self.tempC*10
        # Can we figure out a way to base transducer length on where we think the recording came from?
        sonHead['t'] = 0.108
        # Use recording unix time to calculate each sonar records unix time
        try:
            starttime = float(humDat['unix_time'])
            sonHead['caltime'] = starttime + sonHead['time_s']
        except :
            sonHead['caltime'] = 0

        # Other corrections Dan did, not implemented yet...
        # if sonHead['beam']==3 or sonHead['beam']==2:
        #     dist = ((np.tan(25*0.0174532925))*sonHead['inst_dep_m']) +(tvg)
        #     bearing = 0.0174532925*sonHead['instr_heading'] - (pi/2)
        #     bearing = bearing % 360
        #     sonHead['heading'] = bearing
        # print("\n\n", sonHead, "\n\n")
        return sonHead

    #=======================================================================
    def _getPixSize(self,
                    df):
        '''
        Helper function that determines pixel size of a sonar return based on
        water type, speed of sound in water, and sonar properties.

        ----------
        Parameters
        ----------
        df : DataFrame
            DESCRIPTION - Pandas DataFrame of ping metadata.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from _getSonMeta().

        -------
        Returns
        -------
        Dataframe with pixel size of a single return.  Used for exporting sonar tiles.

        --------------------
        Next Processing Step
        --------------------
        Return values to _getSonMeta()
        '''

        humDat = self.humDat # get DAT metadata

        water_type = humDat['water_type'] # load water type
        if water_type=='fresh':
            S = 36
        elif water_type=='shallow salt':
            S = 30
        elif water_type=='deep salt':
            S = 35
        else:
            S = 1

        t = df['t'].to_numpy() # transducer length
        f = 455 # Pixel size is not dependent on different frequency settings on the Humminbird
        c = 1449.05 + 45.7*t - 5.21*t**2 + 0.23*t**3 + (1.333 - 0.126*t + 0.009*t**2)*(S - 35) # speed of sound in water

        # theta at 3dB in the horizontal
        theta3dB = np.arcsin(c/(t*(f*1000)))
        #resolution of 1 sidescan pixel to nadir
        ft = (np.pi/2)*(1/theta3dB)
        # size of pixel in meters
        pix_m = (1/ft)
        df['pix_m'] = pix_m

        return df

    ############################################################################
    # Export un-rectified sonar tiles                                          #
    ############################################################################

    # ==========================================================================
    def _exportTiles(self,
                     chunk):
        '''
         Main function to read sonar record ping return values.  Stores the
        number of pings per chunk, chunk id, and byte index location in son file,
        then calls self._loadSonChunk() to read the data into memory, then calls
        self._writeTiles to save an unrectified image.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        self._getSonMeta()

        -------
        Returns
        -------
        *.PNG un-rectified sonar tiles (sonograms)

        --------------------
        Next Processing Step
        --------------------
        NA
        '''
        filterIntensity = False

        # Make sonar imagery directory for each beam if it doesn't exist
        try:
            os.mkdir(self.outDir)
        except:
            pass

        # Filter sonMetaDF by chunk
        isChunk = self.sonMetaDF['chunk_id']==chunk
        sonMeta = self.sonMetaDF[isChunk].copy().reset_index()
        # Update class attributes based on current chunk
        # Update class attributes based on current chunk
        self.pingMax = sonMeta['ping_cnt'].astype(int).max() # store to determine max range per chunk
        self.headIdx = sonMeta['index'].astype(int) # store byte offset per ping
        self.pingCnt = sonMeta['ping_cnt'].astype(int) # store ping count per ping
        # Load chunk's sonar data into memory
        self._loadSonChunk()

        if filterIntensity:
            self._doPPDRC()

        # Export water column present (wcp) image
        if self.wcp:
            # self._doPPDRC()
            self._writeTiles(chunk, imgOutPrefix='wcp') # Save image
        # Export slant range corrected (water column removed) imagery
        if self.wcr_src and (self.beamName=='ss_port' or self.beamName=='ss_star'):
            self._WCR_SRC(sonMeta) # Remove water column and redistribute ping returns based on FlatBottom assumption
            # self._doPPDRC()
            self._writeTiles(chunk, imgOutPrefix='wcr') # Save image

        try:
            # Export water column removed and cropped imagery
            if self.wcr_crop and (self.beamName=='ss_port' or self.beamName=='ss_star'):
                self._WCR_crop(sonMeta)
                self._writeTiles(chunk, imgOutPrefix='wcr_crop')
        except:
            pass

        gc.collect()
        return self


    # ==========================================================================
    def _loadSonChunk(self):
        '''
        Reads ping returns into memory based on byte index location in son file
        and number of pings to return.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self._getScanChunkALL() or self._getScanChunkSingle()

        -------
        Returns
        -------
        2-D numpy array containing sonar intensity

        --------------------
        Next Processing Step
        --------------------
        Return numpy array to self._getScanChunkALL() or self._getScanChunkSingle()
        '''
        sonDat = np.zeros((self.pingMax, len(self.pingCnt))).astype(int) # Initialize array to hold sonar returns
        file = open(self.sonFile, 'rb') # Open .SON file
        # Iterate each ping
        for i in range(len(self.headIdx)):
            headIdx = self.headIdx[i] # Get current byte offset to ping
            pingCnt = self.pingCnt[i] # Get current ping count
            pingIdx = headIdx + self.headBytes # Determine byte offset to sonar returns
            file.seek(pingIdx) # Move to that location
            k = 0
            # Decode each sonar return and store in array
            # while k < pingCnt:
            while k < min(pingCnt, self.pingMax):
                byte = self._fread(file, 1, 'B')[0]
                sonDat[k,i] = byte
                k+=1

        file.close() # Close the file
        self.sonDat = sonDat # Store array in class attribute
        return self

    # ======================================================================
    def _WCR_SRC(self,
             sonMeta):
        '''
        Slant range correction is the process of relocating sonar returns after
        water column removal by converting slant range distances to the bed into
        horizontal distances based off the depth at nadir.  As SSS does not
        measure depth across the track, we must assume depth is constant across
        the track (Flat bottom assumption).  The pathagorean theorem is used
        to calculate horizontal distance from slant range distance and depth at
        nadir.

        ----------
        Parameters
        ----------
        sonMeta : DataFrame
            DESCRIPTION - Dataframe containing ping metadata.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self._getScanChunkALL() or self._getScanChunkSingle()

        -------
        Returns
        -------
        Self w/ array of relocated intensities stored in self.sonDat.

        --------------------
        Next Processing Step
        --------------------
        Returns relocated bed intensities to self._getScanChunkALL() or
        self._getScanChunkSingle()
        '''
        # Load depth (in real units) and convert to pixels
        bedPick = round(sonMeta['dep_m'] / sonMeta['pix_m'], 0).astype(int)

        # Initialize 2d array to store relocated sonar records
        srcDat = np.zeros((self.sonDat.shape[0], self.sonDat.shape[1])).astype(int)

        #Iterate each ping
        for j in range(self.sonDat.shape[1]):
            depth = bedPick[j] # Get depth (in pixels) at nadir
            # Create 1d array to store relocated bed pixels.  Set to -1 so we
            ## can later interpolate over gaps.
            pingDat = (np.ones((self.sonDat.shape[0])).astype(np.float32)) * -1
            dataExtent = 0
            #Iterate each sonar/ping return
            for i in range(self.sonDat.shape[0]):
                if i >= depth:
                    intensity = self.sonDat[i,j] # Get the intensity value
                    srcIndex = round(np.sqrt(i**2 - depth**2),0).astype(int) #Calculate horizontal range (in pixels) using pathagorean theorem
                    pingDat[srcIndex] = intensity # Store intensity at appropriate horizontal range
                    dataExtent = srcIndex # Store range extent (max range) of ping
                else:
                    pass
            pingDat[dataExtent:]=0 # Zero out values past range extent so we don't interpolate past this

            # Process of relocating bed pixels will introduce across track gaps
            ## in the array so we will interpolate over gaps to fill them.
            pingDat[pingDat==-1] = np.nan
            nans, x = np.isnan(pingDat), lambda z: z.nonzero()[0]
            pingDat[nans] = np.interp(x(nans), x(~nans), pingDat[~nans])

            # Store relocated ping in output array
            srcDat[:,j] = np.around(pingDat, 0).astype(int)

        self.sonDat = srcDat # Store in class attribute for later use
        return self

    # ======================================================================
    def _WCR_crop(self,
                  sonMeta):
        # Load depth (in real units) and convert to pixels
        bedPick = round(sonMeta['dep_m'] / sonMeta['pix_m'], 0).astype(int)
        minDep = min(bedPick)

        sonDat = self.sonDat
        # Zero out water column
        for j, d in enumerate(bedPick):
            sonDat[:d, j] = 0

        # # Bank crop
        # if 'bank_m' in sonMeta.columns:
        #     bankPick = round(sonMeta['bank_m'] / sonMeta['pix_m'], 0).astype(int)
        #     maxRange = max(bankPick)
        #
        #     for j, b in enumerate(bankPick):
        #         sonDat[b:, j] = 0
        #
        #     sonDat = sonDat[minDep:maxRange,]
        #
        # else:
        #     # Crop to minimum depth
        #     sonDat = sonDat[minDep:,]

        sonDat = sonDat[minDep:,]

        self.sonDat = sonDat
        return self

    # ======================================================================
    def _writeTiles(self,
                    k,
                    imgOutPrefix):
        '''
        Using currently saved ping ping returns stored in self.sonDAT,
        saves an unrectified image of the sonar echogram.

        ----------
        Parameters
        ----------
        k : int
            DESCRIPTION - Chunk number
        imgOutPrefix : str
            DESCRIPTION - Prefix to add to exported image

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self._getScanChunkALL() or self._getScanChunkSingle() after
        sonar data loaded to memory with self._loadSonChunk()

        -------
        Returns
        -------
        *.PNG of sonogram to output directory

        --------------------
        Next Processing Step
        --------------------
        NA
        '''
        data = self.sonDat.astype('uint8') # Get the sonar data

        # File name zero padding
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

        # Prepare output directory if it doesn't exist
        outDir = os.path.join(self.outDir, imgOutPrefix)
        try:
            os.mkdir(outDir)
        except:
            pass

        channel = os.path.split(self.outDir)[-1] #ss_port, ss_star, etc.
        projName = os.path.split(self.projDir)[-1] #to append project name to filename
        imsave(os.path.join(outDir, projName+'_'+imgOutPrefix+'_'+channel+'_'+addZero+str(k)+'.png'), data, check_contrast=False)

    ############################################################################
    # Miscellaneous                                                            #
    ############################################################################

    # ======================================================================
    def _getScanChunkSingle(self,
                            chunk,
                            filterIntensity = False,
                            remWater = False):
        '''
        During rectification, if non-rectified tiles have not been exported,
        this will load the chunk's scan data from the sonar recording.

        Stores the number of pings per chunk, chunk id, and byte index location
        in son file, then calls self._loadSonChunk() to read the data.

        ----------
        Parameters
        ----------
        chunk : int
            DESCRIPTION - Chunk number
        remWater : bool
            DESCRIPTION - Flag indicating if water column should be removed and
                          slant range corrected.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from child class c_rectObj._rectSon()

        -------
        Returns
        -------
        Self with chunk's sonar intensities loaded in memory

        --------------------
        Next Processing Step
        --------------------
        Return to child class c_rectObj._rectSon() to complete rectification
        '''
        # Open sonar metadata file to df
        sonMetaAll = pd.read_csv(self.sonMetaFile)

        # Filter df by chunk
        isChunk = sonMetaAll['chunk_id']==chunk
        sonMeta = sonMetaAll[isChunk].reset_index()
        # Update class attributes based on current chunk
        # self.pingMax = sonMeta['ping_cnt'].astype(int).max() # store to determine max range per chunk

        # set pingMax to most representative range, i.e. range with largest count
        # print(np.unique(sonMeta['ping_cnt'], return_counts=True))
        rangeCnt = np.unique(sonMeta['ping_cnt'], return_counts=True)
        pingMaxi = np.argmax(rangeCnt[1])
        self.pingMax = int(rangeCnt[0][pingMaxi])
        # print(self.pingMax)

        self.headIdx = sonMeta['index'].astype(int) # store byte offset per ping
        self.pingCnt = sonMeta['ping_cnt'].astype(int) # store ping count per ping
        # Load chunk's sonar data into memory
        self._loadSonChunk()
        # Do PPDRC filter
        if filterIntensity:
            self._doPPDRC()
        # Remove water if exporting wcr imagery
        if remWater:
            self._WCR(sonMeta)

        return self

    # ======================================================================
    def _loadSonMeta(self):
        '''
        Load sonar metadata from csv to pandas df
        '''
        meta = pd.read_csv(self.sonMetaFile)
        self.sonMetaDF = meta
        return self

    # ======================================================================
    def __str__(self):
        '''
        Generic print function to print contents of sonObj.
        '''
        output = "sonObj Contents"
        output += '\n\t'
        output += self.__repr__()
        temp = vars(self)
        for item in temp:
            output += '\n\t'
            output += "{} : {}".format(item, temp[item])
        return output

    ############################################################################
    # Corrections                                                              #
    ############################################################################

    # ======================================================================
    def _doPPDRC(self):
        '''
        Reference:
        Peter Kovesi, "Phase Preserving Tone Mapping of Non-Photographic High Dynamic
        Range Images".  Proceedings: Digital Image Computing: Techniques and
        Applications 2012 (DICTA 2012). Available via IEEE Xplore

        Dan Buscombe translated from matlab code posted on:
        http://www.csse.uwa.edu.au/~pk/research/matlabfns/PhaseCongruency/

        Dan Buscombe implemented in PyHum:
        https://github.com/dbuscombe-usgs/PyHum
        '''
        im = self.sonDat.astype('float64')
        im = standardize(im, 0, 1)
        im = im*1e4

        # Populate needed parameters
        n = 2
        eps = 2.2204e-16
        rows, cols = np.shape(im)
        wavelength = cols/2

        IM = np.fft.fft2(im)

        # Generate horizontal and vertical frequency grids that vary from
        # -0.5 to 0.5
        u1, u2 = np.meshgrid((np.r_[0:cols]-(np.fix(cols/2)+1))/(cols-np.mod(cols,2)),(np.r_[0:rows]-(np.fix(rows/2)+1))/(rows-np.mod(rows,2)))

        u1 = np.fft.ifftshift(u1)   # Quadrant shift to put 0 frequency at the corners
        u2 = np.fft.ifftshift(u2)

        radius = np.sqrt(u1*u1 + u2*u2)
        # Matrix values contain frequency values as a radius from centre (but quadrant shifted)

        # Get rid of the 0 radius value in the middle (at top left corner after
        # fftshifting) so that dividing by the radius, will not cause trouble.
        radius[1,1] = 1

        H1 = 1j*u1/radius   # The two monogenic filters in the frequency domain
        H2 = 1j*u2/radius
        H1[1,1] = 0
        H2[1,1] = 0
        radius[1,1] = 0  # undo fudge

        # High pass Butterworth filter
        H =  1.0 - 1.0 / (1.0 + (radius * wavelength)**(2*n))

        f = np.real(np.fft.ifft2(H*IM))
        h1f = np.real(np.fft.ifft2(H*H1*IM))
        h2f = np.real(np.fft.ifft2(H*H2*IM))

        ph = np.arctan(f/np.sqrt(h1f*h1f + h2f*h2f + eps))
        E = np.sqrt(f*f + h1f*h1f + h2f*h2f)
        res = np.sin(ph)*np.log1p(E)

        res = standardize(res, 0, 1)

        # # Try median filter
        # avg = np.nanmedian(res, axis=0)
        # res = res-avg + np.nanmean(avg)
        # res = res + np.abs(np.nanmin(avg))
        # res = median(res, square(3))
        #
        # res = denoise_tv_chambolle(res, weight=0.1, multichannel=False)

        # Try standardizing and rescaling
        res = standardize(res, 0, 255)

        self.sonDat = res
        return self
