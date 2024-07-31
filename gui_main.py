
import sys
sys.path.insert(0, 'src')
import os
PySimpleGUI_License = 'e3yAJ9MVaOWANplCbmndNNl2VwHvlCwpZTSjIl6DIjkiRGpYc53aRty8aBWpJF1qdwGLlzv9bUiHILs3Inkyxpp5Yq2OVku8cg2ZVrJ7RNCQI66bMcTLcnyKMbTRMK57OCTPMGxGNtS8whirTBGTlLjxZEWg5DzWZdUXRUlLcDGfxnv7eiWB1jlOb6nqR8WTZ2XsJVzbabW19ouWI6j0oXiKN0Si4AwtI7iFw8iGTBmtFftjZEUxZMpYcLncNk0rIJj4oyisQq2uFCtqZnXWJvvqbEiCICsSIbkC5jhKbvWTVqM2YtX6Ni0XIJjloji1QEmU9Ak5ayWp5nlnIwi3wiiOQK279ytqcKGwFGuvepS6IH6iIOiYIGs7I4kYNQ13cY33RkvIbqWkVyypSKUOQoiZO2ijIFzaMNTEAp0bNxyWI1sLIwkRRjhZdNGBVoJkcZ3MNN1yZMWTQtihOiieIYyXMDDIIF0ILaTyAt36LKTREj5JI1iYwcixRgGuFk0BZGU5VZ4dciGUl3ykZ3XtMbilOMiBIhy1M5DtId1mL6T1A935LYTLEN5iI3iJwoirR8Wa12h5a0WtxkBNZdGiRJyYZXX9N5zZI2jSoZizYpmp9YkHaIWz5YluLTmcNXzNQmGZd0twYGW6l3sALZmTNWvubcSEItsPITk6lFQgQUWZRrkfcEmAVxz0c9y7IG6sILjZEYyzO8Cf4c0WLDj3QCwSLwjPEt2BMMi0J69p854e39898f71ea82d3a530f7a6ed8a02a4eea9ffd2c7b1279074b491c71b411f392e6d726a2d2f9dbf63388356cf4e083e358fe428852d676073e128607b9ad194c15e34a4feb463a749fd3295606caa293b823d102e854cd845b79b5ec5eaec0b2ef7f9cf0c87b2dfcad3f14cd0d66a2da97e6b38a535eb8707b4486c9802a4bfeb09703382e157449096f0e3551af9f444197cacb3f3d42187cea97ab61978985ddeecd086b9cb86c4ec1c08082d47b3ed0ae9c044d9aa65e5c9bf6e00238f78ed858cfdaf0021fb95d636e0cce84d84d2c2da7ac57f2e54fe793fce44a8b8abf96ce7c381f4b7eeb55dc4b68768e8172a4dffc1b683e62a108b2dfc2ef340dab058e6ee5c1f525f93e89d39258862f099987a8ec7022db5aecb5a58e81d02370d5717d18498ae58749aa5e463cf757ab7fa84efe49c1b770da397eef22423696ad433e7232646e279906bef084b21714ac5fc2af564a03ebc789123aed44531765b3e72c6165131feab68e35e0276a64760ee9abf043bece1e3cd148bcec97ab835395391387ff9d2b74a835a15ea5bac9c7e1218c217481a3999a91e037a138aaf5dddadb2247141242140b130e273aab5e1e6855fae8b7ee80d64be2d09a46f3d49555f53a7a849138fc3b9d2323658ea7e86a0039c40f3c15fd3647f99ec98232d9734a5933177c48c6575a1415e2808640cfb27773e728fe128b99757'
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
    [sg.In(size=(80,1)), sg.FileBrowse(key='humFile', file_types=(("DAT File", "*.DAT"), ), initial_folder=os.path.dirname(default_params['humFile']))],
    [sg.Text('AOI')],
    [sg.In(size=(80,1)), sg.FileBrowse(key='aoi', file_types=(("Shapefile", "*.shp"), (".plan File", "*.plan")), initial_folder=os.path.dirname(default_params['aoi']))],
    [sg.Text('Output Folder')],
    [sg.In(size=(80,1)), sg.FolderBrowse(key='proj', initial_folder=os.path.dirname(default_params['projDir']))],
    [sg.Text('Project Name', size=(15,1)), sg.InputText(key='projName', size=(50,1), default_text=os.path.basename(default_params['projDir']))],
    [sg.Checkbox('Overwrite Existing Project', key='project_mode', default=default_params['project_mode'])],
    [sg.HorizontalSeparator()],
    [sg.Text('General Parameters')],
    [sg.Text('Temperature [C]', size=(20,1)), sg.Input(key='tempC', default_text=default_params['tempC'], size=(10,1))],
    [sg.Text('Chunk Size', size=(20,1)), sg.Input(key='nchunk', default_text=default_params['nchunk'], size=(10,1))],
    [sg.Text('Crop Range [m]', size=(20,1)), sg.Input(key='cropRange', default_text=default_params['cropRange'], size=(10,1))],
    [sg.Checkbox('Export Unknown Ping Attributes', key='exportUnknown', default=default_params['exportUnknown'])],
    [sg.Checkbox('Locate and flag missing pings', key='fixNoDat', default=default_params['fixNoDat'])],
    [sg.Text('Thread Count [0==All Threads]', size=(30,1)), sg.Input(key='threadCnt', default_text=default_params['threadCnt'], size=(10,1))],
    [sg.HorizontalSeparator()],
    [sg.Text('GeoTiff Pixel Resolution [0==Default Resolution (~0.02m)]')],
    [sg.Text('Sonar', size=(10,1)), sg.Input(key='pix_res_son', default_text=default_params['pix_res_son'], size=(10,1)), sg.Text('Substrate', size=(10,1)), sg.Input(key='pix_res_map', default_text=default_params['pix_res_map'], size=(10,1))],
    [sg.HorizontalSeparator()],
    [sg.Text('Position Corrections')],
    [sg.Text('Transducer Offset [X]:', size=(22,1)), sg.Input(key='x_offset', default_text=default_params['x_offset'], size=(10,1)), sg.VerticalSeparator(), sg.Text('Transducer Offset [Y]:', size=(22,1)), sg.Input(key='y_offset', default_text=default_params['y_offset'], size=(10,1))],
    [sg.HorizontalSeparator()],
    [sg.Text('Sonar Intensity Corrections')],
    [sg.Checkbox('Empiracal Gain Normalization (EGN)', key='egn', default=default_params['egn'])],
    [sg.Text('EGN Stretch', size=(10,1)), sg.Combo(['None', 'Min-Max', 'Percent Clip'], key='egn_stretch', default_value=default_params['egn_stretch']), sg.VerticalSeparator(), sg.Text('EGN Stretch Factor', size=(20,1)), sg.Input(key='egn_stretch_factor', default_text=default_params['egn_stretch_factor'], size=(10,1))],
    [sg.HorizontalSeparator()],
    [sg.Text('Sonagram Tile Exports')],
    [sg.Checkbox('WCP', key='wcp', default=default_params['wcp']), sg.Checkbox('WCR', key='wcr', default=default_params['wcr']), sg.Text('Image Format:', size=(12,1)), sg.Combo(['.jpg', '.png'], key='tileFile', default_value=default_params['tileFile'])],
    [sg.HorizontalSeparator()],
    [sg.Text('Speed Corrected Sonagram Exports')],
    [sg.Text('Export Sonograms', size=(20,1)), sg.Combo(['False', 'True: Keep WC & Shadows', 'True: Mask WC & Shadows'], key='lbl_set', default_value=default_params['lbl_set'])],
    [sg.Text('Speed Correction', size=(20,1)), sg.Input(key='spdCor', default_text=default_params['spdCor'], size=(10,1)), sg.VerticalSeparator(), sg.Checkbox('Max Crop', key='maxCrop', default=default_params['maxCrop'])],
    [sg.HorizontalSeparator()],
    [sg.Text('Depth Detection and Shadow Removal')],
    [sg.Text('Shadow Removal', size=(20,1)), sg.Combo(['False', 'Remove all shadows', 'Remove only bank shadows'], key='remShadow', default_value=default_params['remShadow'])],
    [sg.Text('Depth Detection', size=(20,1)), sg.Combo(['Sensor', 'Auto'], key='detectDep', default_value=default_params['detectDep']), sg.VerticalSeparator(), sg.Checkbox('Smooth Depth', key='smthDep', default=default_params['smthDep']), sg.VerticalSeparator(), sg.Text('Adjust Depth [m]'), sg.Input(key='adjDep', default_text=default_params['adjDep'], size=(10,1)), sg.VerticalSeparator(()), sg.Checkbox('Plot Bedpick', key='pltBedPick', default=default_params['pltBedPick'])],
    [sg.HorizontalSeparator()],
    [sg.Text('Sonar Georectification Exports')],
    [sg.Checkbox('WCP', key='rect_wcp', default=default_params['rect_wcp']), sg.Checkbox('WCR', key='rect_wcr', default=default_params['rect_wcr']), sg.Text('Sonar Colormap'), sg.Combo(plt.colormaps(), key='son_colorMap', default_value=default_params['son_colorMap'])],
    [sg.HorizontalSeparator()],
    [sg.Text('Substrate Mapping')],
    # [sg.Checkbox('Predict Substrate', key='pred_sub', default=default_params['pred_sub']), sg.VerticalSeparator(), sg.Checkbox('Export Substrate Plots', key='pltSubClass', default=default_params['pltSubClass'])],
    # [sg.Checkbox('Map Substrate [Raster]', key='map_sub', default=default_params['map_sub']), sg.VerticalSeparator(), sg.Checkbox('Map Substrate [Polygon]', key='export_poly', default=default_params['export_poly']), sg.VerticalSeparator(), sg.Text('Classification Method'), sg.Combo(['max'], key='map_class_method', default_value=default_params['map_class_method'])],
    # [sg.Checkbox('Export Substrate Plots', key='pltSubClass', default=default_params['pltSubClass'])],
    # [sg.Text('Map Predictions', size=(20,1)), sg.Combo(['False', 'Logit', 'Probability'], key='map_predict', default_value=default_params['map_predict'])],
    [sg.Checkbox('Map Substrate [Raster]', key='map_sub', default=default_params['map_sub']), sg.VerticalSeparator(), sg.Checkbox('Map Substrate [Polygon]', key='export_poly', default=default_params['export_poly']), sg.VerticalSeparator(), sg.Checkbox('Export Substrate Plots', key='pltSubClass', default=default_params['pltSubClass'])],
    [sg.HorizontalSeparator()],
    [sg.Text('Mosaic Exports')],
    [sg.Text('# Chunks per Mosaic [0==All Chunks]'), sg.Input(key='mosaic_nchunk', default_text=default_params['mosaic_nchunk'], size=(10,1))],
    [sg.Text('Export Sonar Mosaic'), sg.Combo(['False', 'GTiff', 'VRT'], key='mosaic', default_value=default_params['mosaic']), sg.VerticalSeparator(), sg.Text('Export Substrate Mosaic'), sg.Combo(['False', 'GTiff', 'VRT'], key='map_mosaic', default_value=default_params['map_mosaic'])],
    [sg.HorizontalSeparator()],
    [sg.Text('Miscellaneous Exports')],
    [sg.Checkbox('Banklines', key='banklines', default=default_params['banklines'])],
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

