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

from class_rectObj import rectObj
from class_mapSubstrateObj import mapSubObj

#===============================================================================
def map_master_func(humFile='',
                     sonFiles='',
                     projDir='',
                     tempC=10,
                     nchunk=500,
                     exportUnknown=False,
                     fixNoDat=False,
                     threadCnt=0,
                     tileFile=False,
                     wcp=False,
                     wcr=False,
                     lbl_set=False,
                     spdCor=0,
                     maxCrop=False,
                     USE_GPU=False,
                     remShadow=0,
                     detectDep=0,
                     smthDep=0,
                     adjDep=0,
                     pltBedPick=False,
                     rect_wcp=False,
                     rect_wcr=False,
                     mosaic=False,
                     map_sub=0):

    '''
    Main script to map substrates from side scan sonar imagery.

    ----------
    Parameters
    ----------

    -------
    Returns
    -------
    '''

    ############
    # Parameters
    flip = False #Flip port/star
    filter = int(nchunk*0.1) #Filters trackline coordinates for smoothing
    filterRange = filter #int(nchunk*0.05) #Filters range extent coordinates for smoothing


    # Specify multithreaded processing thread count
    if threadCnt==0: # Use all threads
        threadCnt=cpu_count()
    elif threadCnt<0: # Use all threads except threadCnt; i.e., (cpu_count + (-threadCnt))
        threadCnt=cpu_count()+threadCnt
        if threadCnt<0: # Make sure not negative
            threadCnt=1
    else: # Use specified threadCnt if positive
        pass

    if threadCnt>cpu_count(): # If more than total avail. threads, make cpu_count()
        threadCnt=cpu_count();
        print("\nWARNING: Specified more process threads then available, \nusing {} threads instead.".format(threadCnt))


    ############################################################################
    # Create mapObj() instance from previously created sonObj() instance       #
    ############################################################################

    ####################################################
    # Check if sonObj pickle exists, append to metaFiles
    metaDir = os.path.join(projDir, "meta")
    if os.path.exists(metaDir):
        metaFiles = sorted(glob(metaDir+os.sep+"*.meta"))
    else:
        sys.exit("No SON metadata files exist")
    del metaDir

    ############################################
    # Create a mapObj instance from pickle files
    sonObjs = []
    for meta in metaFiles:
        son = mapSubObj(meta) # Initialize mapObj()
        sonObjs.append(son) # Store mapObj() in mapObjs[]
    del meta, metaFiles

    #####################################
    # Determine which sonObj is port/star
    mapObjs = []
    for son in sonObjs:
        beam = son.beamName
        if beam == "ss_port" or beam == "ss_star":
            mapObjs.append(son)
        else:
            del son
            # pass # Don't add non-port/star objects since they can't be rectified
    del son, beam, sonObjs

    #############################################
    # Determine if smoothed trackline was created
    if hasattr(mapObjs[0], 'smthTrkFile'):
        smthTrk = True
    else:
        smthTrk = False


    ############################################################################
    # Smooth trackline and calculate range extent if necessary                 #
    ############################################################################
    # Smoothing Trackline
    # Tool:
    # https://docs.scipy.org/doc/scipy-0.14.0/reference/tutorial/interpolate.html#spline-interpolation
    # Adapted from:
    # https://github.com/remisalmon/gpx_interpolate

    if smthTrk:
        print("\nUsing existing smoothed trackline.")
    else:
        start_time = time.time()
        print("\nNo smoothed trackline available!\nSmoothing trackline...")

        # As side scan beams use same transducer/gps coords, we will smooth one
        ## beam's trackline and use for both. Use the beam with the most sonar records.
        maxRec = 0 # Stores index of recording w/ most sonar records.
        maxLen = 0 # Stores length of ping
        for i, son in enumerate(mapObjs):
            son._loadSonMeta() # Load ping metadata
            sonLen = len(son.sonMetaDF) # Number of sonar records
            if sonLen > maxLen:
                maxLen = sonLen
                maxRec = i

        # Now we will smooth using sonar beam w/ most records.
        son0 = mapObjs[maxRec]
        sonDF = son0.sonMetaDF # Get ping metadata
        sDF = son._interpTrack(df=sonDF, dropDup=True, filt=filter, deg=3) # Smooth trackline and reinterpolate trackpoints along spline
        del sonDF

        ####################################
        ####################################
        # To remove gap between sonar tiles:
        # For chunk > 0, use coords from previous chunks second to last ping
        # and assign as current chunk's first ping coords
        chunks = pd.unique(sDF['chunk_id'])

        i = 1
        while i <= max(chunks):
            # Get second to last row of previous chunk
            lastRow = sDF[sDF['chunk_id'] == i-1].iloc[[-2]]
            # Get index of first row of current chunk
            curRow = sDF[sDF['chunk_id'] == i].iloc[[0]]
            curRow = curRow.index[0]
            # Update current chunks first row from lastRow
            sDF.at[curRow, "lons"] = lastRow["lons"]
            sDF.at[curRow, "lats"] = lastRow["lats"]
            sDF.at[curRow, "utm_es"] = lastRow["utm_es"]
            sDF.at[curRow, "utm_ns"] = lastRow["utm_ns"]
            sDF.at[curRow, "cog"] = lastRow["cog"]

            i+=1
        del lastRow, curRow, i

        son0.smthTrk = sDF # Store smoothed trackline coordinates in rectObj.

        # Update other channel with smoothed coordinates
        # Determine which rectObj we need to update
        for i, son in enumerate(mapObjs):
            if i != maxRec:
                son1 = son # rectObj to update

        sDF = son0.smthTrk.copy() # Make copy of smoothed trackline coordinates
        # Update with correct record_num
        son1._loadSonMeta() # Load ping metadata
        df = son1.sonMetaDF
        sDF['chunk_id'] = df['chunk_id'] # Update chunk_id for smoothed coordinates
        sDF['record_num'] = df['record_num'] # Update record_num for smoothed coordinates
        son1.smthTrk = sDF # Store smoothed trackline coordinates in rectObj

        del sDF, df, son0, son1

        # Save smoothed trackline coordinates to file
        for son in mapObjs:
            outCSV = os.path.join(son.metaDir, "Trackline_Smth_"+son.beamName+".csv")
            son.smthTrk.to_csv(outCSV, index=False, float_format='%.14f')
            son.smthTrkFile = outCSV
            son._cleanup()
        del son, outCSV
        print("Done!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        gc.collect()
        printUsage()

        ############################################################################
        # Calculate range extent coordinates                                       #
        ############################################################################
        start_time = time.time()
        print("\nCalculating, smoothing, and interpolating range extent coordinates...")
        Parallel(n_jobs= np.min([len(mapObjs), threadCnt]), verbose=10)(delayed(son._getRangeCoords)(flip, filterRange) for son in mapObjs)
        print("Done!")
        print("Time (s):", round(time.time() - start_time, ndigits=1))
        gc.collect()
        printUsage()
