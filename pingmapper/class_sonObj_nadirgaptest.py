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
                          dq_table=False,
                          dq_time_field=False,
                          dq_flag_field=False,
                          dq_keep_values=False,
                          dq_src_utc_offset=0.0,
                          dq_target_utc_offset=0.0,
                          dq_time_offset=0.0,
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

        ####################
        # Data Quality Filter
        if dq_table:
            sonDF = self._filterDQ(
                sonDF,
                dq_table,
                dq_time_field,
                dq_flag_field,
                dq_keep_values,
                dq_src_utc_offset,
                dq_target_utc_offset,
                dq_time_offset,
            )

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
    def _filterDQ(self,
                  sonDF,
                  dq_table,
                  dq_time_field,
                  dq_flag_field,
                  dq_keep_values,
                  dq_src_utc_offset,
                  dq_target_utc_offset,
                  dq_time_offset,
                  ):
        '''
        Filter sonar pings using a data-quality (DQ) log CSV.

        Each row in the DQ log is treated as a state-change event: the flag
        recorded at time T applies to every sonar ping from T until the next
        event row. Pings that occur before the first DQ event are removed.
        '''

        filtDQCol = 'filter_dq'
        filtCol = 'filter'
        dqTimeCol = '_dq_ts'

        if not dq_time_field:
            raise ValueError('dq_time_field is required when dq_table is provided.')
        if not dq_flag_field:
            raise ValueError('dq_flag_field is required when dq_table is provided.')

        keep_vals = self._normalizeDQKeepValues(dq_keep_values)
        if len(keep_vals) == 0:
            raise ValueError('dq_keep_values must contain at least one value to keep.')

        sonDF = sonDF.copy()
        sonDF[filtDQCol] = False

        if filtCol not in sonDF.columns:
            sonDF[filtCol] = True

        dqDF = pd.read_csv(dq_table)
        missing_cols = [c for c in [dq_time_field, dq_flag_field] if c not in dqDF.columns]
        if missing_cols:
            raise ValueError('dqLog missing required column(s): {}'.format(', '.join(missing_cols)))

        dqTimes, dqKind = self._coerceDQTimestampSeries(dqDF[dq_time_field], dq_time_field)
        sonTimes, sonKind = self._getSonarFilterTimestamp(sonDF)

        if dqKind != sonKind:
            raise ValueError(
                'dqLog timestamp type ({}) does not match sonar timestamp type ({}).'.format(dqKind, sonKind)
            )

        if dqKind == 'datetime':
            dqTimes = self._shiftDQDatetimeToTargetOffset(
                dqTimes,
                dq_src_utc_offset,
                dq_target_utc_offset,
            )

        dqDF = dqDF.copy()
        dqDF[dqTimeCol] = dqTimes
        dqDF = dqDF[dqDF[dqTimeCol].notna()].copy()
        if dqDF.empty:
            raise ValueError('dqLog contained no valid timestamps after parsing {}.'.format(dq_time_field))

        offset = float(dq_time_offset)
        if sonKind == 'datetime':
            sonTimes = sonTimes + pd.to_timedelta(offset, unit='s')
        else:
            sonTimes = sonTimes + offset

        sonMerge = pd.DataFrame({
            '_son_idx': sonDF.index,
            '_son_ts': sonTimes,
        })
        sonMerge = sonMerge[sonMerge['_son_ts'].notna()].copy()

        dqDF['_dq_keep'] = dqDF[dq_flag_field].map(self._normalizeDQValue).isin(keep_vals)

        event_state = dqDF[[dqTimeCol, '_dq_keep']].copy()
        event_state.sort_values(dqTimeCol, inplace=True)
        event_state = event_state.groupby(dqTimeCol, as_index=False)['_dq_keep'].last()

        keep_idx = self._applyDQEventState(sonMerge, event_state, dqTimeCol)

        sonDF.loc[keep_idx, filtDQCol] = True
        sonDF[filtCol] = sonDF[filtCol] & sonDF[filtDQCol]

        return sonDF

    # ======================================================================
    def _normalizeDQKeepValues(self, dq_keep_values):

        if dq_keep_values is False or dq_keep_values is None:
            return set()

        if isinstance(dq_keep_values, str):
            dq_keep_values = dq_keep_values.split(',')

        keep_vals = set()
        for value in dq_keep_values:
            norm = self._normalizeDQValue(value)
            if norm:
                keep_vals.add(norm)

        return keep_vals

    # ======================================================================
    def _normalizeDQValue(self, value):

        if pd.isna(value):
            return ''
        return str(value).strip().lower()

    # ======================================================================
    def _coerceDQTimestampSeries(self, series, field_name):

        non_na = series.dropna()
        numeric = pd.to_numeric(series, errors='coerce')
        if len(non_na) > 0 and numeric.notna().sum() == len(non_na):
            return numeric, 'numeric'

        dt = pd.to_datetime(series, errors='coerce')
        if dt.notna().any():
            try:
                if dt.dt.tz is not None:
                    dt = dt.dt.tz_localize(None)
            except AttributeError:
                pass
            return dt, 'datetime'

        if numeric.notna().any():
            return numeric, 'numeric'

        raise ValueError('Unable to parse dqLog timestamps from column: {}'.format(field_name))

    # ======================================================================
    def _shiftDQDatetimeToTargetOffset(self,
                                       dq_times,
                                       dq_src_utc_offset=False,
                                       dq_target_utc_offset=False):

        src_offset = self._coerceDQUtcOffset(dq_src_utc_offset, 'dq_src_utc_offset')
        target_offset = self._coerceDQUtcOffset(dq_target_utc_offset, 'dq_target_utc_offset')

        if src_offset is None and target_offset is None:
            return dq_times

        if src_offset is None or target_offset is None:
            raise ValueError(
                'dq_src_utc_offset and dq_target_utc_offset must both be provided when either is set.'
            )

        return dq_times + pd.to_timedelta(target_offset - src_offset, unit='h')

    # ======================================================================
    def _coerceDQUtcOffset(self, value, field_name):

        if value is False or value is None or value == '':
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            raise ValueError('{} must be a numeric UTC offset in hours.'.format(field_name))

    # ======================================================================
    def _getSonarFilterTimestamp(self, sonDF):

        if 'date' in sonDF.columns and 'time' in sonDF.columns:
            dt = pd.to_datetime(
                sonDF['date'].astype(str).str.strip() + ' ' + sonDF['time'].astype(str).str.strip(),
                errors='coerce',
                format='mixed',
            )
            if dt.notna().any():
                try:
                    if dt.dt.tz is not None:
                        dt = dt.dt.tz_localize(None)
                except AttributeError:
                    pass
                return dt, 'datetime'

        if 'time' in sonDF.columns:
            dt = pd.to_datetime(sonDF['time'], errors='coerce', format='mixed')
            if dt.notna().any():
                try:
                    if dt.dt.tz is not None:
                        dt = dt.dt.tz_localize(None)
                except AttributeError:
                    pass
                return dt, 'datetime'

        if 'time_s' in sonDF.columns:
            numeric = pd.to_numeric(sonDF['time_s'], errors='coerce')
            if numeric.notna().any():
                return numeric, 'numeric'

        raise ValueError('Unable to determine sonar timestamps for dqLog filtering.')


    # ======================================================================
    def _applyDQEventState(self, son, event_state, dqTimeCol):
        '''
        Return the subset of sonar indices whose ping timestamp falls within a
        "keep" state block as defined by the DQ event log.

        Uses np.searchsorted so each ping inherits the state of the most-recent
        event that preceded it.  Pings before the first event are excluded.
        '''

        event_times = event_state[dqTimeCol].to_numpy()
        event_keep  = event_state['_dq_keep'].to_numpy(dtype=bool)
        son_times   = son['_son_ts'].to_numpy()

        # searchsorted(side='right') - 1 gives index of last event <= ping time
        event_idx = np.searchsorted(event_times, son_times, side='right') - 1

        # Pings before the first event get event_idx == -1 → exclude
        valid_idx = event_idx >= 0

        keep_mask = np.zeros(len(son), dtype=bool)
        keep_mask[valid_idx] = event_keep[event_idx[valid_idx]]

        return son.loc[keep_mask, '_son_idx']


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

        sonDat = np.zeros((int(self.pingMax), len(self.pingCnt))).astype(int) # Initialize array to hold sonar returns
        file = open(self.sonFile, 'rb') # Open .SON file

        for i in range(len(self.headIdx)):
            if ~np.isnan(self.headIdx[i]):
                ping_len = min(self.pingCnt[i].astype(int), self.pingMax)


                # #### Do not commit!!!!
                # # if self.beamName == 'ss_star' or self.beamName == 'ss_port':
                # #     ping_len *= 2
                if not self.son8bit:
                    ping_len *= 2

                headIDX = self.headIdx[i].astype(int)
                son_offset = self.son_offset[i].astype(int)
                # pingIdx = headIDX + self.headBytes # Determine byte offset to sonar returns
                pingIdx = headIDX + son_offset

                file.seek(pingIdx) # Move to that location

                # Get the ping
                buffer = file.read(ping_len)

                if self.flip_port:
                    buffer = buffer[::-1]

                # Read the data
                if self.son8bit:# and self.beamName != 'ss_star' and self.beamName != 'ss_port':
                    dat = np.frombuffer(buffer, dtype='>u1')
                else:
                    try:
                        dat = np.frombuffer(buffer, dtype='>u2')
                    except:
                        dat = np.frombuffer(buffer[:-1], dtype='>u2')

                try:
                    sonDat[:ping_len, i] = dat
                except:
                    ping_len = len(dat)
                    sonDat[:ping_len, i] = dat
        
        file.close()
        self.sonDat = self._convert_son_dat_to_uint8(sonDat)
        return

    def _convert_son_dat_to_uint8(self, sonDat):
        if self.son8bit:
            return np.clip(sonDat, 0, 255).astype(np.uint8)

        dat_uint16 = np.clip(sonDat, 0, 65535).astype(np.uint16, copy=False)

        # If values are packed in the high byte, drop the low byte to prevent black tiles.
        low_byte_zero_ratio = np.mean((dat_uint16 & 0x00FF) == 0)
        if low_byte_zero_ratio > 0.9:
            return (dat_uint16 >> 8).astype(np.uint8)

        nonzero = dat_uint16[dat_uint16 > 0]
        if nonzero.size == 0:
            return np.zeros_like(dat_uint16, dtype=np.uint8)

        p_low, p_high = np.percentile(nonzero, [1, 99])
        if p_high <= p_low:
            return np.zeros_like(dat_uint16, dtype=np.uint8)

        scaled = (dat_uint16.astype(np.float32) - p_low) * (255.0 / (p_high - p_low))
        return np.clip(scaled, 0, 255).astype(np.uint8)

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

        # Get max depth
        maxDep = max(bedPick)
        maxGap = int(round(np.tan(np.deg2rad(4)) * maxDep, 0)) # Max nadir gap (assume 4 degrees)

        H_out = H + maxGap

        # Initialize 2d array to store relocated sonar records
        srcDat = np.zeros((H_out, W), dtype=np.float32)

        #Iterate each ping (inner row-loop replaced with numpy vector ops)
        for j in range(W):
            depth = int(bedPick[j])  # Get depth (in pixels) at nadir
            dd = float(depth * depth)

            # Calculate nadir gap (assume 4 degrees) for this ping
            nadirGap = int(round(np.tan(np.deg2rad(4)) * depth, 0))

            # Rows at or beyond the water column boundary
            row_arr = np.arange(depth, H)
            # Horizontal range via Pythagorean theorem, plus nadir gap offset
            src_idx = np.round(
                np.sqrt(row_arr.astype(np.float32) ** 2 - dd)
            ).astype(int) + nadirGap

            # Discard out-of-bounds indices
            valid = src_idx < H_out
            rows_v = row_arr[valid]
            sidx_v = src_idx[valid]

            pingDat = np.full(H_out, np.nan, dtype=np.float32)
            if len(sidx_v) > 0:
                data_extent = int(sidx_v[-1])
                pingDat[sidx_v] = self.sonDat[rows_v, j].astype(np.float32)
                pingDat[data_extent:] = 0  # Zero out values past range extent

            pingDat[:nadirGap] = np.nan  # Remove relocated water column

            # Interpolate over gaps starting from first non-zero pixel
            nonZero = np.where(pingDat > 0)[0]
            if len(nonZero) > 0:
                firstNonZero = nonZero[0]
                tail = pingDat[firstNonZero:]
                nans = np.isnan(tail)
                if nans.any():
                    x = np.arange(len(tail))
                    tail[nans] = np.interp(x[nans], x[~nans], tail[~nans])
                    pingDat[firstNonZero:] = tail

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
        data = self.sonDat.astype('uint8') # Get the sonar data

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
        imsave(os.path.join(outDir, projName+'_'+imgOutPrefix+'_'+channel+'_'+addZero+str(k)+tileFile), data, check_contrast=False)

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
        data = self.sonDat.astype('uint8') # Get the sonar data

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
        outfile = os.path.join(outDir, projName+'_'+imgOutPrefix+'_'+channel+'_'+addZero+str(k)+tileFile)

        # Save as a plot for colormap
        if colormap:
            # plt.imshow(data, cmap=self.sonogram_colorMap)
            # plt.savefig(outfile)

            norm_data = data / 255.0
            colored_data = plt.cm.get_cmap(self.sonogram_colorMap)(norm_data)
            colored_data = (colored_data[:, :, :3] * 255).astype('uint8')
            data = colored_data

            # imsave(outfile, data)

        else:
            pass
        
            # imsave(outfile, data, check_contrast=False)

        imsave(outfile, data, check_contrast=False)
            

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
            self._doSpdCor(chunk, spdCor=spdCor, mask_shdw=mask_shdw, maxCrop=maxCrop, do_egn=self.egn, stretch_wcp=True)

            if self.sonDat is not np.nan:
                self._writeTilesPlot(chunk, imgOutPrefix='wcp', tileFile=tileFile, colormap=True)
            else:
                pass

        if self.wcm:
            # Do speed correction
            self._doSpdCor(chunk, spdCor=spdCor, mask_shdw=mask_shdw, mask_wc=True, maxCrop=maxCrop, do_egn=self.egn, stretch_wcp=True)

            if self.sonDat is not np.nan:
                self._writeTilesPlot(chunk, imgOutPrefix='wcm', tileFile=tileFile, colormap=True)
            else:
                pass

        if self.wcr_src:
            # Do speed correction
            self._doSpdCor(chunk, spdCor=spdCor, mask_shdw=mask_shdw, src=True, maxCrop=maxCrop, do_egn=self.egn, stretch_wcp=True)

            if self.sonDat is not np.nan:
                self._writeTilesPlot(chunk, imgOutPrefix='src', tileFile=tileFile, colormap=True)
            else:
                pass

        if self.wco:
            # Do speed correction
            self._doSpdCor(chunk, spdCor=spdCor, mask_bed=True, maxCrop=maxCrop, do_egn=self.egn, stretch_wcp=True)

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

        # Update class attributes based on current chunk
        self.pingMax = np.nanmax(sonMeta['ping_cnt']) # store to determine max range per chunk

        if ~np.isnan(self.pingMax):
            # Load chunk's sonar data into memory
            if son:
                # self._loadSonChunk()
                self._getScanChunkSingle(chunk)

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
                d = np.max(d) - np.min(d)

                pixM = sonMeta['pixM']
                # Find most common pixel size
                if len(pixM.unique()) > 1:
                    pixM = pixM.mode()[0]
                else:
                    pixM = pixM.iloc[0]

                # Distance in pix
                d = round(d / pixM, 0).astype(int)

                sonDat = resize(sonDat,
                                (sonDat.shape[0], d),
                                mode='reflect',
                                clip=True,
                                preserve_range=True)

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

    # ======================================================================
    def _exportMovWin(self,
                      i : int,
                      stride : int,
                      tileType: list,
                      pingMax: int,
                      depMax: int):
        
        '''
        '''

        # Set chunk index
        a_idx = i-1
        b_idx = i

        # Iterate each tile type
        for t in tileType:
            if t == 'wco':
                cropMax = depMax
            else:
                cropMax = pingMax
            inDir = os.path.join(self.outDir, t)
            outDir = os.path.join(self.outDir, t+'_mw')

            if not os.path.exists(outDir):
                try:
                    os.mkdir(outDir)
                except:
                    pass

            # Find the images
            images = os.listdir(inDir)
            images.sort()

            # Get each image
            a_img = images[a_idx]
            b_img = images[b_idx]

            # Get image name
            img_name = a_img.split('.')[0]

            # Open each image
            a_img = imread(os.path.join(inDir, a_img))
            b_img = imread(os.path.join(inDir, b_img))

            def resize_to_pingMax(img, cropMax):
                ndims = img.ndim
                current_size = img.shape[0]
                if current_size < cropMax:
                    # Pad with zeros 
                    if ndims == 2:
                        padding = ((0, cropMax - current_size), (0, 0))
                    else:
                        padding = ((0, cropMax - current_size), (0, 0), (0,0))
                    resized_img = np.pad(img, padding, mode='constant', constant_values=0)
                elif current_size > cropMax:
                    # Truncate the array
                    resized_img = img[:cropMax, :]
                else:
                    # No change needed
                    resized_img = img
                return resized_img

            # Resize a_img and b_img
            a_img = resize_to_pingMax(a_img, cropMax)
            b_img = resize_to_pingMax(b_img, cropMax)

            # Set stride based on first image
            # stride = int(round(a_img.shape[1] * stride, 0))
            to_stride = int(round(self.nchunk * stride, 0))

            # Set window size based on first image
            # winSize = a_img.shape[1]
            winSize = self.nchunk

            # Concatenate images
            movWin = np.concatenate((a_img, b_img), axis=1)

            # Last window idx
            lastWinIDX = self.nchunk

            win = 0
            # Iterate each window
            while win < lastWinIDX:
                window = movWin[:, win:win+winSize]

                zero = self._addZero(win)

                # Save window
                imsave(os.path.join(outDir, img_name+'_'+zero+str(win)+'.jpg'), window)

                win += to_stride

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

        # Update class attributes based on current chunk
        rangeCnt = np.unique(sonMeta['ping_cnt'], return_counts=True)
        pingMaxi = np.argmax(rangeCnt[1])
        self.pingMax = int(rangeCnt[0][pingMaxi])

        self.headIdx = sonMeta['index']#.astype(int) # store byte offset per ping
        self.son_offset = sonMeta['son_offset']
        self.pingCnt = sonMeta['ping_cnt']#.astype(int) # store ping count per ping

        # Load chunk's sonar data into memory
        self._loadSonChunk()
        # Do PPDRC filter
        if filterIntensity:
            self._doPPDRC()
        # Remove water if exporting wcr imagery
        if remWater:
            self._WCR(sonMeta)     

        del self.headIdx, self.pingCnt

        return
    
    def _getScanSlice(self, transect, start_idx, end_idx, remWater = False):
        '''
        
        '''

        # Open sonar metadata file to df
        sonMetaAll = pd.read_csv(self.sonMetaFile)

        # Filter by transect
        sonMetaAll = sonMetaAll[sonMetaAll['transect'] == transect].reset_index(drop=True)
        
        # Filter sonMeta
        # sonMeta = sonMeta[(sonMeta['index'] >= start_idx) & (sonMeta['index'] <= end_idx)]
        sonMeta = sonMeta.iloc[start_idx:end_idx]
        sonMeta = sonMeta.reset_index()

        # Update class attributes based on current chunk
        rangeCnt = np.unique(sonMeta['ping_cnt'], return_counts=True)
        pingMaxi = np.argmax(rangeCnt[1])
        self.pingMax = int(rangeCnt[0][pingMaxi])

        self.headIdx = sonMeta['index']#.astype(int) # store byte offset per ping
        self.son_offset = sonMeta['son_offset']
        self.pingCnt = sonMeta['ping_cnt']#.astype(int) # store ping count per ping

        # Load chunk's sonar data into memory
        self._loadSonChunk()

        # Remove water if exporting wcr imagery
        if remWater:
            self._WCR(sonMeta)     

        del self.headIdx, self.pingCnt

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