
import sys
sys.path.insert(0, 'src')
import os
import PySimpleGUI as sg
import matplotlib.pyplot as plt

from funcs_common import *
from main_readFiles import read_master_func
from main_rectify import rectify_master_func
from main_mapSubstrate import map_master_func
import json

# Get processing script's dir so we can save it to file
scriptDir = os.getcwd()
copied_script_name = os.path.basename(__file__).split('.')[0]+'_'+time.strftime("%Y-%m-%d_%H%M")+'.py'
script = os.path.join(scriptDir, os.path.basename(__file__))

# For the logfile
logfilename = 'log_'+time.strftime("%Y-%m-%d_%H%M")+'.txt'

start_time = time.time()

#============================================

# Default Values
# Edit values below to change default values in gui
default_params_file = "./user_params.json"
if not os.path.exists(default_params_file):
    default_params_file = "./default_params.json"
with open(default_params_file) as f:
    default_params = json.load(f)


layout = [
    [sg.Text('Recording to Process')],
    [sg.In(size=(80,1)), sg.FileBrowse(file_types=(("DAT File", "*.DAT"),))],
    [sg.Text('Output Folder')],
    [sg.In(size=(80,1)), sg.FolderBrowse(initial_folder=os.path.join(os.getcwd(), 'procData'))],
    [sg.Text('Project Name', size=(15,1)), sg.InputText(size=(50,1))],
    [sg.Checkbox('Overwrite Existing Project', default=default_params['project_mode'])],
    [sg.HorizontalSeparator()],
    [sg.Text('General Parameters')],
    [sg.Text('Temperature [C]', size=(20,1)), sg.Input(default_params['tempC'], size=(10,1))],
    [sg.Text('Chunk Size', size=(20,1)), sg.Input(default_params['nchunk'], size=(10,1))],
    [sg.Text('Crop Range [m]', size=(20,1)), sg.Input(default_params['cropRange'], size=(10,1))],
    [sg.Checkbox('Export Unknown Ping Attributes', default=default_params['exportUnknown'])],
    [sg.Checkbox('Locate and flag missing pings', default=default_params['fixNoDat'])],
    [sg.Text('Thread Count [0==All Threads]', size=(30,1)), sg.Input(default_params['threadCnt'], size=(10,1))],
    [sg.HorizontalSeparator()],
    [sg.Text('Position Corrections')],
    [sg.Text('Transducer Offset [X]:', size=(22,1)), sg.Input(default_params['x_offset'], size=(10,1)), sg.VerticalSeparator(), sg.Text('Transducer Offset [Y]:', size=(22,1)), sg.Input(default_params['y_offset'], size=(10,1))],
    [sg.HorizontalSeparator()],
    [sg.Text('Sonar Intensity Corrections')],
    [sg.Checkbox('Empiracal Gain Normalization (EGN)', default=default_params['egn'])],
    [sg.Text('EGN Stretch', size=(10,1)), sg.Combo(['None', 'Min-Max', 'Percent Clip'], default_value=default_params['egn_stretch']), sg.VerticalSeparator(), sg.Text('EGN Stretch Factor', size=(20,1)), sg.Input(default_params['egn_stretch_factor'], size=(10,1))],
    [sg.HorizontalSeparator()],
    [sg.Text('Sonagram Tile Exports')],
    [sg.Checkbox('WCP', default=default_params['wcp']), sg.Checkbox('WCR', default=default_params['wcr']), sg.Text('Image Format:', size=(12,1)), sg.Combo(['.jpg', '.png'], default_value=default_params['tileFile'])],
    [sg.HorizontalSeparator()],
    [sg.Text('Speed Corrected Sonagram Exports')],
    [sg.Text('Export Sonograms', size=(20,1)), sg.Combo(['False', 'True: Keep WC & Shadows', 'True: Mask WC & Shadows'], default_value=default_params['lbl_set'])],
    [sg.Text('Speed Correction', size=(20,1)), sg.Input(default_params['spdCor'], size=(10,1)), sg.VerticalSeparator(), sg.Checkbox('Max Crop', default=default_params['maxCrop'])],
    [sg.HorizontalSeparator()],
    [sg.Text('Depth Detection and Shadow Removal')],
    [sg.Text('Shadow Removal', size=(20,1)), sg.Combo(['False', 'Remove all shadows', 'Remove only bank shadows'], default_value=default_params['remShadow'])],
    [sg.Text('Depth Detection', size=(20,1)), sg.Combo(['Sensor', 'Auto'], default_value=default_params['detectDep']), sg.VerticalSeparator(), sg.Checkbox('Smooth Depth', default=default_params['smthDep']), sg.VerticalSeparator(), sg.Text('Adjust Depth [m]'), sg.Input(default_params['adjDep'], size=(10,1)), sg.VerticalSeparator(()), sg.Checkbox('Plot Bedpick', default=default_params['pltBedPick'])],
    [sg.HorizontalSeparator()],
    [sg.Text('Sonar Georectification Exports')],
    [sg.Checkbox('WCP', default=default_params['rect_wcp']), sg.Checkbox('WCR', default=default_params['rect_wcr']), sg.Text('Sonar Colormap'), sg.Combo(plt.colormaps(), default_value=default_params['son_colorMap'])],
    [sg.HorizontalSeparator()],
    [sg.Text('Substrate Mapping')],
    [sg.Checkbox('Predict Substrate', default=default_params['pred_sub']), sg.VerticalSeparator(), sg.Checkbox('Export Substrate Plots', default=default_params['pltSubClass'])],
    [sg.Checkbox('Map Substrate [Raster]', default=default_params['map_sub']), sg.VerticalSeparator(), sg.Checkbox('Map Substrate [Polygon]', default=default_params['export_poly']), sg.VerticalSeparator(), sg.Text('Classification Method'), sg.Combo(['max'], default_value=default_params['map_class_method'])],
    [sg.HorizontalSeparator()],
    [sg.Text('Mosaic Exports')],
    [sg.Text('Pixel Size [m, 0==Default Size]'), sg.Input(default_params['pix_res'], size=(10,1)), sg.VerticalSeparator(), sg.Text('# Chunks per Mosaic [0==All Chunks]'), sg.Input(default_params['mosaic_nchunk'], size=(10,1))],
    [sg.Text('Export Sonar Mosaic'), sg.Combo(['False', 'GTiff', 'VRT'], default_value=default_params['mosaic']), sg.VerticalSeparator(), sg.Text('Export Substrate Mosaic'), sg.Combo(['False', 'GTiff', 'VRT'], default_value=default_params['map_mosaic'])],
    [sg.HorizontalSeparator()],
    [sg.Submit(), sg.Quit(), sg.Button('Save Defaults')]
]



