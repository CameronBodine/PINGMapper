
from common_funcs import *
from c_sonObj import sonObj
from scipy.interpolate import splprep, splev

class rectObj(sonObj):
    #===========================================
    def __init__(self):
        sonObj.__init__(self, sonFile=None, humFile=None, projDir=None, tempC=None, nchunk=None)

    #===========================================
    def _interpTrack(self, df, dfOrig=None, dropDup=True, xlon='lon', ylat='lat', xutm='utm_x',
                     yutm='utm_y', zU='time_s', filt=0, deg=3):

        lons = xlon+'s'
        lats = ylat+'s'
        es = xutm+'s'
        ns = yutm+'s'

        # Make copy of df to work on
        if dfOrig is None:
            dfOrig = df
            df = dfOrig.copy()

        # Drop Duplicates
        if dropDup is True:
            df.drop_duplicates(subset=[xlon, ylat], inplace=True)

        # Extract every `filt` record, including last value
        if filt>0:
            lastRow = df.iloc[-1].to_dict()
            try:
                dfFilt = df.iloc[::filt].reset_index(drop=False)
            except:
                dfFilt = df.iloc[::filt].reset_index(drop=True)
            dfFilt = dfFilt.append(lastRow, ignore_index=True)
        else:
            dfFilt = df.reset_index(drop=False)

        # Try smoothing trackline
        x=dfFilt[xlon].to_numpy()
        y=dfFilt[ylat].to_numpy()
        t=dfFilt[zU].to_numpy()

        # Attempt to fix error
        # https://stackoverflow.com/questions/47948453/scipy-interpolate-splprep-error-invalid-inputs
        okay = np.where(np.abs(np.diff(x))+np.abs(np.diff(y))>0)
        x = np.r_[x[okay], x[-1]]
        y = np.r_[y[okay], y[-1]]
        t = np.r_[t[okay], t[-1]]

        # Interpolate trackline
        tck, _ = splprep([x,y], u=t, k=deg, s=0)

        u_interp = dfOrig[zU].to_numpy()
        x_interp = splev(u_interp, tck)

        # Store smoothed trackpoints in df
        smooth = {'chunk_id': dfOrig['chunk_id'],
                  'record_num': dfOrig['record_num'],
                  'ping_cnt': dfOrig['ping_cnt'],
                  'time_s': dfOrig['time_s'],
                  lons: x_interp[0],
                  lats: x_interp[1]}

        sDF = pd.DataFrame(smooth)

        # Calculate smoothed easting/northing
        e_smth, n_smth = self.trans(sDF[lons].to_numpy(), sDF[lats].to_numpy())
        sDF[es] = e_smth
        sDF[ns] = n_smth

        # Calculate COG from smoothed lat/lon
        brng = self._getBearing(sDF, lons, lats)
        last = brng[-1]
        brng = np.append(brng, last)
        sDF['cog'] = brng

        return sDF

    #===========================================
    def _getBearing(self, df, lon, lat):
        lonA = df[lon].to_numpy()
        latA = df[lat].to_numpy()
        lonA = lonA[:-1]
        latA = latA[:-1]
        pntA = [lonA,latA]

        lonB = df[lon].to_numpy()
        latB = df[lat].to_numpy()
        lonB = lonB[1:]
        latB = latB[1:]
        pntB = [lonB,latB]

        lonA, latA = pntA[0], pntA[1]
        lonB, latB = pntB[0], pntB[1]

        lat1 = np.deg2rad(latA)
        lat2 = np.deg2rad(latB)

        diffLong = np.deg2rad(lonB - lonA)
        bearing = np.arctan2(np.sin(diffLong) * np.cos(lat2), np.cos(lat1) * np.sin(lat2) - (np.sin(lat1) * np.cos(lat2) * np.cos(diffLong)))

        db = np.degrees(bearing)
        db = (db + 360) % 360

        return db

    #===========================================
    def _getRangeCoords(self, flip, pix_m):
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

        # Get smoothed trackline
        sDF = self.smthTrk

        # Determine ping bearing
        if self.beamName == 'sidescan_port':
            rotate = -90
        else:
            rotate = 90
        if flip == True:
            rotate *= -1

        sDF[ping_bearing] = (sDF['cog']+rotate) % 360

        # Calculate max range for each chunk
        chunk = sDF.groupby(chunk_id)
        maxPing = chunk[ping_cnt].max()
        for i in maxPing.index:
            sDF.loc[sDF[chunk_id]==i, range] = maxPing[i]*pix_m

        # Calculate range extent lat/lon using bearing and range
        # https://stackoverflow.com/questions/7222382/get-lat-long-given-current-point-distance-and-bearing
        R = 6371.393*1000 #Radius of the Earth
        # R = 6378.1
        brng = np.deg2rad(sDF[ping_bearing]).to_numpy()
        d = (sDF[range].to_numpy())

        lat1 = np.deg2rad(sDF[lats]).to_numpy()
        lon1 = np.deg2rad(sDF[lons]).to_numpy()

        lat2 = np.arcsin( np.sin(lat1) * np.cos(d/R) +
               np.cos(lat1) * np.sin(d/R) * np.cos(brng))

        lon2 = lon1 + np.arctan2( np.sin(brng) * np.sin(d/R) * np.cos(lat1),
                                  np.cos(d/R) - np.sin(lat1) * np.sin(lat2))
        lat2 = np.degrees(lat2)
        lon2 = np.degrees(lon2)

        sDF[rlon] = lon2
        sDF[rlat] = lat2

        e_smth, n_smth = self.trans(sDF[rlon].to_numpy(), sDF[rlat].to_numpy())
        sDF[re] = e_smth
        sDF[rn] = n_smth

        return

    #===========================================
    def _interpRangeCoords(self, filt):
        rlon = 'range_lon'
        rlons = rlon+'s'
        rlat = 'range_lat'
        rlats = rlat+'s'
        re = 'range_e'
        res = re+'s'
        rn = 'range_n'
        rns = rn+'s'

        sDF = self.smthTrk
        rDF = sDF.copy()
        rDF = rDF.iloc[::filt]
        rDF = rDF.append(sDF.iloc[-1], ignore_index=True)

        idx = rDF.index.tolist()
        maxIdx = max(idx)

        drop = np.empty((len(rDF)), dtype=bool)
        drop[:] = False

        for i in idx:
            if i == maxIdx:
                break
            else:
                cRow = rDF.loc[i]
                if drop[i] != True:
                    dropping = self._checkPings(i, rDF)
                    if len(dropping) > 0:
                        drop[i] = True #Potentiall remove this
                        for k, v in dropping.items():
                            drop[k] = True
                            last = k+1
                else:
                    pass
        rDF = rDF[~drop]

        rsDF = self._interpTrack(df=rDF, dfOrig=sDF, xlon=rlon, ylat=rlat, xutm=re, yutm=rn,
                                 filt=0, deg=1)

        e_smth, n_smth = self.trans(rsDF[rlons].to_numpy(), rsDF[rlats].to_numpy())
        rsDF[res] = e_smth
        rsDF[rns] = n_smth

        beam = self.beamName.split('_')[1]
        outCSV = os.path.join(self.metaDir, "RangeExtent_"+beam+".csv")
        rsDF.to_csv(outCSV, index=False, float_format='%.14f')

        self.rangeExt = rsDF
        return

    #===========================================
    def _checkPings(self, i, df):
        range = 'range' # range distance
        x = 'range_e' # range easting extent
        y = 'range_n' # range northing extent
        dThresh = 'distThresh'
        tDist = 'track_dist'
        toCheck = 'toCheck'
        toDrop = 'toDrop'
        es = 'utm_xs' #Trackline smoothed easting
        ns = 'utm_ys' #Trackline smoothed northing

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

    #===========================================
    def _getDist(self, aX, aY, bX, bY):
        dist = np.sqrt( (bX - aX)**2 + (bY - aY)**2)
        return dist

    #===========================================
    def _lineIntersect(self, line1, line2, range):
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
                dist = getDist(x, y, cx, cy)
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
