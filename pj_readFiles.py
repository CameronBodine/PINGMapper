

from common_funcs import *
from c_sonObj import sonObj
from joblib import delayed
import time

# # =========================================================
# def fread(infile, num, typ):
#     """
#     This function reads binary data in a file
#     """
#     dat = arr(typ)
#     dat.fromfile(infile, num)
#     return(list(dat))
#
# #===========================================
# def getHead(son, sonIndex, headStruct, humdat, trans, t):
#     sonHead = {'lat':-1}
#     file = open(son.sonFile, 'rb')
#     for key, val in headStruct.items():
#         index = sonIndex + val[0] + val[1]
#         file.seek(index)
#         if val[2] == 4:
#             byte = struct.unpack('>i', arr('B', fread(file, val[2], 'B')).tobytes())[0]
#         elif 1 < val[2] <4:
#             byte = struct.unpack('>h', arr('b', fread(file, val[2],'b')).tobytes() )[0]
#         else:
#             byte = fread(file, val[2], 'b')[0]
#         # print(val[-1],":",byte)
#         sonHead[val[-1]] = byte
#
#     file.close()
#
#     # Make necessary conversions
#     lat = np.arctan(np.tan(np.arctan(np.exp(sonHead['utm_y']/ 6378388.0)) * 2.0 - 1.570796326794897) * 1.0067642927) * 57.295779513082302
#     lon = (sonHead['utm_x'] * 57.295779513082302) / 6378388.0
#
#     sonHead['lon'] = lon
#     sonHead['lat'] = lat
#
#     lon, lat = trans(lon, lat)
#     sonHead['e'] = lon
#     sonHead['n'] = lat
#
#     sonHead['instr_heading'] = sonHead['instr_heading']/10
#     sonHead['speed_ms'] = sonHead['speed_ms']/10
#     sonHead['inst_dep_m'] = sonHead['inst_dep_m']/10
#     sonHead['f'] = sonHead['f']/1000
#     sonHead['time_s'] = sonHead['time_s']/1000
#     sonHead['tempC'] = t*10
#     # Can we figure out a way to base transducer length on where we think the recording came from?
#     # I can't see anywhere where this value is used.
#     sonHead['t'] = 0.108
#     try:
#         starttime = float(humdat['unix_time'])
#         sonHead['caltime'] = starttime + sonHead['time_s']
#     except :
#         sonHead['caltime'] = 0
#
#     # if sonHead['beam']==3 or sonHead['beam']==2:
#     #     dist = ((np.tan(25*0.0174532925))*sonHead['inst_dep_m']) +(tvg)
#     #     bearing = 0.0174532925*sonHead['instr_heading'] - (pi/2)
#     #     bearing = bearing % 360
#     #     sonHead['heading'] = bearing
#     # print("\n\n", sonHead, "\n\n")
#     return sonHead
#
# #===========================================
# def getSonMeta(son):
#     # Read son header for every ping
#     # Save to csv
#     # Load data from sonObj
#     outDir = son.metaDir
#     headStruct = son.headStruct
#     nchunk = son.nchunk
#     humdat = son.humDat
#     # trans = son.trans
#     idxFile = son.sonFile.replace(".SON", ".IDX")
#     son.idxFile = idxFile
#     t = son.tempC
#     cs2cs_args = son.humDat['epsg']
#
#     try:
#        trans =  pyproj.Proj(init=cs2cs_args)
#     except:
#        trans =  pyproj.Proj(cs2cs_args.lstrip(), inverse=True)
#
#     # Prepare dictionary to hold all header data
#     head = defaultdict(list)
#     for key, val in headStruct.items():
#         head[val[-1]] = []
#
#     # First check if .idx file exists and get that data
#     idx = {'record_num': [],
#            'time_s': [],
#            'index': [],
#            'chunk_id': []}
#
#
#     if os.path.exists(idxFile):
#         idxLen = os.path.getsize(idxFile)
#         idxFile = open(idxFile, 'rb')
#         i = j = chunk = 0
#         while i < idxLen:
#             idx['time_s'].append(struct.unpack('>I', arr('B', fread(idxFile, 4, 'B')).tobytes())[0])
#             sonIndex = struct.unpack('>I', arr('B', fread(idxFile, 4, 'B')).tobytes())[0]
#             idx['index'].append(sonIndex)
#             head['index'].append(sonIndex)
#             idx['chunk_id'].append(chunk)
#             head['chunk_id'].append(chunk)
#             headerDat = getHead(son, sonIndex, headStruct, humdat, trans, t)
#             # headerDat = son._getHead(sonIndex)
#             for key, val in headerDat.items():
#                 head[key].append(val)
#             idx['record_num'].append(headerDat['record_num'])
#             i+=8
#             j+=1
#             if j == nchunk:
#                 j=0
#                 chunk+=1
#             # print("\n\n", idx, "\n\n")
#     else:
#         sys.exit("idx missing.  need to figure this out")
#
#     # print(head,"\n\n\n")
#     # print(idx)
#     headDF = pd.DataFrame.from_dict(head, orient="index").T
#     idxDF = pd.DataFrame.from_dict(idx, orient="index").T
#
#     # Write data to csv
#     beam = os.path.split(son.sonFile)[-1].split(".")[0]
#     outCSV = os.path.join(outDir, beam+"_meta.csv")
#     headDF.to_csv(outCSV, index=False, float_format='%.14f')
#
#     outCSV = os.path.join(outDir, beam+"_idx.csv")
#     idxDF.to_csv(outCSV, index=False, float_format='%.14f')

