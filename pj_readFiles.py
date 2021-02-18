

from common_funcs import *
from py3read_single_csb import pyread
import class_sonMeta
from collections import defaultdict

# =========================================================
def fread(infile, num, typ):
    """
    This function reads binary data in a file
    """
    dat = arr(typ)
    dat.fromfile(infile, num)
    return(list(dat))

#===========================================
def cntHead(son):
    i = 0
    foundEnd = False
    file = open(son, 'rb')
    while foundEnd is False and i < 200:
        lastPos = file.tell() # Get current position in file
        byte = fread(file, 1, 'B')
        # print("Val: {} Pos: {}".format(byte, lastPos))
        if byte[0] == 33 and lastPos > 3:
            # Double check we found the actual end
            file.seek(-6, 1)
            byte = fread(file, 1, 'B')
            if byte[0] == 160:
                foundEnd = True
            else:
                # Didn't find the end of header
                # Move cursor back to lastPos
                file.seek(lastPos)
        else:
            # Haven't found the end
            pass
        i+=1

    # i reaches 200, then we have exceeded known Humminbird header length
    if i == 200:
        i = 0

    file.close()
    headbytes = i
    return headbytes

#===========================================
def getHeadStruct(headbytes):
    # Returns dictionary with header structure
    # Format: byteVal : [byteIndex, offset, dataLen, name]
    # byteVal = Spacer value (integer) preceding attribute values (i.e. depth)
    # byteIndex = Index indicating position of byteVal
    # offset = Byte offset for the actual data
    # dataLen = number of bytes for data (i.e. utm_x is 4 bytes long)
    # name = name of attribute

    if headbytes == 67:
        headStruct = {
        128:[4, 1, 4, 'record_num'], #Record Number (Unique for each ping)
        129:[9, 1, 4, 'time_s'], #Time Elapsed milliseconds
        130:[14, 1, 4, 'utm_x'], #UTM X
        131:[19, 1, 4, 'utm_y'], #UTM Y
        132.1:[24, 1, 2, 'gps1'], #GPS quality flag (?)
        132.2:[24, 3, 2, 'instr_heading'], #Heading
        133.1:[29, 1, 2, 'gps2'], #GPS quality flag (?)
        133.2:[29, 3, 2, 'speed_ms'], #Speed in meters/second
        135:[34, 1, 4, 'inst_dep_m'], #Depth in centimeters, then converted to meters
        80:[39, 1, 1, 'beam'], #Beam number: 0 (50 or 83 kHz), 1 (200 kHz), 2 (SI Poort), 3 (SI Starboard)
        81:[41, 1, 1, 'volt_scale'], #Volt Scale (?)
        146:[43, 1, 4, 'f'], #Frequency of beam in hertz
        83:[48, 1, 1, "unknown_83"], #Unknown (number of satellites???)
        84:[50, 1, 1, "unknown_84"], #Unknown
        149:[52, 1, 4, "unknown_149"], #Unknown (magnetic deviation???)
        86:[57, 1, 1, 'unknown_86'], #Unknown (+-X error)
        87:[59, 1, 1, 'unknown_87'], #Unknown (+-Y error)
        160:[61, 1, 4, 'ping_cnt'] #Number of ping values (in bytes)
        }

    # 1199 and Helix
    elif headbytes == 72:
        headStruct = {
        128:[4, 1, 4, 'record_num'], #Record Number (Unique for each ping)
        129:[9, 1, 4, 'time_s'], #Time Elapsed milliseconds
        130:[14, 1, 4, 'utm_x'], #UTM X
        131:[19, 1, 4, 'utm_y'], #UTM Y
        132.1:[24, 1, 2, 'gps1'], #GPS quality flag (?)
        132.2:[24, 3, 2, 'instr_heading'], #Heading
        133.1:[29, 1, 2, 'gps2'], #GPS quality flag (?)
        133.2:[29, 3, 2, 'speed_ms'], #Speed in meters/second
        134:[34, 1, 4, 'unknown_134'], #Unknown
        135:[39, 1, 4, 'inst_dep_m'], #Depth in centimeters, then converted to meters
        80:[44, 1, 1, 'beam'], #Beam number: 0 (50 or 83 kHz), 1 (200 kHz), 2 (SI Poort), 3 (SI Starboard)
        81:[46, 1, 1, 'volt_scale'], #Volt Scale (?)
        146:[48, 1, 4, 'f'], #Frequency of beam in hertz
        83:[53, 1, 1, "unknown_83"], #Unknown (number of satellites???)
        84:[55, 1, 1, "unknown_84"], #Unknown
        149:[57, 1, 4, "unknown_149"], #Unknown (magnetic deviation???)
        86:[62, 1, 1, 'unknown_86'], #Unknown (+-X error)
        87:[64, 1, 1, 'unknown_87'], #Unknown (+-Y error)
        160:[66, 1, 4, 'ping_cnt'] #Number of ping values (in bytes)
        }

    # Solix
    elif headbytes == 152:
        headStruct = {
        128:[4, 1, 4, 'record_num'], #Record Number (Unique for each ping)
        129:[9, 1, 4, 'time_s'], #Time Elapsed milliseconds
        130:[14, 1, 4, 'utm_x'], #UTM X
        131:[19, 1, 4, 'utm_y'], #UTM Y
        132.1:[24, 1, 2, 'gps1'], #GPS quality flag (?)
        132.2:[24, 3, 2, 'instr_heading'], #Heading
        133.1:[29, 1, 2, 'gps2'], #GPS quality flag (?)
        133.2:[29, 3, 2, 'speed_ms'], #Speed in meters/second
        134:[34, 1, 4, 'unknown_134'], #Unknown
        135:[39, 1, 4, 'inst_dep_m'], #Depth in centimeters, then converted to meters
        136:[44, 1, 4, 'unknown_136'], #Unknown
        137:[49, 1, 4, 'unknown_137'], #Unknown
        138:[54, 1, 4, 'unknown_138'], #Unknown
        139:[59, 1, 4, 'unknown_139'], #Unkown
        140:[64, 1, 4, 'unknown_140'], #Unknown
        141:[69, 1, 4, 'unknown_141'], #Unknown
        142:[74, 1, 4, 'unknown_142'], #Unknown
        143:[79, 1, 4, 'unknown_143'], #Unknown
        80:[84, 1, 1, 'beam'], #Beam number: 0 (50 or 83 kHz), 1 (200 kHz), 2 (SI Poort), 3 (SI Starboard)
        81:[86, 1, 1, 'volt_scale'], #Volt Scale (?)
        146:[88, 1, 4, 'f'], #Frequency of beam in hertz
        83:[93, 1, 1, "unknown_83"], #Unknown (number of satellites???)
        84:[95, 1, 1, "unknown_84"], #Unknown
        149:[97, 1, 4, "unknown_149"], #Unknown (magnetic deviation???)
        86:[102, 1, 1, 'unknown_86'], #Unknown (+-X error)
        87:[104, 1, 1, 'unknown_87'], #Unknown (+-Y error)
        152:[106, 1, 4, 'unknown_152'], #Unknown
        153:[111, 1, 4, 'unknown_153'], #Unknown
        154:[116, 1, 4, 'unknown_154'], #Unknown
        155:[121, 1, 4, 'unknown_155'], #Unknown
        156:[126, 1, 4, 'unknown_156'], #Unknown
        157:[131, 1, 4, 'unknown_157'], #Unknown
        158:[136, 1, 4, 'unknown_158'], #Unknown
        159:[141, 1, 4, 'unknown_159'], #Unknown
        160:[146, 1, 4, 'ping_cnt'] #Number of ping values (in bytes)
        }
    else:
        headStruct = {}

    return headStruct

