from funcs_common import *
from funcs_bedpick import *
# from scipy.signal import savgol_filter

from skimage.filters import gaussian
from skimage.morphology import remove_small_holes, remove_small_objects
from skimage.measure import label, regionprops
from skimage.io import imsave

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

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
        DESCRIPTION - Number of bytes of DAT file.

    self.datMetaFile : str
        DESCRIPTION - Path to .DAT metadata file (.csv).

    self.headBytes : int
        DESCRIPTION - Number of header bytes for a sonar record.

    self.headIdx : list
        DESCRIPTION - List to hold byte index (offset) of each sonar record.

    self.headStruct : dict
        DESCRIPTION - Dictionary to store sonar record header structure.

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
        DESCRIPTION - Number of ping returns for each sonar record.

    self.pingMax : int
        DESCRIPTION - Stores largest pingCnt value (max range) for a currently
                      loaded sonar chunk.

    self.projDir : str
        DESCRIPTION - Path (top level) to output directory.

    self.sonDat : arr
        DESCRIPTION - Array to hold sonar record ping returns for currently
                      loaded chunk.

    self.sonFile : str
        DESCRIPTION - Path to .SON file.

    self.sonIdxFile : str
        DESCRIPTION - Path to .IDX file.

    self.sonMetaDF : DataFrame
        DESCRIPTION - Pandas dataframe to store .SON metadata for currently
                      loaded sonar chunk.

    self.sonMetaFile : str
        DESCRIPTION - Path to .SON metadata file (.csv).

    self.sonMetaPickle : str
        DESCRIPTION - Path to .SON metadata pickle file (.meta).

    self.src : bool
        DESCRIPTION - Flag to export non-rectified sonar tiles w/ water column
                      removed & slant range corrected (src).

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
                 nchunk=500):
        '''
        Initialize a sonObj instance.

        ----------
        Parameters
        ----------
        self.sonFile : str
            DESCRIPTION - Path to .SON file.
            EXAMPLE -     self.sonFile = 'C:/PINGMapper/SonarRecordings/R00001/B002.SON'
        self.humFile : str
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
        self._getHumDatStruct()
        '''

        # Set variables equal to data stored in attributes.
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

        #Onix
        else:
            humdic = {}
            self.isOnix = 1

        self.humDatStruct = humdic
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
        humdic = self.humDatStruct
        humFile = self.humFile
        datLen = self.datLen
        t = self.tempC

        humDat = defaultdict(dict) # Empty dict to store DAT contents
        endian = humdic['endianness'] # Is data big or little endian?
        file = open(humFile, 'rb') # Open the file
        # Search for humdic items in DAT file
        for key, val in humdic.items():
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
                # If the expected data is less than 4 bytes long
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

        # Calculate speed of sound based on temp & salinity
        c = 1449.05 + 45.7*t - 5.21*t**2 + 0.23*t**3 + (1.333 - 0.126*t + 0.009*t**2)*(S - 35)

        # Calculate time varying gain
        tvg = ((8.5*10**-5)+(3/76923)+((8.5*10**-5)/4))*c
        humDat['tvg'] = tvg
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
        self.humDat = humdat # Store data in class attribute for later use
        return

    # ======================================================================
    def _fread(self,
               infile,
               num,
               typ):
        '''
        Helper function that reads binary data in a file.
        '''
        dat = arr(typ)
        dat.fromfile(infile, num)
        return(list(dat))

    # ======================================================================
    def _getEPSG(self):
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
    # Determine sonar record header length (varies by model)                   #
    ############################################################################

    # ======================================================================
    def _cntHead(self):
        '''
        Determine .SON sonar record header length based on known Humminbird
        .SON file structure.  Humminbird stores sonar records in packets, where
        the first x bytes of the packet contain metadata (record number, northing,
        easting, time elapsed, depth, etc.), proceeded by the sonar returns
        associated with that sonar record.  This function will search the first
        sonar record to determine the length of sonar record header.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        self.__init__()

        -------
        Returns
        -------
        self.headBytes, indicating length, in bytes, of sonar record header.

        --------------------
        Next Processing Step
        --------------------
        self._getHeadStruct()
        '''
        file = open(self.sonFile, 'rb')
        i = 0
        foundEnd = False
        while foundEnd is False and i < 200:
            lastPos = file.tell() # Get current position in file (byte offset from beginning)
            byte = self._fread(file, 1, 'B') # Decode byte value

            # Check if we found the end of the sonar record.
            ## A 33 **may** indicate end of sonar record.
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

        # i reaches 200, then we have exceeded known Humminbird header length
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
        Determines .SON header structure based on self.headBytes.

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

        if not exportUnknown:
            toDelete = []
            for key, value in headStruct.items():
                attributeName = value[3]
                if 'unknown' in attributeName:
                    toDelete.append(key)
            for key in toDelete:
                del headStruct[key]

        self.headStruct = headStruct # Store data in class attribute for later use
        return

    # ======================================================================
    def _checkHeadStruct(self):
        '''
        Check to make sure sonar record header was structure determined
        appropriately.  The function searches through first sonar record to make
        sure each of the previously identified metadata attributes are located
        at the appropriate byte offset.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        self._getHeadStruct()

        -------
        Returns
        -------
        A boolean flag stored in self.headValid indicating if the sonar record
        structure was appropriately determined.

        --------------------
        Next Processing Step
        --------------------
        If self.headValid == False:
            self._decodeHeadStruct
        else:
            self._getSonMeta()
        '''
        headStruct = self.headStruct # Load sonar record header structure
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
            # We never determined the sonar record header structure.
            headValid = [-1]
        self.headValid = headValid # Store data in class attribute for later use
        return

    # ======================================================================
    def _decodeHeadStruct(self,
                          exportUnknown = False):
        '''
        If sonar return header structure not previously known, attempt to
        automatically decode.  This function will iterate through each byte at
        the beginning of the sonar file, decode the byte, determine if it matches
        any known or unknown spacer value (sonar record attribute 'name') and if
        it does, store the byte offset.

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
        headBytes = self.headBytes
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

        # If first four bytes match known Humminbird sonar record header
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

        if not exportUnknown:
            toDelete = []
            for key, value in headStruct.items():
                attributeName = value[3]
                if 'unknown' in attributeName:
                    toDelete.append(key)
            for key in toDelete:
                del headStruct[key]

        self.headStruct = headStruct # Store data in class attribute for later use
        return

    ############################################################################
    # Get the metadata for each sonar record                                   #
    ############################################################################

    # ======================================================================
    def _getSonMeta(self):
        '''
        Use .IDX file to find every sonar record in .SON file. If .IDX file is
        not present, automatically determine each sonar record location in bytes.
        Then call _getHeader() to decode sonar return header.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        self._getHeadStruct()

        -------
        Returns
        -------
        B00*_**_*****_meta.csv where each row is associated with a sonar record
        and each column contains a given sonar record's metadata.

        --------------------
        Next Processing Step
        --------------------
        No additional processing is necessary if only interested in data exported
        to .CSV.  If export of non-rectified imagery is desired, next step is
        self._getScansChunk().
        '''

        # Get necessary class attributes
        headStruct = self.headStruct
        nchunk = self.nchunk
        idxFile = self.sonIdxFile

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
        if idxFile != "NA":
            idxLen = os.path.getsize(idxFile) # Determine length in bytes
            idxFile = open(idxFile, 'rb') # Open .IDX file
            i = j = chunk = 0 # Set counters
            while i < idxLen:
                # Decode .IDX data and store in IDX dictionary
                idx['time_s'].append(struct.unpack('>I', arr('B', self._fread(idxFile, 4, 'B')).tobytes())[0])
                sonIndex = struct.unpack('>I', arr('B', self._fread(idxFile, 4, 'B')).tobytes())[0]
                idx['index'].append(sonIndex)
                idx['chunk_id'].append(chunk)

                # Store needed data in head dict
                head['index'].append(sonIndex)
                head['chunk_id'].append(chunk)
                headerDat = self._getHeader(sonIndex) # Get and decode header data in .SON file
                for key, val in headerDat.items():
                    head[key].append(val) # Store in dictionary
                idx['record_num'].append(headerDat['record_num'])
                # Increment counters
                i+=8
                j+=1
                if j == nchunk:
                    j=0
                    chunk+=1
        # If .IDX file is missing
        ## Attempt to automatically decode .SON file
        else:
            print("\n\n{} is missing.  Automatically decoding SON file...".format(idxFile))
            sonFile = self.sonFile # Get .SON file path
            fileLen = os.path.getsize(sonFile) # Determine size of .SON file
            file = open(sonFile, 'rb') # Open .SON file
            i = j = chunk = 0 # Set counters
            while i < fileLen:
                file.seek(i) # Go to appropriate location in file
                headStart = struct.unpack('>I', arr('B', self._fread(file, 4, 'B')).tobytes())[0]
                if headStart == 3235818273: # We are at the beginning of a sonar record
                    # Store needed data in head dict
                    head['index'].append(i)
                    head['chunk_id'].append(chunk)
                else:
                    sys.exit("Not at head of sonar record")

                headerDat = self._getHeader(i) # Get and decode header data in .SON file
                for key, val in headerDat.items():
                    head[key].append(val) # Store in dictionary
                # Increment counters
                i = i + self.headBytes + headerDat['ping_cnt'] # Determine location of next sonar record
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

        # Write data to csv
        outCSV = os.path.join(self.metaDir, self.beam+"_"+self.beamName+"_meta.csv")
        sonMetaAll.to_csv(outCSV, index=False, float_format='%.14f')
        self.sonMetaFile = outCSV

    # ======================================================================
    def _getHeader(self,
                   sonIndex):
        '''
        Helper function that, given a byte index location, decodes a sonar
        record's metadata according to known sonar record header structure.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called by self._getSonMeta()

        -------
        Returns
        -------
        A dictionary containing current sonar record's metadata.

        --------------------
        Next Processing Step
        --------------------
        Return metadata to self._getSonMeta()
        '''

        # Get necessary class attributes
        headStruct = self.headStruct
        humDat = self.humDat
        nchunk = self.nchunk

        sonHead = {'lat':-1} # Create dictionary to store sonar record metadata
        file = open(self.sonFile, 'rb') # Open .SON file
        # Traverse .SON file based on known headStruct
        for key, val in headStruct.items():
            index = sonIndex + val[0] + val[1]
            file.seek(index) # Go to appropriate location
            # Decode data based on expected data byte size
            if val[2] == 4:
                byte = struct.unpack('>i', arr('B', self._fread(file, val[2], 'B')).tobytes())[0]
            elif 1 < val[2] <4:
                byte = struct.unpack('>h', arr('b', self._fread(file, val[2],'b')).tobytes() )[0]
            else:
                byte = self._fread(file, val[2], 'b')[0]

            sonHead[val[-1]] = byte # Store attribute name and data in sonHead

        file.close() # Close .SON file

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

        # Add tvg depth correction?
        # tvg = humDat['tvg']
        # dist_tvg = np.squeeze(((np.tan(np.radians(25)))*np.squeeze(sonHead['inst_dep_m']))-(tvg))
        # sonHead['inst_dep_m_tvg'] = dist_tvg

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

    # ======================================================================
    def _getScansChunk(self,
                       detectDepth,
                       smthDep,
                       adjDep=0):
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
        sonMetaAll = pd.read_csv(self.sonMetaFile) # Load sonar record metadata

        totalChunk = sonMetaAll['chunk_id'].max() #Total chunks to process
        i = 0 # Chunk index counter
        while i <= totalChunk:
            # Filter df by chunk
            isChunk = sonMetaAll['chunk_id']==i
            sonMeta = sonMetaAll[isChunk].reset_index()
            # Update class attributes based on current chunk
            self.pingMax = sonMeta['ping_cnt'].astype(int).max() # store to determine max range per chunk
            self.headIdx = sonMeta['index'].astype(int) # store byte offset per sonar record
            self.pingCnt = sonMeta['ping_cnt'].astype(int) # store ping count per sonar record
            # Load chunk's sonar data into memory
            self._loadSonChunk()
            # Export water column present image
            if self.wcp:
                self._writeTiles(i, imgOutPrefix='wcp')
            # Export slant range corrected (water column removed) imagery
            if self.src and (self.beamName=='ss_port' or self.beamName=='ss_star'):
                # self._remWater(detectDepth, sonMeta, adjDep)
                self._SRC(sonMeta, 'FlatBottom')
                self._writeTiles(i, imgOutPrefix='src')

            i+=1

        return self

    # ======================================================================
    def _loadSonChunk(self):
        '''
        Reads in sonar record ping values based on byte index location in son
        file and number of pings to return.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self._getScansChunk() or self._getScanChunkSingle()

        -------
        Returns
        -------
        2-D numpy array containing sonar intensity

        --------------------
        Next Processing Step
        --------------------
        Return numpy array to self._getScansChunk() or self._getScanChunkSingle()
        '''
        sonDat = np.zeros((self.pingMax, len(self.pingCnt))).astype(int) # Initialize array to hold sonar returns
        file = open(self.sonFile, 'rb') # Open .SON file
        # Iterate each sonar record
        for i in range(len(self.headIdx)):
            headIdx = self.headIdx[i] # Get current byte offset to sonar record
            pingCnt = self.pingCnt[i] # Get current ping count
            pingIdx = headIdx + self.headBytes # Determine byte offset to sonar returns
            file.seek(pingIdx) # Move to that location
            k = 0
            # Decode each sonar return and store in array
            while k < pingCnt:
                byte = self._fread(file, 1, 'B')[0]
                sonDat[k,i] = byte
                k+=1

        file.close() # Close the file
        self.sonDat = sonDat # Store array in class attribute
        return self

    # ======================================================================
    def _writeTiles(self,
                    k,
                    imgOutPrefix):
        '''
        Using currently saved sonar record ping returns in self.sonDAT, saves an
        unrectified image of the sonar echogram.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self._getScansChunk() or self._getScanChunkSingle() after
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
        data = self.sonDat # Get the sonar data
        nx, ny = np.shape(data) # Determine array shape
        Z, ind = sliding_window(data, (nx, ny)) # Probably don't need this...

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
        Z = Z[0].astype('uint8')

        # Prepare output directory
        outDir = os.path.join(self.outDir, imgOutPrefix)
        try:
            os.mkdir(outDir)
        except:
            pass

        channel = os.path.split(self.outDir)[-1] #ss_port, ss_star, etc.
        projName = os.path.split(self.projDir)[-1] #to append project name to filename
        imageio.imwrite(os.path.join(outDir, projName+'_'+imgOutPrefix+'_'+channel+'_'+addZero+str(k)+'.png'), Z)

    # ======================================================================
    def _SRC(self,
             sonMeta,
             type = 'FlatBottom'):
        '''
        Slant range correction is the process of relocating sonar returns after
        water column removal by converting slant range distances to the bed into
        horizontal distances based off the depth at nadir.  As SSS does not
        measure depth across the track, we must assume depth is constant across
        the track (Flat bottom assumption).  The pathagorean theorem is used
        to calculate horizontal distance from slant range distance and depth at
        nadir.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self._remWater()

        -------
        Returns
        -------
        Self w/ array of relocated intensities stored in class attribute.

        --------------------
        Next Processing Step
        --------------------
        Returns relocated bed intensities to self._remWater()
        '''
        bedPick = round(sonMeta['dep_m'] / sonMeta['pix_m'], 0).astype(int)

        # Initialize 2d array to store relocated sonar records
        srcDat = np.zeros((self.sonDat.shape[0], self.sonDat.shape[1])).astype(int)
        # print('\n\n')
        # print(srcDat.shape, self.sonDat.shape, len(bedPick))
        for j in range(self.sonDat.shape[1]): #Iterate each sonar record
            depth = bedPick[j] # Get depth (in pixels) at nadir
            # Create 1d array to store relocated bed pixels.  Set to -1 so we
            ## can later interpolate over gaps.
            pingDat = (np.ones((self.sonDat.shape[0])).astype(np.float32)) * -1
            dataExtent = 0
            for i in range(self.sonDat.shape[0]): #Iterate each sonar return
                if i >= depth:
                    intensity = self.sonDat[i,j] # Get the intensity value
                    srcIndex = round(np.sqrt(i**2 - depth**2),0).astype(int) #Calculate horizontal range (in pixels)
                    pingDat[srcIndex] = intensity # Store intensity at appropriate horizontal range
                    dataExtent = srcIndex # Store range extent (max range) of sonar record
                else:
                    pass
            pingDat[dataExtent:]=0 # Zero out values past range extent so we don't interpolate past this

            # Process of relocating bed pixels will introduce across track gaps
            ## in the array so we will interpolate over gaps to fill them.
            pingDat[pingDat==-1] = np.nan
            nans, x = np.isnan(pingDat), lambda z: z.nonzero()[0]
            pingDat[nans] = np.interp(x(nans), x(~nans), pingDat[~nans])

            # Store relocated sonar record in output array
            srcDat[:,j] = np.around(pingDat, 0).astype(int)

        self.sonDat = srcDat # Store in class attribute for later use
        return self

    ############################################################################
    # For Automatic Depth Detection                                            #
    ############################################################################

    # ======================================================================
    def _detectDepth(self,
                     detectDepth=1,
                     pltBedPick=False):
        '''
        Main function for depth detection.
        '''
        sonMetaAll = pd.read_csv(self.sonMetaFile) # Load sonar record metadata

        totalChunk = sonMetaAll['chunk_id'].max() #Total chunks to process
        i = 0 # Chunk index counter

        while i <= totalChunk:
            print("\t{}: {} of {}".format(self.beamName, i, int(totalChunk)))
            # Filter df by chunk
            isChunk = sonMetaAll['chunk_id']==i
            sonMeta = sonMetaAll[isChunk].reset_index()
            # Update class attributes based on current chunk
            self.pingMax = sonMeta['ping_cnt'].astype(int).max() # store to determine max range per chunk
            self.headIdx = sonMeta['index'].astype(int) # store byte offset per sonar record
            self.pingCnt = sonMeta['ping_cnt'].astype(int) # store ping count per sonar record
            # Load chunk's sonar data into memory
            self._loadSonChunk()

            if detectDepth==0:
                acousticBed = round(sonMeta['inst_dep_m'] / sonMeta['pix_m'], 0).astype(int)
                bedPick1 = None
                bedPick2 = None
                bedPick = acousticBed

            elif detectDepth==1:
                acousticBed = round(sonMeta['inst_dep_m'] / sonMeta['pix_m'], 0).astype(int)
                bedPick1 = self._detectDepth_BinaryThresh(acousticBed)
                bedPick2 = None
                bedPick = bedPick1

            elif detectDepth==2:
                acousticBed = round(sonMeta['inst_dep_m'] / sonMeta['pix_m'], 0).astype(int)
                bedPick1 = None
                bedPick2 = self._detectDepth_segZoo_ResU_Net(acousticBed, doThresh=True)
                bedPick = bedPick2

            elif detectDepth==3:
                acousticBed = round(sonMeta['inst_dep_m'] / sonMeta['pix_m'], 0).astype(int)
                bedPick1 = self._detectDepth_BinaryThresh(acousticBed)
                bedPick2 = self._detectDepth_segZoo_ResU_Net(acousticBed, doThresh=True)
                bedPick = bedPick2

            elif detectDepth==4:
                acousticBed = None
                bedPick1 = None
                bedPick2 = self._detectDepth_segZoo_ResU_Net_Rescale()
                bedPick = bedPick2

            if pltBedPick:
                self._writeBedPick(i, acousticBed, bedPick1, bedPick2)

            sonMetaAll.loc[sonMetaAll['chunk_id']==i, 'dep_m'] = sonMeta['pix_m'].values * bedPick
            i+=1

        # Write output's to .CSV
        sonMetaAll.to_csv(self.sonMetaFile, index=False, float_format='%.14f')

        return self

    # ======================================================================
    def _detectDepth_BinaryThresh(self,
                                  acousticBed):
        '''
        Automatically determine depth from rules-based thresholding method.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self._remWater()

        -------
        Returns
        -------
        A list with depth estimate for each ping.

        --------------------
        Next Processing Step
        --------------------
        Returns depth estimate to self._remWater()
        '''
        # Parameters
        window = 10 # For peak removal in bed pick: moving window size
        max_dev = 5 # For peak removal in bed pick: maximum standard deviation
        pix_buf = 50 # Buffer size around min/max Humminbird depth

        img = self.sonDat # Get sonar intensities
        img = standardize(img)[:,:,0].squeeze() # Standardize and rescale
        W, H = img.shape[1], img.shape[0] # Determine array dimensions

        ##################################
        # Step 1 : Acoustic Bedpick Filter
        # Use acoustic bed pick to crop image
        bedMin = max(min(acousticBed)-50, 0)
        bedMax = max(acousticBed)+pix_buf

        cropMask = np.ones((H, W)).astype(int)
        cropMask[:bedMin,:] = 0
        cropMask[bedMax:,:] = 0

        # Mask the image with bed_mask
        imgMasked = img*cropMask

        ###########################
        # Step 2 - Threshold Filter
        # Binary threshold masked image
        imgMasked = gaussian(imgMasked, 3, preserve_range=True) # Do a gaussian blur
        imgMasked[imgMasked==0]=np.nan # Set zero's to nan

        imgBinaryMask = np.zeros((H, W)).astype(bool) # Create array to store thresholded sonar img
        # Iterate over each sonar record
        for i in range(W):
            thresh = max(np.nanmedian(imgMasked[:,i]), np.nanmean(imgMasked[:,i])) # Determine threshold value
            # stdev = np.nanstd(imgMasked[:,i])
            imgBinaryMask[:,i] = imgMasked[:,i] > thresh # Keep only intensities greater than threshold

        # Clean up image binary mask
        imgBinaryMask = remove_small_objects(imgBinaryMask, 2*H)
        imgBinaryMask = remove_small_holes(imgBinaryMask, 2*H)
        imgBinaryMask = np.squeeze(imgBinaryMask[:H,:W])

        ########################################
        # Step 3 - Non-Contiguous region removal
        # Make sure we didn't accidently zero out the last row, which should be bed.
        # If we did, we will fill it back in
        # Try filtering image_binary_mask through labeling regions
        labelImage, num = label(imgBinaryMask, return_num=True)
        allRegions = []

        # Find the lowest/deepest region (this is the bed pixels)
        max_row = 0
        finalRegion = 0
        for region in regionprops(labelImage):
            allRegions.append(region.label)
            minr, minc, maxr, maxc = region.bbox
            # if (maxr > max_row) and (maxc > max_col):
            if (maxr > max_row):
                max_row = maxr
                finalRegion = region.label

        # If finalRegion is 0, there is only one region
        if finalRegion == 0:
            finalRegion = 1

        # Zero out undesired regions
        for regionLabel in allRegions:
            if regionLabel != finalRegion:
                labelImage[labelImage==regionLabel] = 0

        imgBinaryMask = labelImage # Update thresholded image
        imgBinaryMask[imgBinaryMask>0] = 1 # Now set all val's greater than 0 to 1 to create the mask

        # Now fill in above last row filled to make sure no gaps in bed pixels
        lastRow = bedMax
        imgBinaryMask[lastRow] = True
        for i in range(W):
            if imgBinaryMask[lastRow-1,i] == 0:
                gaps = np.where(imgBinaryMask[:lastRow,i]==0)[0]
                # Split each gap cluster into it's own array, subset the last one,
                ## and take top value
                topOfGap = np.split(gaps, np.where(np.diff(gaps) != 1)[0]+1)[-1][0]
                imgBinaryMask[topOfGap:lastRow,i] = 1

        # Clean up image binary mask
        imgBinaryMask = imgBinaryMask.astype(bool)
        imgBinaryMask = remove_small_objects(imgBinaryMask, 2*H)
        imgBinaryMask = remove_small_holes(imgBinaryMask, 2*H)
        imgBinaryMask = np.squeeze(imgBinaryMask[:H,:W])

        #############################
        # Step 4 - Water Below Filter
        # Iterate each ping and determine if there is water under the bed.
        # If there is, zero out everything except for the lowest region.
        # Iterate each sonar record
        for i in range(W):
            labelPing, num = label(imgBinaryMask[:,i], return_num=True)
            if num > 1:
                labelPing[labelPing!=num] = 0
                labelPing[labelPing>0] = 1
            imgBinaryMask[:,i] = labelPing

        ###################################################
        # Step 5 - Final Bedpick: Locate Bed & Remove Peaks
        # Now relocate bed from image_binary_mask
        bed = []
        for k in range(W):
            try:
                b = np.where(imgBinaryMask[:,k]==1)[0][0]
            except:
                b=0
            bed.append(b)
        bed = np.array(bed).astype(np.float32)

        # Interpolate over nan's
        nans, x = np.isnan(bed), lambda z: z.nonzero()[0]
        bed[nans] = np.interp(x(nans), x(~nans), bed[~nans])

        return bed

    # ======================================================================
    def _detectDepth_segZoo_ResU_Net(self,
                                     acousticBed,
                                     doThresh=False):
        # Trained w/ Segmentation Zoo: https://github.com/dbuscombe-usgs/segmentation_zoo
        '''
        '''
        # Parameters
        USE_GPU = False
        weights = r'.\models\bedpick\bedpick_ModelWeights.h5'
        win_overlap_r = 0.5
        win_overlap_c = 0.5

        configfile = weights.replace('.h5','.json').replace('weights', 'config')

        with open(configfile) as f:
            config = json.load(f)

        globals().update(config)

        # Initialize the model
        model = res_unet((TARGET_SIZE[0], TARGET_SIZE[1], N_DATA_BANDS), BATCH_SIZE, NCLASSES)
        model.compile(optimizer = 'adam', loss = 'categorical_crossentropy', metrics = [mean_iou, dice_coef])
        model.load_weights(weights)

        # Convert array to tensor
        image, w, h, bigimage = seg_file2tensor_3band(self.sonDat, TARGET_SIZE, resize=True)
        if image is None:
            image = bigimage#/255
        w = image.shape[0]; h = image.shape[1] #Model target size shape
        W_orig = bigimage.shape[0]; H_orig = bigimage.shape[1] #Original image shape

        image = standardize(image.numpy()).squeeze()
        bigimage = standardize(bigimage.numpy()).squeeze()

        if doThresh:
            ##############
            # Testing binary threshold filter
            threshBed = self._detectDepth_BinaryThresh(acousticBed).astype(int)

            # Create a mask from rules-based threshold bedpick
            msk = np.ones((W_orig, H_orig)).astype(int)
            for i, bed in enumerate(threshBed):
                msk[:bed,i] = 0

            imgBed = bigimage*msk # Mask out the water, leaving only bed pix
            imgWat = bigimage*(~msk) # Mask out the bed, leaving only water pix

            # Find standard deviations for bed and water
            bedStdv = np.nanstd(imgBed)
            watStdv = np.nanstd(imgWat)

            # Subtract a standard deviation from 'water' region
            imgWat[imgWat>0] = imgWat[imgWat>0]-(watStdv)
            imgWat[imgWat<0] = 0.05
            imgWat[imgWat>1] = 1

            bigimage = imgBed + imgWat

            ######################
            # End threshold filter
            ######################

        # Determine window indecies ensuring complete coverage
        row_i, stride_r = getWindowIndices(W_orig, w, win_overlap_r)
        col_i, stride_c = getWindowIndices(H_orig, h, win_overlap_c)

        # Predict over a moving window
        for win_r in row_i:
            for win_c in col_i:
                winImage = bigimage[win_r:win_r+w, win_c:win_c+h]

                E = []; W = []
                E.append(model.predict(tf.expand_dims(winImage, 0) , batch_size=1).squeeze())
                W.append(1)

                K.clear_session()

                est_label = np.average(np.dstack(E), axis=-1, weights=np.array(W))
                est_label /= est_label.max()

                # if np.max(est_label)-np.min(est_label) > .5:
                #     thres = threshold_otsu(est_label)
                #     print("Threshold: %f" % (thres))
                # else:
                #     thres = .9
                #     print("Default threshold: %f" % (thres))
                thres = 0.90

                var = np.std(np.dstack(E), axis=-1)

                conf = 1-est_label
                conf[est_label<thres] = est_label[est_label<thres]
                conf = 1-conf

                conf[np.isnan(conf)] = 0
                conf[np.isinf(conf)] = 0

                model_conf = np.sum(conf)/np.prod(conf.shape)

                est_label[est_label<thres] = 0
                est_label[est_label>thres] = 1
                est_label = remove_small_holes(est_label.astype(bool), 2*w)
                est_label = remove_small_objects(est_label, 2*w)
                est_label[est_label<thres] = 0
                est_label[est_label>thres] = 1
                est_label = np.squeeze(est_label[:w,:h])

                ## Add results to predictStack
                # First determine row/col offset so predictions population at appropriate index
                row_off = win_r
                col_off = win_c

                # Create nan array of original size to store results
                winPredict = np.zeros((W_orig, H_orig))
                winPredict[:,:] = np.nan

                # Store results
                winPredict[row_off:row_off+w, col_off:col_off+h] = est_label

                # Stack results
                if row_off==0 and col_off==0:
                    predictStack = winPredict.copy()
                else:
                    predictStack = np.dstack((predictStack, winPredict))
                del winPredict

        # Now we have all our results
        # Find the mean of the stack
        predictStack = np.nanmean(predictStack, axis=-1)

        # Threshold predictions
        predictStack = np.nan_to_num(predictStack, nan=1)
        predictStack[predictStack>=0.5] = 1
        predictStack[predictStack<0.5] = 0

        ###########################
        # Post-prediction filtering
        # 1) Remove bed floating on water
        # Determine if more then one water region
        waterRegions = predictStack.copy()
        waterRegions[waterRegions==0] = 2 # Change water pix values to 2
        waterRegions[waterRegions==1] = 0

        labelImage, num = label(waterRegions, return_num=True)

        pingsFiltered = np.zeros((H_orig)).astype(bool)
        if num > 1:
            for i in range(H_orig):
                gaps = np.where(predictStack[:,i]==0)[0]
                # Split each gap cluster into it's own array, subset the last one,
                ## and take top value
                if len(gaps) > 1:
                    topOfGap = np.split(gaps, np.where(np.diff(gaps) != 1)[0]+1)[-1][0]
                    if topOfGap > 0:
                        predictStack[:topOfGap,i] = 0
                        pingsFiltered[i] = True

        # Locate the bed
        bed = []
        for k in range(H_orig):
            try:
                b = np.where(predictStack[:,k]==1)[0][0]
            except:
                b=0
            bed.append(b)

        bed = np.array(bed).astype(np.float32)

        # Set outliers to zero.  We will interpolate over them during final bedpick
        bed = np.where(abs(bed - np.median(bed)) < 2 * np.std(bed), bed, 0)

        return bed.astype(int)

    # ======================================================================
    def _detectDepth_segZoo_ResU_Net_Rescale(self):
        # Trained w/ Segmentation Zoo: https://github.com/dbuscombe-usgs/segmentation_zoo
        '''
        '''
        # Parameters
        USE_GPU = False
        weights = r'.\models\bedpick\bedpick_ModelWeights.h5'

        configfile = weights.replace('.h5','.json').replace('weights', 'config')

        with open(configfile) as f:
            config = json.load(f)

        globals().update(config)

        # Initialize the model
        model = res_unet((TARGET_SIZE[0], TARGET_SIZE[1], N_DATA_BANDS), BATCH_SIZE, NCLASSES)
        model.compile(optimizer = 'adam', loss = 'categorical_crossentropy', metrics = [mean_iou, dice_coef])
        model.load_weights(weights)

        # Convert array to tensor
        image, w, h, bigimage = seg_file2tensor_3band(self.sonDat, TARGET_SIZE, resize=True)
        if image is None:
            image = bigimage#/255
        w = image.shape[0]; h = image.shape[1] #Model target size shape
        W_orig = bigimage.shape[0]; H_orig = bigimage.shape[1] #Original image shape

        # Standardize
        image = standardize(image.numpy()).squeeze()
        bigimage = standardize(bigimage.numpy()).squeeze()

        #################################
        # Do prediction on rescaled image
        E = []; W = []
        E.append(model.predict(tf.expand_dims(image, 0) , batch_size=1).squeeze())
        W.append(1)

        K.clear_session()

        est_label = np.average(np.dstack(E), axis=-1, weights=np.array(W))
        est_label /= est_label.max()

        if np.max(est_label)-np.min(est_label) > .5:
            thres = threshold_otsu(est_label)
            print("Threshold: %f" % (thres))
        else:
            thres = .9
            print("Default threshold: %f" % (thres))

        var = np.std(np.dstack(E), axis=-1)

        conf = 1-est_label
        conf[est_label<thres] = est_label[est_label<thres]
        conf = 1-conf

        conf[np.isnan(conf)] = 0
        conf[np.isinf(conf)] = 0

        model_conf = np.sum(conf)/np.prod(conf.shape)

        est_label[est_label<thres] = 0
        est_label[est_label>thres] = 1
        est_label = remove_small_holes(est_label.astype(bool), 2*w)
        est_label = remove_small_objects(est_label, 2*w)
        est_label[est_label<thres] = 0
        est_label[est_label>thres] = 1
        est_label = np.squeeze(est_label[:w,:h])

        # Locate the bed
        bed = []
        for k in range(H_orig):
            try:
                b = np.where(est_label[:,k]==1)[0][0]
            except:
                b=0
            bed.append(b)

        bed = np.array(bed).astype(np.float32)



    # ======================================================================
    def _writeBedPick(self,
                      k,
                      acousticBed = None,
                      bed1 = None,
                      bed2 = None,
                      finalBed = None,
                      imgOutPrefix = 'bedpick'):

        '''
        Exports a plot of a bedpick on a non-rectified sonogram.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self._detectDepth() or self._writeFinalBedPick()

        -------
        Returns
        -------
        A .png in projDir/*sonar_channel*/bedpick showing bedpick overlain on a
        sonogram.
        '''
        data = self.sonDat # Get the sonar data

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

        # Prepare output directory if it doesn't already exist
        outDir = os.path.join(self.outDir, imgOutPrefix)
        try:
            os.mkdir(outDir)
        except:
            pass

        channel = os.path.split(self.outDir)[-1] #ss_port, ss_star, etc.
        projName = os.path.split(self.projDir)[-1] #to append project name to filename
        outFile = os.path.join(outDir, projName+'_'+imgOutPrefix+'_'+channel+'_'+addZero+str(k)+'.png') #prepare file name

        plt.imshow(data, cmap='gray') # create Matlab plt object
        if acousticBed is not None: # plot acoustic bedpick in yellow
            plt.plot(acousticBed, 'y-.', lw=1, label='Acoustic Depth')
        if bed1 is not None: # plot binary threshold bedpick in magenta
            plt.plot(bed1, 'm-.', lw=1, label='Auto Depth 1')
        if bed2 is not None: # plot residual u-net bedpick in red
            plt.plot(bed2, 'r-.', lw=1, label='Auto Depth 2')
        if finalBed is not None: # plot final bedpick in blue
            plt.plot(finalBed, 'b-.', lw=1, label='Auto Depth Final')
        plt.legend(loc = 'lower right', prop={'size':4}) # create the plot legend
        plt.savefig(outFile, dpi=300, bbox_inches='tight') # save the plot
        plt.close()

    # ======================================================================
    def _writeFinalBedPick(self):
        '''
        '''
        sonMetaAll = pd.read_csv(self.sonMetaFile) # Load sonar record metadata

        totalChunk = sonMetaAll['chunk_id'].max() #Total chunks to process
        i = 0 # Chunk index counter

        while i <= totalChunk:
            # Filter df by chunk
            isChunk = sonMetaAll['chunk_id']==i
            sonMeta = sonMetaAll[isChunk].reset_index()
            # Update class attributes based on current chunk
            self.pingMax = sonMeta['ping_cnt'].astype(int).max() # store to determine max range per chunk
            self.headIdx = sonMeta['index'].astype(int) # store byte offset per sonar record
            self.pingCnt = sonMeta['ping_cnt'].astype(int) # store ping count per sonar record
            # Load chunk's sonar data into memory
            self._loadSonChunk()
            acousticBed = round(sonMeta['inst_dep_m'] / sonMeta['pix_m'], 0).astype(int)
            finalBed = round(sonMeta['dep_m'] / sonMeta['pix_m'], 0).astype(int)
            self._writeBedPick(i, acousticBed, finalBed = finalBed, imgOutPrefix = 'bedpick_final')
            i+=1

    ############################################################################
    # Miscellaneous                                                            #
    ############################################################################

    # ======================================================================
    def _getScanChunkSingle(self,
                            chunk,
                            remWater,
                            adjDep=0):
        '''
        During rectification, if non-rectified tiles have not been exported,
        this will load the chunk's scan data from the sonar recording.

        Stores the number of pings per chunk, chunk id, and byte index location
        in son file, then calls self._loadSonChunk() to read the data.

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

        i = chunk #Chunk index
        # Filter df by chunk
        isChunk = sonMetaAll['chunk_id']==i
        sonMeta = sonMetaAll[isChunk].reset_index()
        # Update class attributes based on current chunk
        self.pingMax = sonMeta['ping_cnt'].astype(int).max() # store to determine max range per chunk
        self.headIdx = sonMeta['index'].astype(int) # store byte offset per sonar record
        self.pingCnt = sonMeta['ping_cnt'].astype(int) # store ping count per sonar record
        # Load chunk's sonar data into memory
        self._loadSonChunk()
        # Remove water if exporting src imagery
        if remWater:
            self._SRC(sonMeta, 'FlatBottom')

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
