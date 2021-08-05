
from funcs_common import *
from c_sonObj import sonObj
from scipy.interpolate import splprep, splev
from skimage.transform import PiecewiseAffineTransform, warp
from rasterio.transform import from_origin
from PIL import Image

class rectObj(sonObj):
    #===========================================
    def __init__(self):
        sonObj.__init__(self, sonFile=None, humFile=None, projDir=None, tempC=None, nchunk=None)

    #===========================================
    def _interpTrack(self, df, dfOrig=None, dropDup=True, xlon='lon', ylat='lat', xutm='utm_e',
                     yutm='utm_n', zU='time_s', filt=0, deg=3):

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

        # Check if enough points to interpolate
        # If not, too many overlapping pings
        if len(x) <= deg:
            return dfOrig[['chunk_id', 'record_num', 'ping_cnt', 'time_s', 'pix_m']]

        # Interpolate trackline
        try:
            tck, _ = splprep([x,y], u=t, k=deg, s=0)
        except:
            # Time is messed up (negative time offset)
            # Use record num instead
            zU = 'record_num'
            t = dfFilt[zU].to_numpy()
            t = np.r_[t[okay], t[-1]]
            tck, _ = splprep([x,y], u=t, k=deg, s=0)

        u_interp = dfOrig[zU].to_numpy()
        x_interp = splev(u_interp, tck)

        # Store smoothed trackpoints in df
        smooth = {'chunk_id': dfOrig['chunk_id'],
                  'record_num': dfOrig['record_num'],
                  'ping_cnt': dfOrig['ping_cnt'],
                  'time_s': dfOrig['time_s'],
                  'pix_m': dfOrig['pix_m'],
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
    def _getRangeCoords(self, flip, filt):
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

        self._loadSonMeta()
        sonMetaDF = self.sonMetaDF

        # Get smoothed trackline
        sDF = self.smthTrk

        # Determine ping bearing
        if self.beamName == 'ss_port':
            rotate = -90
        else:
            rotate = 90
        if flip == True:
            rotate *= -1

        sDF[ping_bearing] = (sDF['cog']+rotate) % 360

        # Calculate max range for each chunk
        chunk = sDF.groupby(chunk_id)
        maxPing = chunk[ping_cnt].max()
        pix_m = chunk['pix_m'].min()
        for i in maxPing.index:
            sDF.loc[sDF[chunk_id]==i, range] = maxPing[i]*pix_m[i]

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
        sDF = sDF.dropna()
        self.smthTrk = sDF

        self._interpRangeCoords(filt)
        # return

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
                    if len(dropping) == 1:
                        drop[i] = True
                    elif len(dropping) > 1:
                        lastKey = max(dropping)
                        del dropping[lastKey] # Don't remove last element
                        drop[i] = True # Potentially remove this
                        for k, v in dropping.items():
                            drop[k] = True
                            last = k+1
                    else:
                        pass
                else:
                    pass
        rDF = rDF[~drop]

        for chunk in pd.unique(rDF['chunk_id']):
            rchunkDF = rDF[rDF['chunk_id']==chunk].copy()
            schunkDF = sDF[sDF['chunk_id']==chunk].copy()
            smthChunk = self._interpTrack(df=rchunkDF, dfOrig=schunkDF, xlon=rlon,
                                          ylat=rlat, xutm=re, yutm=rn, filt=0, deg=1)
            if 'rsDF' not in locals():
                rsDF = smthChunk.copy()
            else:
                rsDF = rsDF.append(smthChunk, ignore_index=True)

        # rsDF = self._interpTrack(df=rDF, dfOrig=sDF, xlon=rlon, ylat=rlat, xutm=re, yutm=rn,
        #                          filt=0, deg=1)

        e_smth, n_smth = self.trans(rsDF[rlons].to_numpy(), rsDF[rlats].to_numpy())
        rsDF[res] = e_smth
        rsDF[rns] = n_smth
        rsDF.rename(columns={'cog': 'range_cog'}, inplace=True)

        # beam = self.beamName.split('_')[1]
        # outCSV = os.path.join(self.metaDir, "RangeExtent_"+beam+".csv")
        # rsDF.to_csv(outCSV, index=False, float_format='%.14f')

        # Join smoothed trackline to smoothed range extent
        # rsDF = rsDF.set_index('record_num').join(sDF.set_index('record_num'))
        sDF = sDF[['record_num', 'lons', 'lats', 'utm_es', 'utm_ns', 'cog']]
        rsDF = rsDF.set_index('record_num').join(sDF.set_index('record_num'))

        # Overwrite Trackline_Smth_son.beamName.csv
        outCSV = os.path.join(self.metaDir, "Trackline_Smth_"+self.beamName+".csv")
        rsDF.to_csv(outCSV, index=True, float_format='%.14f')

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

    #===========================================
    def _rectSon(self, detectDepth, smthDep, remWater=True, filt=50, adjDep=0, wgs=False):
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
        firstChunk = min(chunks)

        if wgs is True:
            epsg = self.humDat['wgs']
            xRange = 'range_lons'
            yRange = 'range_lats'
            xTrk = 'lons'
            yTrk = 'lats'
        else:
            epsg = self.humDat['epsg']
            xRange = 'range_es'
            yRange = 'range_ns'
            xTrk = 'utm_es'
            yTrk = 'utm_ns'

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
                imgName = projName+'_'+imgOutPrefix+'_'+beamName+'_'+addZero+str(int(chunk))+'.png'

                inImgs[int(chunk)] = os.path.join(self.outDir,imgOutPrefix, imgName)

        # test = {}
        # test[chunks[-1]] = inImgs[chunks[-1]]
        #
        # inImgs = test
        # print("\n\n\n", inImgs)
        # Iterate images and rectify
        for i, imgPath in inImgs.items():

            ############################
            # Prepare source coordinates
            # Open image to rectify
            if tileFlag:
                img = np.asarray(Image.open(imgPath)).copy()
            else:
                self._getScanChunkSingle(i, remWater, detectDepth, smthDep)
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