#===========================================
def checkHeadStruct(son, headStruct):
    if len(headStruct) > 0:
        file = open(son, 'rb')

        for key, val in headStruct.items():
            file.seek(val[0])
            byte = fread(file, 1, 'B')[0]
            # print(val[3], "::", key, ":", byte)
            if np.floor(key) == byte:
                headValid = [True]
            else:
                headValid = [False, key, val, byte]
                break
        file.close()
    else:
        headValid = [-1]
    return headValid

#===========================================
def decodeHeadStruct(son, headbytes):
    headStruct = {}
    toCheck = {
        128:[-1, 1, 4, 'record_num'], #Record Number (Unique for each ping)
        129:[-1, 1, 4, 'time_s'], #Time Elapsed milliseconds
        130:[-1, 1, 4, 'utm_x'], #UTM X
        131:[-1, 1, 4, 'utm_y'], #UTM Y
        132.1:[-1, 1, 2, 'gps1'], #GPS quality flag (?)
        132.2:[-1, 3, 2, 'instr_heading'], #Heading
        133.1:[-1, 1, 2, 'gps2'], #GPS quality flag (?)
        133.2:[-1, 3, 2, 'speed_ms'], #Speed in meters/second
        134:[-1, 1, 4, 'unknown_134'], #Unknown
        135:[-1, 1, 4, 'inst_dep_m'], #Depth in centimeters, then converted to meters
        136:[-1, 1, 4, 'unknown_136'], #Unknown
        137:[-1, 1, 4, 'unknown_137'], #Unknown
        138:[-1, 1, 4, 'unknown_138'], #Unknown
        139:[-1, 1, 4, 'unknown_139'], #Unkown
        140:[-1, 1, 4, 'unknown_140'], #Unknown
        141:[-1, 1, 4, 'unknown_141'], #Unknown
        142:[-1, 1, 4, 'unknown_142'], #Unknown
        143:[-1, 1, 4, 'unknown_143'], #Unknown
        80:[-1, 1, 1, 'beam'], #Beam number: 0 (50 or 83 kHz), 1 (200 kHz), 2 (SI Poort), 3 (SI Starboard)
        81:[-1, 1, 1, 'volt_scale'], #Volt Scale (?)
        146:[-1, 1, 4, 'f'], #Frequency of beam in hertz
        83:[-1, 1, 1, "unknown_83"], #Unknown (number of satellites???)
        84:[-1, 1, 1, "unknown_84"], #Unknown
        149:[-1, 1, 4, "unknown_149"], #Unknown (magnetic deviation???)
        86:[-1, 1, 1, 'unknown_86'], #Unknown (+-X error)
        87:[-1, 1, 1, 'unknown_87'], #Unknown (+-Y error)
        152:[-1, 1, 4, 'unknown_152'], #Unknown
        153:[-1, 1, 4, 'unknown_153'], #Unknown
        154:[-1, 1, 4, 'unknown_154'], #Unknown
        155:[-1, 1, 4, 'unknown_155'], #Unknown
        156:[-1, 1, 4, 'unknown_156'], #Unknown
        157:[-1, 1, 4, 'unknown_157'], #Unknown
        158:[-1, 1, 4, 'unknown_158'], #Unknown
        159:[-1, 1, 4, 'unknown_159'], #Unknown
        160:[-1, 1, 4, 'ping_cnt'] #Number of ping values (in bytes)
        }

    file = open(son, 'rb')
    lastPos = 0
    head = fread(file, 4,'B')

    if head[0] == 192 and head[1] == 222 and head[2] == 171 and head[3] == 33:
        while lastPos < headbytes - 1:
            lastPos = file.tell() # Get current position in file
            byte = fread(file, 1, 'B')[0]
            print("B: ", byte, " I: ", lastPos, " H: ", headbytes-1)
            if byte != 132 and byte != 133:
                meta = toCheck[byte]
                meta[0] = lastPos
                headStruct[byte] = meta
                file.seek(meta[0]+meta[1]+meta[2])
            else:
                byte = byte + 0.1
                meta0_1 = toCheck[byte]
                meta0_1[0] = lastPos
                headStruct[byte] = meta0_1
                byte = byte + 0.1
                meta0_2 = toCheck[byte]
                meta0_2[0] = lastPos
                headStruct[byte] = meta0_2
                file.seek(meta0_2[0]+meta0_2[1]+meta0_2[2])
            lastPos = file.tell()

    file.close()

    return headStruct

