
'''
'''


#########
# Imports
import sys, os
sys.path.insert(0, 'src')

from class_mapSubstrateObj import mapSubObj
from class_portstarObj import portstarObj
from joblib import Parallel, delayed, cpu_count
from glob import glob
import numpy as np
import tensorflow as tf
import shutil


############
# Parameters
threadCnt = 0
egnDir = 'WBL_EGN'
inDirs = r'/home/cbodine/Desktop/MN_MusselProject/'+egnDir
rawDir = 'WBL_Raw'
outDir_parent = inDirs.replace('EGN', 'RawEGN_Avg')
map_sub = True
pltSubClass = True
cleanTempFiles = False

if not os.path.exists(outDir_parent):
    os.mkdir(outDir_parent)


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


###########
# Functions
def npzAvg(k, v, npz_raw, outDir_npz, nchunk):

    try:

        # Get npzs
        npz_1 = np.load(v) # EGN
        npz_2 = np.load(npz_raw[k]) # Raw

        # Get class names
        classes = npz_1['classes']

        # Get substrate
        npz_1 = npz_1['substrate']
        npz_2 = npz_2['substrate']

        # # make sure same size
        # if npz_1.shape[1] != nchunk:
        #     npz_1 = np.resize(npz_1, (npz_1.shape[0], nchunk, npz_1.shape[2]))
        # if npz_2.shape[1] != nchunk:
        #     npz_2 = np.resize(npz_2, (npz_2.shape[0], nchunk, npz_2.shape[2]))

        # Convert to probabilities
        npz_1 = tf.nn.softmax(npz_1)
        npz_2 = tf.nn.softmax(npz_2)

        # Get classified wood from EGN
        npz_1_class = np.argmax(npz_1, -1)
        wood = np.where(npz_1_class == 5, 1, 0)
        wood_mask = np.where(npz_1_class == 5, 0, 1)

        # Get classified smooth fines from EGN
        fines_flat = np.where(npz_1_class == 2, 1, 0)
        fines_flat_mask = np.where(npz_1_class == 2, 0, 1)

        # Get classified other from EGN
        other = np.where(npz_1_class == 6, 1, 0)
        other_mask = np.where(npz_1_class == 6, 0, 1)

        # Get average
        npz_3 = np.zeros(npz_1.shape)
        npz_3[:,:,:] = np.nan

        for i in range(npz_1.shape[-1]):
            a = npz_1[:,:,i]
            b = npz_2[:,:,i]

            c = np.nansum(np.dstack((a, b)), axis=-1) / 2
            # c = np.nanmax(np.dstack((a, b)), axis=-1)

            # Mask wood
            c = c*wood_mask

            # If c is wood, set to wood
            if i == 5:
                c = wood + c

            # Mask fines flat
            c = c*fines_flat_mask

            # if c is fines flat, set to fines flat
            if i == 2:
                c = fines_flat + c

            # Mask other
            c = c*other_mask

            # if c is other, set to other
            if i == 6:
                c = other+c

            npz_3[:,:,i] = c
        del a, b, c

        # Save npz file
        datadict = {}
        datadict['substrate'] = npz_3.astype('float16')
        datadict['classes'] = classes

        f = os.path.basename(v)
        f = os.path.join(outDir_npz, f)

        np.savez_compressed(f, **datadict)

        return

    except:
        
        return

    



