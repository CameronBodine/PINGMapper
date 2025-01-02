import sys
sys.path.insert(0, 'src')
import os
import PySimpleGUI as sg
import matplotlib.pyplot as plt

from funcs_common import *
from main_readFiles import read_master_func
from main_rectify import rectify_master_func

# Get processing script's dir so we can save it to file
scriptDir = os.getcwd()
copied_script_name = os.path.basename(__file__).split('.')[0]+'_'+time.strftime("%Y-%m-%d_%H%M")+'.py'
script = os.path.join(scriptDir, 'utils', os.path.basename(__file__))

# For the logfile
logfilename = 'log_'+time.strftime("%Y-%m-%d_%H%M")+'.txt'

start_time = time.time()

#============================================

test = r'/media/cbodine/UDEL_Ubuntu/SynologyDrive/UDEL/Bootcamp/2024/Sharks/SSS_RawData'

layout = [
    [sg.Text('Recording to Process')],
    # [sg.In(size=(80,1)), sg.FileBrowse(file_types=(("DAT File", "*.DAT"),), initial_folder=test)],
    # [sg.In(size=(80,1)), sg.FileBrowse(file_types=(("DAT File", "*.DAT"),))],
    [sg.In(size=(80,1)), sg.FolderBrowse((), initial_folder=test)],
    [sg.Submit(), sg.Quit()]
    ]

layout2 =[[sg.Column(layout, size_subsample_height=2)]]
window = sg.Window('Generate Recording Coverage', layout2, resizable=True)

while True:
    event, values = window.read()
    if event == "Quit" or event == "Submit":
        break

window.close()

if event == "Quit":
    sys.exit()

#============================================

# values = [r'Z:\UDEL\Hydronalix_SEARCHER\sonar_data\Oregon\20240529_apex\Survey 2 Sand Dollars and Landers - North\Rec000010.DAT']

datDirs = glob(os.path.join(values[0], '**', '*.DAT'), recursive=True)

for dat in datDirs:

    try:
        humFile = dat
        projDir = humFile.split('.DAT')[0]
        projDir = os.path.join(projDir, 'PINGMapper_aoi')

        params = {
            'humFile': dat,
            'projDir': projDir,
            'project_mode':1,
            'coverage': True,
        }

        globals().update(params)

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

        sonPath = humFile.split('.DAT')[0]
        sonFiles = sorted(glob(sonPath+os.sep+'*.SON'))
        print(sonFiles)

        #============================================
        # Add ofther params
        params['sonFiles'] = sonFiles
        params['logfilename'] = logfilename
        params['script'] = [script, copied_script_name]

        #============================================

        print('\n\n', '***User Parameters***')
        for k,v in params.items():
            print("| {:<20s} : {:<10s} |".format(k, str(v)))

        #==================================================
        print('\n===========================================')
        print('===========================================')
        print('***** READING *****')
        print("working on "+projDir)
        read_master_func(**params)

        print('\n===========================================')
        print('===========================================')
        print('***** GENERATING COVERAGE *****')
        print("working on "+projDir)
        rectify_master_func(**params)

        # Move shapefiles to main dir and delete subdirs
        print('Cleaning up...')
        shp_dir = os.path.join(projDir, 'meta', 'shapefiles')
        shps = glob(os.path.join(shp_dir, '*.shp'))

        for shp in shps:
            gdf = gpd.read_file(shp)
            f = os.path.basename(shp)
            gdf.to_file(os.path.join(projDir, f))
            del gdf

        # Delete meta and logs
        shutil.rmtree(os.path.join(projDir, 'meta'))

        print('DONE!')
    except:
        pass