# =========================================================
def decode_onix(fid2):
   """
   returns data from .DAT file
   """

   dumpstr = fid2.read()
   fid2.close()

   if sys.version.startswith('3'):
      dumpstr = ''.join(map(chr, dumpstr))

   humdat = {}
   hd = dumpstr.split('<')[0]
   tmp = ''.join(dumpstr.split('<')[1:])
   humdat['NumberOfPings'] = int(tmp.split('NumberOfPings=')[1].split('>')[0])
   humdat['TotalTimeMs'] = int(tmp.split('TotalTimeMs=')[1].split('>')[0])
   humdat['linesize'] = int(tmp.split('PingSizeBytes=')[1].split('>')[0])
   humdat['FirstPingPeriodMs'] = int(tmp.split('FirstPingPeriodMs=')[1].split('>')[0])
   humdat['BeamMask'] = int(tmp.split('BeamMask=')[1].split('>')[0])
   humdat['Chirp1StartFrequency'] = int(tmp.split('Chirp1StartFrequency=')[1].split('>')[0])
   humdat['Chirp1EndFrequency'] = int(tmp.split('Chirp1EndFrequency=')[1].split('>')[0])
   humdat['Chirp2StartFrequency'] = int(tmp.split('Chirp2StartFrequency=')[1].split('>')[0])
   humdat['Chirp2EndFrequency'] = int(tmp.split('Chirp2EndFrequency=')[1].split('>')[0])
   humdat['Chirp3StartFrequency'] = int(tmp.split('Chirp3StartFrequency=')[1].split('>')[0])
   humdat['Chirp3EndFrequency'] = int(tmp.split('Chirp3EndFrequency=')[1].split('>')[0])
   humdat['SourceDeviceModelId2D'] = int(tmp.split('SourceDeviceModelId2D=')[1].split('>')[0])
   humdat['SourceDeviceModelIdSI'] = int(tmp.split('SourceDeviceModelIdSI=')[1].split('>')[0])
   humdat['SourceDeviceModelIdDI'] = int(tmp.split('SourceDeviceModelIdDI=')[1].split('>')[0])
   return humdat