def doWork(i, projDir, outDir_parent):

    # Prepare output directroy
    projName = os.path.basename(projDir)
    outDir = os.path.join(outDir_parent, projName)
    if not os.path.exists(outDir):
        os.mkdir(outDir)

    outDir = os.path.join(outDir, 'substrate')
    if not os.path.exists(outDir):
        os.mkdir(outDir)


    ####################################################
    # Check if sonObj pickle exists, append to metaFiles
    metaDir = os.path.join(projDir, "meta")
    if os.path.exists(metaDir):
        metaFiles = sorted(glob(metaDir+os.sep+"*.meta"))

    #     if len(metaFiles) == 0:
    #         projectMode_2a_inval()

    else:
        # projectMode_2a_inval()
        sys.exit('Meta dir does not exist')
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
        if beam == "ss_port":
            mapObjs.append(son)
        elif beam == "ss_star":
            mapObjs.append(son)
        else:
            pass # Don't add non-port/star objects since they can't be rectified
    del son, beam, sonObjs

    if not os.path.exists(outDir):
        os.mkdir(outDir)


    #############################################
    # Average EGN and Raw prediction, save to npz

    print('\n\nAveraging Raw and EGN predictions...')

    for son in mapObjs:

        # Get EGN npz filenames
        npz_egn = son._getSubstrateNpz()

        # # For Testing
        # for i in range(len(npz_egn)):
        #     if i>10:
        #         npz_egn.pop(i)

        # Update file paths for raw npzs
        npz_raw = {}
        for k, v in npz_egn.items():
            npz_raw[k] = v.replace(egnDir, rawDir)

        # Prepare outDirectory
        son.substrateDir = outDir

        outDir_npz = os.path.join(outDir, 'predict_npz')
        if not os.path.exists(outDir_npz):
            os.mkdir(outDir_npz)


        Parallel(n_jobs= np.min([len(npz_egn), threadCnt]), verbose=10)(delayed(npzAvg)(k, v, npz_raw, outDir_npz, son.nchunk) for k, v in npz_egn.items())
        

    ##########################
    # Plotting substrate class
    if pltSubClass:
        print('\n\nExporting substrate plots...')

        probs = True

        # Out directory
        outDir = os.path.join(mapObjs[0].substrateDir, 'plots')
        if not os.path.exists(outDir):
            os.mkdir(outDir)


        # Get chunk id for mapping substrate
        for son in mapObjs:
            # Set outDir
            son.outDir = outDir

            # Get Substrate npz's
            toMap = son._getSubstrateNpz()

            print('\n\tExporting substrate plots for', len(toMap), son.beamName, 'chunks:')

            # # Plot substrate classification
            # for c, f in toMap.items():
            #     print('\n\n\n\n****Chunk', c)
            #     son._pltSubClass('max', c, f, spdCor=1, maxCrop=True)

            Parallel(n_jobs=np.min([len(toMap), threadCnt]), verbose=10)(delayed(son._pltSubClass)('max', c, f, spdCor=1, maxCrop=True, probs=probs) for c, f in toMap.items())

            del toMap


    ########################
    # Map the classification
    print('\n\n\nMapping substrate classification...')


    # Set output director
    outDir_map = os.path.join(outDir, 'map_substrate_raster')

    for son in mapObjs:
        son.map_sub = map_sub

        # Set outDir
        # son.substrateDir = outDir
        son.outDir = outDir_map

        if not os.path.exists(outDir_map):
            os.mkdir(outDir_map)

        # Store substrate npz filenames
        npz = son._getSubstrateNpz()

        # Create dictionary to store port/star pairs
        if not 'toMap' in locals():
            toMap = npz
        else:
            for k, v in npz.items():
                # Get existing npz file
                e = toMap[k]

                # Add existing and new npz as list. Add port as first element
                if 'port' in e:
                    toMap[k] = [e, v]
                else:
                    toMap[k] = [v, e]


    # Create portstarObj
    psObj = portstarObj(mapObjs)

    # for c, f in toMap.items():
    #     print(c, f)
    #     psObj._mapSubstrate('max', c, f)

    Parallel(n_jobs=np.min([len(toMap), threadCnt]), verbose=10)(delayed(psObj._mapSubstrate)('max', c, f) for c, f in toMap.items())


    del psObj


    ################
    # Create Polygon
    print('\nConverting substrate rasters into shapefile...')

    outDir_map = os.path.join(outDir, 'map_substrate_polygon')
    for son in mapObjs:
        son.outDir = outDir_map
        son.substrateDir = outDir

    # Create portstar object
    psObj = portstarObj(mapObjs)

    # Switch off rect_wcp and rect_wcr
    psObj.port.rect_wcp = False
    psObj.port.rect_wcr = False
    psObj.port.map_predict = False

    # Make sure map_sub is set to true
    psObj.port.map_sub = True

    psObj._rasterToPoly(1, threadCnt, 0)


    ######################################
    # Copy son meta and update directories

    son = mapObjs[0]
    source = son.metaDir
    destination = os.path.dirname(outDir) # remove substrate from dir
    destination = os.path.join(destination, 'meta')

    shutil.copytree(source, destination)

    # Del son and mapObjs
    for son in mapObjs:
        del son
    del mapObjs


    ###########################################################
    # Create son objects from current directory and update dirs

    ####
    # Check if sonObj pickle exists, append to metaFiles
    metaDir = destination
    if os.path.exists(metaDir):
        metaFiles = sorted(glob(metaDir+os.sep+"*.meta"))

        if len(metaFiles) == 0:
            projectMode_2a_inval()

    else:
        projectMode_2a_inval()
    del metaDir


    ####
    # Create a mapObj instance from pickle files
    sonObjs = []
    for meta in metaFiles:
        son = mapSubObj(meta) # Initialize mapObj()
        sonObjs.append(son) # Store mapObj() in mapObjs[]
    del meta, metaFiles

    ####
    # Update project directories
    source = os.path.dirname(source) # remove meta from dir
    destination = os.path.dirname(destination)

    for son in sonObjs:
        
        dir_to_replace = source
        for attr, value in son.__dict__.items():
            if dir_to_replace in str(value):
                v = value.replace(dir_to_replace, '')
                v = v.replace('\\', '/')
                if len(v) > 0:
                    v = v[1:]

                print('\n\n\n', v)
                v = os.path.join(destination, v)
                v = os.path.normpath(v)
                print(v)
                setattr(son, attr, v)

        son._pickleSon()

    
    ##################
    # Clean temp files
    if cleanTempFiles:

        # 'map_substrate_mosaic'
        try:
            shutil.rmtree(os.path.join(outDir, 'map_substrate_mosaic'))
        except:
            pass

        # map_substrate_raster
        try:
            shutil.rmtree(os.path.join(outDir, 'map_substrate_raster'))
        except:
            pass

        # predict_npz
        try:
            shutil.rmtree(os.path.join(outDir, 'predict_npz'))
        except:
            pass





#########
# Do Work

# Get project folders
projDirs = glob(os.path.join(inDirs, '*'))
projDirs = sorted(projDirs, reverse=True)

# # For testing
# projDirs = [d for d in projDirs if 'LEA_020' in d]
# print(projDirs)

proj_cnt = len(projDirs)

for i, p in enumerate(projDirs):
    print(i, p)
    doWork(i, p, outDir_parent)

# Parallel(n_jobs= np.min([len(projDirs), threadCnt]), verbose=10)(delayed(doWork)(i, p, outDir_parent) for i, p in enumerate(projDirs))