# AOI
aoi = values['aoi']
if aoi == '':
    aoi = False

# EGN Stretch
egn_stretch = values['egn_stretch']
if egn_stretch == 'None':
    egn_stretch = 0
elif egn_stretch == 'Min-Max':
    egn_stretch = 1
elif egn_stretch == 'Percent Clip':
    egn_stretch = 2
egn_stretch = int(egn_stretch)

# Speed Corrected Sonograms
lbl_set = values['lbl_set']
if lbl_set == 'False':
    lbl_set = 0
elif lbl_set == 'True: Keep WC & Shadows':
    lbl_set = 1
elif lbl_set == 'True: Mask WC & Shadows':
    lbl_set = 2
lbl_set = int(lbl_set)

# Shadow removal
remShadow = values['remShadow']
if remShadow == 'False':
    remShadow = 0
elif remShadow == 'Remove all shadows':
    remShadow = 1
elif remShadow == 'Remove only bank shadows':
    remShadow = 2
remShadow = int(remShadow)

# Depth detection
detectDep = values['detectDep']
if detectDep == 'Sensor':
    detectDep = 0
elif detectDep == 'Auto':
    detectDep = 1
detectDep = int(detectDep)

# Predict substrate
if values['map_sub']:
    values['pred_sub'] = True
elif values['export_poly']:
    values['pred_sub'] = True
    values['map_sub'] = True