#===========================================
def getHumdat(humfile, datLen, humdic, t):
    """
   returns data from .DAT file
   """
    humdat = {}
    endian = humdic['endianness']
    file = open(humfile, 'rb')
    for key, val in humdic.items():
        if key == 'endianness':
            pass
        else:
            file.seek(val[0])
            if val[2] == 4:
                byte = struct.unpack(endian, arr('B', fread(file, val[2], 'B')).tobytes())[0]
            elif val[2] < 4:
                byte = fread(file, val[2], 'B')[0]
            elif val[2] > 4:
                byte = arr('B', fread(file, val[2], 'B')).tobytes().decode()
            else:
                byte = -9999
            humdat[key] = byte

    file.close()

    waterCode = humdat['water_code']
    if datLen == 64:
        if waterCode == 0:
            humdat['water_type'] = 'fresh'
            S = 1
        elif waterCode == 1:
            humdat['water_type'] = 'deep salt'
            S = 35
        elif waterCode == 2:
            humdat['water_type'] = 'shallow salt'
            S = 30
        else:
            humdat['water_type'] = 'unknown'
    #Need to figure out water code for solix
    elif datLen == 96:
        if waterCode == 1:
            humdat['water_type'] = 'fresh'
            S = 1
        else:
            humdat['water_type'] = 'unknown'
            c = 1475

    c = 1449.05 + 45.7*t - 5.21*t**2 + 0.23*t**3 + (1.333 - 0.126*t + 0.009*t**2)*(S - 35)

    tvg = ((8.5*10**-5)+(3/76923)+((8.5*10**-5)/4))*c
    humdat['tvg'] = tvg

    return humdat

