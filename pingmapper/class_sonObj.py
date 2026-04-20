# Part of PING-Mapper software
#
# GitHub: https://github.com/CameronBodine/PINGMapper
# Website: https://cameronbodine.github.io/PINGMapper/ 
#
# Co-Developed by Cameron S. Bodine and Dr. Daniel Buscombe
#
# Inspired by PyHum: https://github.com/dbuscombe-usgs/PyHum
#
# MIT License
#
# Copyright (c) 2025 Cameron S. Bodine
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

import os, sys

# Add 'pingmapper' to the path, may not need after pypi package...
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.append(PACKAGE_DIR)

from pingmapper.funcs_common import *

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

    #=======================================================================
    def _saveSonMetaCSV(self, sonMetaAll):
        # Write metadata to csv
        if not hasattr(self, 'sonMetaFile'):
            outCSV = os.path.join(self.metaDir, self.beam+"_"+self.beamName+"_meta.csv")
            sonMetaAll.to_csv(outCSV, index=False, float_format='%.14f')
            self.sonMetaFile = outCSV
        else:
            sonMetaAll.to_csv(self.sonMetaFile, index=False, float_format='%.14f')


    ############################################################################
    # Filter sonar recording from user params                                  #
    ############################################################################

    # ======================================================================
    def _doSonarFiltering(self, 
                          max_heading_dev,
                          distance,
                          min_speed,
                          max_speed,
                          aoi,
                          time_table,
                          ):
        '''
        '''
        #################
        # Get metadata df
        self._loadSonMeta()
        sonDF = self.sonMetaDF

        # print('len', len(sonDF))
        # print(sonDF)

        #############################
        # Do Heading Deviation Filter
        if max_heading_dev > 0:
            sonDF = self._filterHeading(sonDF, max_heading_dev, distance)

        #################
        # Do Speed Filter
        if min_speed > 0 or max_speed > 0:
            sonDF = self._filterSpeed(sonDF, min_speed, max_speed)

        ###############
        # Do AOI Filter
        if aoi:
            sonDF = self._filterAOI(sonDF, aoi)

        #############
        # Time Filter
        if time_table:
            sonDF = self._filterTime(sonDF, time_table)

        return sonDF
    
    # ======================================================================
    def _filterShortTran(self, df):

        '''
        '''

        # Make transects from consective pings using dataframe index
        idx = df.index.values
        transect_groups = np.split(idx, np.where(np.diff(idx) != 1)[0]+1)

        for t in transect_groups:
            if len(t) < self.nchunk:
                # False means remove
                df.loc[t, 'filter'] = False

        return df


    # ======================================================================
    def _filterHeading(self,
                       df,
                       dev,
                       d,
                       ):
        '''
        '''

        #######
        # Setup

        # convert dev to radians
        dev = np.deg2rad(dev)

        # Set Fields for Filtering
        trk_dist = 'trk_dist'       # Along track distance
        head = 'instr_heading'      # Heading reported by instrument
        filtCol = 'filter'

        # Get max distance
        max_dist = df[trk_dist].max()

        # Set counters
        win = 1                     # stride of moving window
        dist_start = 0              # Counter for beginning of current window
        dist_end = dist_start + d   # Counbter for end of current window

        df = df.copy()
        df[filtCol] = False

        # If distance is invalid, do not remove all pings
        if not np.isfinite(max_dist):
            df[filtCol] = True
            return df

        # If heading distance window covers the entire recording,
        # evaluate the complete record once.
        if max_dist <= d:
            head_vals = df[head].to_numpy(copy=True)
            head_vals = head_vals[np.isfinite(head_vals)]

            if len(head_vals) < 2:
                df[filtCol] = True
                return df

            head_vals = np.deg2rad(head_vals)
            head_vals = np.unwrap(head_vals)
            vessel_dev = np.ptp(head_vals)

            if vessel_dev < dev:
                df[filtCol] = True

            return df

        ##############################
        # Iterator through each window

        # Compare heading deviation across each window
        while dist_start < max_dist:

            # Filter df by window
            if dist_end < max_dist:
                window_mask = (df[trk_dist] >= dist_start) & (df[trk_dist] < dist_end)
            else:
                window_mask = (df[trk_dist] >= dist_start) & (df[trk_dist] <= max_dist)
            dfFilt = df.loc[window_mask]

            if len(dfFilt) > 1:

                head_vals = dfFilt[head].to_numpy(copy=True)
                head_vals = head_vals[np.isfinite(head_vals)]

                if len(head_vals) > 1:
                    head_vals = np.deg2rad(head_vals)
                    # Unwrap the heading because heading is circular
                    head_vals = np.unwrap(head_vals)

                    # Get total heading spread in the window
                    vessel_dev = np.ptp(head_vals)

                    # Compare vessel deviation to threshold deviation
                    if vessel_dev < dev:
                        # Keep these pings
                        df.loc[dfFilt.index, filtCol] = True

                    # dist_start += win
                    # dist_start = dist_end

                else:
                    # dist_start = dist_end

                    # df[filtCol].loc[dfFilt.index] = False

                    # dist_start += win

                    pass
                

            dist_start = dist_end
            dist_end = dist_start + d

        # Explicitly reject discontinuities where adjacent pings are farther
        # apart than the heading-distance window. These boundaries can otherwise
        # pass when each side of the gap is internally consistent.
        if d > 0:
            trk_step = df[trk_dist].diff().abs()
            jump_idx = trk_step[(trk_step > d) & np.isfinite(trk_step)].index

            if len(jump_idx) > 0:
                df.loc[jump_idx, filtCol] = False

                prev_idx = jump_idx - 1
                prev_idx = prev_idx[prev_idx >= df.index.min()]
                if len(prev_idx) > 0:
                    df.loc[prev_idx, filtCol] = False

        try:
            return df
        except:
            sys.exit('\n\n\nERROR:\nMax heading standard deviation too small.\nPlease specify a larger value.')

    # ======================================================================
    def _filterTime(self,
                     sonDF,
                     time_table):
        
        '''
        '''

        time_col = 'time_s'
        filtTimeCol = 'filter_time'
        filtCol = 'filter'

        sonDF[filtTimeCol] = False

        if not filtCol in sonDF.columns:
            sonDF[filtCol] = True

        time_table = pd.read_csv(time_table)

        for i, row in time_table.iterrows():

            start = row['start_seconds']
            end = row['end_seconds']

            # dfFilt = sonDF[(sonDF['time_s'] >= start) & (sonDF['time_s'] <= end)]
            sonDF.loc[(sonDF[time_col] >= start) & (sonDF[time_col] <= end) & (sonDF[filtCol] == True), filtTimeCol] = True

        sonDF[filtCol] *= sonDF[filtTimeCol]

        return sonDF
    

    # ======================================================================
    def _filterSpeed(self,
                     sonDF,
                     min_speed,
                     max_speed):
        
        '''
        
        '''

        speed_col = 'speed_ms'
        filtCol = 'filter'

        if not filtCol in sonDF.columns:
            sonDF[filtCol] = True

        # Filter min_speed
        if min_speed > 0:
            # sonDF = sonDF[sonDF['speed_ms'] >= min_speed]
            sonDF.loc[sonDF[speed_col] < min_speed, filtCol] = False

        # Filter max_speed
        if max_speed > 0:
            # sonDF = sonDF[sonDF['speed_ms'] <= max_speed]
            sonDF.loc[sonDF[speed_col] > max_speed, filtCol] = False

        return sonDF

    # ======================================================================
    def _filterAOI(self,
                   sonDF,
                   aoi):
        
        filtCol = 'filter'

        if not filtCol in sonDF.columns:
            sonDF[filtCol] = True
        
        # If .plan file (from Hydronaulix)
        if os.path.basename(aoi.split('.')[-1]) == 'plan':            
            with open(aoi, 'r', encoding='utf-8') as f:
                f = json.load(f)
                # Find 'polygon' coords in nested json
                # polys = []
                # poly_coords = getPolyCoords(f, 'polygon')
                # print(poly_coords)

                f = f['mission']
                f = f['items']
                poly_coords = []
                for i in f:
                    for k, v in i.items():
                        if k == 'polygon':
                            poly_coords.append(v)

                aoi_poly_all = gpd.GeoDataFrame()

                for poly in poly_coords:
                
                    # Extract coordinates
                    lat_coords = [i[0] for i in poly]
                    lon_coords = [i[1] for i in poly]

                    polygon_geom = Polygon(zip(lon_coords, lat_coords))
                    aoi_poly = gpd.GeoDataFrame(index=[0], crs='epsg:4326', geometry=[polygon_geom])

                    aoi_poly_all = pd.concat([aoi_poly_all, aoi_poly], ignore_index=True)

        # If shapefile
        elif os.path.basename(aoi.split('.')[-1]) == 'shp':
            aoi_poly_all = gpd.read_file(aoi)

        else:
            print(os.path.basename, ' is not a valid aoi file type.')
            sys.exit()

        # Reproject to utm
        epsg = int(self.humDat['epsg'].split(':')[-1])
        aoi_poly = aoi_poly_all.to_crs(crs=epsg)
        aoi_poly = aoi_poly.dissolve()

        # Buffer aoi
        if os.path.basename(aoi.split('.')[-1]) == 'plan': 
            buf_dist = 0.5
            aoi_poly['geometry'] = aoi_poly.geometry.buffer(buf_dist)

        # Save aoi
        aoi_dir = os.path.join(self.projDir, 'aoi')
        aoiOut = os.path.basename(self.projDir) + '_aoi.shp'
        if not os.path.exists(aoi_dir):
            os.makedirs(aoi_dir)

        aoiOut = os.path.join(aoi_dir, aoiOut)
        aoi_poly.to_file(aoiOut)

        # Convert to geodataframe
        epsg = int(self.humDat['epsg'].split(':')[-1])
        sonDF = gpd.GeoDataFrame(sonDF, geometry=gpd.points_from_xy(sonDF.e, sonDF.n), crs=epsg)

        # Get polygon
        aoi_poly = aoi_poly.geometry[0]

        # Subset
        mask = sonDF.within(aoi_poly)
        sonDF[filtCol] *= mask

        return sonDF

    # ======================================================================
    def _reassignChunks(self,
                        sonDF):
        
        #################
        # Reassign Chunks
        nchunk = self.nchunk

        if sonDF.empty:
            sonDF = sonDF.copy()
            sonDF['transect'] = pd.Series(dtype='int64')
            sonDF['chunk_id'] = pd.Series(dtype='int64')
            return sonDF

        # Make transects from consective pings using dataframe index
        idx = sonDF.index.values
        transect_groups = np.split(idx, np.where(np.diff(idx) != 1)[0]+1)


        # Assign transect
        transect = 0
        for t in transect_groups:
            if len(t) == 0:
                continue
            sonDF.loc[t, 'transect'] = transect
            transect += 1

        # Set chunks
        lastChunk = 0
        newChunk = []
        for name, group in sonDF.groupby('transect'):

            if (len(group)%nchunk) != 0:
                rdr = nchunk-(len(group)%nchunk)
                chunkCnt = int(len(group)/nchunk)
                chunkCnt += 1
            else:
                rdr = False
                chunkCnt = int(len(group)/nchunk)

            chunks = np.arange(chunkCnt) + lastChunk
            chunks = np.repeat(chunks, nchunk)
            
            if rdr:
                chunks = chunks[:-rdr]
            
            newChunk += list(chunks)
            lastChunk = chunks[-1] + 1
            del chunkCnt

        sonDF['chunk_id'] = newChunk

        # self._saveSonMetaCSV(sonDF)
        # self._cleanup()

        return sonDF


    ############################################################################
    # Fix corrupt recording w/ missing pings                                   #
    ############################################################################

    # ======================================================================
    def _fixNoDat(self, dfA, beams):
        # Empty dataframe to store final results
        df = pd.DataFrame(columns = dfA.columns)

        # For tracking beam presence
        b = defaultdict()
        bCnt = 0
        for i in beams:
            b[i] = np.nan
            bCnt+=1
        del i

        c = 0 # Current row index

        while ((c) < len(dfA)):

            cRow = dfA.loc[[c]]

            # Check if b['beam'] is > 0, if it is, we found end of 'ping packet':
            ## add unfound beams as NoData to ping packet
            if ~np.isnan(b[cRow['beam'].values[0]]):
                # Add valid data to df
                noDat = []
                for k, v in b.items():
                    # Store valid data in df
                    if ~np.isnan(v):
                        df = pd.concat([df,dfA.loc[[v]]], ignore_index=True)
                    # Add beam to noDat list
                    else:
                        noDat.append(k)

                # Duplicate valid data for missing rows. Remove unneccessary values.
                for beam in noDat:
                    df = pd.concat([df, df.iloc[[-1]]], ignore_index=True)
                    # df.iloc[-1, df.columns.get_loc('record_num')] = np.nan
                    df.iloc[-1, df.columns.get_loc('index')] = np.nan
                    df.iloc[-1, df.columns.get_loc('volt_scale')] = np.nan
                    df.iloc[-1, df.columns.get_loc('f')] = np.nan
                    # df.iloc[-1, df.columns.get_loc('ping_cnt')] = np.nan
                    df.iloc[-1, df.columns.get_loc('beam')] = beam
                    del beam
                del noDat

                # reset b
                for k, v in b.items():
                    b.update({k:np.nan})
                del k, v

            else:
                # Add c idx to b and keep searching for beams in current packet
                b[cRow['beam'].values[0]] = c
                c+=1

        del beams, dfA, cRow, bCnt, c, b

        return df

    ############################################################################
    # Export un-rectified sonar tiles                                          #
    ############################################################################

    # ==========================================================================
    def _exportTiles(self,
                     chunk,
                     tileFile):
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
        sonMeta = self._sanitize_chunk_sonmeta(sonMeta)

        # Update class attributes based on current chunk
        self.pingMax = np.nanmax(sonMeta['ping_cnt']) # store to determine max range per chunk
        # self.headIdx = sonMeta['index'] # store byte offset per ping
        # self.pingCnt = sonMeta['ping_cnt'] # store ping count per ping

        if ~np.isnan(self.pingMax):
            # Load chunk's sonar data into memory
            # self._loadSonChunk()
            self._getScanChunkSingle(chunk)

            # Remove shadows
            if self.remShadow:
                # Get mask
                self._SHW_mask(chunk)

                # Mask out shadows
                self.sonDat = self.sonDat*self.shadowMask


            # Export water column present (wcp) image
            if self.wcp:
                son_copy = self.sonDat.copy()
                # self._doPPDRC()

                # egn
                if self.egn:
                    self._egn_wcp(chunk, sonMeta)

                    if self.egn_stretch > 0:
                        self._egnDoStretch()

                self._writeTiles(chunk, imgOutPrefix='wcp', tileFile=tileFile) # Save image

                self.sonDat = son_copy
                del son_copy

            # Export slant range corrected (water column removed) imagery
            if self.wcr_src:
                self._WCR_SRC(sonMeta) # Remove water column and redistribute ping returns based on FlatBottom assumption

                # self._doPPDRC()

                # Empirical gain normalization
                if self.egn:
                    self._egn()
                    self.sonDat = np.nan_to_num(self.sonDat, nan=0)

                    if self.egn_stretch > 0:
                        self._egnDoStretch()

                self._writeTiles(chunk, imgOutPrefix='wcr', tileFile=tileFile) # Save image

            gc.collect()
        return #self


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

        use_jsf_weighting = bool(getattr(self, '_use_jsf_weighting', False))
        use_tvg = bool(getattr(self, 'tvg', False))
        crop_samples_after_flip = getattr(self, '_range_crop_samples_after_flip', None)

        if crop_samples_after_flip is not None:
            try:
                crop_samples_after_flip = int(crop_samples_after_flip)
            except Exception:
                crop_samples_after_flip = None

        if crop_samples_after_flip is not None and crop_samples_after_flip <= 0:
            crop_samples_after_flip = None

        sample_dtype = getattr(self, 'sample_dtype', None)
        sample_is_float = False
        if sample_dtype is not None:
            try:
                sample_is_float = np.dtype(sample_dtype).kind == 'f'
            except Exception:
                sample_is_float = False

        if use_jsf_weighting or use_tvg or sample_is_float:
            sonDat = np.zeros((int(self.pingMax), len(self.pingCnt)), dtype=np.float32)
        else:
            sonDat = np.zeros((int(self.pingMax), len(self.pingCnt))).astype(int) # Initialize array to hold sonar returns
        file = open(self.sonFile, 'rb') # Open .SON file
        file_size = os.path.getsize(self.sonFile)
        skipped_reads = 0

        for i in range(len(self.headIdx)):
            if ~np.isnan(self.headIdx[i]):
                full_ping_len = self.pingCnt[i].astype(int)
                if crop_samples_after_flip is not None:
                    ping_samples = full_ping_len
                else:
                    ping_samples = min(full_ping_len, self.pingMax)

                try:
                    bytes_per_sample = int(self.bytesPerSample[i])
                    if bytes_per_sample <= 0:
                        raise ValueError
                except Exception:
                    try:
                        sample_dtype = getattr(self, 'sample_dtype', None)
                        if sample_dtype is not None:
                            bytes_per_sample = int(np.dtype(sample_dtype).itemsize)
                        else:
                            bytes_per_sample = 1 if self.son8bit else 2
                    except Exception:
                        bytes_per_sample = 1 if self.son8bit else 2


                # #### Do not commit!!!!
                # # if self.beamName == 'ss_star' or self.beamName == 'ss_port':
                # #     ping_len *= 2
                ping_len = int(ping_samples) * int(bytes_per_sample)

                headIDX = self.headIdx[i].astype(int)
                son_offset = self.son_offset[i].astype(int)
                # pingIdx = headIDX + self.headBytes # Determine byte offset to sonar returns
                pingIdx = headIDX + son_offset

                if pingIdx < 0 or pingIdx >= file_size:
                    skipped_reads += 1
                    continue

                remaining_bytes = int(file_size - pingIdx)
                if remaining_bytes <= 0:
                    skipped_reads += 1
                    continue

                max_samples_available = int(remaining_bytes // max(1, int(bytes_per_sample)))
                if max_samples_available <= 0:
                    skipped_reads += 1
                    continue

                if int(ping_samples) > max_samples_available:
                    ping_samples = max_samples_available

                ping_len = int(ping_samples) * int(bytes_per_sample)
                if ping_len <= 0:
                    skipped_reads += 1
                    continue

                file.seek(pingIdx) # Move to that location

                # Get the ping
                buffer = file.read(ping_len)

                # Read the data
                if self.son8bit:# and self.beamName != 'ss_star' and self.beamName != 'ss_port':
                    dat = np.frombuffer(buffer, dtype='>u1')
                else:
                    sample_dtype = getattr(self, 'sample_dtype', None)
                    try:
                        if sample_dtype is not None:
                            dat = np.frombuffer(buffer, dtype=np.dtype(sample_dtype))
                        else:
                            dat = np.frombuffer(buffer, dtype='>u2')
                    except:
                        if sample_dtype is not None:
                            dat = np.frombuffer(buffer[:-1], dtype=np.dtype(sample_dtype))
                        else:
                            dat = np.frombuffer(buffer[:-1], dtype='>u2')

                if self.flip_port:
                    dat = dat[::-1]

                if crop_samples_after_flip is not None:
                    dat = dat[:crop_samples_after_flip]

                if use_jsf_weighting:
                    dat = dat.astype(np.float32, copy=False)
                    if hasattr(self, 'weightingFactor') and i < len(self.weightingFactor):
                        wf = self.weightingFactor[i]
                        if np.isfinite(wf) and wf > 0:
                            dat = dat * (2.0 ** (-float(wf)))

                n_samples = min(len(dat), sonDat.shape[0])
                if n_samples <= 0:
                    skipped_reads += 1
                    continue

                try:
                    sonDat[:n_samples, i] = dat[:n_samples]
                except:
                    n_samples = min(len(dat), sonDat.shape[0])
                    sonDat[:n_samples, i] = dat[:n_samples]
        
        file.close()

        if skipped_reads > 0:
            print(f"Warning: skipped {skipped_reads} out-of-bounds sonar reads for {getattr(self, 'beamName', 'unknown beam')}")

        if crop_samples_after_flip is not None and sonDat.shape[0] > crop_samples_after_flip:
            sonDat = sonDat[:crop_samples_after_flip, :]

        if use_tvg:
            sonDat = self._apply_tvg(sonDat)

        if bool(getattr(self, 'export_16bit', False)) and not bool(getattr(self, 'son8bit', True)):
            self.sonDat16 = np.clip(sonDat, 0, 65535).astype(np.uint16, copy=False)
        else:
            self.sonDat16 = None

        self.sonDat = self._convert_son_dat_to_uint8(sonDat)
        return

    def _apply_tvg(self, sonDat):
        sonDat = np.asarray(sonDat, dtype=np.float32)

        if sonDat.size == 0 or sonDat.shape[0] == 0:
            return sonDat

        pix_m = getattr(self, '_chunk_pixM', np.nan)
        if not np.isfinite(pix_m) or pix_m <= 0:
            pix_m = getattr(self, 'pixM', np.nan)
        if not np.isfinite(pix_m) or pix_m <= 0:
            return sonDat

        k = float(getattr(self, 'tvg_spreading_k', 40.0))
        alpha = float(getattr(self, 'tvg_absorption_db_m', 0.035))
        min_r = float(getattr(self, 'tvg_min_range', 0.2))
        cap_db = float(getattr(self, 'tvg_cap_db', 50.0))

        if not np.isfinite(k):
            k = 40.0
        if not np.isfinite(alpha):
            alpha = 0.035
        if not np.isfinite(min_r) or min_r <= 0:
            min_r = 0.2
        if not np.isfinite(cap_db) or cap_db <= 0:
            cap_db = 50.0

        sample_idx = np.arange(sonDat.shape[0], dtype=np.float32)
        ranges_m = np.maximum(sample_idx * np.float32(pix_m), np.float32(min_r))
        tvg_db = (k * np.log10(ranges_m)) + (2.0 * alpha * ranges_m)
        tvg_db = np.clip(tvg_db, 0.0, cap_db)
        gain = np.power(10.0, tvg_db / 20.0).astype(np.float32)

        sonDat *= gain[:, None]
        return sonDat

    def _convert_son_dat_to_uint8(self, sonDat):
        if np.issubdtype(sonDat.dtype, np.floating):
            arr = np.asarray(sonDat, dtype=np.float32)
            arr[~np.isfinite(arr)] = 0.0
            arr[arr < 0] = 0.0

            valid = arr > 0
            if not np.any(valid):
                return np.zeros(arr.shape, dtype=np.uint8)

            vals = arr[valid]

            lo = float(np.nanpercentile(vals, 1.0))
            hi = float(np.nanpercentile(vals, 99.5))

            max_val = None
            if bool(getattr(self, '_use_jsf_weighting', False)):
                global_max = getattr(self, '_float_global_scale_max', None)
                if global_max is not None and np.isfinite(global_max) and float(global_max) > 0:
                    max_val = float(global_max)
                    hi = min(hi, max_val)

            if (not np.isfinite(lo)) or (not np.isfinite(hi)) or hi <= lo:
                lo = float(np.nanmin(vals))
                hi = float(np.nanmax(vals))

            if (not np.isfinite(lo)) or (not np.isfinite(hi)) or hi <= lo:
                return np.zeros(arr.shape, dtype=np.uint8)

            scaled = (arr - lo) * (255.0 / (hi - lo))
            return np.clip(scaled, 0, 255).astype(np.uint8)

        if self.son8bit:
            return np.clip(sonDat, 0, 255).astype(np.uint8)

        dat_uint16 = np.clip(sonDat, 0, 65535).astype(np.uint16, copy=False)

        # Detect high-byte packing using only non-zero samples so ping padding
        # (zeros below each ping length) does not trigger false detection.
        nz = dat_uint16[dat_uint16 > 0]
        if nz.size == 0:
            return np.zeros(dat_uint16.shape, dtype=np.uint8)

        max_val = int(nz.max())
        low_byte_zero_ratio = np.mean((nz & 0x00FF) == 0)

        # Some XTF chunks appear as 12-bit amplitudes packed in high-byte-aligned
        # 16-bit words (e.g., 0..15 represented as 0, 256, 512, ...). In that case,
        # shift by 4 (not 8) to recover usable 8-bit contrast.
        if low_byte_zero_ratio > 0.95:
            if max_val <= 4095:
                return (dat_uint16 >> 4).astype(np.uint8)
            return (dat_uint16 >> 8).astype(np.uint8)

        return dat_uint16.astype(np.uint8)

    def _sanitize_chunk_sonmeta(self, sonMeta):
        if sonMeta is None or len(sonMeta) == 0 or 'ping_cnt' not in sonMeta.columns:
            return sonMeta

        df = sonMeta.copy()
        ping_cnt = pd.to_numeric(df['ping_cnt'], errors='coerce')
        valid = np.isfinite(ping_cnt) & (ping_cnt > 0)

        filtered = df.loc[valid].copy()

        if 'pixM' in filtered.columns:
            pix_m = pd.to_numeric(filtered['pixM'], errors='coerce')
            plausible_pix = np.isfinite(pix_m) & (pix_m > 1e-4)
            if np.any(plausible_pix):
                filtered = filtered.loc[plausible_pix].copy()

        if len(filtered) == 0:
            filtered = df.loc[valid].copy()

        if len(filtered) == 0:
            return sonMeta

        ping_cnt = pd.to_numeric(filtered['ping_cnt'], errors='coerce')
        plausible_ping = np.isfinite(ping_cnt) & (ping_cnt > 0) & (ping_cnt < 1_000_000)
        if np.any(plausible_ping):
            filtered = filtered.loc[plausible_ping].copy()

        if len(filtered) == 0:
            return sonMeta

        return filtered.reset_index(drop=True)

    def _get_sidescan_pair_meta_file(self):
        if not hasattr(self, 'sonMetaFile'):
            return None

        meta_file = str(self.sonMetaFile)
        base_name = os.path.basename(meta_file)
        dir_name = os.path.dirname(meta_file)

        if 'ss_port' in base_name:
            pair_name = base_name.replace('ss_port', 'ss_star', 1)
        elif 'ss_star' in base_name:
            pair_name = base_name.replace('ss_star', 'ss_port', 1)
        else:
            return None

        pair_file = os.path.join(dir_name, pair_name)
        if os.path.exists(pair_file):
            return pair_file
        return None

    def _compute_jsf_global_scale_max(self, son_meta_df: pd.DataFrame):
        wf_all = pd.to_numeric(son_meta_df['weighting_factor'], errors='coerce').to_numpy(dtype=float)
        wf_valid = wf_all[np.isfinite(wf_all)]

        global_max = np.nan
        if 'max_abs_adc_raw' in son_meta_df.columns:
            adc_all = pd.to_numeric(son_meta_df['max_abs_adc_raw'], errors='coerce').to_numpy(dtype=float)
            pair_valid = np.isfinite(wf_all) & np.isfinite(adc_all) & (adc_all > 0)
            if np.any(pair_valid):
                scaled_adc = adc_all[pair_valid] * np.power(2.0, -wf_all[pair_valid])
                if len(scaled_adc) > 0:
                    pct = float(getattr(self, '_jsf_global_scale_percentile', 99.5))
                    pct = min(max(pct, 95.0), 100.0)
                    global_max = float(np.nanpercentile(scaled_adc, pct))
                    if (not np.isfinite(global_max)) or (global_max <= 0):
                        global_max = float(np.nanmax(scaled_adc))

        if not np.isfinite(global_max) or global_max <= 0:
            if len(wf_valid) > 0:
                min_wf = float(np.nanmin(wf_valid))
                global_max = float(65535.0 * (2.0 ** (-min_wf)))

        return global_max

    def _ensure_jsf_global_scale_max(self, son_meta_df: pd.DataFrame):
        cur = getattr(self, '_float_global_scale_max', np.nan)
        if np.isfinite(cur) and float(cur) > 0:
            return

        meta_frames = [son_meta_df]
        pair_meta_file = self._get_sidescan_pair_meta_file()
        if pair_meta_file is not None:
            try:
                pair_df = pd.read_csv(pair_meta_file)
                if 'weighting_factor' in pair_df.columns:
                    meta_frames.append(pair_df)
            except Exception:
                pass

        if len(meta_frames) > 1:
            combined = pd.concat(meta_frames, ignore_index=True)
        else:
            combined = meta_frames[0]

        global_max = self._compute_jsf_global_scale_max(combined)
        if np.isfinite(global_max) and global_max > 0:
            self._float_global_scale_max = float(global_max)

    # def _loadSonChunk(self, df):
    #     """
    #     Read pings and apply per-ping gain normalization.
    #     - Assumes gain index is in df['gain'] aligned with loop index i.
    #     - Uses table_value = (gidx - 255) * 137 and unit_scale to convert to physical units.
    #     - For 'dB' mode: undo applied gain by multiplying with 10^(-gain_dB/20).
    #     - For 'linear' mode: subtract the (scaled) offset: dat_corrected = dat - phys_value.
    #     """

    #     # Configurable defaults (set on self if desired)
    #     gain_mode = 'linear'         # 'dB' or 'linear'
    #     unit_scale = 100.0  # divisor to convert table units -> dB or linear units

    #     # Only apply for RSD files (your earlier check)
    #     apply_gain = self.sonFile.lower().endswith(".rsd")
    #     sonDat = np.zeros((int(self.pingMax), len(self.pingCnt)), dtype=np.int32)

    #     with open(self.sonFile, "rb") as file:
    #         for i in range(len(self.headIdx)):
    #             if ~np.isnan(self.headIdx[i]):
    #                 ping_len = min(int(self.pingCnt[i]), int(self.pingMax))
    #                 if not self.son8bit:
    #                     ping_len *= 2

    #                 headIDX = int(self.headIdx[i])
    #                 son_offset = int(self.son_offset[i])
    #                 pingIdx = headIDX + son_offset

    #                 file.seek(pingIdx)
    #                 buffer = file.read(ping_len)

    #                 if self.flip_port:
    #                     buffer = buffer[::-1]

    #                 # Read raw samples: big-endian in file per your original code
    #                 if self.son8bit:
    #                     dat = np.frombuffer(buffer, dtype=">u1").astype(np.float32)
    #                 else:
    #                     # read big-endian uint16, then convert to native-endian float32
    #                     try:
    #                         dat_be = np.frombuffer(buffer, dtype=">u2")
    #                     except Exception:
    #                         dat_be = np.frombuffer(buffer[:-1], dtype=">u2")
    #                     # convert to native-endian 16-bit then to float
    #                     dat = dat_be.astype(np.uint16).astype(np.float32)

    #                 # Apply gain correction if appropriate
    #                 if apply_gain and gain_mode in ("dB", "linear"):
    #                     # read gain index from your df (ensure integer)
    #                     try:
    #                         gidx = int(df.iloc[i]["gain"])
    #                     except Exception:
    #                         gidx = 0
    #                     gidx = max(0, min(255, gidx))

    #                     # table value in raw units
    #                     table_unit_value = (gidx - 255) * 137
    #                     phys_value = table_unit_value / float(unit_scale)

    #                     if gain_mode == "dB":
    #                         # phys_value is gain in dB that was applied when recording.
    #                         # To normalize, undo that gain: multiply by 10^(-gain_dB/20).
    #                         scale = 10.0 ** (-phys_value / 20.0)
    #                         dat_corr = dat * scale
    #                     else:
    #                         # Linear offset case: subtract the stored offset to undo it.
    #                         dat_corr = dat - phys_value
    #                 else:
    #                     dat_corr = dat

    #                 # Clip and store into integer array, keep dynamic range
    #                 # Here we store into sonDat as int32 to avoid overflow during processing.
    #                 n = len(dat_corr)
    #                 sonDat[:n, i] = np.round(dat_corr).astype(np.int32)

    #     # Finalize sonDat dtype choice: keep float-like behavior downstream by using float32,
    #     # or map to uint8/uint16 if your pipeline expects those dtypes.
    #     if self.son8bit:
    #         # clip to 0..255 and save as uint8
    #         self.sonDat = np.clip(sonDat, 0, 255).astype(np.uint8)
    #     else:
    #         # preserve range as uint16 (clip to uint16) if desired
    #         self.sonDat = np.clip(sonDat, 0, 65535).astype(np.uint16)

    #     return



    # ======================================================================
    def _WC_mask(self, i, son=True):
        '''

        '''
        # Get sonMeta
        if not hasattr(self, 'sonMetaDF'):
            self._loadSonMeta()

        if son:
            # self._loadSonMeta()
            self._getScanChunkSingle(i)

        # Filter sonMetaDF by chunk
        isChunk = self.sonMetaDF['chunk_id']==i
        sonMeta = self.sonMetaDF[isChunk].copy().reset_index()
        sonMeta = self._sanitize_chunk_sonmeta(sonMeta)

        # Load depth (in real units) and convert to pixels
        # bedPick = round(sonMeta['dep_m'] / sonMeta['pix_m'], 0).astype(int)
        bedPick = round(sonMeta['dep_m'] / sonMeta['pixM'], 0).astype(int)
        minDep = min(bedPick)

        del sonMeta, self.sonMetaDF

        # Make zero mask
        wc_mask = np.zeros((self.sonDat.shape))

        # Fill non-wc pixels with 1
        for p, s in enumerate(bedPick):
            wc_mask[s:, p] = 1

        self.wcMask = wc_mask
        self.minDep = minDep
        self.bedPick = bedPick

        return



    # ======================================================================
    def _WCR_SRC(self, sonMeta, son=True):
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
        # bedPick = round(sonMeta['dep_m'] / sonMeta['pix_m'], 0).astype(int)
        bedPick = round(sonMeta['dep_m'] / sonMeta['pixM'], 0).astype(int).reset_index(drop=True)

        H, W = self.sonDat.shape[0], self.sonDat.shape[1]

        # Initialize 2d array to store relocated sonar records
        srcDat = np.zeros((H, W), dtype=np.float32)

        # Iterate each ping.  The inner row-loop is replaced with numpy vector
        # ops: compute all slant→horizontal index mappings at once, scatter
        # intensities, then interpolate gaps.
        for j in range(W):
            depth = int(bedPick[j])  # depth at nadir (pixels)
            if depth >= H:
                continue
            dd = float(depth * depth)

            # Rows at or beyond the water column boundary
            row_arr = np.arange(depth, H)
            # Horizontal range index via Pythagorean theorem (vectorised)
            src_idx = np.round(
                np.sqrt(row_arr.astype(np.float32) ** 2 - dd)
            ).astype(int)

            # Discard out-of-bounds indices
            valid = src_idx < H
            rows_v = row_arr[valid]
            sidx_v = src_idx[valid]
            if len(sidx_v) == 0:
                continue

            data_extent = int(sidx_v[-1])

            # Scatter intensities; duplicate src_idx writes keep last value
            pingDat = np.full(H, np.nan, dtype=np.float32)
            pingDat[sidx_v] = self.sonDat[rows_v, j].astype(np.float32)
            pingDat[data_extent:] = 0  # zero past range extent

            # Interpolate across-track gaps introduced by SRC
            nans = np.isnan(pingDat)
            if nans.any():
                x = np.arange(H)
                pingDat[nans] = np.interp(x[nans], x[~nans], pingDat[~nans])

            # Store relocated ping in output array
            if son:
                srcDat[:, j] = np.around(pingDat, 0)
            else:
                srcDat[:, j] = pingDat

        if son:
            self.sonDat = srcDat.astype(int)  # Store in class attribute for later use
        else:
            self.sonDat = srcDat
        del srcDat
        return #self

    # ======================================================================
    def _WCR_crop(self,
                  sonMeta,
                  crop=True):
        # Load depth (in real units) and convert to pixels
        bedPick = round(sonMeta['dep_m'] / sonMeta['pixM'], 0).astype(int)
        minDep = min(bedPick)

        sonDat = self.sonDat
        # Zero out water column
        for j, d in enumerate(bedPick):
            sonDat[:d, j] = 0

        # Crop to min depth
        if crop:
            sonDat = sonDat[minDep:,]

        self.sonDat = sonDat

        return minDep
    
    # ======================================================================
    def _WCO(self,
                  sonMeta):
        # Load depth (in real units) and convert to pixels
        bedPick = round(sonMeta['dep_m'] / sonMeta['pixM'], 0).astype(int)
        maxDep = max(bedPick)

        sonDat = self.sonDat
        # Zero out water column
        for j, d in enumerate(bedPick):
            sonDat[d:, j] = 0

        # Crop to min depth
        sonDat = sonDat[:maxDep,]

        self.sonDat = sonDat

        return maxDep

    # ======================================================================
    def _SHW_mask(self, i, son=True):
        '''

        '''

        # Get sonar data and shadow pix coordinates
        if son:
            self._getScanChunkSingle(i)
        sonDat = self.sonDat
        shw_pix = self.shadow[i]

        # Create a mask and work on that first, then mask sonDat
        mask = np.ones(sonDat.shape)

        for k, val in shw_pix.items():
            for v in val:
                try:
                    mask[v[0]:v[1], k] = 0
                except:
                    pass

        self.shadowMask = mask

        return #self


    # ======================================================================
    def _SHW_crop(self, i, maxCrop=True, croprange=True):
        '''
        maxCrop: True: ping-wise crop; False: crop tile to max range
        '''
        buf=50 # Add buf if maxCrop is false

        # Get sonar data
        sonDat = self.sonDat

        # Get sonar data and shadow pix coordinates
        self._SHW_mask(i)
        mask = self.shadowMask

        # Remove non-contiguous regions
        reg = label(mask)

        # Find region w/ min row value/highest up on sonogram
        highReg = -1
        minRow = mask.shape[0]
        for region in regionprops(reg):
            minr, minc, maxr, maxc = region.bbox

            if (minr < minRow) and (highReg != 0):
                highReg = region.label
                minRow = minr

        # Keep only region matching highReg, update mask with reg
        mask = np.where(reg==highReg, 1, 0)

        # Find max range of valid son returns
        max_r = []
        mask[mask.shape[0]-1, :] = 0 # Zero-out last row

        R = mask.shape[0] # max range
        P = mask.shape[1] # number of pings

        for c in range(P):
            bed = np.where(mask[:,c]==1)[0]
            try:
                bed = np.split(bed, np.where(np.diff(bed) != 1)[0]+1)[-1][-1]
            except:
                bed = np.nan

            max_r.append(bed)

        # Find max range
        max_r = np.nanmax(max_r).astype(int)

        if maxCrop:
            # Keep ping-wise crop (aggressive crop)
            pass
        else:
            # Keep all returns up to max_r
            if (max_r+buf) > mask.shape[0]:
                mask[:max_r,:] = 1
            else:
                mask[:max_r+buf,:] = 1
                max_r += buf

        # Mask shadows on sonDat
        sonDat = sonDat * mask

        # Crop SonDat
        if croprange:
            sonDat = sonDat[:max_r,:]

        self.sonDat = sonDat
        del mask, reg

        return max_r

    # ======================================================================
    def _prepare_export_uint16(self, data):
        cached = getattr(self, 'sonDat16', None)
        if cached is not None:
            try:
                if cached.shape == data.shape:
                    return cached.astype(np.uint16, copy=False)
            except Exception:
                pass

        arr = np.asarray(data)

        if arr.dtype == np.uint16:
            return arr

        if np.issubdtype(arr.dtype, np.floating):
            arr = np.nan_to_num(arr, nan=0.0, posinf=65535.0, neginf=0.0)
            arr[arr < 0] = 0
            max_val = float(np.max(arr)) if arr.size > 0 else 0.0
            if 0 < max_val <= 255.0:
                arr = arr * 257.0
            return np.clip(arr, 0, 65535).astype(np.uint16)

        if arr.dtype == np.uint8:
            return (arr.astype(np.uint16) * 257).astype(np.uint16)

        return np.clip(arr, 0, 65535).astype(np.uint16)

    # ======================================================================
    def _normalize_for_colormap(self, data, bit_depth=8):
        arr = np.asarray(data, dtype=np.float32)
        arr[~np.isfinite(arr)] = 0.0

        valid = arr > 0
        if not np.any(valid):
            return np.zeros(arr.shape, dtype=np.float32)

        vals = arr[valid]
        lo = float(np.nanpercentile(vals, 1.0))
        hi = float(np.nanpercentile(vals, 99.5))

        if (not np.isfinite(lo)) or (not np.isfinite(hi)) or hi <= lo:
            lo = float(np.nanmin(vals))
            hi = float(np.nanmax(vals))

        if (not np.isfinite(lo)) or (not np.isfinite(hi)) or hi <= lo:
            denom = 255.0 if bit_depth <= 8 else 65535.0
            if denom <= 0:
                return np.zeros(arr.shape, dtype=np.float32)
            return np.clip(arr / denom, 0.0, 1.0)

        norm = (arr - lo) / (hi - lo)
        norm = np.clip(norm, 0.0, 1.0)
        return norm.astype(np.float32)

    # ======================================================================
    def _prepare_export_uint16_display(self, data):
        arr = self._prepare_export_uint16(data).astype(np.float32, copy=False)
        norm = self._normalize_for_colormap(arr, bit_depth=16)
        out = np.clip(norm * 65535.0, 0, 65535).astype(np.uint16)
        return out

    def _colorize_array_batched(self, norm_data, valid_mask, cmap_name, scale_max, out_dtype):
        cmap = plt.cm.get_cmap(cmap_name)
        height, width = norm_data.shape
        out = np.zeros((height, width, 3), dtype=out_dtype)

        target_batch_bytes = 256 * 1024 * 1024
        bytes_per_row = max(width * 4 * 8, 1)
        rows_per_batch = max(1, int(target_batch_bytes // bytes_per_row))

        for start in range(0, height, rows_per_batch):
            end = min(start + rows_per_batch, height)
            colored = cmap(norm_data[start:end])
            rgb = np.clip(colored[:, :, :3] * scale_max, 0, scale_max).astype(out_dtype)
            valid = valid_mask[start:end]
            rgb[valid] = np.maximum(rgb[valid], 1)
            out[start:end] = rgb

        return out

    # ======================================================================
    def _colorize_sonar_array(self, data, cmap_name, bit_depth=8, rgb_uint8=False):
        if bit_depth >= 16:
            arr = self._prepare_export_uint16(data)
            norm_data = self._normalize_for_colormap(arr, bit_depth=16)
            if rgb_uint8:
                return self._colorize_array_batched(norm_data, arr > 0, cmap_name, 255.0, np.uint8)
            return self._colorize_array_batched(norm_data, arr > 0, cmap_name, 65535.0, np.uint16)

        arr = np.clip(np.asarray(data), 0, 255).astype(np.uint8)
        norm_data = self._normalize_for_colormap(arr, bit_depth=8)
        return self._colorize_array_batched(norm_data, arr > 0, cmap_name, 255.0, np.uint8)

    # ======================================================================
    def _colorize_pre_normalized_uint16(self, data, cmap_name, rgb_uint8=False):
        arr = self._prepare_export_uint16(data).astype(np.float32, copy=False)
        norm_data = np.clip(arr / 65535.0, 0.0, 1.0)
        if rgb_uint8:
            return self._colorize_array_batched(norm_data, arr > 0, cmap_name, 255.0, np.uint8)
        return self._colorize_array_batched(norm_data, arr > 0, cmap_name, 65535.0, np.uint16)

    # ======================================================================
    def _is_colormap_selected(self, cmap_name):
        if cmap_name is None:
            return False
        name = str(cmap_name).strip().lower()
        return name not in ['', 'none', 'false']

    # ======================================================================
    def _export_colormap_as_uint8(self):
        return bool(getattr(self, 'export_colormap_uint8', True))

    # ======================================================================
    def _reserve_zero_for_nodata(self, data):
        arr = np.asarray(data)

        if arr.size == 0:
            return arr

        out = arr.copy()

        if np.issubdtype(out.dtype, np.floating):
            mask = np.isfinite(out) & (out == 0)
            out[mask] = 1.0
            return out

        if np.issubdtype(out.dtype, np.integer) or np.issubdtype(out.dtype, np.bool_):
            out[out == 0] = 1
            return out

        return out

    # ======================================================================
    def _save_tile_image(self, outfile, data):
        ext = os.path.splitext(outfile)[1].lower()

        if ext in ['.tif', '.tiff']:
            try:
                import tifffile

                if data.ndim == 3 and data.shape[-1] in [3, 4]:
                    tifffile.imwrite(
                        outfile,
                        data,
                        compression='deflate',
                        predictor=True,
                        photometric='rgb',
                    )
                else:
                    tifffile.imwrite(
                        outfile,
                        data,
                        compression='deflate',
                        predictor=True,
                    )
                return
            except Exception:
                pass

        imsave(outfile, data, check_contrast=False)

    # ======================================================================
    def _writeTiles(self,
                    k,
                    imgOutPrefix,
                    tileFile='.jpg',
                    colormap=False):
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
        export_16bit = bool(getattr(self, 'export_16bit', False)) and not bool(getattr(self, 'son8bit', False))
        if export_16bit and str(tileFile).lower() not in ['.tif', '.tiff']:
            tileFile = '.tif'

        if export_16bit:
            data = self._prepare_export_uint16(self.sonDat)
            data = self._reserve_zero_for_nodata(data)
        else:
            data = self.sonDat.astype('uint8') # Get the sonar data
            data = self._reserve_zero_for_nodata(data)

        # File name zero padding
        addZero = self._addZero(k)

        # Prepare output directory if it doesn't exist
        outDir = os.path.join(self.outDir, imgOutPrefix)
        try:
            os.mkdir(outDir)
        except:
            pass

        channel = os.path.split(self.outDir)[-1] #ss_port, ss_star, etc.
        projName = os.path.split(self.projDir)[-1] #to append project name to filename
        self._save_tile_image(os.path.join(outDir, projName+'_'+imgOutPrefix+'_'+channel+'_'+addZero+str(k)+tileFile), data)

        return

    def _writeTilesPlot(self,
                    k,
                    imgOutPrefix,
                    tileFile='.jpg',
                    colormap=False):
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
        export_16bit = bool(getattr(self, 'export_16bit', False)) and not bool(getattr(self, 'son8bit', False))
        colormap_requested = bool(colormap) and self._is_colormap_selected(getattr(self, 'sonogram_colorMap', None))
        if export_16bit and str(tileFile).lower() not in ['.tif', '.tiff']:
            tileFile = '.tif'

        if export_16bit:
            data = self._prepare_export_uint16(self.sonDat)
            data = self._reserve_zero_for_nodata(data)
        else:
            data = self.sonDat.astype('uint8') # Get the sonar data
            data = self._reserve_zero_for_nodata(data)

        # File name zero padding
        addZero = self._addZero(k)

        # Prepare output directory if it doesn't exist
        outDir = os.path.join(self.outDir, imgOutPrefix)
        try:
            os.mkdir(outDir)
        except:
            pass
        
        # Prepare the name
        channel = os.path.split(self.outDir)[-1] #ss_port, ss_star, etc.
        projName = os.path.split(self.projDir)[-1] #to append project name to filename
        base_outfile = os.path.join(outDir, projName+'_'+imgOutPrefix+'_'+channel+'_'+addZero+str(k))
        outfile = base_outfile + tileFile

        # Save as a plot for colormap
        if colormap_requested:
            # plt.imshow(data, cmap=self.sonogram_colorMap)
            # plt.savefig(outfile)

            if export_16bit:
                data = self._colorize_sonar_array(
                    data,
                    self.sonogram_colorMap,
                    bit_depth=16,
                    rgb_uint8=self._export_colormap_as_uint8(),
                )
            else:
                data = self._colorize_sonar_array(data, self.sonogram_colorMap, bit_depth=8)

            # imsave(outfile, data)

        else:
            pass
        
            # imsave(outfile, data, check_contrast=False)

        self._save_tile_image(outfile, data)
            

        return


    ############################################################################
    # Export imagery for labeling                                              #
    ############################################################################

    # ======================================================================
    def _exportTilesSpd(self,
                        chunk,
                        spdCor = False, 
                        mask_shdw = False,
                        maxCrop = False,
                        tileFile='.jpg'):
        '''

        '''
        # Make sonar imagery directory for each beam if it doesn't exist
        try:
            os.mkdir(self.outDir)
        except:
            pass

        if self.wcp:
            # Do speed correction
            export_16bit = bool(getattr(self, 'export_16bit', False)) and not bool(getattr(self, 'son8bit', False))
            self._doSpdCor(chunk, spdCor=spdCor, mask_shdw=mask_shdw, maxCrop=maxCrop, do_egn=self.egn, stretch_wcp=True, integer=not export_16bit)

            if self.sonDat is not np.nan:
                self._writeTilesPlot(chunk, imgOutPrefix='wcp', tileFile=tileFile, colormap=True)
            else:
                pass

        if self.wcm:
            # Do speed correction
            export_16bit = bool(getattr(self, 'export_16bit', False)) and not bool(getattr(self, 'son8bit', False))
            self._doSpdCor(chunk, spdCor=spdCor, mask_shdw=mask_shdw, mask_wc=True, maxCrop=maxCrop, do_egn=self.egn, stretch_wcp=True, integer=not export_16bit)

            if self.sonDat is not np.nan:
                self._writeTilesPlot(chunk, imgOutPrefix='wcm', tileFile=tileFile, colormap=True)
            else:
                pass

        if self.wcr_src:
            # Do speed correction
            export_16bit = bool(getattr(self, 'export_16bit', False)) and not bool(getattr(self, 'son8bit', False))
            self._doSpdCor(chunk, spdCor=spdCor, mask_shdw=mask_shdw, src=True, maxCrop=maxCrop, do_egn=self.egn, stretch_wcp=True, integer=not export_16bit)

            if self.sonDat is not np.nan:
                self._writeTilesPlot(chunk, imgOutPrefix='src', tileFile=tileFile, colormap=True)
            else:
                pass

        if self.wco:
            # Do speed correction
            export_16bit = bool(getattr(self, 'export_16bit', False)) and not bool(getattr(self, 'son8bit', False))
            self._doSpdCor(chunk, spdCor=spdCor, mask_bed=True, maxCrop=maxCrop, do_egn=self.egn, stretch_wcp=True, integer=not export_16bit)

            if self.sonDat is not np.nan:
                self._writeTilesPlot(chunk, imgOutPrefix='wco', tileFile=tileFile, colormap=True)
            else:
                pass

        gc.collect()
        return


    # ======================================================================
    def _doSpdCor(self, 
                  chunk, 
                  spdCor=False,
                  mask_shdw=False, 
                  src=False,
                  mask_wc=False,
                  mask_bed=False,
                  maxCrop=0, 
                  son=True, 
                  integer=True, 
                  do_egn=False, 
                  stretch_wcp=False):

        if not hasattr(self, 'sonMetaDF'):
            self._loadSonMeta()

        # Filter sonMetaDF by chunk
        isChunk = self.sonMetaDF['chunk_id']==chunk
        sonMeta = self.sonMetaDF[isChunk].copy().reset_index()
        sonMeta = self._sanitize_chunk_sonmeta(sonMeta)

        # Update class attributes based on current chunk
        self.pingMax = np.nanmax(sonMeta['ping_cnt']) # store to determine max range per chunk

        if ~np.isnan(self.pingMax):
            # Load chunk's sonar data into memory
            if son:
                # self._loadSonChunk()
                self._getScanChunkSingle(chunk)

            export_16bit = bool(getattr(self, 'export_16bit', False)) and not bool(getattr(self, 'son8bit', False))
            if export_16bit and getattr(self, 'sonDat16', None) is not None:
                self.sonDat = self.sonDat16.astype(np.float32, copy=False)

            # egn
            if do_egn:

                self._egn_wcp(chunk, sonMeta, do_rescale=True)
                self._egnDoStretch(stretch_wcp=stretch_wcp)

            # Remove shadows and crop
            # if self.remShadow and (lbl_set==2):
            if (self.remShadow and mask_shdw) or (self.remShadow and maxCrop):
                self._SHW_crop(chunk, maxCrop=mask_shdw, croprange=maxCrop)
            sonDat = self.sonDat

            if src:
                # slant range correction
                self._WCR_SRC(sonMeta)

            # Remove water column and crop
            if mask_wc:
                _ = self._WCR_crop(sonMeta, crop=maxCrop)

            if mask_bed:
                _ = self._WCO(sonMeta)

            sonDat = self.sonDat

            if spdCor == 0:
                # Don't do speed correction
                pass
            elif spdCor == 1:

                # Distance (in meters)
                d = sonMeta['trk_dist'].to_numpy()
                # d = np.max(d) - np.min(d)
                d = d[-1] - d[0]

                

                pixM = sonMeta['pixM']
                # Find most common pixel size
                if len(pixM.unique()) > 1:
                    pixM = pixM.mode()[0]
                else:
                    pixM = pixM.iloc[0]

                # Distance in pix
                d = round(d / pixM, 0).astype(int)

                # to avoid oom errors
                rows = sonDat.shape[0]
                new_cols = d  # your target width
                item_size = sonDat.itemsize  # bytes per element

                estimated_bytes = rows * new_cols * item_size
                estimated_MB = estimated_bytes / 1e6

                available_bytes = psutil.virtual_memory().available
                available_MB = available_bytes / 1e6


                mem_margin = 0.9
                safe_limit_MB = available_MB * (1 - mem_margin)

                if d > 0 and estimated_MB < safe_limit_MB and new_cols<65500:
                    sonDat = resize(
                        sonDat,
                        (rows, new_cols),
                        mode='reflect',
                        clip=True,
                        preserve_range=True
                    )
                if estimated_MB > safe_limit_MB:
                    print(f"Resize skipped for chunk {chunk}: estimated {estimated_MB:.2f} MB exceeds safe limit of {safe_limit_MB:.2f} MB.")
                    # Optionally: fallback to chunked resize or downsampling
                elif new_cols>65500:
                    print(f"Resize skipped for chunk {chunk}: Maximum supported image dimension is 65500 pixels.")
                elif d == 0:
                    print(f"Resize skipped for chunk {chunk}: Vessel did not move.")
                else:
                    pass

            else:
                sonDat = resize(sonDat,
                                (sonDat.shape[0], sonDat.shape[1]*spdCor),
                                mode='reflect',
                                clip=False, preserve_range=True)#.astype('uint8')

            if integer:
                self.sonDat = sonDat.astype('uint8')
            else:
                self.sonDat = sonDat

        else:
            self.sonDat = np.nan

        return


    
    ############################################################################
    # Miscellaneous                                                            #
    ############################################################################

    # ======================================================================
    def _getScanChunkSingle(self,
                            chunk,
                            cog=True,
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
        if cog:
            isChunk = sonMetaAll['chunk_id']==chunk
        else:
            isChunk = sonMetaAll['chunk_id_2']==chunk
            isChunk.iloc[chunk+1] = True
        sonMeta = sonMetaAll[isChunk].reset_index()
        sonMeta = self._sanitize_chunk_sonmeta(sonMeta)

        # Update class attributes based on current chunk
        rangeCnt = np.unique(sonMeta['ping_cnt'], return_counts=True)
        pingMaxi = np.argmax(rangeCnt[1])
        self.pingMax = int(rangeCnt[0][pingMaxi])

        self.headIdx = sonMeta['index']#.astype(int) # store byte offset per ping
        self.son_offset = sonMeta['son_offset']
        self.pingCnt = sonMeta['ping_cnt']#.astype(int) # store ping count per ping
        if 'bytes_per_sample' in sonMeta.columns:
            self.bytesPerSample = sonMeta['bytes_per_sample']
        elif hasattr(self, 'bytesPerSample'):
            del self.bytesPerSample

        if 'pixM' in sonMeta.columns:
            chunk_pix_m = pd.to_numeric(sonMeta['pixM'], errors='coerce').to_numpy(dtype=float)
            if np.any(np.isfinite(chunk_pix_m)):
                self._chunk_pixM = float(np.nanmedian(chunk_pix_m[np.isfinite(chunk_pix_m)]))
            elif hasattr(self, '_chunk_pixM'):
                del self._chunk_pixM
        elif hasattr(self, '_chunk_pixM'):
            del self._chunk_pixM

        if bool(getattr(self, 'range_crop_after_flip', False)):
            self._range_crop_samples_after_flip = None
            crop_range_m = float(getattr(self, 'cropRange', 0.0))
            pix_m = getattr(self, '_chunk_pixM', np.nan)
            if crop_range_m > 0 and np.isfinite(pix_m) and pix_m > 0:
                crop_samples = int(round(crop_range_m / pix_m, 0))
                if crop_samples > 0:
                    self._range_crop_samples_after_flip = crop_samples
        elif hasattr(self, '_range_crop_samples_after_flip'):
            del self._range_crop_samples_after_flip

        self._use_jsf_weighting = False
        if 'weighting_factor' in sonMeta.columns:
            self.weightingFactor = pd.to_numeric(sonMeta['weighting_factor'], errors='coerce').to_numpy(dtype=float)
            self._use_jsf_weighting = True
            self._ensure_jsf_global_scale_max(sonMetaAll)

        # Load chunk's sonar data into memory
        self._loadSonChunk()
        # Do PPDRC filter
        if filterIntensity:
            self._doPPDRC()
        # Remove water if exporting wcr imagery
        if remWater:
            self._WCR(sonMeta)     

        del self.headIdx, self.pingCnt
        if hasattr(self, 'bytesPerSample'):
            del self.bytesPerSample
        if hasattr(self, 'weightingFactor'):
            del self.weightingFactor
        self._use_jsf_weighting = False

        return
    
    def _getScanSlice(self, transect, start_idx, end_idx, remWater = False):
        '''
        
        '''

        # Open sonar metadata file to df
        sonMetaAll = pd.read_csv(self.sonMetaFile)
        sonMetaAll_full = sonMetaAll

        # Filter by transect
        sonMetaAll = sonMetaAll[sonMetaAll['transect'] == transect].reset_index(drop=True)
        
        # Filter sonMeta
        # sonMeta = sonMeta[(sonMeta['index'] >= start_idx) & (sonMeta['index'] <= end_idx)]
        sonMeta = sonMeta.iloc[start_idx:end_idx]
        sonMeta = sonMeta.reset_index()
        sonMeta = self._sanitize_chunk_sonmeta(sonMeta)

        # Update class attributes based on current chunk
        rangeCnt = np.unique(sonMeta['ping_cnt'], return_counts=True)
        pingMaxi = np.argmax(rangeCnt[1])
        self.pingMax = int(rangeCnt[0][pingMaxi])

        self.headIdx = sonMeta['index']#.astype(int) # store byte offset per ping
        self.son_offset = sonMeta['son_offset']
        self.pingCnt = sonMeta['ping_cnt']#.astype(int) # store ping count per ping
        if 'bytes_per_sample' in sonMeta.columns:
            self.bytesPerSample = sonMeta['bytes_per_sample']
        elif hasattr(self, 'bytesPerSample'):
            del self.bytesPerSample

        if 'pixM' in sonMeta.columns:
            chunk_pix_m = pd.to_numeric(sonMeta['pixM'], errors='coerce').to_numpy(dtype=float)
            if np.any(np.isfinite(chunk_pix_m)):
                self._chunk_pixM = float(np.nanmedian(chunk_pix_m[np.isfinite(chunk_pix_m)]))
            elif hasattr(self, '_chunk_pixM'):
                del self._chunk_pixM
        elif hasattr(self, '_chunk_pixM'):
            del self._chunk_pixM

        self._use_jsf_weighting = False
        if 'weighting_factor' in sonMeta.columns:
            self.weightingFactor = pd.to_numeric(sonMeta['weighting_factor'], errors='coerce').to_numpy(dtype=float)
            self._use_jsf_weighting = True
            self._ensure_jsf_global_scale_max(sonMetaAll_full)

        # Load chunk's sonar data into memory
        self._loadSonChunk()

        # Remove water if exporting wcr imagery
        if remWater:
            self._WCR(sonMeta)     

        del self.headIdx, self.pingCnt
        if hasattr(self, 'bytesPerSample'):
            del self.bytesPerSample
        if hasattr(self, 'weightingFactor'):
            del self.weightingFactor
        self._use_jsf_weighting = False

        return

    # ======================================================================
    def _loadSonMeta(self):
        '''
        Load sonar metadata from csv to pandas df
        '''
        meta = pd.read_csv(self.sonMetaFile)
        self.sonMetaDF = meta
        return

    # ======================================================================
    def _getChunkID(self):
        '''
        Utility to load unique chunk ID's from son obj and return in a list
        '''

        # Load son metadata csv to df
        self._loadSonMeta()

        df = self.sonMetaDF

        if 'filter' in df.columns:
            # Remove filtered pings
            df = df[df['filter'] == True]

        # Get unique chunk id's
        df = df.groupby(['chunk_id', 'index']).size().reset_index().rename(columns={0:'count'})
        chunks = pd.unique(df['chunk_id']).astype(int)

        del self.sonMetaDF, df
        return chunks
    
    # ======================================================================
    def _getChunkID_Update(self):
        '''
        Utility to load unique chunk ID's from son obj and return in a list
        '''

        # Load son metadata csv to df
        self._loadSonMeta()

        # # Get unique chunk id's
        # df = self.sonMetaDF.groupby(['chunk_id', 'index']).size().reset_index().rename(columns={0:'count'})
        # chunks = pd.unique(df['chunk_id']).astype(int)

        # Use index as chunk id
        df = self.sonMetaDF
        chunks = df.index.values.astype(int)

        df['chunk_id_2'] = chunks
        self._saveSonMetaCSV(df)

        del self.sonMetaDF, df
        return chunks

    # ======================================================================
    def _addZero(self, chunk):
        # Determine leading zeros to match naming convention
        if chunk < 10:
            addZero = '0000'
        elif chunk < 100:
            addZero = '000'
        elif chunk < 1000:
            addZero = '00'
        elif chunk < 10000:
            addZero = '0'
        else:
            addZero = ''

        return addZero


    # ======================================================================
    def _cleanup(self):

        try:
            del self.sonMetaDF
        except:
            pass

        try:
            del self.sonDat
        except:
            pass

        # Delete temp files
        t = glob(os.path.join(self.projDir, '*', '*temp*'), recursive=True)
        for f in t:
            try:
                os.remove(f)
            except:
                pass

    # ======================================================================
    def _pickleSon(self):
        '''
        Pickle sonObj so we can reload later if needed.
        '''
        if not hasattr(self, 'sonMetaPickle'):
            outFile = self.sonMetaFile.replace(".csv", ".meta")
            self.sonMetaPickle = outFile
        else:
            outFile = self.sonMetaPickle

        with open(outFile, 'wb') as sonFile:
            pickle.dump(self, sonFile)

        return


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
    def _egnCalcChunkMeans(self, chunk):
        '''

        '''

        # Filter sonMetaDF by chunk
        isChunk = self.sonMetaDF['chunk_id']==chunk
        sonMeta = self.sonMetaDF[isChunk].copy().reset_index()
        sonMeta = self._sanitize_chunk_sonmeta(sonMeta)

        # Update class attributes based on current chunk
        self.pingMax = np.nanmax(sonMeta['ping_cnt']) # store to determine max range per chunk
        self.headIdx = sonMeta['index'] # store byte offset per ping
        self.pingCnt = sonMeta['ping_cnt'] # store ping count per ping

        ############
        # load sonar
        # self._loadSonChunk()
        self._getScanChunkSingle(chunk)

        #####################################
        # Get wc avg (for wcp egn) before src
        self._WC_mask(chunk, son=False) # Son false because sonDat already loaded
        bedMask = 1-self.wcMask # Invert zeros and ones
        wc = self.sonDat*bedMask # Mask bed pixels
        wc[wc == 0] = np.nan # Set zeros to nan
        mean_intensity_wc = np.nanmean(wc, axis=1) # get one avg for wc
        del bedMask, wc, self.wcMask

        ################
        # remove shadows
        if self.remShadow:
            # Get mask
            self._SHW_mask(chunk)

            # Mask out shadows
            self.sonDat = self.sonDat*self.shadowMask
            del self.shadowMask

        ########################
        # slant range correction
        self._WCR_SRC(sonMeta)

        # Set zeros to nans (????)
        self.sonDat = self.sonDat.astype('float')
        self.sonDat[self.sonDat == 0] = np.nan

        #####
        # WCR
        #####

        ##############################
        # Calculate range-wise average
        mean_intensity_wcr = np.nanmean(self.sonDat, axis=1)

        del self.sonDat
        gc.collect()
        return mean_intensity_wcr, mean_intensity_wc

    # ======================================================================
    def _egnCalcGlobalMeans(self, chunk_means):
        '''
        Calculate weighted average of chunk_means
        '''

        #####################
        # Find largest vector
        lv = 0
        for c in chunk_means:
            if c[0].shape[0] > lv:
                lv = c[0].shape[0]

        ########################
        # Stack vectors in array

        # Create nan array
        wc_means = np.empty((lv, len(chunk_means)))
        wc_means[:] = np.nan
        
        bed_means = np.empty((lv, len(chunk_means)))
        bed_means[:] = np.nan
        
        # Stack arrays
        for i, m in enumerate(chunk_means):
            ## Bed means
            bed_means[:m[0].shape[0], i] = m[0]
        
            ## WC means
            wc_means[:m[1].shape[0], i] = m[1]

        del chunk_means

        ################
        # Calculate mean
        self.egn_bed_means = np.nanmean(bed_means, axis=1)
        self.egn_wc_means = np.nanmean(wc_means, axis=1)
        del bed_means, wc_means

        gc.collect()
        return

    # ======================================================================
    def _egnCalcHist(self, chunk):
        '''
        Calculate EGN statistics
        '''
        if not hasattr(self, "sonMetaDF"):
            self._loadSonMeta()

        # Filter sonMetaDF by chunk
        isChunk = self.sonMetaDF['chunk_id']==chunk
        sonMeta = self.sonMetaDF[isChunk].copy().reset_index()
        sonMeta = self._sanitize_chunk_sonmeta(sonMeta)

        # Update class attributes based on current chunk
        self.pingMax = np.nanmax(sonMeta['ping_cnt']) # store to determine max range per chunk
        self.headIdx = sonMeta['index'] # store byte offset per ping
        self.pingCnt = sonMeta['ping_cnt'] # store ping count per ping

        ############
        # load sonar
        # self._loadSonChunk()
        self._getScanChunkSingle(chunk)


        ################
        # remove shadows
        if self.remShadow:
            # Get mask
            self._SHW_mask(chunk)

            # Mask out shadows
            self.sonDat = self.sonDat*self.shadowMask
            del self.shadowMask

        ########
        # Do EGN
        nonEGNSonDat = self.sonDat.copy()
        self._egn_wcp(chunk, sonMeta, do_rescale=True)
        
        
        ######################
        # Calculate histograms
        
        # Histgram with water column present
        wcp_hist, _ = np.histogram(self.sonDat, bins=255, range=(0,255))

        ########
        # Do EGN
        self.sonDat = nonEGNSonDat
        self._egn()

        ######################
        # Calculate histograms

        # Histogram with water column removed
        self._WCR_SRC(sonMeta)
        wcr_hist, _ = np.histogram(self.sonDat, bins=255, range=(0,255))


        del self.sonDat, nonEGNSonDat

        return wcp_hist, wcr_hist
        # return wcr_hist

    # ======================================================================
    def _egnCalcGlobalHist(self, hist):
        '''
        '''

        # Zero arrays to store sum of histograms
        wcp_hist = np.zeros((hist[0][0].shape))
        wcr_hist = np.zeros((hist[0][0].shape))

        for (wcp, wcr) in hist:
            wcp_hist += wcp
            wcr_hist += wcr

        del hist

        self.egn_wcp_hist = wcp_hist
        self.egn_wcr_hist = wcr_hist

        return

    # ======================================================================
    def _egnCalcMinMax(self, chunk):
        '''
        Calculate local min and max values after applying EGN
        '''
        # Get sonMetaDF
        if not hasattr(self, 'sonMetaDF'):
            self._loadSonMeta()

        # Filter sonMetaDF by chunk
        isChunk = self.sonMetaDF['chunk_id']==chunk
        sonMeta = self.sonMetaDF[isChunk].copy().reset_index()
        sonMeta = self._sanitize_chunk_sonmeta(sonMeta)

        # Update class attributes based on current chunk
        self.pingMax = np.nanmax(sonMeta['ping_cnt']) # store to determine max range per chunk
        self.headIdx = sonMeta['index'] # store byte offset per ping
        self.pingCnt = sonMeta['ping_cnt'] # store ping count per ping

        ############
        # load sonar
        # self._loadSonChunk()
        self._getScanChunkSingle(chunk)

        ################
        # remove shadows
        if self.remShadow:
            # Get mask
            self._SHW_mask(chunk)

            # Mask out shadows
            self.sonDat = self.sonDat*self.shadowMask
            del self.shadowMask

        #############
        # Do wc stats

        # Get wc pixels
        self._WC_mask(chunk, son=False) # Son false because sonDat already loaded
        bedMask = 1-self.wcMask # Invert zeros and ones
        wc = self.sonDat*bedMask # Mask bed pixels
        wc[wc == 0] = np.nan # Set zeros to nan
        
        # Get copy of sonDat so we can calculate egn on wc pixels
        sonDat = self.sonDat.copy()
        self.sonDat = wc
        
        # Do EGN
        self._egn(wc=True, do_rescale=False)

        # Calculate min and max
        wc_min = np.nanmin(self.sonDat)
        wc_max = np.nanmax(self.sonDat)

        ##############
        # Do bed stats

        # Store sonDat
        self.sonDat = sonDat

        ########################
        # slant range correction
        self._WCR_SRC(sonMeta)

        ########
        # Do EGN
        self._egn(do_rescale=False)

        ###################
        # Calculate min/max
        min = np.nanmin(self.sonDat)
        max = np.nanmax(self.sonDat)

        del self.sonDat

        return (min, max), (wc_min, wc_max)

    # ======================================================================
    def _egnCalcGlobalMinMax(self, min_max):
        '''
        '''

        bed_mins = []
        bed_maxs = []
        wc_mins = []
        wc_maxs = []
        for ((b_min, b_max), (w_min, w_max)) in min_max:
            bed_mins.append(b_min)
            bed_maxs.append(b_max)
        
            wc_mins.append(w_min)
            wc_maxs.append(w_max)

        self.egn_bed_min = np.nanmin(bed_mins)
        self.egn_bed_max = np.nanmax(bed_maxs)

        self.egn_wc_min = np.nanmin(wc_mins)
        self.egn_wc_max = np.nanmax(wc_maxs)

        return

    # ======================================================================
    def _egn(self, wc = False, do_rescale=True):
        '''
        Apply empirical gain normalization to sonDat
        '''

        # Get sonar data
        sonDat = self.sonDat

        # Get egn means
        if wc:
            egn_means = self.egn_wc_means.copy() # Don't want to overwrite
        else:
            egn_means = self.egn_bed_means.copy() # Don't want to overwrite

        # Slice egn means if too long
        egn_means = egn_means[:sonDat.shape[0]]

        # Take last value of egn means and add to end if not long enough
        if sonDat.shape[0] > egn_means.shape[0]:
            t = np.ones((sonDat.shape[0]))
            l = egn_means[-1] # last value
            t[:egn_means.shape[0]] = egn_means
            t[egn_means.shape[0]:] = l # insert last value
            egn_means = t
            del t

        # Divide each ping by mean vector
        sonDat = sonDat / egn_means[:, None]

        if do_rescale:
            # Rescale by global min and max
            if wc:
                m = self.egn_wc_min
                M = self.egn_wc_max
            else:
                m = self.egn_bed_min
                M = self.egn_bed_max

            mn = 0
            mx = 255
            sonDat = (mx-mn)*(sonDat-m)/(M-m)+mn

        self.sonDat = sonDat
        del sonDat, egn_means
        return

    # ======================================================================
    def _egn_wcp_OLD(self, chunk, sonMeta, do_rescale=True):
        '''
        Apply empirical gain normalization to sonDat
        '''

        # Get sonar data
        sonDat = self.sonDat.astype(np.float32).copy()

        # Get water column mask
        self._WC_mask(chunk, son=False) # So we don't reload sonDat
        wcMask = 1-self.wcMask # Get the mask, invert zeros and ones
        del self.sonDat

        # Get water column, mask bed
        wc = sonDat * wcMask

        # Apply egn to wc
        self.sonDat = wc
        self._egn(wc=True, do_rescale=False)
        wc = self.sonDat.copy()
        wc = np.nan_to_num(wc, nan=0) # replace nans with zero
        del self.sonDat

        # Get egn_means
        egn_means = self.egn_bed_means.copy() # Don't want to overwrite

        # Get bedpicks, in pixel units
        bedPick = round(sonMeta['dep_m'] / sonMeta['pixM'], 0).astype(int).to_numpy()

        # Iterate each ping
        for j in range(sonDat.shape[1]):
            depth = bedPick[j] # Get bedpick
            # Create 1d array to store relocated egn avgs for given ping.
            egn_p = (np.zeros((sonDat.shape[0])).astype(np.float32))

            # Iterate over each avg
            for i in range(sonDat.shape[0]):
                # Set wc avgs to 1 (unchanged)
                if i < depth:
                    egn_p[i] = 1

                else:
                    # Get egn_means index (range) for given slant range (i)
                    avgIndex = round(np.sqrt(i**2 - depth**2),0).astype(int)
                    r_avg = egn_means[avgIndex] # Get egn_mean value
                    egn_p[i] = r_avg # Store range avg at appropriate slant range

            sonDat[:,j] = sonDat[:,j] / egn_p

        # Mask water column in sonDat
        # wcMask = 1-wcMask
        sonDat = sonDat * self.wcMask
        sonDat = np.nan_to_num(sonDat, nan=0) # replace nans with zero

        # Add water column pixels back in
        sonDat = sonDat + wc

        if do_rescale:
            # Rescale by global min and max
            m = min(self.egn_wc_min, self.egn_bed_min)
            M = max(self.egn_wc_max, self.egn_bed_max)
            mn = 0
            mx = 255
            sonDat = (mx-mn)*(sonDat-m)/(M-m)+mn

        sonDat = np.where(sonDat < mn, mn, sonDat)
        sonDat = np.where(sonDat > mx, mx, sonDat)

        self.sonDat = sonDat.astype('uint8')
        return

    # ======================================================================
    def _egn_wcp(self, chunk, sonMeta, do_rescale=True):
        '''
        Apply empirical gain normalization to sonDat
        '''

        # Get sonar data
        sonDat = self.sonDat.astype(np.float32).copy()

        # Get egn_bed_means
        egn_means = self.egn_bed_means.copy() # Don't want to overwrite

        # Get egn_wc_means
        egn_wc_means = self.egn_wc_means.copy()

        # Take last value of egn means and add to end if not long enough
        if sonDat.shape[0] > egn_means.shape[0]:
            t = np.ones((sonDat.shape[0]))
            l = egn_means[-1] # last value
            t[:egn_means.shape[0]] = egn_means
            t[egn_means.shape[0]:] = l # insert last value
            egn_means = t
            del t, l

        # Get bedpicks, in pixel units
        bedPick = round(sonMeta['dep_m'] / sonMeta['pixM'], 0).astype(int).to_numpy()

        # Iterate each ping
        for j in range(sonDat.shape[1]):
            depth = bedPick[j] # Get bedpick
            dd = depth**2

            # Create 1d array to store relocated egn avgs for given ping.
            egn_p = (np.zeros((sonDat.shape[0])).astype(np.float32))

            # Iterate over each avg
            for i in range(sonDat.shape[0]):
                # Set wc avgs to 1 (unchanged)
                if i < depth:
                    # egn_p[i] = 1 # Original crappy method


                    # Using the WC means is the 'correct' way to normalize the wc
                    # but it ends up being brighter and 'noisier' which may be good
                    # for looking at suspended sediments, but using the bed means
                    # helps to eliminate the noise
                    denoiseWC = True # Could be added as param in future

                    if denoiseWC:
                        egn_p[i] = egn_means[i] # Use bed means
                    else:
                        egn_p[i] = egn_wc_means[i] # Use wc means

                # Relocate egn mean based on slant range
                else:
                    # Get egn_means index (range) for given slant range (i)
                    avgIndex = int(round(math.sqrt(i**2 - dd),0))
                    r_avg = egn_means[avgIndex] # Get egn_mean value
                    egn_p[i] = r_avg # Store range avg at appropriate slant range
                    del avgIndex, r_avg

            # Apply correction to ping
            sonDat[:,j] = sonDat[:,j] / egn_p

            del egn_p

        mn = 0
        mx = 255

        if do_rescale:
            # Rescale by global min and max

            m = min(self.egn_wc_min, self.egn_bed_min)
            M = max(self.egn_wc_max, self.egn_bed_max)

            sonDat = (mx-mn)*(sonDat-m)/(M-m)+mn

        # Set values below/above 0/255 to 0/255
        sonDat = np.where(sonDat < mn, mn, sonDat)
        sonDat = np.where(sonDat > mx, mx, sonDat)

        self.sonDat = sonDat.astype('uint8')
        del sonDat
        return


    # ======================================================================
    def _egnCalcStretch(self, egn_stretch, egn_stretch_factor):
        '''
        '''
        # Store variables
        self.egn_stretch = egn_stretch
        self.egn_stretch_factor = egn_stretch_factor

        # Get histogram percentages
        wcp_pcnt = self.egn_wcp_hist_pcnt
        wcr_pcnt = self.egn_wcr_hist_pcnt

        if egn_stretch == 1:

            # Find Globabl mins and max
            histIndex = np.where(wcr_pcnt[1:]>0)[0]
            self.egn_wcr_stretch_min = histIndex[0]
            self.egn_wcr_stretch_max = histIndex[-1]

            histIndex = np.where(wcp_pcnt[1:]>0)[0]
            self.egn_wcp_stretch_min = histIndex[0]
            self.egn_wcp_stretch_max = histIndex[-1]


        elif egn_stretch == 2:
            # Percent clip
            egn_stretch_factor = egn_stretch_factor / 100

            #####
            # WCP
            
            # Left tail
            m = 1 # Store pixel value (Don't count 0)
            mp = 0 # Store percentage
            v = wcp_pcnt[m]
            while (mp+v) < egn_stretch_factor:
            # while ((mp+v) < egn_stretch_factor) and (m < 255):
                m += 1
                mp += v
                # v = wcp_pcnt[m]
                try:
                    v = wcp_pcnt[m]
                except:
                    v = 0
                    break
            
            self.egn_wcp_stretch_min = m
            del m, mp, v
            
            # Right tail
            m = 254
            mp = 0
            v = wcp_pcnt[m]
            while (mp+v) < egn_stretch_factor:
            # while ((mp+v) < egn_stretch_factor) and (m >= 0):
                m -= 1
                mp += v
                # v = wcp_pcnt[m]
                try:
                    v = wcp_pcnt[m]
                except:
                    v = 0
                    break
            
            
            self.egn_wcp_stretch_max = m
            del m, mp, v

            #####
            # WCR

            # Left tail
            m = 1 # Store pixel value (Don't count 0)
            mp = 0 # Store percentage
            v = wcr_pcnt[m]
            while (mp+v) < egn_stretch_factor:
            # while ((mp+v) < egn_stretch_factor) and (m < 255):
                m += 1
                mp += v
                # v = wcp_pcnt[m]
                try:
                    v = wcr_pcnt[m]
                except:
                    v = 0
                    break

            self.egn_wcr_stretch_min = m
            del m, mp, v

            # Right tail
            m = 254
            mp = 0
            v = wcr_pcnt[m]
            while (mp+v) < egn_stretch_factor:
            # while ((mp+v) < egn_stretch_factor) and (m >= 0):
                m -= 1
                mp += v
                # v = wcp_pcnt[m]
                try:
                    v = wcr_pcnt[m]
                except:
                    v = 0
                    break

            self.egn_wcr_stretch_max = m
            del m, mp, v

        return (self.egn_wcp_stretch_min, self.egn_wcp_stretch_max), (self.egn_wcr_stretch_min, self.egn_wcr_stretch_max)


    # ======================================================================
    def _egnDoStretch(self, stretch_wcp=False):
        '''
        '''

        # Get sonDat
        sonDat = self.sonDat.astype('float32')

        # Create mask from zero values
        mask = np.where(sonDat == 0, 0, 1)

        # Get stretch min max
        if stretch_wcp:
            m = self.egn_wcp_stretch_min
            M = self.egn_wcp_stretch_max
        else:
            m = self.egn_wcr_stretch_min
            M = self.egn_wcr_stretch_max

        mn = 0
        mx = 255

        sonDat = np.clip(sonDat, m, M)

        sonDat = (mx-mn)*(sonDat-m)/(M-m)+mn

        # Optional tone adjustment to brighten/darken mid-tones after EGN stretch.
        sonDat = self._applyEGNTone(sonDat)

        # Try masking out zeros
        sonDat = sonDat*mask
        del mask

        self.sonDat = sonDat.astype('uint8')
        del sonDat
        return


    # ======================================================================
    def _applyEGNTone(self, sonDat):
        '''
        Apply optional post-EGN tone controls.

        Notes
        -----
        - tone_gamma < 1.0 brightens mid-tones; > 1.0 darkens.
        - tone_gain > 1.0 boosts overall brightness; < 1.0 reduces.
        '''
        gamma = getattr(self, 'tone_gamma', 1.0)
        gain = getattr(self, 'tone_gain', 1.0)

        try:
            gamma = float(gamma)
            gain = float(gain)
        except Exception:
            gamma = 1.0
            gain = 1.0

        if gamma <= 0:
            gamma = 1.0
        if gain < 0:
            gain = 0.0

        # Preserve legacy behavior when defaults are used.
        if gamma == 1.0 and gain == 1.0:
            return sonDat

        sonNorm = np.clip(sonDat, 0, 255) / 255.0
        sonNorm = np.power(sonNorm, gamma) * gain
        return np.clip(sonNorm * 255.0, 0, 255)