elif values['pltSubClass']:
    values['pred_sub'] = True
else:
    values['pred_sub'] = False

# Map class method
values['map_class_method'] = 'max'

# Map predictions #### DISABLED ####
# map_predict = values['map_predict']
# if map_predict == 'False':
#     map_predict = 0
# elif map_predict == 'Probability':
#     map_predict = 1
# elif map_predict == 'Logit':
#     map_predict = 2
# map_predict = int(map_predict)
map_predict = 0 # Disable workflow

# Sonar mosaic
mosaic = values['mosaic']
if mosaic == 'False':
    mosaic = int(0)
elif mosaic == 'GTiff':
    mosaic = int(1)
elif mosaic == 'VRT':
    mosaic = int(2)
mosaic = int(mosaic)

# Substrate mosaic
map_mosaic = values['map_mosaic']
if map_mosaic == 'False':
    map_mosaic = 0
elif map_mosaic == 'GTiff':
    map_mosaic = 1
elif map_mosaic == 'VRT':
    map_mosaic = 2
map_mosaic = int(map_mosaic)


params = {
    'humFile':values['humFile'],
    'aoi':aoi,
    'projDir':os.path.join(values['proj'], values['projName']),
    'project_mode':int(values['project_mode']),
    'tempC':float(values['tempC']),
    'nchunk':int(values['nchunk']),
    'cropRange':float(values['cropRange']),
    'exportUnknown':values['exportUnknown'],
    'fixNoDat':values['fixNoDat'],
    'threadCnt':int(values['threadCnt']),
    'pix_res_son':float(values['pix_res_son']),
    'pix_res_map':float(values['pix_res_map']),
    'x_offset':float(values['x_offset']),
    'y_offset':float(values['y_offset']),
    'egn':values['egn'],
    'egn_stretch':egn_stretch,
    'egn_stretch_factor':float(values['egn_stretch_factor']),
    'wcp':values['wcp'],
    'wcr':values['wcr'],
    'tileFile':values['tileFile'],
    'lbl_set':lbl_set,
    'spdCor':float(values['spdCor']),
    'maxCrop':values['maxCrop'],
    'remShadow':remShadow,
    'detectDep':detectDep,
    'smthDep':values['smthDep'],
    'adjDep':float(values['adjDep']),
    'pltBedPick':values['pltBedPick'],
    'rect_wcp':values['rect_wcp'],
    'rect_wcr':values['rect_wcr'],
    'son_colorMap':values['son_colorMap'],
    'pred_sub':values['pred_sub'],
    'pltSubClass':values['pltSubClass'],
    'map_sub':values['map_sub'],
    'export_poly':values['export_poly'],
    'map_class_method':values['map_class_method'],
    'map_predict':map_predict,
    'mosaic_nchunk':int(values['mosaic_nchunk']),
    'mosaic':mosaic,
    'map_mosaic':map_mosaic,
    'banklines':values['banklines']
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

try:

    #==================================================
    print('\n===========================================')
    print('===========================================')
    print('***** READING *****')
    print("working on "+projDir)
    read_master_func(**params)
    # read_master_func(sonFiles, humFile, projDir, t, nchunk, exportUnknown, wcp, wcr, tileFile, detectDepth, smthDep, adjDep, pltBedPick, threadCnt)

    #==================================================
    if rect_wcp or rect_wcr or banklines:
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

except Exception as Argument:
    unableToProcessError(logfilename)