#===========================================
def decode_humdat(humfile, datLen, t, nchunk):
    """
   determines .DAT file structure then
   gets the data from .DAT using getHumdat()
   or decode_onix()
   """
    # Returns dictionary with dat structure
    # Format: name : [byteIndex, offset, dataLen, data]
    # name = name of attribute
    # byteIndex = Index indicating position of name
    # offset = Byte offset for the actual data
    # dataLen = number of bytes for data (i.e. utm_x is 4 bytes long)
    # data = actual value of the attribute

    #1199, Helix
    if datLen == 64:
        humdic = {
        'endianness':'>i', #>=big endian; I=unsigned Int
        'SP1':[0, 0, 1, -1], #Unknown (spacer)
        'water_code':[1, 0, 1, -1], #Water code: 0=fresh,1=deep salt, 2=shallow salt
        'SP2':[2, 0, 1, -1], #Unknown (spacer)
        'unknown_1':[3, 0, 1, -1], #Unknown (gps flag?)
        'sonar_name':[4, 0, 4, -1], #Sonar name
        'unknown_2':[8, 0, 4, -1], #Unknown
        'unknown_3':[12, 0, 4, -1], #Unknown
        'unknown_4':[16, 0, 4, -1], #Unknown
        'unix_time':[20, 0, 4, -1], #Unix Time
        'utm_x':[24, 0, 4, -1], #UTM X
        'utm_y':[28, 0, 4, -1], #UTM Y
        'filename':[32, 0, 10, -1], #Recording name
        'unknown_5':[42, 0, 2, -1], #Unknown
        'numrecords':[44, 0, 4, -1], #Number of records
        'recordlens_ms':[48, 0, 4, -1], #Recording length milliseconds
        'linesize':[52, 0, 4, -1], #Line Size (?)
        'unknown_6':[56, 0, 4, -1], #Unknown
        'unknown_7':[60, 0, 4, -1], #Unknown
        }
        humdat = getHumdat(humfile, datLen, humdic, t)

    #Solix (Little Endian)
    elif datLen == 96:
        humdic = {
        'endianness':'<i', #<=little endian; I=unsigned Int
        'SP1':[0, 0, 1, -1], #Unknown (spacer)
        'water_code':[1, 0, 1, -1], #Need to check if consistent with other models (1=fresh?)
        'SP2':[2, 0, 1, -1], #Unknown (spacer)
        'unknown_1':[3, 0, 1, -1], #Unknown (gps flag?)
        'sonar_name':[4, 0, 4, -1], #Sonar name
        'unknown_2':[8, 0, 4, -1], #Unknown
        'unknown_3':[12, 0, 4, -1], #Unknown
        'unknown_4':[16, 0, 4, -1], #Unknown
        'unix_time':[20, 0, 4, -1], #Unix Time
        'utm_x':[24, 0, 4, -1], #UTM X
        'utm_y':[28, 0, 4, -1], #UTM Y
        'filename':[32, 0, 12, -1], #Recording name
        'numrecords':[44, 0, 4, -1], #Number of records
        'recordlens_ms':[48, 0, 4, -1], #Recording length milliseconds
        'linesize':[52, 0, 4, -1], #Line Size (?)
        'unknown_5':[56, 0, 4, -1], #Unknown
        'unknown_6':[60, 0, 4, -1], #Unknown
        'unknown_7':[64, 0, 4, -1], #Unknown
        'unknown_8':[68, 0, 4, -1], #Unknown
        'unknown_9':[72, 0, 4, -1], #Unknown
        'unknown_10':[76, 0, 4, -1], #Unknown
        'unknown_11':[80, 0, 4, -1], #Unknown
        'unknown_12':[84, 0, 4, -1], #Unknown
        'unknown_13':[88, 0, 4, -1], #Unknown
        'unknown_14':[92, 0, 4, -1]
        }
        humdat = getHumdat(humfile, datLen, humdic, t)

    #Onix
    else:
        humdic = {}
        fid2 = open(humfile,'rb')
        humdat = decode_onix(fid2)
        fid2.close()

    humdat['chunk_size'] = nchunk
    return humdat

