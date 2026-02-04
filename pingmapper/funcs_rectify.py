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

import sys, os

# Add 'pingmapper' to the path, may not need after pypi package...
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.append(PACKAGE_DIR)

# # For Debug
# from funcs_common import *
# from class_rectObj import rectObj

from pingmapper.funcs_common import *
from pingmapper.class_rectObj import rectObj


# =========================================================
def smoothTrackline(projDir='', x_offset='', y_offset='', nchunk ='', cog=True, threadCnt=''):

    ############
    # Parameters
    flip = False #Flip port/star
    filter = int(nchunk*0.1) #Filters trackline coordinates for smoothing
    filterRange = filter #int(nchunk*0.05) #Filters range extent coordinates for smoothing

    if cog:
        headingCol = 'cog'
    else:
        headingCol = 'heading'

    ####################################################
    # Check if sonObj pickle exists, append to metaFiles
    metaDir = os.path.join(projDir, "meta")
    if os.path.exists(metaDir):
        metaFiles = sorted(glob(metaDir+os.sep+"*.meta"))

        if len(metaFiles) == 0:
            projectMode_2a_inval()

    else:
        projectMode_2a_inval()
    del metaDir

    #############################################
    # Create a rectObj instance from pickle files
    rectObjs = []
    for meta in metaFiles:
        son = rectObj(meta) # Initialize rectObj()
        rectObjs.append(son) # Store rectObj() in rectObjs[]
    del meta, metaFiles

    #####################################
    # Determine which sonObj is port/star
    portstar = []
    for son in rectObjs:
        beam = son.beamName
        if beam == "ss_port" or beam == "ss_star":
            portstar.append(son)
        else:
            pass # Don't add non-port/star objects since they can't be rectified
    del son, beam, rectObjs

    #############################################
    # Determine if smoothed trackline was created
    if hasattr(portstar[0], 'smthTrkFile'):
        smthTrk = False
    else:
        smthTrk = True

    ############################################################################
    # Smooth GPS trackpoint coordinates                                        #
    ############################################################################

    if smthTrk:
        #####################
        #####################
        # Smoothing Trackline
        # Tool:
        # https://docs.scipy.org/doc/scipy-0.14.0/reference/tutorial/interpolate.html#spline-interpolation
        # Adapted from:
        # https://github.com/remisalmon/gpx_interpolate
        start_time = time.time()
        print("\nSmoothing trackline...")

        # As side scan beams use same transducer/gps coords, we will smooth one
        ## beam's trackline and use for both. Use the beam with the most sonar records.
        maxRec = 0 # Stores index of recording w/ most sonar records.
        maxLen = 0 # Stores length of ping
        for i, son in enumerate(portstar):
            son._loadSonMeta() # Load ping metadata
            sonLen = len(son.sonMetaDF) # Number of sonar records
            if sonLen > maxLen:
                maxLen = sonLen
                maxRec = i

        # Now we will smooth using sonar beam w/ most records.
        son0 = portstar[maxRec]
        sonDF = son0.sonMetaDF # Get ping metadata
        # sDF = son._interpTrack(df=sonDF, dropDup=True, filt=filter, deg=3) # Smooth trackline and reinterpolate trackpoints along spline
        sDF = pd.DataFrame()
        transect_dropped = []

        for name, group in sonDF.groupby('transect'):

            # # Set filter by length of group instead of chunk length
            # filter = int(len(group) * 0.1)
            # if filter > nchunk*0.1:
            #     filter = int(nchunk*0.1)

            # print('\n\n\ntransect:', name, 'filter:', filter)
            smoothed = son._interpTrack(df=group, dropDup=True, filt=filter, deg=3)

            # smooth trackline fit
            # if smoothed is not None:
            if len(smoothed.columns) > 4:
                smoothed['transect'] = int(name)
                sDF = pd.concat([sDF, smoothed], ignore_index=False)

            # Smooth trackline not fit. Need to remove transect from df
            else:
                # sonDF = sonDF.drop(group.get_group(group).index)
                # sonDF = sonDF.drop(group.index)
                sonDF = sonDF[sonDF['transect'] != name]
                transect_dropped.append(name)

            del smoothed

        # Save sonDF
        if len(transect_dropped) > 0:

            # Reassign chunk, save sonDF, update sDF (chunk/transect)
            # son0._reassignChunks(sonDF)
            # son0._loadSonMeta()
            # sonDF = son0.sonMetaDF

            c = 0
            t = 0
            for name, group in sonDF.groupby('transect'):
                for n, g in group.groupby('chunk_id'):
                    # sonDF.loc[sonDF['chunk_id'] == n]
                    sonDF['chunk_id'].loc[sonDF['chunk_id'] == n] = c 
                    sonDF['transect'].loc[sonDF['transect'] == name] = t
                    c += 1
                t+=1

            sDF['chunk_id'] = sonDF['chunk_id']
            sDF['transect'] = sonDF['transect']
            # sDF['pixM'] = sonDF['pixM'] # Add pixel size to smoothed trackline coordinates

            sDF.reset_index(inplace=True)

            # Save sonDF
            son0._saveSonMetaCSV(sonDF)

            # print(len(sDF))
            # print(sDF)
            # print(len(sonDF))
            # print(sonDF)
            # sys.exit()

            # Update other son object
            if maxRec == 0:
                son1 = portstar[1]
            else:
                son1 = portstar[0]
            
            # Get son metadata
            son1._loadSonMeta()
            sonDF = son1.sonMetaDF

            # for name, group in sonDF.groupby('transect'):
            #     if name in transect_dropped:
            #         # sonDF = sonDF.drop(group.get_group(group).index)
            #         # sonDF = sonDF.drop(group.index)
            #         sonDF = sonDF[sonDF['transect'] != name]

            for name in transect_dropped:
                sonDF = sonDF[sonDF['transect'] != name]

            c = 0
            t = 0
            for name, group in sonDF.groupby('transect'):
                for n, g in group.groupby('chunk_id'):
                    # sonDF.loc[sonDF['chunk_id'] == n]
                    sonDF['chunk_id'].loc[sonDF['chunk_id'] == n] = c 
                    sonDF['transect'].loc[sonDF['transect'] == name] = t
                    c += 1
                t+=1

            # Save sonDF
            son1._saveSonMetaCSV(sonDF)

        del sonDF

        ####################################
        ####################################
        # To remove gap between sonar tiles:
        # For chunk > 0, use coords from previous chunks second to last ping
        # and assign as current chunk's first ping coords

        chunks = pd.unique(sDF['chunk_id'])
        transects = pd.unique(sDF['transect'])

        i = 1
        t = 0
        while i <= max(chunks):

        # for i in chunks:

            # # Get second to last row of previous chunk
            # lastRow = sDF[sDF['chunk_id'] == i-1].iloc[[-2]]
            # Get index of first row of current chunk
            curRow = sDF[sDF['chunk_id'] == i].iloc[[0]]
            curTransect = curRow['transect'].values[0]
            curRow = curRow.index[0]
            
            if curTransect == t:
                # Get second to last row of previous chunk
                lastRow = sDF[sDF['chunk_id'] == i-1].iloc[-2]

                # Update current chunks first row from lastRow
                sDF.at[curRow, "lons"] = float(lastRow["lons"])
                sDF.at[curRow, "lats"] = float(lastRow["lats"])
                sDF.at[curRow, "utm_es"] = float(lastRow["utm_es"])
                sDF.at[curRow, "utm_ns"] = float(lastRow["utm_ns"])
                sDF.at[curRow, "cog"] = float(lastRow["cog"])
                sDF.at[curRow, "instr_heading"] = float(lastRow["instr_heading"])
                # sDF.at[curRow, 'pixM'] = lastRow['pixM']

                del lastRow
            else:
                t += 1

            i+=1
        del curRow, i

        son0.smthTrk = sDF # Store smoothed trackline coordinates in rectObj.
        
        # Do positional correction
        if x_offset != 0.0 or y_offset != 0.0:
            son0._applyPosOffset(x_offset, y_offset)

        # Update other channel with smoothed coordinates
        # Determine which rectObj we need to update
        for i, son in enumerate(portstar):
            if i != maxRec:
                son1 = son # rectObj to update

        sDF = son0.smthTrk.copy() # Make copy of smoothed trackline coordinates
        # Update with correct record_num
        son1._loadSonMeta() # Load ping metadata
        df = son1.sonMetaDF
        sDF['chunk_id'] = df['chunk_id'] # Update chunk_id for smoothed coordinates
        sDF['record_num'] = df['record_num'] # Update record_num for smoothed coordinates
        # sDF['pixM'] = df['pixM']
        son1.smthTrk = sDF # Store smoothed trackline coordinates in rectObj

        del sDF, df, son0, son1

        # Save smoothed trackline coordinates to file
        csvNames = {}
        for son in portstar:
            outCSV = os.path.join(son.metaDir, "Trackline_Smth_"+son.beamName+".csv")
            son.smthTrk.to_csv(outCSV, index=False, float_format='%.14f')
            son.smthTrkFile = outCSV
            csvNames[son.beamName] = outCSV
            son._cleanup()
        del son, outCSV
        print("Done!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        gc.collect()
        printUsage()

        ############################################################################
        # Calculate range extent coordinates                                       #
        ############################################################################
        # cog=True

        start_time = time.time()
        if cog:
            print("\nCalculating, smoothing, and interpolating range extent coordinates...")
        else:
            print("\nCalculating range extent coordinates from vessel heading...")
        Parallel(n_jobs= np.min([len(portstar), threadCnt]), verbose=10)(delayed(son._getRangeCoords)(flip, filterRange, cog) for son in portstar)
        print("Done!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        gc.collect()
        printUsage()

        return csvNames

    else:
        print("\nUsing existing smoothed trackline.")