layout2 =[[sg.Column(layout, scrollable=True,  vertical_scroll_only=True, size_subsample_height=2)]]
window = sg.Window('Process Single Humminbird Sonar Recording', layout2, resizable=True)

while True:
    event, values = window.read()
    if event == "Quit" or event == "Submit":
        break
    if event == "Save Defaults":
        saveDefaultParams(values)

window.close()

if event == "Quit":
    sys.exit()


#################################
# Convert parameters if necessary

# EGN Stretch
egn_stretch = values[17]
if egn_stretch == 'None':
    egn_stretch = 0
elif egn_stretch == 'Min-Max':
    egn_stretch = 1
elif egn_stretch == 'Percent Clip':
    egn_stretch = 2
egn_stretch = int(egn_stretch)

# Speed Corrected Sonograms
lbl_set = values[25]
if lbl_set == 'False':
    lbl_set = 0
elif lbl_set == 'True: Keep WC & Shadows':
    lbl_set = 1
elif lbl_set == 'True: Mask WC & Shadows':
    lbl_set = 2
lbl_set = int(lbl_set)

# Shadow removal
remShadow = values[30]
if remShadow == 'False':
    remShadow = 0
elif remShadow == 'Remove all shadows':
    remShadow = 1
elif remShadow == 'Remove only bank shadows':
    remShadow = 2
remShadow = int(remShadow)

# Depth detection
detectDep = values[31]
if detectDep == 'Sensor':
    detectDep = 0
elif detectDep == 'Auto':
    detectDep = 1
detectDep = int(detectDep)

# Sonar mosaic
mosaic = values[55]
if mosaic == 'False':
    mosaic = int(0)
elif mosaic == 'GTiff':
    mosaic = int(1)
elif mosaic == 'VRT':
    mosaic = int(2)
mosaic = int(mosaic)

# Substrate mosaic
map_mosaic = values[57]
if map_mosaic == 'False':
    map_mosaic = 0
elif map_mosaic == 'GTiff':
    map_mosaic = 1
elif map_mosaic == 'VRT':
    map_mosaic = 2
map_mosaic = int(map_mosaic)


params = {
    'humFile':values[0],
    'projDir':os.path.join(values[1], values[2]),
    'project_mode':int(values[3]),
    'tempC':float(values[5]),
    'nchunk':int(values[6]),
    'cropRange':float(values[7]),
    'exportUnknown':values[8],
    'fixNoDat':values[9],
    'threadCnt':int(values[10]),
    'x_offset':float(values[12]),
    'y_offset':float(values[14]),
    'egn':values[16],
    'egn_stretch':egn_stretch,
    'egn_stretch_factor':float(values[19]),
    'wcp':values[21],
    'wcr':values[22],
    'tileFile':values[23],
    'lbl_set':lbl_set,
    'spdCor':float(values[26]),
    'maxCrop':values[28],
    'remShadow':remShadow,
    'detectDep':detectDep,
    'smthDep':values[33],
    'adjDep':float(values[35]),
    'pltBedPick':values[37],
    'rect_wcp':values[39],
    'rect_wcr':values[40],
    'son_colorMap':values[41],
    'pred_sub':values[43],
    'pltSubClass':values[45],
    'map_sub':values[46],
    'export_poly':values[48],
    'map_class_method':values[50],
    'pix_res':float(values[52]),
    'mosaic_nchunk':int(values[54]),
    'mosaic':mosaic,
    'map_mosaic':map_mosaic
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

if not 'map_predict' in locals():
    map_predict = 0

#============================================

print('\n\n', '***User Parameters***')
for k,v in params.items():
    print("| {:<20s} : {:<10s} |".format(k, str(v)))

#============================================
# Add ofther params
params['sonFiles'] = sonFiles
params['logfilename'] = logfilename
params['script'] = [script, copied_script_name]

#==================================================
print('\n===========================================')
print('===========================================')
print('***** READING *****')
print("working on "+projDir)
read_master_func(**params)
# read_master_func(sonFiles, humFile, projDir, t, nchunk, exportUnknown, wcp, wcr, tileFile, detectDepth, smthDep, adjDep, pltBedPick, threadCnt)

#==================================================
if rect_wcp or rect_wcr:
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

sys.stdout.log.close()