#===========================================
def getHead(son, sonIndex, headStruct, humdat, t, trans):
    sonHead = {'lat':-1}
    file = open(son, 'rb')
    for key, val in headStruct.items():
        index = sonIndex + val[0] + val[1]
        file.seek(index)
        if val[2] == 4:
            byte = struct.unpack('>i', arr('B', fread(file, val[2], 'B')).tobytes())[0]
        elif 1 < val[2] <4:
            byte = struct.unpack('>h', arr('b', fread(file, val[2],'b')).tobytes() )[0]
        else:
            byte = fread(file, val[2], 'b')[0]
        # print(val[-1],":",byte)
        sonHead[val[-1]] = byte

    file.close()

    # Make necessary conversions
    lat = np.arctan(np.tan(np.arctan(np.exp(sonHead['utm_y']/ 6378388.0)) * 2.0 - 1.570796326794897) * 1.0067642927) * 57.295779513082302
    lon = (sonHead['utm_x'] * 57.295779513082302) / 6378388.0

    sonHead['lon'] = lon
    sonHead['lat'] = lat

    lon, lat = trans(lon, lat)
    sonHead['e'] = lon
    sonHead['n'] = lat

    sonHead['instr_heading'] = sonHead['instr_heading']/10
    sonHead['speed_ms'] = sonHead['speed_ms']/10
    sonHead['inst_dep_m'] = sonHead['inst_dep_m']/10
    sonHead['f'] = sonHead['f']/1000
    sonHead['time_s'] = sonHead['time_s']/1000
    sonHead['tempC'] = t*10
    # Can we figure out a way to base transducer length on where we think the recording came from?
    # I can't see anywhere where this value is used.
    sonHead['t'] = 0.108
    try:
        starttime = float(humdat['unix_time'])
        sonHead['caltime'] = starttime + sonHead['time_s']
    except :
        sonHead['caltime'] = 0

    # if sonHead['beam']==3 or sonHead['beam']==2:
    #     dist = ((np.tan(25*0.0174532925))*sonHead['inst_dep_m']) +(tvg)
    #     bearing = 0.0174532925*sonHead['instr_heading'] - (pi/2)
    #     bearing = bearing % 360
    #     sonHead['heading'] = bearing
    # print("\n\n", sonHead, "\n\n")
    return sonHead

