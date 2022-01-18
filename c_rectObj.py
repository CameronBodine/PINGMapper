
from funcs_common import *
from c_sonObj import sonObj
from scipy.interpolate import splprep, splev
from skimage.transform import PiecewiseAffineTransform, warp
from rasterio.transform import from_origin
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
        t=dfFilt[zU].to_numpy() # Store parameter values in numpy array.  Used to space points along spline.

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

        u_interp = dfOrig[zU].to_numpy() # Get all time ellapsed OR record number values from unfilterd df
        x_interp = splev(u_interp, tck) # Use u_interp to get smoothed x/y coordinates from spline

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
            chunkDF = chunkDF.iloc[::filt]
            chunkDF = chunkDF.append(last, ignore_index=True)

            idx = chunkDF.index.tolist() # Store sonar record index in list
            maxIdx = max(idx) # Find last record index value

            drop = np.empty((len(chunkDF)), dtype=bool) # Bool numpy array to flag which sonar records overlap and should be dropped
            drop[:] = False # Prepopulate array w/ `False` (i.e. False==don't drop)

            #########################################
            # Find and drop overlapping sonar records
            # Iterate each sonar record if filtered dataframe
            for i in idx:
                if i == maxIdx: # Break loop once we reach the last sonar record
                    break
                else:
                    cRow = chunkDF.loc[i] # Get current sonar record
                    if drop[i] != True: # If current sonar record flagged to drop, don't need to check it
                        dropping = self._checkPings(i, chunkDF) # Find subsequent sonar records that overlap current record
                        if maxIdx in dropping.keys(): # Make sure we don't drop last sonar record in chunk
                            del dropping[maxIdx]
                        if len(dropping) > 0: # We have overlapping sonar records we need to drop
                            lastKey = max(dropping)
                            del dropping[lastKey] # Don't remove last element
                            for k, v in dropping.items():
                                drop[k] = True
                                last = k+1
                        else:
                            pass
                    else:
                        pass
            chunkDF = chunkDF[~drop]

            rchunkDF = chunkDF.copy()
            schunkDF = sDF[sDF['chunk_id']==chunk].copy()

            # outCSV = os.path.join(self.metaDir, "Trackline_Smth_"+str(int(chunk))+'_'+self.beamName+".csv")
            # rchunkDF.to_csv(outCSV, index=True, float_format='%.14f')

            smthChunk = self._interpTrack(df=rchunkDF, dfOrig=schunkDF, xlon=rlon,
                                          ylat=rlat, xutm=re, yutm=rn, filt=0, deg=1)
            if 'rsDF' not in locals():
                rsDF = smthChunk.copy()
            else:
                rsDF = rsDF.append(smthChunk, ignore_index=True)

        # Join smoothed trackline to smoothed range extent
        sDF = sDF[['record_num', 'chunk_id', 'ping_cnt', 'time_s', 'pix_m', 'lons', 'lats', 'utm_es', 'utm_ns', 'cog']].copy()
        sDF.rename(columns={'lons': 'trk_lons', 'lats': 'trk_lats', 'utm_es': 'trk_utm_es', 'utm_ns': 'trk_utm_ns', 'cog': 'trk_cog'}, inplace=True)
        rsDF.rename(columns={'cog': 'range_cog'}, inplace=True)
        rsDF = rsDF[['record_num', 'range_lons', 'range_lats', 'range_cog']]
        rsDF = sDF.set_index('record_num').join(rsDF.set_index('record_num'))

        # Calculate easting/northing for smoothed range extent
        e_smth, n_smth = self.trans(rsDF[rlons].to_numpy(), rsDF[rlats].to_numpy())
        rsDF[res] = e_smth
        rsDF[rns] = n_smth

        # Overwrite Trackline_Smth_son.beamName.csv
        outCSV = os.path.join(self.metaDir, "Trackline_Smth_"+self.beamName+".csv")
        rsDF.to_csv(outCSV, index=True, float_format='%.14f')

        self.rangeExt = rsDF
        return

    #===========================================================================
    def _checkPings(self, i, df):
        '''


        ----------
        Parameters
        ----------

        -------
        Returns
        -------

        '''
        range = 'range' # range distance
        x = 'range_e' # range easting extent
        y = 'range_n' # range northing extent
        dThresh = 'distThresh'
        tDist = 'track_dist'
        toCheck = 'toCheck'
        toDrop = 'toDrop'
        es = 'utm_es' #Trackline smoothed easting
        ns = 'utm_ns' #Trackline smoothed northing

        # Filter df
        rowI = df.loc[i]
        df = df.copy()
        df = df.iloc[df.index > i]

        # Calc distance threshold
        df[dThresh] = rowI[range] + df[range]

        # Calc track straight line distance
        rowIx, rowIy = rowI[x], rowI[y]
        dfx, dfy = df[x].to_numpy(), df[y].to_numpy()
        dist = self._getDist(rowIx, rowIy, dfx, dfy)

        # Check if dist < distThresh
        df[tDist] = dist
        df.loc[df[tDist] <= df[dThresh], toCheck] = True
        df.loc[df[tDist] > df[dThresh], toCheck] = False
        df[toCheck]=df[toCheck].astype(bool)

        # Check if we need to drop
        line1 = ((rowI[es],rowI[ns]), (rowI[x], rowI[y]))
        dfFilt = df[df[toCheck]==True].copy()
        dropping = {}
        # line2 = ((df[es].to_numpy(),df[ns].to_numpy()), (df[x].to_numpy(), df[y].to_numpy()))
        for i, row in dfFilt.iterrows():
            line2=((row[es], row[ns]), (row[x], row[y]))
            isIntersect = self._lineIntersect(line1, line2, row[range])
            dfFilt.loc[i, toDrop] = isIntersect
            if isIntersect == True:
                dropping[i]=isIntersect

        return dropping

    #===========================================================================
    def _getDist(self, aX, aY, bX, bY):
        '''


        ----------
        Parameters
        ----------

        -------
        Returns
        -------

        '''
        dist = np.sqrt( (bX - aX)**2 + (bY - aY)**2)
        return dist

    #===========================================================================
    def _lineIntersect(self, line1, line2, range):
        '''


        ----------
        Parameters
        ----------

        -------
        Returns
        -------

        '''
        #https://stackoverflow.com/questions/20677795/how-do-i-compute-the-intersection-point-of-two-lines
        def line(p1, p2):
            A = (p1[1] - p2[1])
            B = (p2[0] - p1[0])
            C = (p1[0]*p2[1] - p2[0]*p1[1])
            return A, B, -C

        def intersection(L1, L2):
            D  = L1[0] * L2[1] - L1[1] * L2[0]
            Dx = L1[2] * L2[1] - L1[1] * L2[2]
            Dy = L1[0] * L2[2] - L1[2] * L2[0]
            if D != 0:
                x=Dx/D
                y=Dy/D
                return x,y
            else:
                return False

        def isBetween(line1, line2, c):
            ax, ay = line1[0][0], line1[0][1]
            bx, by = line1[1][0], line2[1][1]
            cx, cy = c[0], c[1]
            xIntersect=yIntersect=False

            if (cx >= min(ax,bx)-5) and (cx <= max(ax,bx)+5) and \
               (cy >= min(ay,by)-5) and (cy <= max(ay,by)+5):
               checkDist = True
            else:
               checkDist = isIntersect = False

            if checkDist is True:
                x,y = line2[0][0], line2[0][1]
                dist = self._getDist(x, y, cx, cy)
                if range < dist:
                    isIntersect = False
                else:
                    isIntersect = True

            return isIntersect

        L1 = line(line1[0], line1[1])
        L2 = line(line2[0], line2[1])
        c = intersection(L1, L2)
        if c is not False:
            I = isBetween(line1, line2, c)
        else:
            I = False
        return I

    #===========================================================================
    def _rectSon(self, remWater=True, filt=50, adjDep=0, wgs=False):
        '''


        ----------
        Parameters
        ----------

        -------
        Returns
        -------

        '''
        if remWater == True:
            imgInPrefix = 'src'
            imgOutPrefix = 'rect_src'
            tileFlag = self.src #Indicates if non-rectified src images were exported
        else:
            imgInPrefix = 'wcp'
            imgOutPrefix = 'rect_wcp'
            tileFlag = self.wcp #Indicates if non-rectified wcp images were exported

        # Prepare initial variables
        outDir = self.outDir
        try:
            os.mkdir(outDir)
        except:
            pass
        outDir = os.path.join(outDir, imgOutPrefix) #Img output/input directory
        try:
            os.mkdir(outDir)
        except:
            pass

        # Locate and open necessary meta files
        # ssSide = (self.beamName).split('_')[-1] #Port or Star
        # pingMetaFile = glob(self.metaDir+os.sep+'RangeExtent_'+ssSide+'.csv')[0]
        # pingMeta = pd.read_csv(pingMetaFile)
        trkMetaFile = os.path.join(self.metaDir, "Trackline_Smth_"+self.beamName+".csv")
        trkMeta = pd.read_csv(trkMetaFile)

        # Determine what chunks to process
        # chunks = pd.unique(pingMeta['chunk_id'])
        chunks = pd.unique(trkMeta['chunk_id'])
        # chunks = chunks[11:]
        firstChunk = min(chunks)

        if wgs is True:
            epsg = self.humDat['wgs']
            xRange = 'range_lons'
            yRange = 'range_lats'
            xTrk = 'trk_lons'
            yTrk = 'trk_lats'
        else:
            epsg = self.humDat['epsg']
            xRange = 'range_es'
            yRange = 'range_ns'
            xTrk = 'trk_utm_es'
            yTrk = 'trk_utm_ns'

        if tileFlag:
            allImgs = sorted(glob(os.path.join(self.outDir, imgInPrefix,"*"+imgInPrefix+"*"))) #List of imgs to rectify
            # Make sure destination coordinates are available for each image
            # If dest coords not available, remove image from inImgs
            allImgsDict = defaultdict()
            for img in allImgs:
                imgName=os.path.basename(img).split('.')[0]
                chunk=int(imgName.split('_')[-1])
                allImgsDict[chunk] = img

            inImgs = {c: allImgsDict[c] for c in chunks}
        else:
            inImgs = defaultdict()
            for chunk in chunks:
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

                projName = os.path.split(self.projDir)[-1]
                beamName = self.beamName
                imgName = projName+'_'+imgInPrefix+'_'+beamName+'_'+addZero+str(int(chunk))+'.png'

                inImgs[int(chunk)] = os.path.join(self.outDir, imgName)

        # Iterate images and rectify
        for i, imgPath in inImgs.items():

            ############################
            # Prepare source coordinates
            # Open image to rectify
            if tileFlag:
                img = np.asarray(Image.open(imgPath)).copy()
            else:
                self._getScanChunkSingle(i, remWater)
                img = self.sonDat
            img[0]=0 # To fix extra white on curves

            # Prepare src coordinates
            rows, cols = img.shape[0], img.shape[1]
            src_cols = np.arange(0, cols)
            src_rows = np.linspace(0, rows, 2)
            src_rows, src_cols = np.meshgrid(src_rows, src_cols)
            srcAll = np.dstack([src_rows.flat, src_cols.flat])[0]

            # Create mask for filtering array
            mask = np.zeros(len(srcAll), dtype=bool)
            mask[0::filt] = 1
            mask[1::filt] = 1
            mask[-2], mask[-1] = 1, 1

            # Filter src
            src = srcAll[mask]

            #################################
            # Prepare destination coordinates
            # pingMeta = pd.read_csv(pingMetaFile)
            # pingMeta = pingMeta[pingMeta['chunk_id']==i].reset_index()
            # pix_m = pingMeta['pix_m'].min()

            trkMeta = pd.read_csv(trkMetaFile)
            trkMeta = trkMeta[trkMeta['chunk_id']==i].reset_index(drop=False)
            pix_m = trkMeta['pix_m'].min()

            # trkMeta = trkMeta.filter(items=[xTrk, yTrk])
            # pingMeta = pingMeta.join(trkMeta)

            # Get range (outer extent) coordinates
            # xR, yR = pingMeta[xRange].to_numpy().T, pingMeta[yRange].to_numpy().T
            xR, yR = trkMeta[xRange].to_numpy().T, trkMeta[yRange].to_numpy().T
            xyR = np.vstack((xR, yR)).T

            # Get trackline (inner extent) coordinates
            # xT, yT = pingMeta[xTrk].to_numpy().T, pingMeta[yTrk].to_numpy().T
            xT, yT = trkMeta[xTrk].to_numpy().T, trkMeta[yTrk].to_numpy().T
            xyT = np.vstack((xT, yT)).T

            # Stack the coordinates (range[0,0], trk[0,0], range[1,1]...)
            dstAll = np.empty([len(xyR)+len(xyT), 2])
            dstAll[0::2] = xyT
            dstAll[1::2] = xyR

            # Filter dst
            dst = dstAll[mask]

            # Determine min/max for rescaling
            xMin, xMax = dst[:,0].min(), dst[:,0].max()
            yMin, yMax = dst[:,1].min(), dst[:,1].max()

            # Determine output shape
            outShapeM = [xMax-xMin, yMax-yMin]
            outShape=[0,0]
            outShape[0], outShape[1] = round(outShapeM[0]/pix_m,0), round(outShapeM[1]/pix_m,0)

            # Rescale destination coordinates
            # X values
            xStd = (dst[:,0]-xMin) / (xMax-xMin) # Standardize
            xScaled = xStd * (outShape[0] - 0) + 0 # Rescale
            dst[:,0] = xScaled

            # Y values
            yStd = (dst[:,1]-yMin) / (yMax-yMin) # Standardize
            yScaled = yStd * (outShape[1] - 0) + 0 # Rescale
            dst[:,1] = yScaled

            ########################
            # Perform transformation
            # PiecewiseAffineTransform
            tform = PiecewiseAffineTransform()
            tform.estimate(src, dst) # Calculate H matrix

            # Warp image
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
            # Determine resolution and calc affine transform matrix
            xMin, xMax = dstAll[:,0].min(), dstAll[:,0].max()
            yMin, yMax = dstAll[:,1].min(), dstAll[:,1].max()

            xres = (xMax - xMin) / outShape[0]
            yres = (yMax - yMin) / outShape[1]
            # transform = Affine.translation(xMin - xres / 2, yMin - yres / 2) * Affine.scale(xres, yres)
            transform = from_origin(xMin - xres/2, yMax - yres/2, xres, yres)

            # gtiff = 'E:\\NAU\\Python\\PINGMapper\\procData\\SFE_20170801_R00014\\sidescan_port\\image-00010-rect-prj.tif'
            outImg=os.path.basename(inImgs[i]).replace(imgInPrefix, imgOutPrefix)
            outImg=outImg.replace('png', 'tif')
            gtiff = os.path.join(outDir, outImg)
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

            # i+=1



        pass
