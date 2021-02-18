

from common_funcs import *
from c_sonObj import sonObj
from dask.distributed import Client, wait
from joblib import delayed as jd
import time


#===========================================
def read_master_func(sonFiles, humFile, projDir, tempC, nchunk):
    start_time = time.time()
    # client = Client()

    ###################################
    # Decode DAT file (varies by model)
    print("\nGetting DAT Metadata...")
    # 1) Create sonObj to store sonar attributes, access processing
    # functions, and access sonar data
    son = sonObj(sonFiles[0], humFile, projDir, tempC, nchunk)
    son.datLen = os.path.getsize(son.humFile)

    # 2) Attempt to decode DAT file
    son._decodeHumdat()

    # 3) Determine epsg code and transformation (if we can, ONIX doesn't have lat/lon in DAT)
    son._getEPSG()

    # 4) Save DAT metadata to file (csv)
    metaDir = os.path.join(projDir, 'meta')
    try:
        os.mkdir(metaDir)
    except:
        pass

    son.metaDir = metaDir
    outFile = os.path.join(metaDir, 'DAT_meta.csv')
    son._toCSV(son.humDat, outFile)
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
            B000.sonFile = file
            sonObjs.append(B000)

        elif chan == 'B001':
            B001 = deepcopy(son)
            B001.beamName = 'down_highfreq'
            B001.sonFile = file
            sonObjs.append(B001)

        elif chan == 'B002':
            B002 = deepcopy(son)
            B002.beamName = 'sidescan_port'
            B002.sonFile = file
            sonObjs.append(B002)

        elif chan == 'B003':
            B003 = deepcopy(son)
            B003.beamName = 'sidescan_starboard'
            B003.sonFile = file
            sonObjs.append(B003)

        elif chan == 'B004':
            B004 = deepcopy(son)
            B004.beamName = 'down_vhighfreq'
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
        # for son in toProcess:
        #     son._getSonMeta()
        # backend="threading" makes it so same object is returned
        Parallel(n_jobs= np.min([len(toProcess), cpu_count()]), verbose=10, backend="threading")(jd(son._getSonMeta)() for son in toProcess)
    print("Done!")

    ########################
    # Let's export the tiles
    print("\nGetting sonar data and exporting tile images:")

    Parallel(n_jobs= np.min([len(sonObjs), cpu_count()]), verbose=10)(delayed(son._getScansChunk)() for son in sonObjs)

    for son in sonObjs:
        print(son)

    ## Below works
    # try:
    #     B000 = client.submit(sonObjs[0]._getScansChunk)
    #     B001 = client.submit(sonObjs[1]._getScansChunk)
    #     B002 = client.submit(sonObjs[2]._getScansChunk)
    #     B003 = client.submit(sonObjs[3]._getScansChunk)
    # except:
    #     pass
    # wait(B003)
    ## Above works

    print("Done!")
    print(round((time.time() - start_time),ndigits=2))