#===========================================
def getSonMeta(son, proj_name, t, headStruct, nchunk, humdat, trans):
    # Read son header for every ping
    # Save to csv
    # Prepare dictionary to hold all header data
    head = defaultdict(list)
    for key, val in headStruct.items():
        head[val[-1]] = []

    # First check if .idx file exists and get that data
    idx = {'record_num': [],
           'time_s': [],
           'index': [],
           'chunk_id': []}

    idxFile = son.replace(".SON", ".IDX")
    if os.path.exists(idxFile):
        idxLen = os.path.getsize(idxFile)
        idxFile = open(idxFile, 'rb')
        i = j = chunk = 0
        while i < idxLen:
            idx['time_s'].append(struct.unpack('>I', arr('B', fread(idxFile, 4, 'B')).tobytes())[0])
            sonIndex = struct.unpack('>I', arr('B', fread(idxFile, 4, 'B')).tobytes())[0]
            idx['index'].append(sonIndex)
            head['index'].append(sonIndex)
            idx['chunk_id'].append(chunk)
            head['chunk_id'].append(chunk)
            headerDat = getHead(son, sonIndex, headStruct, humdat, t, trans)
            for key, val in headerDat.items():
                head[key].append(val)
            idx['record_num'].append(headerDat['record_num'])
            i+=8
            j+=1
            if j == nchunk:
                j=0
                chunk+=1
            # print("\n\n", idx, "\n\n")
    else:
        sys.exit("idx missing.  need to figure this out")

    # print(head,"\n\n\n")
    # print(idx)
    headDF = pd.DataFrame.from_dict(head, orient="index").T
    idxDF = pd.DataFrame.from_dict(idx, orient="index").T

    # Write data to csv
    beam = os.path.split(son)[-1].split(".")[0]
    outCSV = os.path.join('proc_data', proj_name, proj_name+"_"+beam+"_meta.csv")
    headDF.to_csv(outCSV, index=False, float_format='%.14f')

    outCSV = os.path.join('proc_data', proj_name, proj_name+"_"+beam+"_idx.csv")
    idxDF.to_csv(outCSV, index=False, float_format='%.14f')

#===========================================
def writetiles(data, namestr, proj_name, nchunk, k):
    """
    This function applies a -sliding window in the alongtrack and writes scan tile image files
    """
    nx, ny = np.shape(data)
    Z, ind = sliding_window(data, (nx,nchunk)) #512))
    if k < 10:
        addZero = '0000'
    elif k < 100:
        addZero = '000'
    elif k < 1000:
        addZero = '00'
    elif k < 10000:
        addZero = '0'
    else:
        addZero = ''
    Z = Z[0].astype('uint8')
    imageio.imwrite(os.path.join('proc_data',proj_name, namestr, proj_name+'-image-'+addZero+str(k)+'.png'), Z)

#===========================================
def getscans(proj_name, son, sonMeta, datMeta, headbytes):

    datMeta = pd.read_csv(datMeta)
    sonMetaAll = pd.read_csv(sonMeta)
    print(type(sonMetaAll))

    # Which beam?
    beam = sonMetaAll['beam'].astype(int)[0]
    if beam == 0:
        beam = 'down_lowfreq'
    elif beam == 1:
        beam = 'down_highfreq'
    elif beam == 2:
        beam = 'sidescan_port'
    elif beam == 3:
        beam = 'sidescan_starboard'
    elif beam == 4:
        beam = 'down_vhighfreq'
    else:
        beam = 'unknown'

    outPath = os.path.join('proc_data', proj_name, beam)
    try:
        os.mkdir(outPath)
    except:
        pass

    totalChunk = sonMetaAll['chunk_id'].max() #Total chunks to process
    maxRange = sonMetaAll['ping_cnt'].max()
    i = 0 #Chunk index
    while i <= totalChunk:
        # print("\nProcessing Chunk", i)
        isChunk = sonMetaAll['chunk_id']==i
        sonMeta = sonMetaAll[isChunk].reset_index()
        # print(sonMeta['ping_cnt'].max(), "\n\n")
        data = pyread(son, datMeta, sonMeta, headbytes, outPath, maxRange) # Create sonar data object
        data._loadSon()
        sonDat = data.sonDat
        writetiles(sonDat, beam, proj_name, sonMeta.shape[0], i)

        del data
        i+=1

