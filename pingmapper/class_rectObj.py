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
from pingmapper.class_sonObj import sonObj
from osgeo import gdal, ogr, osr
from osgeo_utils.gdal_sieve import gdal_sieve
from scipy.interpolate import splprep, splev
from skimage.transform import warp
from rasterio.transform import from_origin
from rasterio.enums import Resampling
from PIL import Image, ImageColor
from shapely.geometry import Polygon
from shapely import affinity

from matplotlib import colormaps    

from scipy.interpolate import NearestNDInterpolator, griddata, UnivariateSpline
from scipy.sparse import coo_matrix
from scipy.spatial import cKDTree, ConvexHull
from skimage.draw import polygon
from shapely.geometry import Polygon, Point, MultiPoint, LineString
from shapely.ops import unary_union
from shapely.vectorized import contains

import rasterio.features
from shapely.geometry import mapping
import rasterio.mask

from scipy.signal import savgol_filter
from scipy import ndimage


class rectObj(sonObj):
    '''
    Python child class of sonObj() to store everything related to georectification
    of imagery from Humminbird sonar recordings.  Since this is a child class of
    sonObj(), all attributes and functions provided in sonObj() are available to
    a rectObj() instance.

    ----------------
    Class Attributes
    ----------------
    * Alphabetical order *
    self.rangeExt : DataFrame
        DESCRIPTION - Pandas dataframe to store range extent.

    self.rect_wcr : bool
        DESCRIPTION - Flag indicating if rectified wcr data was exported.

    self.rect_wcp : bool
        DESCRIPTION - Flag indicating if rectified wcp data was exported.

    self.smthTrk : DataFrame
        DESCRIPTION - Pandas dataframe to store smoothed trackline.
    '''

    ############################################################################
    # Create rectObj() instance from previously created sonObj() instance      #
    ############################################################################

    #=======================================================================
    def __init__(self,
                 metaFile):
        '''
        Initialize an empty rectObj() class, child of sonObj() class.  All sonObj()
        parameters initialized to `None` so that they can be loaded from a
        previously created pickle file.

        ----------
        Parameters
        ----------
        metaFile : str
        DESCRIPTION - Path to pickled sonObj() file containing sonObj() attribute
                      values.
        EXAMPLE -     metaFile = './PINGMapperTest/meta/B002_ss_port_meta.meta'

        -------
        Returns
        -------
        rectObj instance with sonObj attributes loaded.
        '''
        sonObj.__init__(self, sonFile=None, humFile=None, projDir=None, tempC=None, nchunk=None)

        metaFile = pickle.load(open(metaFile, 'rb')) # Load sonObj() pickle file into memory

        for attr, value in metaFile.__dict__.items(): # Store sonObj() attributes in self
            setattr(self, attr, value)

        if not hasattr(self, 'rect_wcp'):
            self.rect_wcp = False

        if not hasattr(self, 'rect_wcr'):
            self.rect_wcr = False

        return

    ############################################################################
    # Smooth GPS trackpoint coordinates                                        #
    ############################################################################

    #=======================================================================
    def _interpTrack(self,
                     df,
                     dfOrig=None,
                     dropDup=True,
                     xlon='lon',
                     ylat='lat',
                     xutm='utm_e',
                     yutm='utm_n',
                     zU='time_s',
                     filt=0,
                     deg=3):
        '''
        Smooths 'noisy' ping trackpoints by completing the following:
        1) Removes duplicate geographic coordinates;
        2) Filter coordinates to reduce point density;
        3) Fits n-degree spline to filtered coordinates;
        4) Reinterpolate all input sonar records along the spline.

        Smoothed coordinates are reprojected into utm zone coordinates and course
        over ground (COG) is calculated.

        ----------
        Parameters
        ----------
        df : DataFrame
            DESCRIPTION - Pandas dataframe with geographic coordinates of sonar
                          records.
        dfOrig : DataFrame : [Default=None]
            DESCRIPTION - Pandas dataframe with geographic coordinates of sonar
                          records.  If `None`, a copy of `df` will be used.
        dropDup : bool : [Default=True]
            DESCRIPTION - Flag indicating if coincident coordinates will be dropped.
        xlon : str : [Default='lon']
            DESCRIPTION - DataFrame column name for longitude coordinates.
        ylat : str : [Default='lat']
            DESCRIPTION - DataFrame column name for latitude coordinates.
        xutm : str : [Default='utm_e']
            DESCRIPTION - DataFrame column name for easting coordinates.
        yutm : str : [Default='utm_y']
            DESCRIPTION - DataFrame column name for northing coordinates.
        zU : str : [Default='time_s']
            DESCRIPTION - DataFrame column name used to reinterpolate coordinates
                          along spline (i.e. determines spacing between coordinates)
        filt : int : [Default=0]
            DESCRIPTION - Every `filt` ping will be used to fit a spline.
        deg : int : [Default=3]
            DESCRIPTION - Indicates n-degree spline that will be fit to filtered
                          coordinates.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        self.__init__()

        -------
        Returns
        -------
        Smoothed trackpoints in a Pandas DataFrame

        --------------------
        Next Processing Step
        --------------------
        self._getRangeCoords()
        '''

        lons = xlon+'s' # Name of smoothed longitude column in df
        lats = ylat+'s' # Name of smoothed latitude column in df
        es = xutm+'s' # Name of smoothed easting column in df
        ns = yutm+'s' # Name of smoothed northing column in df

        # Make copy of df to work on
        if dfOrig is None:
            dfOrig = df.copy()

        # Check for duplicate zU values. If there are duplicate zU values, then
        ## there will be pings that share smoothed lat/lon coordinates, which will
        ## result in a COG == 0, messing up rectification.
        zUvals = dfOrig[zU].to_numpy()
        u, c = np.unique(zUvals, return_counts=True)
        if len(u[c > 1]) > 0:
            dups = True
        else:
            dups = False

        # Drop duplicate coordinates
        if dropDup is True:
            df.drop_duplicates(subset=[xlon, ylat], inplace=True)

        # Extract every `filt` record, including last value
        if (filt>0) and (len(df)>filt):
            lastRow = df.iloc[-1].to_frame().T
            dfFilt = df.iloc[::filt]
            dfFilt = pd.concat([dfFilt, lastRow]).reset_index(drop=True)
        else:
            dfFilt = df.reset_index(drop=False)

        # Try smoothing trackline
        x=dfFilt[xlon].to_numpy(dtype='float64') # Store longitude coordinates in numpy array
        y=dfFilt[ylat].to_numpy(dtype='float64') # Store latitude coordinates in numpy array
        if dups is True:
            # Force unique zU value by multiplying time ellapsed and record number
            t = dfFilt[zU].to_numpy(dtype='float64') * dfFilt['record_num'].to_numpy(dtype='float64')
            u_interp = dfOrig[zU].to_numpy(dtype='float64') * dfOrig['record_num'].to_numpy(dtype='float64')
        else:
            t=dfFilt[zU].to_numpy(dtype='float64') # Store parameter values in numpy array.  Used to space points along spline.
            u_interp = dfOrig[zU].to_numpy(dtype='float64') # Get all time ellapsed OR record number values from unfilterd df

        # Attempt to fix error
        # https://stackoverflow.com/questions/47948453/scipy-interpolate-splprep-error-invalid-inputs
        okay = np.where(np.abs(np.diff(x))+np.abs(np.diff(y))>0)
        x = np.r_[x[okay], x[-1]]
        y = np.r_[y[okay], y[-1]]
        t = np.r_[t[okay], t[-1]]

        # Check if enough points to interpolate
        # If not, too many overlapping pings
        if len(x) <= deg:
            # return dfOrig[['chunk_id', 'record_num', 'ping_cnt', 'time_s', 'pix_m']]
            return dfOrig[['chunk_id', 'record_num', 'ping_cnt', 'time_s']]

        # Fit a spline to filtered coordinates and parameterize with time ellapsed
        try:
            tck, _ = splprep([x,y], u=t, k=deg, s=0)
        except:
            # Time is messed up (negative time offset)
            # Parameterize with record num instead
            zU = 'record_num'
            t = dfFilt[zU].to_numpy()
            t = np.r_[t[okay], t[-1]]
            tck, _ = splprep([x,y], u=t, k=deg, s=0)
            u_interp = dfOrig[zU].to_numpy()

        x_interp = splev(u_interp, tck) # Use u_interp to get smoothed x/y coordinates from spline

        u, indices, c = np.unique(u_interp, return_index= True,return_counts=True)
        for val in zip(c, u, indices):
            if val[0] > 1:
                print(val)

        # Store smoothed trackpoints in a dictionary
        smooth = {'chunk_id': dfOrig['chunk_id'],
                  'record_num': dfOrig['record_num'],
                  'ping_cnt': dfOrig['ping_cnt'],
                  'time_s': dfOrig['time_s'],
                  'pix_m': self.pixM,
                  lons: x_interp[0],
                  lats: x_interp[1],
                  'dep_m': dfOrig['dep_m'],
                  'instr_heading': dfOrig['instr_heading']
                  }

        sDF = pd.DataFrame(smooth) # Convert dictionary to Pandas df
        
        # Calculate smoothed easting/northing
        e_smth, n_smth = self.trans(sDF[lons].to_numpy(), sDF[lats].to_numpy())
        # Store in df
        sDF[es] = e_smth
        sDF[ns] = n_smth

        # Calculate COG (course over ground; i.e. heading) from smoothed lat/lon
        brng = self._getBearing(sDF, lons, lats)
        # self._getBearing() returns n-1 values because last ping can't
        ## have a COG value.  We will duplicate the last COG value and use it for
        ## the last ping.
        last = brng[-1]
        brng = np.append(brng, last)
        sDF['cog'] = brng # Store COG in sDF

        return sDF

    #===========================================
    def _getBearing(self,
                    df,
                    lon = 'lons',
                    lat = 'lats'):
        '''
        Calculates course over ground (COG) from a set of coordinates.  Since the
        last coordinate pair cannot have a COG value, the length of the returned
        array is len(n-1) where n == len(df).

        ----------
        Parameters
        ----------
        df : DataFrame
            DESCRIPTION - Pandas dataframe with geographic coordinates of sonar
                          records.
        lon : str : [Default='lons']
            DESCRIPTION - DataFrame column name for longitude coordinates.
        lat : str : [Default='lats']
            DESCRIPTION - DataFrame column name for latitude coordinates.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self._interpTrack()

        -------
        Returns
        -------
        Numpy array of COG values.

        --------------------
        Next Processing Step
        --------------------
        Return to self._interpTrack()
        '''
        # COG calculation will be calculated on numpy arrays for speed.  Since
        ## COG is calculated from one point to another (pntA -> pntB), we need
        ## to store pntA values, beginning with the first value and ending at
        ## second to last value, in one array and pntB values, beginning at second
        ## value and ending at last value, in another array.  We can then use
        ## vector algebra to efficiently calculate COG.

        # Prepare pntA values [0:n-1]
        lonA = df[lon].to_numpy() # Store longitude coordinates in numpy array
        latA = df[lat].to_numpy() # Store longitude coordinates in numpy array
        lonA = lonA[:-1] # Omit last coordinate
        latA = latA[:-1] # Omit last coordinate
        pntA = [lonA,latA] # Store in array of arrays

        # Prepare pntB values [0+1:n]
        lonB = df[lon].to_numpy() # Store longitude coordinates in numpy array
        latB = df[lat].to_numpy() # Store longitude coordinates in numpy array
        lonB = lonB[1:] # Omit first coordinate
        latB = latB[1:] # Omit first coordinate
        pntB = [lonB,latB] # Store in array of arrays

        # Convert latitude values into radians
        lat1 = np.deg2rad(pntA[1])
        lat2 = np.deg2rad(pntB[1])

        diffLong = np.deg2rad(pntB[0] - pntA[0]) # Calculate difference in longitude then convert to degrees
        bearing = np.arctan2(np.sin(diffLong) * np.cos(lat2), np.cos(lat1) * np.sin(lat2) - (np.sin(lat1) * np.cos(lat2) * np.cos(diffLong))) # Calculate bearing in radians

        db = np.degrees(bearing) # Convert radians to degrees
        db = (db + 360) % 360 # Ensure degrees in range 0-360

        return db

    ############################################################################
    # Apply offset to coordinates                                              #
    ############################################################################

    #===========================================
    def _applyPosOffset(self, x_offset, y_offset):
        '''
        Apply offset to smoothed coordinates to account for GPS and transducer
        offset.
        '''
        # Store necessary dataframe column names in variables
        lons = 'lons'
        lats = 'lats'
        bearing = 'cog'
        utm_es = 'utm_es'
        utm_ns = 'utm_ns'

        # Get smoothed trackline
        sDF = self.smthTrk

        #######################
        # Go along x-axis first

        R = 6371.393*1000 #Radius of the Earth in meters
        if x_offset < 0:
            rotate = 180
        else:
            rotate = 0

        brng = (sDF['cog']+rotate) % 360
        brng = np.deg2rad(brng)
        d = abs(x_offset)

        # Get lat/lon for origin of each ping, convert to numpy array
        lat1 = np.deg2rad(sDF[lats]).to_numpy()
        lon1 = np.deg2rad(sDF[lons]).to_numpy()

        # Calculate position down boat x-axis
        # Calculate latitude of range extent
        lat2 = np.arcsin( np.sin(lat1) * np.cos(d/R) +
               np.cos(lat1) * np.sin(d/R) * np.cos(brng))

        # Calculate longitude of range extent
        lon2 = lon1 + np.arctan2( np.sin(brng) * np.sin(d/R) * np.cos(lat1),
                                  np.cos(d/R) - np.sin(lat1) * np.sin(lat2))

        lat2 = np.degrees(lat2)
        lon2 = np.degrees(lon2)

        sDF[lons] = lon2
        sDF[lats] = lat2

        ######################################
        # Calculate position along boat y-axis
        if y_offset > 0:
            rotate = 90
        else:
            rotate = -90

        brng = (sDF['cog']+rotate) % 360
        brng = np.deg2rad(brng)
        d = abs(y_offset)

        # Get lat/lon for origin of each ping, convert to numpy array
        lat1 = np.deg2rad(sDF[lats]).to_numpy()
        lon1 = np.deg2rad(sDF[lons]).to_numpy()

        # Calculate position down boat x-axis
        # Calculate latitude of range extent
        lat2 = np.arcsin( np.sin(lat1) * np.cos(d/R) +
               np.cos(lat1) * np.sin(d/R) * np.cos(brng))

        # Calculate longitude of range extent
        lon2 = lon1 + np.arctan2( np.sin(brng) * np.sin(d/R) * np.cos(lat1),
                                  np.cos(d/R) - np.sin(lat1) * np.sin(lat2))

        lat2 = np.degrees(lat2)
        lon2 = np.degrees(lon2)

        sDF[lons] = lon2
        sDF[lats] = lat2

        # Calculate easting and northing
        e_smth, n_smth = self.trans(sDF[lons].to_numpy(), sDF[lats].to_numpy())
        # Store in dataframe
        sDF[utm_es] = e_smth
        sDF[utm_ns] = n_smth
        sDF = sDF.dropna() # Drop any NA's
        self.smthTrk = sDF # Store df in class attribute

        return

    ############################################################################
    # Calculate range extent coordinates                                       #
    ############################################################################

    #===========================================
    def _getRangeCoords(self,
                        flip = False,
                        filt = 25,
                        cog = True):
        '''
        Humminbird SSS store one set geographic coordinates where each ping
        orriginates from (assuming GPS is located directly above sonar transducer).
        In order to georectify the sonar imagery, we need to know geographically
        where each ping terminates.  The range (distance, length) of each
        ping is not stored in the Humminbird recording, so we estimate
        the size of one ping return (estimated previously in self._getPixSize)
        and multiply by the number of ping returns for each ping to
        estimate the range.  Range coordinates for each ping are then
        estimated using the range of each ping, the coordinates where the
        ping originated, and the COG.

        A spline is then fit to filtered range coordinates, the same as the trackpoints,
        to help ensure no pings overlapm, resulting in higher quality sonar imagery.

        ----------
        Parameters
        ----------
        flip : bool : [Default=False]
            DESCRIPTION - Flip port and starboard sonar channels (if transducer
                          was facing backwards duing survey).
        filt : int : [Default=25]
            DESCRIPTION - Every `filt` ping will be used to fit a spline.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        self._interpTrack()

        -------
        Returns
        -------
        A Pandas DataFrame with range extent coordinates stored in self.rangeExt

        --------------------
        Next Processing Step
        --------------------
        self._rectSon()
        '''
        # Store necessary dataframe column names in variables
        lons = 'lons'
        lats = 'lats'
        ping_cnt = 'ping_cnt'
        ping_bearing = 'ping_bearing'
        rlon = 'range_lon'
        rlat = 'range_lat'
        re = 'range_e'
        rn = 'range_n'
        range_ = 'range'
        chunk_id = 'chunk_id'

        self._loadSonMeta() # Load ping metadata
        sonMetaDF = self.sonMetaDF

        # Get smoothed trackline
        if not hasattr(self, 'smthTrk'):
            self.smthTrk = pd.read_csv(self.smthTrkFile)
        else:
            pass
        sDF = self.smthTrk

        ########################
        # Calculate ping bearing
        # Determine ping bearing.  Ping bearings are perpendicular to COG.
        if self.beamName == 'ss_port':
            rotate = -90  # Rotate COG by 90 degrees to the left
        else:
            rotate = 90 # Rotate COG by 90 degrees to the right
        if flip: # Flip rotation factor if True
            rotate *= -1

        # Calculate ping bearing and normalize to range 0-360
        # cog = False
        if cog:
            sDF[ping_bearing] = (sDF['cog']+rotate) % 360
        else:
            sDF[ping_bearing] = (sDF['instr_heading']+rotate) % 360

        ############################################
        # Calculate range (in meters) for each chunk
        # Calculate max range for each chunk to ensure none of the sonar image
        ## is cut off due to changing the range setting during the survey.
        # chunk = sDF.groupby(chunk_id) # Group dataframe by chunk_id

        # Old method
        # maxPing = chunk[ping_cnt].max() # Find max ping count for each chunk
        # New method to find maxPing based on most numerous ping count
        maxPing = []
        for name, group in sDF.groupby(chunk_id):
            rangeCnt = np.unique(group[ping_cnt], return_counts=True)
            pingMaxi = np.argmax(rangeCnt[1])
            maxPing.append(int(rangeCnt[0][pingMaxi]))
        # Convert maxPing i to pd series
        maxPing = pd.Series(maxPing)

        # pix_m = chunk['pix_m'].min() # Get pixel size for each chunk
        pix_m = self.pixM # Get pixel size for each chunk
        for i in maxPing.index: # Calculate range (in meters) for each chunk
            sDF.loc[sDF[chunk_id]==i, range_] = maxPing[i]*pix_m

        ##################################################
        # Calculate range extent coordinates for each ping
        # Calculate range extent lat/lon using ping bearing and range
        # https://stackoverflow.com/questions/7222382/get-lat-long-given-current-point-distance-and-bearing
        # R = 6371.393*1000 #Radius of the Earth in meters
        R = 6378137.0 # WGS 1984
        brng = np.deg2rad(sDF[ping_bearing]).to_numpy() # Convert ping bearing to radians and store in numpy array
        d = (sDF[range_].to_numpy()) # Store range in numpy array

        # Get lat/lon for origin of each ping, convert to numpy array
        lat1 = np.deg2rad(sDF[lats]).to_numpy()
        lon1 = np.deg2rad(sDF[lons]).to_numpy()

        # Calculate latitude of range extent
        lat2 = np.arcsin( np.sin(lat1) * np.cos(d/R) +
               np.cos(lat1) * np.sin(d/R) * np.cos(brng))

        # Calculate longitude of range extent
        lon2 = lon1 + np.arctan2( np.sin(brng) * np.sin(d/R) * np.cos(lat1),
                                  np.cos(d/R) - np.sin(lat1) * np.sin(lat2))

        # Convert range extent coordinates into degrees
        lat2 = np.degrees(lat2)
        lon2 = np.degrees(lon2)

        # Store in dataframe
        sDF[rlon] = lon2
        sDF[rlat] = lat2

        # Calculate easting and northing
        e_smth, n_smth = self.trans(sDF[rlon].to_numpy(), sDF[rlat].to_numpy())
        # Store in dataframe
        sDF[re] = e_smth
        sDF[rn] = n_smth
        sDF = sDF.dropna() # Drop any NA's
        self.smthTrk = sDF # Store df in class attribute

        ##########################################
        # Smooth and interpolate range coordinates
        if cog:
            self._interpRangeCoords(filt)
        else:
            sDF = sDF[['record_num', 'chunk_id', 'ping_cnt', 'time_s', 'lons', 'lats', 'utm_es', 'utm_ns', 'instr_heading', 'cog', 'dep_m', 'range', 'range_lon', 'range_lat', 'range_e', 'range_n', ping_bearing, 'transect']].copy()
            sDF.rename(columns={'lons': 'trk_lons', 'lats': 'trk_lats', 'utm_es': 'trk_utm_es', 'utm_ns': 'trk_utm_ns', 'cog': 'trk_cog', 'range_lat':'range_lats', 'range_lon':'range_lons', 'range_e':'range_es', 'range_n':'range_ns'}, inplace=True)
            sDF['chunk_id_2'] = sDF.index.astype(int)

            ###########################################
            # Overwrite Trackline_Smth_son.beamName.csv
            # outCSV = os.path.join(self.metaDir, "Trackline_Smth_"+self.beamName+".csv")
            outCSV = self.smthTrkFile
            sDF.to_csv(outCSV, index=True, float_format='%.14f')

        # sys.exit()
        gc.collect()
        self._pickleSon()
        return #self

    #===========================================
    def _interpRangeCoords(self,
                           filt = 25):
        '''
        This function fits a spline to the range extent coordinates.  Before fitting
        the spline, overlapping pings are identified and removed to ensure spline
        does not have any loops.  A spline is then fit for each individual chunk
        to avoid undesirable rectification effects caused by changing the range
        during a survey.  The spline is used to reinterpolate range extent
        coordinates, ensuring no overlap between pings.

        ----------
        Parameters
        ----------
        filt : int : [Default=25]
            DESCRIPTION - Every `filt` ping will be used to fit a spline.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self._interpRangeCoords()

        -------
        Returns
        -------
        A Pandas dataframe stored in self.rangeExt with smoothed trackline and
        range extent coordinates.  This DataFrame is exported to .csv and overwrites
        Trackline_Smth_BXXX.csv.

        --------------------
        Next Processing Step
        --------------------
        Returns smoothed coordinates to self._interpRangeCoords().
        '''
        # Store necessary dataframe column names in variables
        rlon = 'range_lon'
        rlons = rlon+'s'
        rlat = 'range_lat'
        rlats = rlat+'s'
        re = 'range_e'
        res = re+'s'
        rn = 'range_n'
        rns = rn+'s'

        sDF = self.smthTrk # Load smoothed trackline coordinates
        rDF = sDF.copy() # Make a copy to work on

        # Work on one chunk at a time
        for chunk, chunkDF in rDF.groupby('chunk_id'):
            chunkDF.reset_index(drop=True, inplace=True)

            # Extract every `filt` recording, including last value
            last = chunkDF.iloc[-1].to_frame().T
            chunkDF = chunkDF.iloc[::filt]
            chunkDF = pd.concat([chunkDF, last]).reset_index(drop=True)

            idx = chunkDF.index.tolist() # Store ping index in list
            maxIdx = max(idx) # Find last record index value

            drop = np.empty((len(chunkDF)), dtype=bool) # Bool numpy array to flag which sonar records overlap and should be dropped
            drop[:] = False # Prepopulate array w/ `False` (i.e. False==don't drop)

            #########################################
            # Find and drop overlapping sonar records
            for i in idx: # Iterate each ping if filtered dataframe
                if i == maxIdx: # Break loop once we reach the last ping
                    break
                else:
                    if drop[i] != True: # If current ping flagged to drop, don't need to check it
                        dropping = self._checkPings(i, chunkDF) # Find subsequent sonar records that overlap current record
                        if maxIdx in dropping.keys(): # Make sure we don't drop last ping in chunk
                            del dropping[maxIdx]
                            dropping[i]=True # Drop current ping instead
                        else:
                            pass
                        if len(dropping) > 0: # We have overlapping sonar records we need to drop
                            for k, v in dropping.items(): # Flag records to drop
                                drop[k] = True
                        else:
                            pass
                    else:
                        pass

            ######################################################
            # Drop all overlapping sonar records for current chunk
            chunkDF = chunkDF[~drop]

            rchunkDF = chunkDF.copy() # Make copy of df w/ no overlapping sonar records for current chunk
            schunkDF = sDF[sDF['chunk_id']==chunk].copy() # Get original df for current chunk

            #################################################
            # Smooth and interpolate range extent coordinates
            smthChunk = self._interpTrack(df=rchunkDF, dfOrig=schunkDF, xlon=rlon,
                                          ylat=rlat, xutm=re, yutm=rn, filt=0, deg=1)

            # Store smoothed range extent in output df
            if 'rsDF' not in locals(): # If output df doesn't exist, make it
                rsDF = smthChunk.copy()
            else: # If output df exists, append results to it
                rsDF = pd.concat([rsDF, smthChunk], axis=0).reset_index(drop=True)

        ##################################################
        # Join smoothed trackline to smoothed range extent
        # sDF = sDF[['record_num', 'chunk_id', 'ping_cnt', 'time_s', 'pix_m', 'lons', 'lats', 'utm_es', 'utm_ns', 'cog', 'dep_m']].copy()
        sDF = sDF[['record_num', 'chunk_id', 'ping_cnt', 'time_s', 'lons', 'lats', 'utm_es', 'utm_ns', 'instr_heading', 'cog', 'dep_m', 'transect']].copy()
        sDF.rename(columns={'lons': 'trk_lons', 'lats': 'trk_lats', 'utm_es': 'trk_utm_es', 'utm_ns': 'trk_utm_ns', 'cog': 'trk_cog'}, inplace=True)
        rsDF.rename(columns={'cog': 'range_cog'}, inplace=True)
        rsDF = rsDF[['record_num', 'range_lons', 'range_lats', 'range_cog']]
        rsDF = sDF.set_index('record_num').join(rsDF.set_index('record_num'))

        # Calculate easting/northing for smoothed range extent
        e_smth, n_smth = self.trans(rsDF[rlons].to_numpy(), rsDF[rlats].to_numpy())
        rsDF[res] = e_smth # Store smoothed easting range extent in rsDF
        rsDF[rns] = n_smth # Store smoothed northing range extent in rsDF

        ###########################################
        # Overwrite Trackline_Smth_son.beamName.csv
        # outCSV = os.path.join(self.metaDir, "Trackline_Smth_"+self.beamName+".csv")
        outCSV = self.smthTrkFile
        rsDF.to_csv(outCSV, index=True, float_format='%.14f')

        self.rangeExt = rsDF # Store smoothed range extent in rectObj
        return #self

    #===========================================================================
    def _checkPings(self,
                    i,
                    df):
        '''
        On sinuous survey transects (i.e. river bends), it is possible for range
        extent coordinates to overlap with each other.  Overlapping sonar records
        will produce issues during the georectification process and need to be
        removed.  This function checks subsequent sonar records from the current
        index i and determines if the sonar records overlap with the current record.
        If they do, they are flagged for removal.

        ----------
        Parameters
        ----------
        i : int
            DESCRIPTION - Current index of ping which will be compared
                          against subsequent sonar records.
        df : Pandas DataFrame
            DESCRIPTION - DataFrame containing range extent coordinates of sonar
                          records.

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self._interpRangeCoords()

        -------
        Returns
        -------
        A dictionary containing dataframe index as key and bool value indicating
        if dataframe ping should be dropped or not.

        --------------------
        Next Processing Step
        --------------------
        Returns dictionary to self._interpRangeCoords()
        '''
        range = 'range' # range distance
        x = 'range_e' # range easting extent coordinate
        y = 'range_n' # range northing extent coordinate
        dThresh = 'distThresh' # max distance to check for overlap
        tDist = 'track_dist' # straight line distance from ping i to subsequent sonar records
        toCheck = 'toCheck' # Flag indicating subsequent ping is close enough to i to check for potential overlap
        toDrop = 'toDrop' # Flag indicating ping overlaps with i
        es = 'utm_es' #Trackline smoothed easting
        ns = 'utm_ns' #Trackline smoothed northing

        ###########
        # Filter df
        rowI = df.loc[i] # Get current df row to compare against
        df = df.copy() # Make copy of dataframe
        df = df.iloc[df.index > i] # Filter out first (i.e. current) row

        #########################
        # Calc distance threshold
        ## We only need to check sonar records which are close enough to the
        ## current ping to potentially overlap.
        df[dThresh] = rowI[range] + df[range]

        # Calc straight line distance along the track from current ping
        ## to all other sonar records.  It is impossible for overlap to occur for
        ## subsequent sonar records to overlap current ping if they are
        ## further then the threshold distance.
        rowIx, rowIy = rowI[x], rowI[y] # Get current ping range extent coordinates
        # dfx, dfy = df[x].to_numpy(), df[y].to_numpy() # Get subsequent ping range extent coordinates
        dfx, dfy = df[x].values.astype(np.float64), df[y].values.astype(np.float64)
        dist = self._getDist(rowIx, rowIy, dfx, dfy) # Calculate distance from current ping

        # Check if dist < distThresh. True==Check for possible overlap; False==No need to check
        df[tDist] = dist # Store distance calculation
        df.loc[df[tDist] <= df[dThresh], toCheck] = True # Check for overlap
        df.loc[df[tDist] > df[dThresh], toCheck] = False # Don't check for overlap
        df[toCheck]=df[toCheck].astype(bool) # Make sure toCheck column is type bool

        # Determine which sonar records overlap with current ping
        line1 = ((rowI[es],rowI[ns]), (rowI[x], rowI[y])) # Store current ping coordinates as tuple
        dfFilt = df[df[toCheck]==True].copy() # Get sonar records that could overlap with current
        dropping = {} # Dictionary to store ping index to drop
        for i, row in dfFilt.iterrows(): # Iterate subsequent sonar records
            line2=((row[es], row[ns]), (row[x], row[y])) # Store ping coordinates to check in tuple
            isIntersect = self._lineIntersect(line1, line2, row[range]) # Determine if line1 intersects line2
            dfFilt.loc[i, toDrop] = isIntersect # Store bool in dataframe (don't need this but keeping in case)
            if isIntersect == True: # If line2 intersects line1, flag ping for dropping
                dropping[i]=isIntersect

        return dropping

    #===========================================================================
    def _getDist(self,
                 aX,
                 aY,
                 bX,
                 bY):
        '''
        Determine distance between two points `a` and `b`.  `a` and `b` can also
        be numpy arrays of coordinates.  This function is used to calculate distance
        between a single point `a` and a series of points `b` stored in numpy arrays.

        ----------
        Parameters
        ----------
        aX : float or numpy array of floats
            DESCRIPTION - X coordinate of point `a`
        aY : float or numpy array of floats
            DESCRIPTION - Y coordinate of point `a`
        bX : float or numpy array of floats
            DESCRIPTION - X coordinate of point `b`
        bY : float or numpy array of floats
            DESCRIPTION - Y coordinate of point `b`

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self._checkPings() or self._lineIntersect()

        -------
        Returns
        -------
        A numpy array with distances calculated

        --------------------
        Next Processing Step
        --------------------
        Returns numpy array to self._checkPings() or self._lineIntersect()
        '''
        dist = np.sqrt( (bX - aX)**2 + (bY - aY)**2) # Calculate distance
        return dist

    #===========================================================================
    def _lineIntersect(self,
                       line1,
                       line2,
                       range):
        '''
        Determines if two lines intersect.  Helper functions are included in this
        method to aid in computation:

        self._lineIntersect.line() : function
            DESCRIPTION - Determines coeficients describing line connecting two
                          points.
        self._lineIntersect.intersection() : function
            DESCRIPTION - Determines if two (infinite) lines intersect and returns
                          x, y coordinates of the intersection.
        self._lineIntersect.isBetween() : function
            DESCRIPTION - Determines if intersecting point falls on the line
                          segments.

        ----------
        Parameters
        ----------
        line1 : tuple
            DESCRIPTION - Two sets of points describing a line ((x1, y1), (x2, y2))
        line2 : tuple
            DESCRIPTION - Two sets of points describing a line ((x1, y1), (x2, y2))
        range : float
            DESCRIPTION - Range (length) of line2

        ----------------------------
        Required Pre-processing step
        ----------------------------
        Called from self._checkPings()

        -------
        Returns
        -------
        Bool flag indicating if line2 intersects line1

        --------------------
        Next Processing Step
        --------------------
        Returns flag to self._checkPings()
        '''

        #https://stackoverflow.com/questions/20677795/how-do-i-compute-the-intersection-point-of-two-lines
        def line(p1, p2):
            # Find general equation (normal form) coeficients to describe a line
            ## connecting two points: Ay + Bx = C
            A = (p1[1] - p2[1])
            B = (p2[0] - p1[0])
            C = (p1[0]*p2[1] - p2[0]*p1[1])
            return A, B, -C

        def intersection(L1, L2):
            # Following Cramer's rules
            D  = L1[0] * L2[1] - L1[1] * L2[0] # Determinant using x, y values
            Dx = L1[2] * L2[1] - L1[1] * L2[2] # Determinant using x, c values
            Dy = L1[0] * L2[2] - L1[2] * L2[0] # Determinant using y, c values
            if D != 0: # Check if divisor == 0
                x=Dx/D
                y=Dy/D
                return x,y # Coordinate of intersection
            else:
                return False # No intersection found

        def isBetween(line1, line2, c):
            ax, ay = line1[0][0], line1[0][1] # Get x,y for line1
            bx, by = line1[1][0], line2[1][1] # Get x,y for line2
            cx, cy = c[0], c[1] # Get x,y for intersection
            xIntersect=yIntersect=False # Set flags

            # Check if cx,cy falls between either lines coordinates with a small
            ## buffer of +-5.  If it does, we will need to check distance between
            ## line2 origin and (cx,cy).
            if (cx >= min(ax,bx)-5) and (cx <= max(ax,bx)+5) and \
               (cy >= min(ay,by)-5) and (cy <= max(ay,by)+5):
               checkDist = True
            else:
               checkDist = isIntersect = False

            # Check distance between line2 origin and (cx,cy). If the distance is
            ## shorter then the range, then intersecting point falls on line
            ## segments and the two lines do intersect.
            if checkDist is True:
                x,y = line2[0][0], line2[0][1]
                dist = self._getDist(x, y, cx, cy)
                if range < dist:
                    isIntersect = False
                else:
                    isIntersect = True

            return isIntersect

        L1 = line(line1[0], line1[1]) # Get coefficients for line1
        L2 = line(line2[0], line2[1]) # Get coefficients for line1
        c = intersection(L1, L2) # Determine if infinite lines could intersect
        if c is True:
            I = isBetween(line1, line2, c) # Determine if intersect occurs on line segments
        else:
            I = False
        return I
    
    ############################################################################
    # Rectify sonar imagery - Ping-wise (heading)                              #
    ############################################################################

    #===========================================================================
    def _rectSonHeadingMain(self, df: pd.DataFrame, chunk, son=True, heading='instr_heading', interp_dist=50):

        '''
        '''
        start_time = time.time()

        # Calculate the sonar return coordinates
        dfOut = []
        for i, row in df.iterrows():
            dfOut.append(self._calcSonReturnCoords(row, heading))

        dfAll = pd.concat(dfOut)

        t1 = round(time.time() - start_time, ndigits=1)

        # Calculate pixel coordinates
        start_time = time.time()
        # dfAll = self._calcSonReturnPixCoords(dfAll, chunk, son=son)
        dfAll = self._getSonarReturns(dfAll, chunk, son=son)
        t2 = round(time.time() - start_time, ndigits=1)

        # Do rectification
        start_time = time.time()
        self._rectSonHeading(dfAll, chunk, son=son, interpolation_distance=interp_dist)
        t3 = round(time.time() - start_time, ndigits=1)
        # print("Chunk {}: {} - {} - {}".format(chunk, t1, t2, t3))
        # return dfAll
        return
    
    #===========================================================================
    def _calcSonReturnCoords(self, row, heading):

        son_range = 'son_range'
        son_idx = 'son_idx'
        ping_cnt = 'ping_cnt'
        ping_bearing = 'ping_bearing'
        trk_lons = 'trk_lons'
        trk_lats = 'trk_lats'
        lons = 'lon'
        lats = 'lat'
        e = 'e'
        n = 'n'
        record_num = 'record_num'
        chunk_id = 'chunk_id'

        flip = False

        # Make a data frame for the ping
        pingDF = pd.DataFrame()

        # Get necessary values
        # pingDF[son_idx] = range(1, int(row[ping_cnt])+1)
        pingDF[son_idx] = range(0, int(row[ping_cnt]))
        pingDF[record_num] = row[record_num]
        pingDF[chunk_id] = row[chunk_id]

        # pingDF[ping_bearing] = row[ping_bearing]
        pingDF[trk_lons] = row[trk_lons]
        pingDF[trk_lats] = row[trk_lats]

        ########################
        # Calculate ping bearing
        # Determine ping bearing.  Ping bearings are perpendicular to COG.
        if self.beamName == 'ss_port':
            rotate = -90  # Rotate COG by 90 degrees to the left
        else:
            rotate = 90 # Rotate COG by 90 degrees to the right
        if flip: # Flip rotation factor if True
            rotate *= -1

        # Calculate ping bearing and normalize to range 0-360
        pingDF[ping_bearing] = (row[heading]+rotate) % 360

        pix_m = self.pixM # Get pixel size for each chunk

        # Calculate pixel size
        pingDF[son_range] = pingDF[son_idx] * pix_m

        ##################################################
        # Calculate range extent coordinates for each ping
        # Calculate range extent lat/lon using ping bearing and range
        # https://stackoverflow.com/questions/7222382/get-lat-long-given-current-point-distance-and-bearing
        # R = 6371.393*1000 #Radius of the Earth in meters
        # R = 6369.823*1000
        R = 6378137.0 # WGS 1984
        # def _estEarthRadius(lat: float):
        #     '''
        #     Estimate Earth's radius at survey latitude

        #     https://rechneronline.de/earth-radius/
        #     https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html
        #     '''

        #     r1 = 6378.137*1000 # Equitorial radius
        #     r2 = 6356.752*1000 # Polar radius

        #     lat = np.deg2rad(lat) # Convert lat to radians

        #     R = np.sqrt( ( ( r1**2 * np.cos(lat) )**2 + ( r2**2 * np.sin(lat) )**2 ) / ( ( r1 * np.cos(lat) )**2 + ( r2 * np.sin(lat) )**2 ) )

        #     return R

        brng = np.deg2rad(pingDF[ping_bearing]).to_numpy() # Convert ping bearing to radians and store in numpy array
        d = (pingDF[son_range].to_numpy()) # Store range in numpy array

        # Get lat/lon for origin of each ping, convert to numpy array
        lat1 = np.deg2rad(pingDF[trk_lats]).to_numpy()
        lon1 = np.deg2rad(pingDF[trk_lons]).to_numpy()

        # R = _estEarthRadius(lat1[0])

        # Calculate latitude of range extent
        lat2 = np.arcsin( np.sin(lat1) * np.cos(d/R) +
            np.cos(lat1) * np.sin(d/R) * np.cos(brng))

        # Calculate longitude of range extent
        lon2 = lon1 + np.arctan2( np.sin(brng) * np.sin(d/R) * np.cos(lat1),
                                np.cos(d/R) - np.sin(lat1) * np.sin(lat2))

        # Convert range extent coordinates into degrees
        lat2 = np.degrees(lat2)
        lon2 = np.degrees(lon2)

        # Store in dataframe
        pingDF[lons] = lon2
        pingDF[lats] = lat2

        # Calculate easting and northing
        pingDF[e], pingDF[n] = self.trans(pingDF[lons].to_numpy(), pingDF[lats].to_numpy())

        pingDF = pingDF[[chunk_id, record_num, son_idx, lons, lats, e, n, son_range]]

        # Set index to help speed concatenation
        pingDF.set_index([record_num, son_idx], inplace=True)

        return pingDF

    #===========================================================================
    def _calcSonReturnPixCoords(self, df: pd.DataFrame, chunk, son=True, wgs=False):

        '''
        
        '''

        # Use WGS 1984 coordinates and set variables as needed
        if wgs is True:
            epsg = self.humDat['wgs']
            xCoord = 'lon'
            yCoord = 'lat'
        else:
            epsg = self.humDat['epsg']
            xCoord = 'e'
            yCoord = 'n'

        xPix = 'x'
        yPix = 'y'

        df.reset_index(inplace=True)

        #######################################
        # Prepare destination (dst) coordinates
        ## Destination coordinates describe the geographic location in lat/lon
        ## or easting/northing that directly map to the pix coordinates.

        pix_m = self.pixM # Get pixel size

        # Get extent of chunk
        xMin, xMax = df[xCoord].min(), df[xCoord].max()
        yMin, yMax = df[yCoord].min(), df[yCoord].max()

        # Determine output shape dimensions
        outShapeM = [xMax-xMin, yMax-yMin] # Calculate range of x,y coordinates
        outShape=[0,0]
        # Divide by pixel size to arrive at output shape of warped image
        outShape[0], outShape[1] = round(outShapeM[0]/pix_m,0), round(outShapeM[1]/pix_m,0)

        # Rescale destination coordinates
        # X values
        xStd = (df[xCoord]-xMin) / (xMax-xMin) # Standardize
        xScaled = xStd * (outShape[0] - 0) + 0 # Rescale to output shape
        df[xPix] = round(xScaled).astype(int) # Store rescaled x coordinates

        # Y values
        yStd = (df[yCoord]-yMin) / (yMax-yMin) # Standardize
        yScaled = yStd * (outShape[1] - 0) + 0 # Rescale to output shape
        df[yPix] = round(yScaled).astype(int) # Store rescaled y coordinates

        # # Load sonar data
        # df = self._getSonarReturns(df=df, chunk=chunk)

        return df
    
    #===========================================================================
    def _getSonarReturns(self, df: pd.DataFrame, chunk, son=True):

        '''
        
        '''

        df.reset_index(inplace=True)

        record_num = 'record_num'
        son_idx = 'son_idx'

        # Filter sonMetaDF by chunk
        if not hasattr(self, 'sonMetaDF'):
            self._loadSonMeta()

        sonMetaAll = self.sonMetaDF
        isChunk = sonMetaAll['chunk_id']==chunk
        sonMeta = sonMetaAll[isChunk].reset_index()

        # Get sonar data
        if son:
            # Open image to rectify
            self._getScanChunkSingle(chunk)
        else:
            # Rectifying substrate classification
            pass

        # Remove shadows
        if self.remShadow:
            # Get mask
            self._SHW_mask(chunk)

            # Mask out shadows
            self.sonDat = self.sonDat*self.shadowMask
            del self.shadowMask

        # Sort Dataframe and reset index
        df.sort_values(by=[record_num, son_idx], inplace=True)
        df.reset_index(inplace=True, drop=True)

        #####
        # WCP
        if self.rect_wcp:

            dfAll = []
            # egn
            if self.egn:
                self._egn_wcp(chunk, sonMeta)

                if self.egn_stretch > 0:
                    self._egnDoStretch()

            img = self.sonDat.copy()

            # img[0]=0 # To fix extra white on curves

            i = 0
            for idx, group in df.groupby(by=[record_num]):
                sonData = img[:, i]

                if len(sonData) > len(group):
                    sonData = sonData[:len(group)]
                elif len(group) > len(sonData):
                    group = group[:len(sonData)]
                else:
                    pass

                group['son_wcp'] = sonData

                # group = group.dropna()

                dfAll.append(group)            
                
                i += 1

            dfAll = pd.concat(dfAll)

            if self.rect_wcr:
                df = dfAll.copy()

        #####
        # WCR
        if self.rect_wcr:

            dfAll = []

            self._WCR_SRC(sonMeta)

            # Empirical gain normalization
            if not self.rect_wcp:
                if self.egn:
                    self._egn()
                    self.sonDat = np.nan_to_num(self.sonDat, nan=0)

                    if self.egn_stretch > 0:
                        self._egnDoStretch()

            img = self.sonDat.copy()

            # img[0]=0 # To fix extra white on curves

            i = 0
            for _, group in df.groupby(by=[record_num]):
                sonData = img[:, i]

                # group = group[:len(sonData)]

                if len(sonData) > len(group):
                    sonData = sonData[:len(group)]
                elif len(group) > len(sonData):
                    group = group[:len(sonData)]
                else:
                    pass

                group['son_wcr'] = sonData

                # group = group.dropna()

                dfAll.append(group)            
                
                i += 1

            dfAll = pd.concat(dfAll)

        dfAll = self._calcSonReturnPixCoords(dfAll, chunk, son=son)

        # Set index to help speed concatenation
        dfAll.set_index([record_num, son_idx], inplace=True)

        return dfAll
    
    #===========================================================================
    def _rectSonHeading(self, df: pd.DataFrame, chunk, son=True, wgs=False, interpolation_distance=50):

        '''
        
        '''

        pix_res = self.pix_res_son
        do_resize = True
        if pix_res == 0:
            pix_res = self.pixM
            do_resize = False

        if son:
            # Create output directory if it doesn't exist
            outDir = self.outDir # Parent directory
            try:
                os.mkdir(outDir)
            except:
                pass


        # Use WGS 1984 coordinates and set variables as needed
        if wgs is True:
            epsg = self.humDat['wgs']
            xCoord = 'lon'
            yCoord = 'lat'
        else:
            epsg = self.humDat['epsg']
            xCoord = 'e'
            yCoord = 'n'

        xPix = 'x'
        yPix = 'y'

        # Determine leading zeros to match naming convention
        addZero = self._addZero(chunk)

        df.sort_index(ascending=True, inplace=True)

        ###################
        # Get coverage mask
        # covShp = self._getCoverageMask(df, wgs)

        ##################
        # Do Rectification

        pix_m = self.pixM # Get pixel size

        xPixMax, yPixMax = df[xPix].max().astype(int), df[yPix].max().astype(int)

        # Get extent of chunk
        xMin, xMax = df[xCoord].min().astype(int), df[xCoord].max().astype(int)
        yMin, yMax = df[yCoord].min().astype(int), df[yCoord].max().astype(int)

        # Setup outupt array
        # Determine output shape dimensions
        outShapeM = [xMax-xMin, yMax-yMin] # Calculate range of x,y coordinates
        outShape=[0,0]
        # Divide by pixel size to arrive at output shape of warped image
        outShape[0], outShape[1] = round(outShapeM[0]/pix_m,0).astype(int), round(outShapeM[1]/pix_m,0).astype(int)

        # Calculate x,y resolution of a single pixel
        xres = (xMax - xMin) / outShape[0]
        yres = (yMax - yMin) / outShape[1]

        # Calculate transformation matrix by providing geographic coordinates
        ## of upper left corner of the image and the pixel size
        xMin = df[xCoord].min()
        yMax = df[yCoord].max()
        transform = from_origin(xMin - xres/2, yMax - yres/2, xres, yres)

        #########################
        # Create geotiff and save

        to_rect = []

        if self.rect_wcp:
            to_rect.append(('rect_wcp', 'son_wcp'))
        if self.rect_wcr:
            to_rect.append(('rect_wcr', 'son_wcr'))

        for imgOutPrefix, sonCol in to_rect:

            outDir = os.path.join(self.outDir, imgOutPrefix) # Sub-directory

            try:
                os.mkdir(outDir)
            except:
                pass

            # New way below using sparse matrix
            row = df[yPix].to_numpy().astype(int)
            col = df[xPix].to_numpy().astype(int)
            data = df[sonCol].to_numpy()

            # Create a dictionary to store the maximum value for each coordinate
            max_values = {}
            for r, c, d in zip(row, col, data):
                if (r, c) in max_values:
                    max_values[(r, c)] = max(max_values[(r, c)], d)
                else:
                    max_values[(r, c)] = d

            # Convert the dictionary back to arrays
            row = np.array([k[0] for k in max_values.keys()])
            col = np.array([k[1] for k in max_values.keys()])
            data = np.array(list(max_values.values()))

            # Create the sparse matrix
            sonRect = coo_matrix((data, (row, col)), shape=(yPixMax+1, xPixMax+1))
            sonRect = sonRect.toarray()

            # Rotate 180 and flip
            # https://stackoverflow.com/questions/47930428/how-to-rotate-an-array-by-%C2%B1-180-in-an-efficient-way
            sonRect = np.flip(np.flip(np.flip(sonRect,1),0),1).astype('float')

            ##########
            # Fill Gaps
            if interpolation_distance > 0:
                # First pad sonRect with 0's (helps with masking) by interpolation_distance
                sonRect = np.pad(sonRect, (interpolation_distance, ), mode='constant', constant_values=0)

                # Replace 0 values with NaN
                sonRect[sonRect == 0] = np.nan

                # Prepare data for interpolation
                x = np.arange(sonRect.shape[1])
                y = np.arange(sonRect.shape[0])
                xx, yy = np.meshgrid(x, y)

                # Mask for valid values
                mask = ~np.isnan(sonRect)

                # Coordinates of valid values
                valid_coords = np.array([yy[mask], xx[mask]]).T

                # Values of valid points
                valid_values = sonRect[mask]

                # Create a KDTree for fast lookup of nearest neighbors
                tree = cKDTree(valid_coords)

                # Mask for points within the interpolation distance
                distances, _ = tree.query(np.c_[yy.ravel(), xx.ravel()], distance_upper_bound=interpolation_distance)
                distance_mask = distances.reshape(sonRect.shape) <= interpolation_distance

                # Try erroding the mask....IT WORKS!!!!
                # https://forum.image.sc/t/shrink-labeled-regions/50443
                distance_mask = distance_mask.astype('uint8')
                distance_mask = self._erode_labels(distance_mask, interpolation_distance)

                # Much faster - Create interpolator using only valid points
                interpolated_values = griddata(valid_coords, valid_values, (yy, xx), method='linear')
                # interpolated_values[np.isnan(interpolated_values)] = sonRect[np.isnan(interpolated_values)]

                # Apply distance mask
                sonRect = interpolated_values * distance_mask

                # Get sonRect back to original dims
                sonRect = sonRect[interpolation_distance-1:-interpolation_distance+1, interpolation_distance-1:-interpolation_distance+1]

                sonRect = sonRect.astype('uint8')


            ###############
            # Create output

            projName = os.path.split(self.projDir)[-1] # Get project name
            beamName = self.beamName # Determine which sonar beam we are working with
            imgName = projName+'_'+imgOutPrefix+'_'+beamName+'_'+addZero+str(int(chunk))+'.tif' # Create output image name

            gtiff = os.path.join(outDir, imgName) # Output file name

            if do_resize:
                gtiff = gtiff.replace('.tif', 'temp.tif')

            if son:
                colormap = self.son_colorMap
            else:
                # colormap = class_colormap
                pass
            with rasterio.open(
                gtiff,
                'w',
                driver='GTiff',
                height=sonRect.shape[0],
                width=sonRect.shape[1],
                count=1,
                dtype=sonRect.dtype,
                crs=epsg,
                transform=transform,
                compress='lzw',
                resampling=Resampling.bilinear
                ) as dst:
                    dst.nodata=0
                    dst.write_colormap(1, colormap)
                    dst.write(sonRect,1)
                    dst=None

            del dst

            #############
            # Do resizing
            if do_resize:
                self._pixresResize(gtiff)

        return df


    #===========================================================================
    def _getCoverageMask(self, df: pd.DataFrame, wgs):
        '''
        '''

        filter = int(self.nchunk*0.1)

        # Use WGS 1984 coordinates and set variables as needed
        if wgs is True:
            epsg = self.humDat['wgs']
            xCoord = 'lon'
            yCoord = 'lat'
        else:
            epsg = self.humDat['epsg']
            xCoord = 'e'
            yCoord = 'n'

        trk_x = []
        trk_y = []
        rng_x = []
        rng_y = []

        

        # df is already sorted by record_num and son_idx
        # iterate through each record_num

        i = 0
        for name, group in df.groupby(level=['record_num']):
            
            # Trackline coordinate is first row
            trk = group.iloc[0]
            trk_x.append(trk[xCoord])
            trk_y.append(trk[yCoord])

            # Range extent coordinate is last row
            rng = group.iloc[-1]
            rng_x.append(rng[xCoord])
            rng_y.append(rng[yCoord])

            i += 1

        trk_x = np.array(trk_x)
        trk_y = np.array(trk_y)
        rng_x = np.array(rng_x)
        rng_y = np.array(rng_y)

        # Get Zu values for interpolation
        t = np.arange(0, i).astype(float)

        # Attempt to fix error
        # https://stackoverflow.com/questions/47948453/scipy-interpolate-splprep-error-invalid-inputs
        okay = np.where(np.abs(np.diff(rng_x))+np.abs(np.diff(rng_y))>0)
        x = np.r_[rng_x[okay], rng_x[-1]]
        y = np.r_[rng_y[okay], rng_y[-1]]
        t = np.r_[t[okay], t[-1]]

        # Interpolate
        tck, _ = splprep([x,y], u=t, k=3, s=0)
        x_interp, y_interp = splev(t, tck)

        # Put lists together
        x = trk_x.tolist() + x_interp.tolist()[::-1][::filter]
        y = trk_y.tolist() + y_interp.tolist()[::-1][::filter]

        # Create polygon from points
        chunk_geom = Polygon(zip(x, y))
        chunk_geom = gpd.GeoDataFrame(index=[1], crs=epsg, geometry=[chunk_geom])

        # Buffer to fix funky stuff
        bufDist = 10
        buf = chunk_geom.buffer(bufDist)
        bufDist *= -1
        buf = buf.buffer(bufDist, join_style='mitre')

        chunk_geom = gpd.GeoDataFrame(geometry=buf, crs=chunk_geom.crs)

        # # Save to shapefile
        # beam = self.beamName
        # projName = os.path.basename(self.projDir)
        # outFile = os.path.join(self.metaDir, projName+"_"+beam+"_coverage.shp")
        # chunk_geom.to_file(outFile)

        # # try linestring
        # rng_line = LineString(zip(x_interp, y_interp))
        # rng_line = gpd.GeoDataFrame(index=[1], crs=epsg, geometry=[rng_line])

        # outFile = outFile.replace('coverage', 'range')
        # rng_line.to_file(outFile)

        # trk_line = LineString(zip(trk_x, trk_y))
        # trk_line = gpd.GeoDataFrame(index=[1], crs=epsg, geometry=[trk_line])

        # outFile = outFile.replace('range', 'trk')
        # trk_line.to_file(outFile)

        return chunk_geom

    #===========================================================================
    def _erode_labels(self, segmentation, erosion_iterations):
        # create empty list where the eroded masks can be saved to
        list_of_eroded_masks = list()
        regions = regionprops(segmentation)
        def erode_mask(segmentation_labels, label_id, erosion_iterations):
            
            only_current_label_id = np.where(segmentation_labels == label_id, 1, 0)
            eroded = ndimage.binary_erosion(only_current_label_id, iterations = erosion_iterations)
            relabeled_eroded = np.where(eroded == 1, label_id, 0)
            return(relabeled_eroded)

        for i in range(len(regions)):
            label_id = regions[i].label
            list_of_eroded_masks.append(erode_mask(segmentation, label_id, erosion_iterations))

        # convert list of numpy arrays to stacked numpy array
        final_array = np.stack(list_of_eroded_masks)

        # max_IP to reduce the stack of arrays, each containing one labelled region, to a single 2D np array. 
        final_array_labelled = np.sum(final_array, axis = 0)
        return(final_array_labelled)

    ############################################################################
    # Export Trackline and Coverage shapefiles                                 #
    ############################################################################

    def _exportTrkShp(self,
                      wgs=False,
                      ):
        
        '''
        
        '''

        # Create output directory if it doesn't exist
        outDir = os.path.join(self.metaDir, 'shapefiles')
        try:
            os.mkdir(outDir)
        except:
            pass

        # Get trackline/range extent file path
        trkMetaFile = os.path.join(self.metaDir, "Trackline_Smth_"+self.beamName+".csv")

        # Use WGS 1984 coordinates and set variables as needed
        if wgs is True:
            epsg = self.humDat['wgs']
            xRange = 'range_lons'
            yRange = 'range_lats'
            xTrk = 'trk_lons'
            yTrk = 'trk_lats'
        ## Use projected coordinates and set variables as needed
        else:
            epsg = self.humDat['epsg']
            xRange = 'range_es'
            yRange = 'range_ns'
            xTrk = 'trk_utm_es'
            yTrk = 'trk_utm_ns'

        # Open smoothed trackline/range extent file
        trkMeta = pd.read_csv(trkMetaFile)

        # Create geodataframe
        gdf = gpd.GeoDataFrame(
            trkMeta, geometry=gpd.points_from_xy(trkMeta[xTrk], trkMeta[yTrk], crs=epsg)
        )
        del trkMeta

        # Save to shp
        trkMetaShp = os.path.basename(trkMetaFile).replace('csv', 'shp')
        trkMetaShp = os.path.join(outDir, trkMetaShp)
        gdf.to_file(trkMetaShp)
        del trkMetaFile        

        return
    
    #===========================================================================
    def _exportCovShp(self,
                      dissolve=False,
                      filt=10,
                      wgs=False
                      ):
        
        beam = self.beamName
        
        # Create output directory if it doesn't exist
        outDir = os.path.join(self.metaDir, 'shapefiles')
        try:
            os.mkdir(outDir)
        except:
            pass

        # Use WGS 1984 coordinates and set variables as needed
        if wgs is True:
            epsg = self.humDat['wgs']
            xRange = 'range_lons'
            yRange = 'range_lats'
            xTrk = 'trk_lons'
            yTrk = 'trk_lats'
        ## Use projected coordinates and set variables as needed
        else:
            epsg = self.humDat['epsg']
            xRange = 'range_es'
            yRange = 'range_ns'
            xTrk = 'trk_utm_es'
            yTrk = 'trk_utm_ns'

        # max chunks
        chunkMax = self.chunkMax

        # Get df's
        # df1 = pd.read_csv(covFiles[0])
        # df2 = pd.read_csv(covFiles[1])

        # # Filter
        # if filt > 0:
        #     df1 = df1[::filt]
        #     df2 = df2[::filt]

        # dfs = [df1, df2]

        df1 = pd.read_csv(self.smthTrkFile)
        dfs = [df1]

        filt = 0

        # Iterate chunks
        for chunk in range(0, chunkMax+1):
            # Iterate dfs
            for df in dfs:
                # Get chunk
                isChunk = df['chunk_id'] == chunk
                df = df[isChunk].reset_index()

                # Get last row
                dfLast = df.iloc[-1]

                if filt > 0:
                    df = df[::filt]
                    df = pd.concat([df, dfLast])

                # if 'lat_list' not in locals():
                #     lat_list = df[yRange].tolist()
                #     lon_list = df[xRange].tolist()
                # else:
                #     lat_list += df[yRange].tolist()[::-1] #reverse order
                #     lon_list += df[xRange].tolist()[::-1]

                lat_list = df[yRange].tolist()
                lon_list = df[xRange].tolist()

                lat_list += df[yTrk].tolist()[::-1]
                lon_list += df[xTrk].tolist()[::-1]

                del df

            # Create polygon from points
            chunk_geom = Polygon(zip(lon_list, lat_list))
            chunk_geom = gpd.GeoDataFrame(index=[chunk], crs=epsg, geometry=[chunk_geom])
            del lat_list, lon_list

            # # Do buffer to help fix geometry issues
            # chunk_geom['geometry'] = chunk_geom.buffer(10, join_style=2)
            # chunk_geom['geometry'] = chunk_geom.buffer(-10, join_style=2)


            # Append to final geodataframe
            if 'gdf' not in locals():
                gdf = chunk_geom.copy()
            else:
                gdf = pd.concat([gdf, chunk_geom])
            del chunk_geom

        gdf['chunk_id'] = gdf.index

        # gdf['geometry'] = gdf.buffer(10, join_style=2)

        if dissolve:
            try:
                gdf = gdf.dissolve()
            except:
                gdf = gdf.loc[gdf.geometry.is_valid]
                gdf = gdf.dissolve()

        # gdf['geometry'] = gdf.buffer(-10, join_style=2)

        # Save to shapefile
        projName = os.path.basename(self.projDir)
        outFile = os.path.join(self.metaDir, 'shapefiles', projName+"_"+beam+"_coverage.shp")
        gdf.to_file(outFile)
        del gdf

        return
            
    ############################################################################
    # Rectify sonar imagery - Rubbersheeting                                   #
    ############################################################################

    def _rectSonRubber(self,
                       chunk,
                       filt=50,
                       cog=True,
                       wgs=False,
                       son=True):
        '''
        This function will georectify sonar tiles with water column present
        (rect_wcp) OR water column removed and slant range corrected (rect_wcr).
        Sonar intensity will be loaded directly from the .SON file. Once
        determined, each chunk will be iterated, sonar intensities loaded into
        memory and:
        1) Pixel (pix) coordinates are formated as a numpy array based on shape
           of sonar chunk.  Coordinates are filtered to aid computation efficiency.
        2) Geographic, or destination (dst), coordinates for the smoothed trackline
           and range extent are loaded from the "Trackline_Smth_BXXX.csv" file and
           formated as a numpy array and filtered as pix.
        3) A Piecewise Affine Transform is used to map pix coordinates to the shape
           of the dst coordinates in order to warp (or rectify) the sonar intensities.
           Warped sonar intensities are stored in a new numpy array.
        4) The warped array is then mapped to geographic coordinates using a
           transformation matrix and exported as a geotiff.

        ----------
        Parameters
        ----------
        remWater : bool
            DESCRIPTION - Flag indicating if wcp [False] or pix [True] imagery.
        filt : int
            DESCRIPTION - Every `filt` ping will be used to fit a spline.
        wgs : bool
            DESCRIPTION - Flag indicating if sonar images should be rectified using
                          WGS 1984 coordinate system [True] or UTM state plane [False]

        ----------------------------
        Required Pre-processing step
        ----------------------------
        self._getRangeCoords()

        -------
        Returns
        -------
        Georectified geotiffs

        --------------------
        Next Processing Step
        --------------------
        NA
        '''
        filterIntensity = False
        pix_res = self.pix_res_son
        do_resize = True
        if pix_res == 0:
            pix_res = self.pixM
            do_resize = False

        if son:
            # Create output directory if it doesn't exist
            outDir = self.outDir # Parent directory
            try:
                os.mkdir(outDir)
            except:
                pass

        # Get trackline/range extent file path
        trkMetaFile = os.path.join(self.metaDir, "Trackline_Smth_"+self.beamName+".csv")

        # Use WGS 1984 coordinates and set variables as needed
        if wgs is True:
            epsg = self.humDat['wgs']
            xRange = 'range_lons'
            yRange = 'range_lats'
            xTrk = 'trk_lons'
            yTrk = 'trk_lats'
        ## Use projected coordinates and set variables as needed
        else:
            epsg = self.humDat['epsg']
            xRange = 'range_es'
            yRange = 'range_ns'
            xTrk = 'trk_utm_es'
            yTrk = 'trk_utm_ns'

        # # Determine leading zeros to match naming convention
        addZero = self._addZero(chunk)

        #################################
        # Prepare pixel (pix) coordinates
        ## Pix coordinates describe the size of the coordinates in pixel
        ## coordinates (top left of image == (0,0); top right == (0,nchunk)...)

        # Filter sonMetaDF by chunk
        if not hasattr(self, 'sonMetaDF'):
            self._loadSonMeta()

        sonMetaAll = self.sonMetaDF
        if cog:
            isChunk = sonMetaAll['chunk_id']==chunk
        else:
            isChunk = sonMetaAll['chunk_id_2']==chunk
            # next = sonMetaAll['chunk_id_2']==(chunk+1)
            # isChunk = pd.concat([isChunk, next], ignore_index=True)
            isChunk.iloc[chunk+1] = True

        sonMeta = sonMetaAll[isChunk].reset_index()

        # Update class attributes based on current chunk
        self.pingMax = np.nanmax(sonMeta['ping_cnt']) # store to determine max range per chunk
        self.headIdx = sonMeta['index'] # store byte offset per ping
        self.pingCnt = sonMeta['ping_cnt'] # store ping count per ping

        if son:
            # Open image to rectify
            self._getScanChunkSingle(chunk, cog)
        else:
            # Rectifying substrate classification
            pass

        # Remove shadows
        if self.remShadow:
            # Get mask
            self._SHW_mask(chunk)

            # Mask out shadows
            self.sonDat = self.sonDat*self.shadowMask
            del self.shadowMask

        img = self.sonDat
        # if not cog:
        #     # Zero out second ping
        #     img[:,1] = 0

        # For each ping, we need the pixel coordinates where the sonar
        ## originates on the trackline, and where it terminates based on the
        ## range of the ping.  This results in an array of coordinate
        ## pairs that describe the edge of the non-rectified image tile.
        rows, cols = img.shape[0], img.shape[1] # Determine number rows/cols
        pix_cols = np.arange(0, cols) # Create array of column indices
        pix_rows = np.linspace(0, rows, 2).astype('int') # Create array of two row indices (0 for points at ping origin, `rows` for max range)
        pix_rows, pix_cols = np.meshgrid(pix_rows, pix_cols) # Create grid arrays that we can stack together
        pixAll = np.dstack([pix_rows.flat, pix_cols.flat])[0] # Stack arrays to get final map of pix pixel coordinats [[row1, col1], [row2, col1], [row1, col2], [row2, col2]...]

        # Create mask for filtering array. This makes fitting PiecewiseAffineTransform
        ## more efficient
        mask = np.zeros(len(pixAll), dtype=bool) # Create mask same size as pixAll
        if cog:
            mask[0::filt] = 1 # Filter row coordinates
            mask[1::filt] = 1 # Filter column coordinates
            mask[-2], mask[-1] = 1, 1 # Make sure we keep last row/col coordinates
        else:
            mask[:] = 1

        # Filter pix
        pix = pixAll[mask]

        #######################################
        # Prepare destination (dst) coordinates
        ## Destination coordinates describe the geographic location in lat/lon
        ## or easting/northing that directly map to the pix coordinates.

        # Open smoothed trackline/range extent file
        trkMeta = pd.read_csv(trkMetaFile)
        if cog:
            trkMeta = trkMeta[trkMeta['chunk_id']==chunk].reset_index(drop=False) # Filter df by chunk_id
        else:
            # trkMeta = trkMeta[trkMeta['chunk_id_2']==chunk].reset_index(drop=False)
            # next = trkMeta[trkMeta['chunk_id_2']==chunk+1].reset_index(drop=False)
            # trkMeta = pd.concat([trkMeta, next], ignore_index=True)
            isChunk = trkMeta['chunk_id_2']==chunk
            isChunk.iloc[chunk+1] = True
            trkMeta = trkMeta[isChunk].reset_index(drop=False)

        pix_m = self.pixM # Get pixel size

        # Get range (outer extent) coordinates [xR, yR] to transposed numpy arrays
        xR, yR = trkMeta[xRange].to_numpy().T, trkMeta[yRange].to_numpy().T
        xyR = np.vstack((xR, yR)).T # Stack the arrays

        # Get trackline (origin of ping) coordinates [xT, yT] to transposed numpy arrays
        xT, yT = trkMeta[xTrk].to_numpy().T, trkMeta[yTrk].to_numpy().T
        xyT = np.vstack((xT, yT)).T # Stack the  arrays
        del trkMeta

        # Stack the coordinates (range[0,0], trk[0,0], range[1,1]...) following
        ## pattern of pix coordinates
        dstAll = np.empty([len(xyR)+len(xyT), 2]) # Initialize appropriately sized np array
        dstAll[0::2] = xyT # Add trackline coordinates
        dstAll[1::2] = xyR # Add range extent coordinates

        # Filter dst using previously made mask
        dst = dstAll[mask]
        del mask

        ##################
        ## Before applying a geographic projection to the image, the image
        ## must be warped to conform to the shape specified by the geographic
        ## coordinates.  We don't want to warp the image to real-world dimensions,
        ## so we will normalize and rescale the dst coordinates to give the
        ## top-left coordinate a value of (0,0)

        # Determine min/max for rescaling
        xMin, xMax = dst[:,0].min(), dst[:,0].max() # Min/Max of x coordinates
        yMin, yMax = dst[:,1].min(), dst[:,1].max() # Min/Max of y coordinates

        # Determine output shape dimensions
        outShapeM = [xMax-xMin, yMax-yMin] # Calculate range of x,y coordinates
        outShape=[0,0]
        # Divide by pixel size to arrive at output shape of warped image
        outShape[0], outShape[1] = round(outShapeM[0]/pix_m,0), round(outShapeM[1]/pix_m,0)

        # Rescale destination coordinates
        # X values
        xStd = (dst[:,0]-xMin) / (xMax-xMin) # Standardize
        xScaled = xStd * (outShape[0] - 0) + 0 # Rescale to output shape
        dst[:,0] = xScaled # Store rescaled x coordinates

        # Y values
        yStd = (dst[:,1]-yMin) / (yMax-yMin) # Standardize
        yScaled = yStd * (outShape[1] - 0) + 0 # Rescale to output shape
        dst[:,1] = yScaled # Store rescaled y coordinates

        ########################
        # Perform transformation
        # PiecewiseAffineTransform
        # tform = PiecewiseAffineTransform()
        tform = FastPiecewiseAffineTransform() # Huge speedup! From: https://github.com/scikit-image/scikit-image/issues/6864
        tform.estimate(pix, dst) # Calculate H matrix

        ##############
        # Save Geotiff
        ## In order to visualize the warped image in a GIS at the appropriate
        ## spatial extent, the pixel coordinates of the warped image must be
        ## mapped to spatial coordinates. This is accomplished by calculating
        ## the transformation matrix using rasterio.transform.from_origin

        # First get the min/max values for x,y geospatial coordinates
        xMin, xMax = dstAll[:,0].min(), dstAll[:,0].max()
        yMin, yMax = dstAll[:,1].min(), dstAll[:,1].max()

        # Calculate x,y resolution of a single pixel
        xres = (xMax - xMin) / outShape[0]
        yres = (yMax - yMin) / outShape[1]

        # Calculate transformation matrix by providing geographic coordinates
        ## of upper left corner of the image and the pixel size
        transform = from_origin(xMin - xres/2, yMax - yres/2, xres, yres)

        if self.rect_wcp:
            imgOutPrefix = 'rect_wcp'
            outDir = os.path.join(self.outDir, imgOutPrefix) # Sub-directory

            try:
                os.mkdir(outDir)
            except:
                pass

            # egn
            if self.egn:
                self._egn_wcp(chunk, sonMeta)

                if self.egn_stretch > 0:
                    self._egnDoStretch()

            img = self.sonDat.copy()

            img[0]=0 # To fix extra white on curves

            # Warp image from the input shape to output shape
            out = warp(img.T,
                       tform.inverse,
                       output_shape=(outShape[1], outShape[0]),
                       mode='constant',
                       cval=np.nan,
                       clip=False,
                       preserve_range=True)

            # Rotate 180 and flip
            # https://stackoverflow.com/questions/47930428/how-to-rotate-an-array-by-%C2%B1-180-in-an-efficient-way
            out = np.flip(np.flip(np.flip(out,1),0),1).astype('uint8')

            projName = os.path.split(self.projDir)[-1] # Get project name
            beamName = self.beamName # Determine which sonar beam we are working with
            imgName = projName+'_'+imgOutPrefix+'_'+beamName+'_'+addZero+str(int(chunk))+'.tif' # Create output image name

            gtiff = os.path.join(outDir, imgName) # Output file name

            if do_resize:
                gtiff = gtiff.replace('.tif', 'temp.tif')

            # Export georectified image
            with rasterio.open(
                gtiff,
                'w',
                driver='GTiff',
                height=out.shape[0],
                width=out.shape[1],
                count=1,
                dtype=out.dtype,
                crs=epsg,
                transform=transform,
                compress='lzw'
                ) as dst:
                    dst.nodata=0
                    dst.write_colormap(1, self.son_colorMap)
                    dst.write(out,1)
                    dst=None

            del out, dst, img

            if do_resize:
                self._pixresResize(gtiff)

        if self.rect_wcr:
            if son:
                imgOutPrefix = 'rect_wcr'
                outDir = os.path.join(self.outDir, imgOutPrefix) # Sub-directory
            else:
                imgOutPrefix = 'map_substrate_{}'.format(self.beamName)

            if son:
                try:
                    os.mkdir(outDir)
                except:
                    pass

            self._WCR_SRC(sonMeta)

            # Empirical gain normalization
            if not self.rect_wcp:
                if self.egn:
                    self._egn()
                    self.sonDat = np.nan_to_num(self.sonDat, nan=0)

                    if self.egn_stretch > 0:
                        self._egnDoStretch()

            img = self.sonDat

            img[0]=0 # To fix extra white on curves

            # Warp image from the input shape to output shape
            out = warp(img.T,
                       tform.inverse,
                       output_shape=(outShape[1], outShape[0]),
                       mode='constant',
                       cval=np.nan,
                       clip=False,
                       preserve_range=True)

            del img, self.sonDat

            # Warping substrate classification adds anomlies which must be removed
            if not son:
                # Set minSize
                min_size = int((out.shape[0] + out.shape[1])/2)

                # Set nan's to zero
                out = np.nan_to_num(out, nan=0)#.astype('uint8')

                # Label all regions
                lbl = label(out)

                # First set small objects to background value (0)
                noSmall = remove_small_objects(lbl, min_size)

                # Punch holes in original label
                holes = ~(noSmall==0)

                l = (out*holes).astype('uint8')

                del holes, lbl

                # Remove small holes
                # Convert l to binary
                binary_objects = l.astype(bool)
                # Remove the holes
                binary_filled = remove_small_holes(binary_objects, min_size+100)
                # Recover classification with holes filled
                out = watershed(binary_filled, l, mask=binary_filled)

                out = out.astype('uint8')
                del binary_filled, binary_objects, l

                # Prepare colors
                class_colormap = {0: '#3366CC',
                                1: '#DC3912',
                                2: '#FF9900',
                                3: '#109618',
                                4: '#990099', 
                                5: '#0099C6',
                                6: '#DD4477',
                                7: '#66AA00',
                                8: '#B82E2E'}
                
                for k, v in class_colormap.items():
                    rgb = ImageColor.getcolor(v, 'RGB')
                    class_colormap[k] = rgb

            # Rotate 180 and flip
            # https://stackoverflow.com/questions/47930428/how-to-rotate-an-array-by-%C2%B1-180-in-an-efficient-way
            out = np.flip(np.flip(np.flip(out,1),0),1).astype('uint8')

            if son:
                projName = os.path.split(self.projDir)[-1] # Get project name
                beamName = self.beamName # Determine which sonar beam we are working with
                imgName = projName+'_'+imgOutPrefix+'_'+beamName+'_'+addZero+str(int(chunk))+'.tif' # Create output image name
                gtiff = os.path.join(outDir, imgName) # Output file name
            else:
                # Set output name
                projName = os.path.split(self.projDir)[-1] # Get project name
                imgName = projName+'_'+imgOutPrefix+'_'+addZero+str(int(chunk))+'.tif'
                gtiff = os.path.join(self.outDir, imgName)

            if do_resize:
                gtiff = gtiff.replace('.tif', 'temp.tif')

            # Export georectified image
            if son:
                colormap = self.son_colorMap
            else:
                colormap = class_colormap
            with rasterio.open(
                gtiff,
                'w',
                driver='GTiff',
                height=out.shape[0],
                width=out.shape[1],
                count=1,
                dtype=out.dtype,
                crs=epsg,
                transform=transform,
                compress='lzw',
                resampling=Resampling.bilinear
                ) as dst:
                    dst.nodata=0
                    dst.write_colormap(1, colormap)
                    dst.write(out,1)
                    dst=None

            del out, dst

            if do_resize:
                self._pixresResize(gtiff)

        gc.collect()

        # DON"T RETURN SELF
        # Unnecessary here and leads to massive memory leaks
        # Also very slow

        return

    #===========================================================================
    def _getSonColorMap(self, name):
        '''
        '''

        son_colorMap = {}
        try:
            color = colormaps.get_cmap(name)            
        except:
            print('****WARNING*****\n', name, 'is not a valid colormap.\nSetting to Greys...')
            color = colormaps.get_cmap('Greys_r')

        # need to get values for 0-255 but test_color in 0-1
        color = color(np.linspace(0, 1, 256))
        color = rescale(color, 0, 255).astype('uint8')

        vals = range(0, 255)
        for i,v in zip(vals, (color)):
            son_colorMap[i] = tuple(v)

        self.son_colorMap = son_colorMap
        del son_colorMap, color
        return
    
    #===========================================================================
    def _pixresResize(self, f, son=True):
        '''
        Resize x,y pixel resolution
        '''

        # Get pixel resolution
        if son:
            pix_res = self.pix_res_son
        elif not son:
            pix_res = self.pix_res_map

        # Set output name
        f_out = f.replace('temp.tif', '.tif')

        # Reopen f and warp to pix_res
        t = gdal.Warp(f_out, f, xRes = pix_res, yRes = pix_res, targetAlignedPixels=True)

        t = None
        
        try:
            os.remove(f)
        except:
            pass

        return

    #===========================================================================
    def _getTiffAttributes(self, tif):

        # Open tif
        t = gdal.Open(tif)

        # Get Attributes
        bandCount = t.RasterCount

        band = t.GetRasterBand(1)
        bandDtype = gdal.GetDataTypeName(band.DataType)
        nodataVal = band.GetNoDataValue()

        t = None

        return bandCount, bandDtype, nodataVal