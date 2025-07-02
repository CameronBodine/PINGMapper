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



import sys, os, zipfile, requests

# Add 'pingmapper' to the path, may not need after pypi package...
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.append(PACKAGE_DIR)

# # For debug
# from funcs_common import *
# from main_readFiles import read_master_func
# from main_rectify import rectify_master_func
# from main_mapSubstrate import map_master_func

from pingmapper.funcs_common import *
from pingmapper.main_readFiles import read_master_func
from pingmapper.main_rectify import rectify_master_func
from pingmapper.main_mapSubstrate import map_master_func

user_home_path = os.path.expanduser('~')

orig_stdout = sys.stdout

def test(ds):

    # Get processing script's dir so we can save it to file
    scriptDir = SCRIPT_DIR
    copied_script_name = os.path.basename(__file__).split('.')[0]+'_'+time.strftime("%Y-%m-%d_%H%M")+'.py'
    script = os.path.abspath(__file__)

    # For the logfile
    logfilename = 'log_'+time.strftime("%Y-%m-%d_%H%M")+'.txt'

    start_time = time.time()

    #============================================

    # if len(sys.argv) == 2:
    #     ds = int(sys.argv[1])
    # else:
    #     print("\n\nERROR: \nPlease enter argument to choose which test file to process:")
    #     print("1 = Short recording \n2 = Long recording \n\nSYNTAX: python test_PINGMapper.py <1 or 2>\n\n")
    #     sys.exit()

    #################
    # User Parameters
    #################

    if ds == 1:
        ds_name = 'Test-Small-DS'
        download_name = ds_name
    elif ds == 2:
        ds_name = 'Test-Large-DS'
        download_name = 'sample_recording'
    else:
        print("\n\nERROR: \nPlease enter argument to choose which test file to process:")
        print("1 = Short recording \n2 = Long recording \n\nSYNTAX: python test_PINGMapper.py <1 or 2>\n\n")
        sys.exit()

    d = os.environ['CONDA_PREFIX']
    exampleDir = os.path.join(d, 'exampleData')
    ds_path = os.path.join(exampleDir, ds_name)
    ds_path = os.path.normpath(ds_path)

    os.makedirs(exampleDir, exist_ok=True)

    # Check if files have already been downloaded
    if os.path.exists(ds_path) and os.path.exists(ds_path+'.DAT'):
        print('Files already downloaded!')

    else:
        print('Need to download {} recording dataset...\n'.format(ds_name))
        url='https://github.com/CameronBodine/PINGMapper/releases/download/data/{}.zip'.format(download_name)
        filename = ds_path+'.zip'
        r = requests.get(url, allow_redirects=True)
        # open(filename, 'wb').write(r.content)
        with open(filename, 'wb') as f:
            f.write(r.content)

        with zipfile.ZipFile(filename, 'r') as z_fp:
            z_fp.extractall(exampleDir)
        os.remove(filename)
        print('Downloaded and extracted', filename)
            
    # Path to data/output
    inFile = ds_path+'.DAT'
    sonPath = ds_path
    projDir = os.path.join(user_home_path, 'Desktop', 'PINGMapper-'+ds_name)

    inFile = os.path.abspath(inFile)
    sonPath = os.path.abspath(sonPath)
    projDir = os.path.abspath(projDir)

    # *** IMPORTANT ****
    # Export Mode: project_mode
    ## 0==NEW PROJECT: Create a new project. [DEFAULT]
    ##      If project already exists, program will exit without any project changes.
    ##
    ## 1==OVERWRITE MODE: Create new project, regardless of previous project state.
    ##      If project exists, it will be DELETED and reprocessed.
    ##      If project does not exist, a new project will be created.
    project_mode = 1


    # General Parameters
    tempC = 10 #Temperature in Celsius
    nchunk = 500 #Number of pings per chunk
    cropRange = 0.0 #Crop imagery to specified range [in meters]; 0.0==No Cropping
    exportUnknown = True #Option to export Unknown ping metadata
    fixNoDat = False # Locate and flag missing pings; add NoData to exported imagery.
    threadCnt = 0.5 #Number of compute threads to use; 0==All threads; <0==(Total threads + threadCnt); >0==Threads to use up to total threads


    # Output Pixel Resolution
    pix_res_son = 0.05 # Sonar GeoTiff Resolution [in meters]; 0 = Default (~0.02 m)
    pix_res_map = 0.25 # Substrate GeoTiff Resolution [in meters]; 0 = Default (~0.02 m)


    # Position Corrections
    ## Provide an x and y offset to account for position offset between
    ## control head (or external GPS) and transducer.
    ## Origin (0,0) is the location of control head (or external GPS)
    ## X-axis runs from bow (fore, or front) to stern (aft, or rear) with positive offset towards the bow, negative towards stern
    ## Y-axis runs from portside (left) to starboard (right), with negative values towards the portside, positive towards starboard
    ## Z-offsets can be provided with `adjDep` below.
    x_offset = 0.0 # [meters]
    y_offset = 0.0 # [meters]


    # Sonar Intensity Corrections
    egn = True
    egn_stretch = 1 # 0==Min-Max; 1==% Clip; 2==Standard deviation
    egn_stretch_factor = 0.5 # If % Clip, the percent of histogram tails to clip (1.0 == 1%);
                            ## If std, the number of standard deviations to retain


    # Sonogram Exports
    tileFile = '.jpg' # Img format for plots and sonogram exports
    wcp = True #Export tiles with water column present: 0==False; 1==True, side scan channels only; 2==True, all available channels.
    wcr = True #Export Tiles with water column removed (and slant range corrected): 0==False; 1==True, side scan channels only; 2==True, all available channels.
    wco = True
    wcm = True
    sonogram_colorMap = "copper"
    spdCor = True
    maxCrop = True


    # Depth Detection and Shadow Removal Parameters
    remShadow = 1  # 0==Leave Shadows; 1==Remove all shadows; 2==Remove only bank shadows
    detectDep = 1 #0==Use Humminbird depth; 1==Auto detect depth w/ Zheng et al. 2021;
    ## 2==Auto detect depth w/ Thresholding

    smthDep = True #Smooth depth before water column removal
    adjDep = 0 #Aditional depth adjustment (in meters) for water column removaL
    pltBedPick = True #Plot bedpick on sonogram


    # Rectification Parameters
    rect_wcp = True #Export rectified tiles with water column present
    rect_wcr = True #Export rectified tiles with water column removed/slant range corrected
    son_colorMap = 'Greys_r' # Specify colorramp for rectified imagery. '_r'==reverse the ramp: https://matplotlib.org/stable/tutorials/colors/colormaps.html


    # Substrate Mapping
    pred_sub = 1 # Automatically predict substrates and save to npz: 0==False; 1==True, SegFormer Model
    pltSubClass = True # Export plots of substrate classification and predictions
    map_sub = 1 # Export substrate maps (as rasters): 0==False; 1==True. Requires substrate predictions saved to npz.
    export_poly = True # Convert substrate maps to shapefile: map_sub must be > 0 or raster maps previously exported
    map_predict = False # Export substrate heat maps (probabilities) for each class. Requires substrate predictions saved to npz.
    map_class_method = 'max' # 'max' only current option. Take argmax of substrate predictions to get final classification.


    # Mosaic Exports
    mosaic_nchunk = 0 # Number of chunks per mosaic: 0=All chunks. Specifying a value >0 generates multiple mosaics if number of chunks exceeds mosaic_nchunk.
    mosaic = 1 #Export sonar mosaic; 0==Don't Mosaic; 1==Do Mosaic - GTiff; 2==Do Mosaic - VRT
    map_mosaic = 1 #Export substrate mosaic; 0==Don't Mosaic; 1==Do Mosaic - GTiff; 2==Do Mosaic - VRT


    # Miscellaneous Exports
    banklines = True # Export banklines from sonar imagery
    coverage = True # Export coverage and trackline shapefile


    #################
    #################

    # =========================================================
    # Determine project_mode
    print(project_mode)
    if project_mode == 0:
        # Create new project
        if not os.path.exists(projDir):
            os.mkdir(projDir)
        else:
            projectMode_1_inval()

    elif project_mode == 1:
        # Overwrite existing project
        if os.path.exists(projDir):
            shutil.rmtree(projDir)

        os.mkdir(projDir)        

    elif project_mode == 2:
        # Update project
        # Make sure project exists, exit if not.
        
        if not os.path.exists(projDir):
            projectMode_2_inval()

    # =========================================================
    # For logging the console output

    logdir = os.path.join(projDir, 'logs')
    if not os.path.exists(logdir):
        os.makedirs(logdir)

    logfilename = os.path.join(logdir, logfilename)

    sys.stdout = Logger(logfilename)

    #============================================

    sonFiles = sorted(glob(sonPath+os.sep+'*.SON'))
    print(sonFiles)

    #============================================

    params = {
        'logfilename':logfilename,
        'project_mode':project_mode,
        'script':[script, copied_script_name],
        'inFile':inFile,
        'sonFiles':sonFiles,
        'projDir':projDir,
        'tempC':tempC,
        'nchunk':nchunk,
        'exportUnknown':exportUnknown,
        'fixNoDat':fixNoDat,
        'threadCnt':threadCnt,
        'pix_res_son': pix_res_son,
        'pix_res_map': pix_res_map,
        'x_offset':x_offset,
        'y_offset':y_offset,
        'egn':egn,
        'egn_stretch':egn_stretch,
        'egn_stretch_factor':egn_stretch_factor,
        'tileFile':tileFile,
        'wcp':wcp,
        'wcr':wcr,
        'wco':wco,
        'wcm':wcm,
        'sonogram_colorMap':sonogram_colorMap,
        'spdCor':spdCor,
        'maxCrop':maxCrop,
        'USE_GPU':False,
        'remShadow':remShadow,
        'detectDep':detectDep,
        'smthDep':smthDep,
        'adjDep':adjDep,
        'pltBedPick':pltBedPick,
        'rect_wcp':rect_wcp,
        'rect_wcr':rect_wcr,
        'son_colorMap':son_colorMap,
        'pred_sub':pred_sub,
        'map_sub':map_sub,
        'export_poly':export_poly,
        'map_predict':map_predict,
        'pltSubClass':pltSubClass,
        'map_class_method':map_class_method,
        'mosaic_nchunk':mosaic_nchunk,
        'mosaic':mosaic,
        'map_mosaic':map_mosaic,
        'banklines':banklines,
        'coverage':coverage,
        }

    print('\n\n', '***User Parameters***')
    for k,v in params.items():
        print("| {:<20s} : {:<10s} |".format(k, str(v)))

    #==================================================
    print('\n===========================================')
    print('===========================================')
    print('***** READING *****')
    print("working on "+projDir)
    read_master_func(**params)
    # read_master_func(sonFiles, humFile, projDir, t, nchunk, exportUnknown, wcp, wcr, tileFile, detectDepth, smthDep, adjDep, pltBedPick, threadCnt)

    try:
        #==================================================
        if rect_wcp or rect_wcr or banklines or coverage:
            print('\n===========================================')
            print('===========================================')
            print('***** RECTIFYING *****')
            print("working on "+projDir)
            rectify_master_func(**params)
            # rectify_master_func(sonFiles, humFile, projDir, nchunk, rect_wcp, rect_wcr, mosaic, threadCnt)

        #==================================================
        if pred_sub or map_sub or export_poly or map_predict or pltSubClass:
            print('\n===========================================')
            print('===========================================')
            print('***** MAPPING SUBSTRATE *****')
            print("working on "+projDir)
            map_master_func(**params)

        gc.collect()
        print("\n\nTotal Processing Time: ",datetime.timedelta(seconds = round(time.time() - start_time, ndigits=0)))

        print("\n\nFiles saved to: ", projDir)

        sys.stdout.log.close()
        sys.stdout = orig_stdout

    except Exception as Argument:
        unableToProcessError(logfilename)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("\n\nERROR: \nNo argument given to select which test file to process, setting to:")
        print("1 = Small dataset\n\n")
        ds = 1
    elif sys.argv[1] == 'small':
        ds = 1
    elif sys.argv[1] == 'large':
        ds = 2
    else:
        ds = int(sys.argv[1])

    test(ds)