#===========================================
def read_master_func(sonFiles, humFile, projDir, tempC, nchunk):
    start_time = time.time()

    ###################################
    # Decode DAT file (varies by model)
    print("\nGetting DAT Metadata...")
    # 1) Create sonObj to store sonar attributes, access processing
    # functions, and access sonar data
    son = sonObj(sonFiles[0], humFile, projDir, tempC, nchunk)
    son.datLen = os.path.getsize(son.humFile)

    # 2) Determine humdat structure
    son._getHumDatStruct()

    # 3) Read in the humdat data
    if son.isOnix == 0:
        son._getHumdat()
    else:
        son._decodeOnix()

    # 4) Determine epsg code and transformation (if we can, ONIX doesn't have lat/lon in DAT)
    son._getEPSG()

    # 5) Save DAT metadata to file (csv)
    metaDir = os.path.join(projDir, 'meta')
    try:
        os.mkdir(metaDir)
    except:
        pass

    son.metaDir = metaDir
    outFile = os.path.join(metaDir, 'DAT_meta.csv')
    pd.DataFrame.from_dict(son.humDat, orient='index').T.to_csv(outFile, index=False)
    son.datMetaFile = outFile
    print("Done!")

    #####################################################
    # Try copying sonObj instance for every sonar channel
    chanAvail = {}
    for s in sonFiles:
        beam = os.path.split(s)[-1].split('.')[0]
        chanAvail[beam] = s

    sonObjs = []
    for chan, file in chanAvail.items():
        if chan == 'B000':
            B000 = deepcopy(son)
            B000.beamName = 'down_lowfreq'
            B000.outDir = os.path.join(B000.projDir, B000.beamName)
            B000.beam = chan
            B000.sonFile = file
            sonObjs.append(B000)

        elif chan == 'B001':
            B001 = deepcopy(son)
            B001.beamName = 'down_highfreq'
            B001.outDir = os.path.join(B001.projDir, B001.beamName)
            B001.beam = chan
            B001.sonFile = file
            sonObjs.append(B001)

        elif chan == 'B002':
            B002 = deepcopy(son)
            B002.beamName = 'sidescan_port'
            B002.outDir = os.path.join(B002.projDir, B002.beamName)
            B002.beam = chan
            B002.sonFile = file
            sonObjs.append(B002)

        elif chan == 'B003':
            B003 = deepcopy(son)
            B003.beamName = 'sidescan_starboard'
            B003.outDir = os.path.join(B003.projDir, B003.beamName)
            B003.beam = chan
            B003.sonFile = file
            sonObjs.append(B003)

        elif chan == 'B004':
            B004 = deepcopy(son)
            B004.beamName = 'down_vhighfreq'
            B004.outDir = os.path.join(B004.projDir, B004.beamName)
            B004.beam = chan
            B004.sonFile = file
            sonObjs.append(B004)

        else:
            pass


    ################################################
    # # Determine ping header length (varies by model)
    print("\nGetting Header Structure...")
    cntSON = len(sonObjs) # Number of sonar files
    gotHeader = False # Flag indicating if length of header is found
    i = 0 # Counter for iterating son files
    while gotHeader is False:
        try:
            son = sonObjs[i]
            headbytes = son._cntHead() # Try counting head bytes
            if headbytes > 0: # See if
                print("Header Length: {}".format(headbytes))
                gotHeader = True
            else:
                i+=1
        except:
            sys.exit("\n#####\nERROR: Out of SON files... \n"+
            "Unable to determine header length.")

    # Update sonar objects with headBytes
    if headbytes > 0:
        for son in sonObjs:
            son.headBytes = headbytes

    #################################################
    # Now get the SON header structure and attributes
    for son in sonObjs:
        son._getHeadStruct()

    # Let's check and make sure the header structure is correct
    # If it is not correct, try to automatically decode structure
    for son in sonObjs:
        son._checkHeadStruct()

    for son in sonObjs:
        headValid = son.headValid
        if headValid[0] is True:
            print(son.beamName, ":", "Done!")
        elif headValid[0] is False:
            print("\n#####\nERROR: Wrong Header Structure")
            print("Expected {} at index {}.".format(headValid[1], headValid[2]))
            print("Found {} instead.".format(headValid[3]))
            print("Attempting to decode header structure.....")
            son._decodeHeadStruct()
        else:
            print("\n#####\nERROR: Wrong Header Structure")
            print("Attempting to decode header structure.....")
            son._decodeHeadStruct()

    #If we had to decode header structure,
    #let's make sure it decoded correctly
    for son in sonObjs:
        if son.headValid[0] is not True:
            son._checkHeadStruct()
            headValid = son.headValid
            if headValid[0] is True:
                print("Succesfully determined header structure!")
            else:
                print("\n#####\nERROR:Unable to decode header structure")
                print("Expected {} at index {}.".format(headValid[1], headValid[2]))
                print("Found {} instead.".format(headValid[3]))
                print("Terminating script.")
                sys.exit()

    ######################################
    # Let's get the metadata for each ping
    print("\nGetting SON file header metadata:")
    # Check to see if metadata is already saved to csv
    toProcess = []
    for son in sonObjs:
        beam = os.path.split(son.sonFile)[-1].split(".")[0]
        file = os.path.join(son.metaDir, beam+"_meta.csv")
        if os.path.exists(file):
            print("File {0} exists. No need to re-process.".format(file))
            son.sonMetaFile = file
        else:
            toProcess.append(son)

    if len(toProcess) > 0:
        Parallel(n_jobs= np.min([len(toProcess), cpu_count()]), verbose=10)(delayed(son._getSonMeta)() for son in toProcess)
    print("Done!")

    ########################
    # Let's export the tiles
    print("\nGetting sonar data and exporting tile images:")

    metaDir = sonObjs[0].metaDir
    sonMeta = sorted(glob(os.path.join(metaDir,'*B*_meta.csv')))
    for i in range(0,len(sonObjs)):
        sonObjs[i].sonMetaFile = sonMeta[i]

    for son in sonObjs:
        try:
            os.mkdir(son.outDir)
        except:
            pass

    Parallel(n_jobs= np.min([len(sonObjs), cpu_count()]), verbose=10)(delayed(son._getScansChunk)() for son in sonObjs)












    for son in sonObjs:
        print("\n\n")
        print(son)

    print(round((time.time() - start_time),ndigits=2))
