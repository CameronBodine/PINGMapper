
from funcs_common import *
from c_sonObj import sonObj
from scipy.interpolate import splprep, splev
from skimage.transform import PiecewiseAffineTransform, warp
from rasterio.transform import from_origin
from rasterio.enums import Resampling
from PIL import Image

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
        Smooths 'noisy' sonar record trackpoints by completing the following:
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
        dfOrig : DataFrame
            DESCRIPTION - Pandas dataframe with geographic coordinates of sonar
                          records.  If `None`, a copy of `df` will be used.
        dropDup : bool
            DESCRIPTION - Flag indicating if coincident coordinates will be dropped.
        xlon : str
            DESCRIPTION - DataFrame column name for longitude coordinates.
        ylat : str
            DESCRIPTION - DataFrame column name for latitude coordinates.
        xutm : str
            DESCRIPTION - DataFrame column name for easting coordinates.
        yutm : str
            DESCRIPTION - DataFrame column name for northing coordinates.
        zU : str
            DESCRIPTION - DataFrame column name used to reinterpolate coordinates
                          along spline (i.e. determines spacing between coordinates)
        filt : int
            DESCRIPTION - Every `filt` sonar record will be used to fit a spline.
        deg : int
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
        if filt>0:
            lastRow = df.iloc[-1].to_dict() # Store last sonar record
            try:
                dfFilt = df.iloc[::filt].reset_index(drop=False) # Get every 'filt' sonar record.  Keep df index column.
            except:
                dfFilt = df.iloc[::filt].reset_index(drop=True) # Get every 'filt' sonar record.  Drop df index column.
            dfFilt = dfFilt.append(lastRow, ignore_index=True) # Add last sonar record to filtered df
        else:
            dfFilt = df.reset_index(drop=False) # Don't filter df

        # Try smoothing trackline
        x=dfFilt[xlon].to_numpy() # Store longitude coordinates in numpy array
        y=dfFilt[ylat].to_numpy() # Store latitude coordinates in numpy array
        if dups is True:
            # Force unique zU value by multiplying time ellapsed and record number
            t = dfFilt[zU].to_numpy() * dfFilt['record_num'].to_numpy()
            u_interp = dfOrig[zU].to_numpy() * dfOrig['record_num'].to_numpy()
        else:
            t=dfFilt[zU].to_numpy() # Store parameter values in numpy array.  Used to space points along spline.
            u_interp = dfOrig[zU].to_numpy() # Get all time ellapsed OR record number values from unfilterd df

        # Attempt to fix error
        # https://stackoverflow.com/questions/47948453/scipy-interpolate-splprep-error-invalid-inputs
        okay = np.where(np.abs(np.diff(x))+np.abs(np.diff(y))>0)
        x = np.r_[x[okay], x[-1]]
        y = np.r_[y[okay], y[-1]]
        t = np.r_[t[okay], t[-1]]

        # Check if enough points to interpolate
        # If not, too many overlapping pings
        if len(x) <= deg:
            return dfOrig[['chunk_id', 'record_num', 'ping_cnt', 'time_s', 'pix_m']]

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

        # u_interp = dfOrig[zU].to_numpy() # Get all time ellapsed OR record number values from unfilterd df
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
                  'pix_m': dfOrig['pix_m'],
                  lons: x_interp[0],
                  lats: x_interp[1]}

        sDF = pd.DataFrame(smooth) # Convert dictionary to Pandas df

        # Calculate smoothed easting/northing
        e_smth, n_smth = self.trans(sDF[lons].to_numpy(), sDF[lats].to_numpy())
        # Store in df
        sDF[es] = e_smth
        sDF[ns] = n_smth

        # Calculate COG (course over ground; i.e. heading) from smoothed lat/lon
        brng = self._getBearing(sDF, lons, lats)
        # self._getBearing() returns n-1 values because last sonar record can't
        ## have a COG value.  We will duplicate the last COG value and use it for
        ## the last sonar record.
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
        lon : str
            DESCRIPTION - DataFrame column name for longitude coordinates.
        lat : str
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
    # Calculate range extent coordinates                                       #
    ############################################################################

    #===========================================
    def _getRangeCoords(self,
                        flip = False,
                        filt = 25):
        '''
        Humminbird SSS store one set geographic coordinates where each sonar record
        orriginates from (assuming GPS is located directly above sonar transducer).
        In order to georectify the sonar imagery, we need to know geographically
        where each sonar record terminates.  The range (distance, length) of each
        sonar record is not stored in the Humminbird recording, so we estimate
        the size of one ping return (estimated previously in self._getPixSize)
        and multiply by the number of ping returns for each sonar record to
        estimate the range.  Range coordinates for each sonar record are then
        estimated using the range of each sonar record, the coordinates where the
        sonar record originated, and the COG.

        A spline is then fit to filtered range coordinates, the same as the trackpoints,
        to help ensure no pings overlapm, resulting in higher quality sonar imagery.

        ----------
        Parameters
        ----------
        flip : bool
            DESCRIPTION - Flip port and starboard sonar channels (if transducer
                          was facing backwards duing survey).
        filt : int
            DESCRIPTION - Every `filt` sonar record will be used to fit a spline.

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
        range = 'range'
        chunk_id = 'chunk_id'

        self._loadSonMeta() # Load sonar record metadata
        sonMetaDF = self.sonMetaDF

        # Get smoothed trackline
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
        sDF[ping_bearing] = (sDF['cog']+rotate) % 360

        ############################################
        # Calculate range (in meters) for each chunk
        # Calculate max range for each chunk to ensure none of the sonar image
        ## is cut off due to changing the range setting during the survey.
        chunk = sDF.groupby(chunk_id) # Group dataframe by chunk_id
        maxPing = chunk[ping_cnt].max() # Find max ping count for each chunk
        pix_m = chunk['pix_m'].min() # Get pixel size for each chunk
        for i in maxPing.index: # Calculate range (in meters) for each chunk
            sDF.loc[sDF[chunk_id]==i, range] = maxPing[i]*pix_m[i]

        ##################################################
        # Calculate range extent coordinates for each ping
        # Calculate range extent lat/lon using ping bearing and range
        # https://stackoverflow.com/questions/7222382/get-lat-long-given-current-point-distance-and-bearing
        R = 6371.393*1000 #Radius of the Earth in meters
        brng = np.deg2rad(sDF[ping_bearing]).to_numpy() # Convert ping bearing to radians and store in numpy array
        d = (sDF[range].to_numpy()) # Store range in numpy array

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
        self._interpRangeCoords(filt)
        return self

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
        filt : int
            DESCRIPTION - Every `filt` sonar record will be used to fit a spline.

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
            last = chunkDF.iloc[-1].copy()
            #####
            # Tried to add variable chunk size to fix rectification issues,
            ## but didn't fix and added new issues
            # filt = int(len(chunkDF.index)*0.1)
            # if filt != 0:
            #     chunkDF = chunkDF.iloc[::filt]
            #####
            chunkDF = chunkDF.iloc[::filt]
            chunkDF = chunkDF.append(last, ignore_index=True)

            idx = chunkDF.index.tolist() # Store sonar record index in list
            maxIdx = max(idx) # Find last record index value

            drop = np.empty((len(chunkDF)), dtype=bool) # Bool numpy array to flag which sonar records overlap and should be dropped
            drop[:] = False # Prepopulate array w/ `False` (i.e. False==don't drop)

            #########################################
            # Find and drop overlapping sonar records
            for i in idx: # Iterate each sonar record if filtered dataframe
                if i == maxIdx: # Break loop once we reach the last sonar record
                    break
                else:
                    if drop[i] != True: # If current sonar record flagged to drop, don't need to check it
                        dropping = self._checkPings(i, chunkDF) # Find subsequent sonar records that overlap current record
                        if maxIdx in dropping.keys(): # Make sure we don't drop last sonar record in chunk
                            del dropping[maxIdx]
                            dropping[i]=True # Drop current sonar record instead
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
                rsDF = rsDF.append(smthChunk, ignore_index=True)

        ##################################################
        # Join smoothed trackline to smoothed range extent
        sDF = sDF[['record_num', 'chunk_id', 'ping_cnt', 'time_s', 'pix_m', 'lons', 'lats', 'utm_es', 'utm_ns', 'cog']].copy()
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
        outCSV = os.path.join(self.metaDir, "Trackline_Smth_"+self.beamName+".csv")
        rsDF.to_csv(outCSV, index=True, float_format='%.14f')

        self.rangeExt = rsDF # Store smoothed range extent in rectObj
        return self

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
            DESCRIPTION - Current index of sonar record which will be compared
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
        if dataframe sonar record should be dropped or not.

        --------------------
        Next Processing Step
        --------------------
        Returns dictionary to self._interpRangeCoords()
        '''
        range = 'range' # range distance
        x = 'range_e' # range easting extent coordinate
        y = 'range_n' # range northing extent coordinate
        dThresh = 'distThresh' # max distance to check for overlap
        tDist = 'track_dist' # straight line distance from sonar record i to subsequent sonar records
        toCheck = 'toCheck' # Flag indicating subsequent sonar record is close enough to i to check for potential overlap
        toDrop = 'toDrop' # Flag indicating sonar record overlaps with i
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
        ## current sonar record to potentially overlap.
        df[dThresh] = rowI[range] + df[range]

        # Calc straight line distance along the track from current sonar record
        ## to all other sonar records.  It is impossible for overlap to occur for
        ## subsequent sonar records to overlap current sonar record if they are
        ## further then the threshold distance.
        rowIx, rowIy = rowI[x], rowI[y] # Get current sonar record range extent coordinates
        dfx, dfy = df[x].to_numpy(), df[y].to_numpy() # Get subsequent sonar record range extent coordinates
        dist = self._getDist(rowIx, rowIy, dfx, dfy) # Calculate distance from current sonar record

        # Check if dist < distThresh. True==Check for possible overlap; False==No need to check
        df[tDist] = dist # Store distance calculation
        df.loc[df[tDist] <= df[dThresh], toCheck] = True # Check for overlap
        df.loc[df[tDist] > df[dThresh], toCheck] = False # Don't check for overlap
        df[toCheck]=df[toCheck].astype(bool) # Make sure toCheck column is type bool

        # Determine which sonar records overlap with current sonar record
        line1 = ((rowI[es],rowI[ns]), (rowI[x], rowI[y])) # Store current sonar record coordinates as tuple
        dfFilt = df[df[toCheck]==True].copy() # Get sonar records that could overlap with current
        dropping = {} # Dictionary to store sonar record index to drop
        for i, row in dfFilt.iterrows(): # Iterate subsequent sonar records
            line2=((row[es], row[ns]), (row[x], row[y])) # Store sonar record coordinates to check in tuple
            isIntersect = self._lineIntersect(line1, line2, row[range]) # Determine if line1 intersects line2
            dfFilt.loc[i, toDrop] = isIntersect # Store bool in dataframe (don't need this but keeping in case)
            if isIntersect == True: # If line2 intersects line1, flag sonar record for dropping
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
    # Rectify sonar imagery                                                    #
    ############################################################################

    #===========================================================================
    def _rectSonParallel(self,
                         chunk,
                         remWater=True,
                         filt=50,
                         wgs=False):
        '''
        This function will georectify sonar tiles with water column present
        (rect_wcp) OR water column removed and slant range corrected (rect_src).
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
            DESCRIPTION - Every `filt` sonar record will be used to fit a spline.
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

        # Prepare initial variables
        ## Variables for water column removal and slant range corrected imagery
        if remWater == True:
            imgOutPrefix = 'rect_src'
            tileFlag = self.src #Indicates if non-rectified src images were exported
        ## Variables for water column present imagery
        else:
            imgOutPrefix = 'rect_wcp'
            tileFlag = self.wcp #Indicates if non-rectified wcp images were exported

        # Create output directory if it doesn't exist
        outDir = self.outDir # Parent directory
        try:
            os.mkdir(outDir)
        except:
            pass
        outDir = os.path.join(outDir, imgOutPrefix) # Sub-directory
        try:
            os.mkdir(outDir)
        except:
            pass

        # Get trackline/range extent file path
        trkMetaFile = os.path.join(self.metaDir, "Trackline_Smth_"+self.beamName+".csv")

        # What coordinates should be used?
        ## Use WGS 1984 coordinates and set variables as needed
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

        projName = os.path.split(self.projDir)[-1] # Get project name
        beamName = self.beamName # Determine which sonar beam we are working with
        imgName = projName+'_'+imgOutPrefix+'_'+beamName+'_'+addZero+str(int(chunk))+'.tif' # Create output image name

        gtiff = os.path.join(outDir, imgName) # Output file name

        # Following workflow adapted from scikit-image:
        # # https://scikit-image.org/docs/dev/auto_examples/transform/plot_piecewise_affine.html

        #################################
        # Prepare pixel (pix) coordinates
        ## Pix coordinates describe the size of the coordinates in pixel
        ## coordinates (top left of image == (0,0); top right == (0,nchunk)...)

        # Open image to rectify
        if tileFlag: # Open non-rectified image as numpy array
            img = np.asarray(Image.open(imgPath)).copy()
        else: # Load ping return values from .SON/.IDX file
            self._getScanChunkSingle(chunk, remWater)
            img = self.sonDat
        img[0]=0 # To fix extra white on curves

        # For each sonar record, we need the pixel coordinates where the sonar
        ## originates on the trackline, and where it terminates based on the
        ## range of the sonar record.  This results in an array of coordinate
        ## pairs that describe the edge of the non-rectified image tile.
        rows, cols = img.shape[0], img.shape[1] # Determine number rows/cols
        pix_cols = np.arange(0, cols) # Create array of column indices
        pix_rows = np.linspace(0, rows, 2).astype('int') # Create array of two row indices (0 for points at sonar record origin, `rows` for max range)
        pix_rows, pix_cols = np.meshgrid(pix_rows, pix_cols) # Create grid arrays that we can stack together
        pixAll = np.dstack([pix_rows.flat, pix_cols.flat])[0] # Stack arrays to get final map of pix pixel coordinats [[row1, col1], [row2, col1], [row1, col2], [row2, col2]...]

        # Create mask for filtering array. This makes fitting PiecewiseAffineTransform
        ## more efficient
        mask = np.zeros(len(pixAll), dtype=bool) # Create mask same size as pixAll
        mask[0::filt] = 1 # Filter row coordinates
        mask[1::filt] = 1 # Filter column coordinates
        mask[-2], mask[-1] = 1, 1 # Make sure we keep last row/col coordinates

        # Filter pix
        pix = pixAll[mask]

        #######################################
        # Prepare destination (dst) coordinates
        ## Destination coordinates describe the geographic location in lat/lon
        ## or easting/northing that directly map to the pix coordinates.

        # Open smoothed trackline/range extent file
        trkMeta = pd.read_csv(trkMetaFile)
        trkMeta = trkMeta[trkMeta['chunk_id']==chunk].reset_index(drop=False) # Filter df by chunk_id
        pix_m = trkMeta['pix_m'].min() # Get pixel size

        # Get range (outer extent) coordinates [xR, yR] to transposed numpy arrays
        xR, yR = trkMeta[xRange].to_numpy().T, trkMeta[yRange].to_numpy().T
        xyR = np.vstack((xR, yR)).T # Stack the arrays

        # Get trackline (origin of sonar record) coordinates [xT, yT] to transposed numpy arrays
        xT, yT = trkMeta[xTrk].to_numpy().T, trkMeta[yTrk].to_numpy().T
        xyT = np.vstack((xT, yT)).T # Stack the  arrays

        # Stack the coordinates (range[0,0], trk[0,0], range[1,1]...) following
        ## pattern of pix coordinates
        dstAll = np.empty([len(xyR)+len(xyT), 2]) # Initialize appropriately sized np array
        dstAll[0::2] = xyT # Add trackline coordinates
        dstAll[1::2] = xyR # Add range extent coordinates

        # Filter dst using previously made mask
        dst = dstAll[mask]

        ##################
        # Warp sonar image
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
        tform = PiecewiseAffineTransform()
        tform.estimate(pix, dst) # Calculate H matrix

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
                dst.write(out,1)
                ## Uncomment below code if overviews should be created for each file
                # dst.build_overviews([2 ** j for j in range(1,8)], Resampling.nearest)
                # dst.update_tags(ns='rio_overview', resampling='nearest')
                # dst.close()

        pass

    #===========================================================================
    # Deprecated rectSon() workflow
    # def _rectSon(self,
    #              remWater=True,
    #              filt=50,
    #              wgs=False):
    #     '''
    #     This function will georectify sonar tiles with water column present
    #     (rect_wcp) OR water column removed and slant range corrected (rect_src).
    #     The function will use non-rectified images if they were previously exported.
    #     If not, the sonar intensity will be loaded directly from the .SON file.
    #     Once determined, each chunk will be iterated, sonar intensities loaded
    #     into memory and:
    #     1) Pixel (pix) coordinates are formated as a numpy array based on shape
    #        of sonar chunk.  Coordinates are filtered to aid computation efficiency.
    #     2) Geographic, or destination (dst), coordinates for the smoothed trackline
    #        and range extent are loaded from the "Trackline_Smth_BXXX.csv" file and
    #        formated as a numpy array and filtered as pix.
    #     3) A Piecewise Affine Transform is used to map pix coordinates to the shape
    #        of the dst coordinates in order to warp (or rectify) the sonar intensities.
    #        Warped sonar intensities are stored in a new numpy array.
    #     4) The warped array is then mapped to geographic coordinates using a
    #        transformation matrix and exported as a geotiff.
    #
    #     ----------
    #     Parameters
    #     ----------
    #     remWater : bool
    #         DESCRIPTION - Flag indicating if wcp [False] or pix [True] imagery.
    #     filt : int
    #         DESCRIPTION - Every `filt` sonar record will be used to fit a spline.
    #     wgs : bool
    #         DESCRIPTION - Flag indicating if sonar images should be rectified using
    #                       WGS 1984 coordinate system [True] or UTM state plane [False]
    #
    #     ----------------------------
    #     Required Pre-processing step
    #     ----------------------------
    #     self._getRangeCoords()
    #
    #     -------
    #     Returns
    #     -------
    #     Georectified geotiffs
    #
    #     --------------------
    #     Next Processing Step
    #     --------------------
    #     NA
    #     '''
    #
    #     # Prepare initial variables
    #     ## Variables for water column removal and slant range corrected imagery
    #     if remWater == True:
    #         imgInPrefix = 'src'
    #         imgOutPrefix = 'rect_src'
    #         tileFlag = self.src #Indicates if non-rectified src images were exported
    #     ## Variables for water column present imagery
    #     else:
    #         imgInPrefix = 'wcp'
    #         imgOutPrefix = 'rect_wcp'
    #         tileFlag = self.wcp #Indicates if non-rectified wcp images were exported
    #
    #     # Create output directory if it doesn't exist
    #     outDir = self.outDir # Parent directory
    #     try:
    #         os.mkdir(outDir)
    #     except:
    #         pass
    #     outDir = os.path.join(outDir, imgOutPrefix) # Sub-directory
    #     try:
    #         os.mkdir(outDir)
    #     except:
    #         pass
    #
    #     # Locate and open smoothed trackline/range extent file
    #     trkMetaFile = os.path.join(self.metaDir, "Trackline_Smth_"+self.beamName+".csv")
    #     trkMeta = pd.read_csv(trkMetaFile)
    #
    #     # Determine what chunks to process
    #     chunks = pd.unique(trkMeta['chunk_id']) # Store chunk values in list
    #     # chunks = chunks[72:73] # For troubleshooting and subsetting chunks to process
    #     firstChunk = min(chunks) # Find first chunk
    #
    #     # What coordinates should be used?
    #     ## Use WGS 1984 coordinates and set variables as needed
    #     if wgs is True:
    #         epsg = self.humDat['wgs']
    #         xRange = 'range_lons'
    #         yRange = 'range_lats'
    #         xTrk = 'trk_lons'
    #         yTrk = 'trk_lats'
    #     ## Use projected coordinates and set variables as needed
    #     else:
    #         epsg = self.humDat['epsg']
    #         xRange = 'range_es'
    #         yRange = 'range_ns'
    #         xTrk = 'trk_utm_es'
    #         yTrk = 'trk_utm_ns'
    #
    #     # If non-rectified imagery were previously exported, we can rectify those
    #     ## images directly without having to reopen .SON/.IDX files
    #     if tileFlag:
    #         allImgs = sorted(glob(os.path.join(self.outDir, imgInPrefix,"*"+imgInPrefix+"*"))) #List of imgs to rectify
    #         allImgsDict = defaultdict() # Dictionary to store {chunk: path to output image}
    #         for img in allImgs:
    #             imgName=os.path.basename(img).split('.')[0] # Get image name
    #             chunk=int(imgName.split('_')[-1]) # Get chunk id
    #             allImgsDict[chunk] = img # Add chunk:path to output image
    #
    #         # Verify that each exported non-rectified image has associate smoothed
    #         ## trackline and range extent coordinates
    #         inImgs = {c: allImgsDict[c] for c in chunks}
    #
    #     # Non-rectified images not previously exported so we need to handle creation
    #     ## of inImgs differently.
    #     else:
    #         inImgs = defaultdict() # Initialize inImgs dictionary
    #         # Determine leading zeros to match naming convention
    #         for chunk in chunks:
    #             if chunk < 10:
    #                 addZero = '0000'
    #             elif chunk < 100:
    #                 addZero = '000'
    #             elif chunk < 1000:
    #                 addZero = '00'
    #             elif chunk < 10000:
    #                 addZero = '0'
    #             else:
    #                 addZero = ''
    #
    #             projName = os.path.split(self.projDir)[-1] # Get project name
    #             beamName = self.beamName # Determine which sonar beam we are working with
    #             imgName = projName+'_'+imgInPrefix+'_'+beamName+'_'+addZero+str(int(chunk))+'.png' # Create output image name
    #
    #             inImgs[int(chunk)] = os.path.join(self.outDir, imgName) # Store {chunk: path to output image}
    #
    #     # Iterate chunk/image path and rectify
    #     for i, imgPath in inImgs.items():
    #         # Following workflow adapted from scikit-image:
    #         # # https://scikit-image.org/docs/dev/auto_examples/transform/plot_piecewise_affine.html
    #
    #         #################################
    #         # Prepare pixel (pix) coordinates
    #         ## Pix coordinates describe the size of the coordinates in pixel
    #         ## coordinates (top left of image == (0,0); top right == (0,nchunk)...)
    #
    #         # Open image to rectify
    #         if tileFlag: # Open non-rectified image as numpy array
    #             img = np.asarray(Image.open(imgPath)).copy()
    #         else: # Load ping return values from .SON/.IDX file
    #             self._getScanChunkSingle(i, remWater)
    #             img = self.sonDat
    #         img[0]=0 # To fix extra white on curves
    #
    #         # For each sonar record, we need the pixel coordinates where the sonar
    #         ## originates on the trackline, and where it terminates based on the
    #         ## range of the sonar record.  This results in an array of coordinate
    #         ## pairs that describe the edge of the non-rectified image tile.
    #         rows, cols = img.shape[0], img.shape[1] # Determine number rows/cols
    #         pix_cols = np.arange(0, cols) # Create array of column indices
    #         pix_rows = np.linspace(0, rows, 2).astype('int') # Create array of two row indices (0 for points at sonar record origin, `rows` for max range)
    #         pix_rows, pix_cols = np.meshgrid(pix_rows, pix_cols) # Create grid arrays that we can stack together
    #         pixAll = np.dstack([pix_rows.flat, pix_cols.flat])[0] # Stack arrays to get final map of pix pixel coordinats [[row1, col1], [row2, col1], [row1, col2], [row2, col2]...]
    #
    #         # Create mask for filtering array. This makes fitting PiecewiseAffineTransform
    #         ## more efficient
    #         mask = np.zeros(len(pixAll), dtype=bool) # Create mask same size as pixAll
    #         mask[0::filt] = 1 # Filter row coordinates
    #         mask[1::filt] = 1 # Filter column coordinates
    #         mask[-2], mask[-1] = 1, 1 # Make sure we keep last row/col coordinates
    #
    #         # Filter pix
    #         pix = pixAll[mask]
    #
    #         #######################################
    #         # Prepare destination (dst) coordinates
    #         ## Destination coordinates describe the geographic location in lat/lon
    #         ## or easting/northing that directly map to the pix coordinates.
    #
    #         # Open smoothed trackline/range extent file
    #         trkMeta = pd.read_csv(trkMetaFile)
    #         trkMeta = trkMeta[trkMeta['chunk_id']==i].reset_index(drop=False) # Filter df by chunk_id
    #         pix_m = trkMeta['pix_m'].min() # Get pixel size
    #
    #         # Get range (outer extent) coordinates [xR, yR] to transposed numpy arrays
    #         xR, yR = trkMeta[xRange].to_numpy().T, trkMeta[yRange].to_numpy().T
    #         xyR = np.vstack((xR, yR)).T # Stack the arrays
    #
    #         # Get trackline (origin of sonar record) coordinates [xT, yT] to transposed numpy arrays
    #         xT, yT = trkMeta[xTrk].to_numpy().T, trkMeta[yTrk].to_numpy().T
    #         xyT = np.vstack((xT, yT)).T # Stack the  arrays
    #
    #         # Stack the coordinates (range[0,0], trk[0,0], range[1,1]...) following
    #         ## pattern of pix coordinates
    #         dstAll = np.empty([len(xyR)+len(xyT), 2]) # Initialize appropriately sized np array
    #         dstAll[0::2] = xyT # Add trackline coordinates
    #         dstAll[1::2] = xyR # Add range extent coordinates
    #
    #         # Filter dst using previously made mask
    #         dst = dstAll[mask]
    #
    #         ##################
    #         # Warp sonar image
    #         ## Before applying a geographic projection to the image, the image
    #         ## must be warped to conform to the shape specified by the geographic
    #         ## coordinates.  We don't want to warp the image to real-world dimensions,
    #         ## so we will normalize and rescale the dst coordinates to give the
    #         ## top-left coordinate a value of (0,0)
    #
    #         # Determine min/max for rescaling
    #         xMin, xMax = dst[:,0].min(), dst[:,0].max() # Min/Max of x coordinates
    #         yMin, yMax = dst[:,1].min(), dst[:,1].max() # Min/Max of y coordinates
    #
    #         # Determine output shape dimensions
    #         outShapeM = [xMax-xMin, yMax-yMin] # Calculate range of x,y coordinates
    #         outShape=[0,0]
    #         # Divide by pixel size to arrive at output shape of warped image
    #         outShape[0], outShape[1] = round(outShapeM[0]/pix_m,0), round(outShapeM[1]/pix_m,0)
    #
    #         # Rescale destination coordinates
    #         # X values
    #         xStd = (dst[:,0]-xMin) / (xMax-xMin) # Standardize
    #         xScaled = xStd * (outShape[0] - 0) + 0 # Rescale to output shape
    #         dst[:,0] = xScaled # Store rescaled x coordinates
    #
    #         # Y values
    #         yStd = (dst[:,1]-yMin) / (yMax-yMin) # Standardize
    #         yScaled = yStd * (outShape[1] - 0) + 0 # Rescale to output shape
    #         dst[:,1] = yScaled # Store rescaled y coordinates
    #
    #         ########################
    #         # Perform transformation
    #         # PiecewiseAffineTransform
    #         tform = PiecewiseAffineTransform()
    #         tform.estimate(pix, dst) # Calculate H matrix
    #
    #         # Warp image from the input shape to output shape
    #         out = warp(img.T,
    #                    tform.inverse,
    #                    output_shape=(outShape[1], outShape[0]),
    #                    mode='constant',
    #                    cval=np.nan,
    #                    clip=False,
    #                    preserve_range=True)
    #
    #         # Rotate 180 and flip
    #         # https://stackoverflow.com/questions/47930428/how-to-rotate-an-array-by-%C2%B1-180-in-an-efficient-way
    #         out = np.flip(np.flip(np.flip(out,1),0),1).astype('uint8')
    #
    #         ##############
    #         # Save Geotiff
    #         ## In order to visualize the warped image in a GIS at the appropriate
    #         ## spatial extent, the pixel coordinates of the warped image must be
    #         ## mapped to spatial coordinates. This is accomplished by calculating
    #         ## the transformation matrix using rasterio.transform.from_origin
    #
    #         # First get the min/max values for x,y geospatial coordinates
    #         xMin, xMax = dstAll[:,0].min(), dstAll[:,0].max()
    #         yMin, yMax = dstAll[:,1].min(), dstAll[:,1].max()
    #
    #         # Calculate x,y resolution of a single pixel
    #         xres = (xMax - xMin) / outShape[0]
    #         yres = (yMax - yMin) / outShape[1]
    #
    #         # Calculate transformation matrix by providing geographic coordinates
    #         ## of upper left corner of the image and the pixel size
    #         transform = from_origin(xMin - xres/2, yMax - yres/2, xres, yres)
    #
    #         # Prepare output image name
    #         outImg=os.path.basename(inImgs[i]).replace(imgInPrefix, imgOutPrefix)
    #         outImg=outImg.replace('png', 'tif')
    #         gtiff = os.path.join(outDir, outImg)
    #
    #         # Export georectified image
    #         with rasterio.open(
    #             gtiff,
    #             'w',
    #             driver='GTiff',
    #             height=out.shape[0],
    #             width=out.shape[1],
    #             count=1,
    #             dtype=out.dtype,
    #             crs=epsg,
    #             transform=transform,
    #             compress='lzw'
    #             ) as dst:
    #                 dst.nodata=0
    #                 dst.write(out,1)
    #                 ## Uncomment below code if overviews should be created for each file
    #                 # dst.build_overviews([2 ** j for j in range(1,8)], Resampling.nearest)
    #                 # dst.update_tags(ns='rio_overview', resampling='nearest')
    #                 # dst.close()
    #
    #     pass