#===========================================
def read_master_func(sonfiles, humfile, proj_name, t, nchunk):

    ###################################
    # Decode DAT file (varies by model)
    print("\nGetting DAT Metadata...")
    datLen = os.path.getsize(humfile)
    humdat = decode_humdat(humfile, datLen, t, nchunk)

    # for key, val in humdat.items():
    #     print("K:", key, "V:", val)

    lat = np.arctan(np.tan(np.arctan(np.exp(humdat['utm_y']/ 6378388.0)) * 2.0 - 1.570796326794897) * 1.0067642927) * 57.295779513082302
    lon = (humdat['utm_x'] * 57.295779513082302) / 6378388.0

    cs2cs_args = "epsg:"+str(int(float(convert_wgs_to_utm(lon, lat))))
    humdat['epsg'] = cs2cs_args.split(":")[1]
    print(cs2cs_args)

    try:
       trans =  pyproj.Proj(init=cs2cs_args)
    except:
       trans =  pyproj.Proj(cs2cs_args.lstrip(), inverse=True)

    # Write DAT to csv
    outCSV = os.path.join('proc_data', proj_name, proj_name+"_DAT_meta.csv")
    pd.DataFrame.from_dict(humdat, orient="index").T.to_csv(outCSV, index=False)
    print("Done!")

    ################################################
    # Determine ping header length (varies by model)
    print("\nGetting Header Structure...")
    cntSON = len(sonfiles) # Number of sonar files
    gotHeader = False # Flag indicating if length of header is found
    i = 0 # Counter for iterating son files
    while gotHeader is False:
        try:
            headbytes = cntHead(sonfiles[i]) # Try counting head bytes
            if headbytes > 0: # See if
                print("Header Length: {}".format(headbytes))
                gotHeader = True
            else:
                i+=1
        except:
            sys.exit("\n#####\nERROR: Out of SON files... \n"+
            "Unable to determine header length.")

    #################################################
    # Now get the SON header structure and attributes
    headStruct = getHeadStruct(headbytes)

    # Let's check and make sure the header structure is correct
    # If it is not correct, try to automatically decode structure
    headValid = checkHeadStruct(sonfiles[i], headStruct)
    if headValid[0] is True:
        print("Done!")
    elif headValid[0] is False:
        print("\n#####\nERROR: Wrong Header Structure")
        print("Expected {} at index {}.".format(headValid[1], headValid[2]))
        print("Found {} instead.".format(headValid[3]))
        print("Attempting to decode header structure.....")
        headStruct = decodeHeadStruct(sonfiles[i], headbytes)
    else:
        print("\n#####\nERROR: Wrong Header Structure")
        print("Attempting to decode header structure.....")
        headStruct = decodeHeadStruct(sonfiles[i], headbytes)

    # for key, val in headStruct.items():
    #     print(key, ": ", val)

    #If we had to decode header structure,
    #let's make sure it decoded correctly
    if headValid[0] is not True:
        headValid = checkHeadStruct(sonfiles[i], headStruct)
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
    for son in sonfiles:
        beam = os.path.split(son)[-1].split(".")[0]
        file = os.path.join('proc_data', proj_name, proj_name+"_"+beam+"_meta.csv")
        if os.path.exists(file):
            print("File {0} exists. No need to re-process.".format(file))
        else:
            toProcess.append(son)

    if len(toProcess)>0:
        # getSonMeta(toProcess[0], proj_name, t, headStruct, nchunk)
        Parallel(n_jobs= np.min([len(toProcess), cpu_count()]), verbose=10)(delayed(getSonMeta)(k, proj_name, t, headStruct, nchunk, humdat, trans) for k in sonfiles)

    ########################
    # Let's export the tiles
    print("\nGetting sonar data and exporting tile images:")
    sonMeta = sorted(glob(os.path.join('proc_data',proj_name,'*B*_meta.csv')))
    datMeta = sorted(glob(os.path.join('proc_data',proj_name,'*DAT_meta.csv')))

    # getscans(proj_name, sonfiles[2], sonMeta[2], datMeta[0], headbytes)
    Parallel(n_jobs= np.min([len(sonfiles), cpu_count()]), verbose=10)(delayed(getscans)(proj_name, sonfiles[k], sonMeta[k], datMeta[0], headbytes) for k in range(0,len(sonfiles)))
