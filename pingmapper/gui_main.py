
import sys, os
import webbrowser

PySimpleGUI_License = 'e3yAJ9MVaOWANplCbmndNNl2VwHvlCwpZTSjIl6DIjkiRGpYc53aRty8aBWpJF1qdwGLlzv9bUiHILs3Inkyxpp5Yq2OVku8cg2ZVrJ7RNCQI66bMcTLcnyKMbTRMK57OCTPMGxGNtS8whirTBGTlLjxZEWg5DzWZdUXRUlLcDGfxnv7eiWB1jlOb6nqR8WTZ2XsJVzbabW19ouWI6j0oXiKN0Si4AwtI7iFw8iGTBmtFftjZEUxZMpYcLncNk0rIJj4oyisQq2uFCtqZnXWJvvqbEiCICsSIbkC5jhKbvWTVqM2YtX6Ni0XIJjloji1QEmU9Ak5ayWp5nlnIwi3wiiOQK279ytqcKGwFGuvepS6IH6iIOiYIGs7I4kYNQ13cY33RkvIbqWkVyypSKUOQoiZO2ijIFzaMNTEAp0bNxyWI1sLIwkRRjhZdNGBVoJkcZ3MNN1yZMWTQtihOiieIYyXMDDIIF0ILaTyAt36LKTREj5JI1iYwcixRgGuFk0BZGU5VZ4dciGUl3ykZ3XtMbilOMiBIhy1M5DtId1mL6T1A935LYTLEN5iI3iJwoirR8Wa12h5a0WtxkBNZdGiRJyYZXX9N5zZI2jSoZizYpmp9YkHaIWz5YluLTmcNXzNQmGZd0twYGW6l3sALZmTNWvubcSEItsPITk6lFQgQUWZRrkfcEmAVxz0c9y7IG6sILjZEYyzO8Cf4c0WLDj3QCwSLwjPEt2BMMi0J69p854e39898f71ea82d3a530f7a6ed8a02a4eea9ffd2c7b1279074b491c71b411f392e6d726a2d2f9dbf63388356cf4e083e358fe428852d676073e128607b9ad194c15e34a4feb463a749fd3295606caa293b823d102e854cd845b79b5ec5eaec0b2ef7f9cf0c87b2dfcad3f14cd0d66a2da97e6b38a535eb8707b4486c9802a4bfeb09703382e157449096f0e3551af9f444197cacb3f3d42187cea97ab61978985ddeecd086b9cb86c4ec1c08082d47b3ed0ae9c044d9aa65e5c9bf6e00238f78ed858cfdaf0021fb95d636e0cce84d84d2c2da7ac57f2e54fe793fce44a8b8abf96ce7c381f4b7eeb55dc4b68768e8172a4dffc1b683e62a108b2dfc2ef340dab058e6ee5c1f525f93e89d39258862f099987a8ec7022db5aecb5a58e81d02370d5717d18498ae58749aa5e463cf757ab7fa84efe49c1b770da397eef22423696ad433e7232646e279906bef084b21714ac5fc2af564a03ebc789123aed44531765b3e72c6165131feab68e35e0276a64760ee9abf043bece1e3cd148bcec97ab835395391387ff9d2b74a835a15ea5bac9c7e1218c217481a3999a91e037a138aaf5dddadb2247141242140b130e273aab5e1e6855fae8b7ee80d64be2d09a46f3d49555f53a7a849138fc3b9d2323658ea7e86a0039c40f3c15fd3647f99ec98232d9734a5933177c48c6575a1415e2808640cfb27773e728fe128b99757'
import PySimpleGUI as sg
import matplotlib.pyplot as plt

# Add 'pingmapper' to the path, may not need after pypi package...
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PACKAGE_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.append(PACKAGE_DIR)

from pingmapper.funcs_common import *
from pingmapper.main_readFiles import read_master_func
from pingmapper.main_rectify import rectify_master_func
from pingmapper.main_mapSubstrate import map_master_func

import json
import pandas as pd

filter_time_csv = os.path.join(SCRIPT_DIR, 'clip_table.csv')
filter_time_csv = os.path.normpath(filter_time_csv)

def gui(batch: bool):  

    # Get processing script's dir so we can save it to file
    scriptDir = SCRIPT_DIR

    # For the logfile
    oldOutput = sys.stdout

    start_time = time.time()

    #============================================

    # Default Values
    # Edit values below to change default values in gui
    primary_default_params = os.path.join(SCRIPT_DIR, "default_params.json")

    if not os.path.exists(primary_default_params):
        d = os.environ['CONDA_PREFIX']
        primary_default_params = os.path.join(d, 'pingmapper_config', 'default_params.json')
    
    default_params_file = os.path.join(SCRIPT_DIR, "user_params.json")

    if not os.path.exists(default_params_file):
        default_params_file = primary_default_params
    with open(default_params_file) as f:
        default_params = json.load(f)

    # Make sure all params in user params
    with open(primary_default_params) as f:
        primary_defaults = json.load(f)

    for k, v in primary_defaults.items():
        if k not in default_params:
            default_params[k] = v

    #============================================
    # Set up gui

    layout = []

    ########################
    # Help and Documentation

    text_help = sg.Text('Help and Documentation\n', font=("Helvetica", 14, "underline"))
    button_help_run_pm = sg.Button('Using PINGMapper', key='doc_link', size=(20,1))
    button_help_pm_handbook = sg.Button('PINGMapper Handbook', key='handbook_link', size=(20,1))
    button_ask_question = sg.Button('Ask a Question', key='question_link', size=(20,1))
    button_issue_report = sg.Button('Report an Issue', key='issue_link', size=(20,1))

    # Add to layout
    layout.append([text_help])
    layout.append([button_help_run_pm, button_help_pm_handbook])
    layout.append([button_ask_question, button_issue_report])
    layout.append([sg.HorizontalSeparator()])

    ##################
    # Input parameters
    text_io = sg.Text('I/O\n', font=("Helvetica", 14, "underline"))

    if batch:
        text_input = sg.Text('Parent Folder of Recordings to Process')
        in_input = sg.In(key='inDir', size=(80,1))
        browse_input = sg.FolderBrowse(initial_folder=(default_params['inDir']))

    else:
        text_input = sg.Text('Recording to Process')
        # in_input = sg.In(key='inFile', size=(80,1))
        in_input = sg.In(key='inFile', size=(80,1), default_text=default_params['inFile'])
        browse_input = sg.FileBrowse(file_types=(("Sonar File", "*.DAT *.sl2 *.sl3 *.RSD *.svlog") ), initial_folder=os.path.dirname(default_params['inFile']))
        # browse_input = sg.FileBrowse(file_types=(("Sonar File", "*.DAT *.sl2 *.sl3 *.svlog") ), initial_folder=os.path.dirname(default_params['inFile']))

    # Add to layout
    layout.append([text_io])
    layout.append([text_input])
    layout.append([in_input, browse_input])

    ###################
    # Output parameters
    text_output = sg.Text('Output Folder')
    # in_output = sg.In(key='proj', size=(80,1))
    in_output = sg.In(key='proj', size=(80,1), default_text=os.path.dirname(default_params['projDir']))
    browse_output = sg.FolderBrowse(initial_folder=os.path.dirname(default_params['projDir']))

    # Add to layout
    layout.append([text_output])
    layout.append([in_output, browse_output])

    ##############
    # Project Name
    if batch:
        text_prefix = sg.Text('Project Name Prefix:', size=(20,1))
        in_prefix = sg.Input(key='prefix', size=(10,1))

        text_suffix = sg.Text('Project Name Suffix:', size=(20,1))
        in_suffix = sg.Input(key='suffix', size=(10,1))

        # Add to layout
        layout.append([text_prefix, in_prefix, sg.VerticalSeparator(), text_suffix, in_suffix])

    else:
        text_project = sg.Text('Project Name', size=(15,1))
        in_project = sg.InputText(key='projName', size=(50,1), default_text=default_params['projName'])

        # Add to layout
        layout.append([text_project, in_project])

    ###########
    # Overwrite
    check_overwrite = sg.Checkbox('Overwrite Existing Project', key='project_mode', default=default_params['project_mode'])

    # Add to layout
    layout.append([check_overwrite])

    ####################
    # General Parameters
    text_general = sg.Text('General Parameters\n', font=("Helvetica", 14, "underline"))

    # Temperature
    text_temp = sg.Text('Temperature [C]', size=(30,1))
    in_temp = sg.Input(key='tempC', default_text=default_params['tempC'], size=(10,1))

    # Chunk
    text_chunk = sg.Text('Chunk Size', size=(30,1))
    in_chunk = sg.Input(key='nchunk', default_text=default_params['nchunk'], size=(10,1))

    # Ping Attributes
    check_attr = sg.Checkbox('Export Unknown Ping Attributes', key='exportUnknown', default=default_params['exportUnknown'])

    # Missing Pings
    check_missing = sg.Checkbox('Locate and flag missing pings', key='fixNoDat', default=default_params['fixNoDat'])

    # Thread count
    text_thread = sg.Text('Thread Count [0==All Threads]', size=(30,1))
    in_thread = sg.Input(key='threadCnt', default_text=default_params['threadCnt'], size=(10,1))

    col_general_1 = sg.Column([[text_temp, in_temp], [text_chunk, in_chunk], [text_thread, in_thread]], pad=0)
    col_general_2 = sg.Column([[check_attr], [check_missing]], pad=0)

    # Add to layout
    layout.append([sg.HorizontalSeparator()])
    layout.append([text_general])
    layout.append([col_general_1, sg.VerticalSeparator(), col_general_2])

    
    ###########
    # Filtering
    text_filtering = sg.Text('Filter Sonar Log\n', font=("Helvetica", 14, "underline"))

    # Cropping
    text_crop = sg.Text('Crop Range [m]', size=(22,1))
    in_crop = sg.Input(key='cropRange', default_text=default_params['cropRange'], size=(10,1))

    # Heading
    text_heading = sg.Text('Max. Heading Deviation [deg]:', size=(22,1))
    in_heading = sg.Input(key='max_heading_deviation', default_text=default_params['max_heading_deviation'], size=(10,1))
    text_distance = sg.Text('Distance [m]:', size=(15,1))
    in_distance = sg.Input(key='max_heading_distance', default_text=default_params['max_heading_distance'], size=(10,1))

    # Speed
    text_speed_min = sg.Text('Min. Speed [m/s]:', size=(22,1))
    in_speed_min = sg.Input(key='min_speed', default_text=default_params['min_speed'], size=(10,1))
    text_speed_max = sg.Text('Max. Speed [m/s]:', size=(15,1))
    in_speed_max = sg.Input(key='max_speed', default_text=default_params['max_speed'], size=(10,1))

    # AOI
    text_aoi = sg.Text('AOI')
    in_aoi = sg.In(size=(80,1))
    browse_aoi = sg.FileBrowse(key='aoi', file_types=(("Shapefile", "*.shp"), (".plan File", "*.plan")), initial_folder=os.path.dirname(default_params['aoi']))

    # Time table
    button_time_table = sg.Button('Edit Table')
    check_time_load = sg.Checkbox('Filter by Time', key='filter_table', default=default_params['filter_table'])

    # Add to layout
    layout.append([sg.HorizontalSeparator()])
    layout.append([text_filtering])
    layout.append([text_crop, in_crop])
    layout.append([text_heading, in_heading, sg.VerticalSeparator(), text_distance, in_distance])
    layout.append([text_speed_min, in_speed_min, sg.VerticalSeparator(), text_speed_max, in_speed_max])
    layout.append([text_aoi])
    layout.append([in_aoi, browse_aoi])
    layout.append([check_time_load, button_time_table])

    ######################
    # Position Corrections

    # Position text
    text_position = sg.Text('Position Corrections - Transducer Offset', font=("Helvetica", 14, "underline"))

    # Add link to documentation
    button_help_position = sg.Button('?', key='doc_link_transducer_offset', size=(2,1))

    # X offset
    text_x_offset = sg.Text('X Offset [m]:', size=(22,1))
    in_x_offset = sg.Input(key='x_offset', default_text=default_params['x_offset'], size=(10,1))
    
    # Y offset
    text_y_offset = sg.Text('Y Offset [m]:', size=(22,1))
    in_y_offset = sg.Input(key='y_offset', default_text=default_params['y_offset'], size=(10,1))

    # Add to layout
    layout.append([sg.HorizontalSeparator()])
    layout.append([text_position, button_help_position])
    layout.append([sg.Text('', size=(1,1))])
    layout.append([text_x_offset, in_x_offset, sg.VerticalSeparator(), text_y_offset, in_y_offset])


    #################
    # EGN Corrections

    # EGN text
    text_egn = sg.Text('Sonar Intensity Corrections\n', font=("Helvetica", 14, "underline"))

    # EGN
    check_egn = sg.Checkbox('Empiracal Gain Normalization (EGN)', key='egn', default=default_params['egn'])

    # EGN options
    text_egn_stretch = sg.Text('EGN Stretch', size=(20,1))
    combo_egn_stretch = sg.Combo(['None', 'Min-Max', 'Percent Clip'], key='egn_stretch', default_value=default_params['egn_stretch'])
    text_egn_factor = sg.Text('EGN Stretch Factor', size=(20,1))
    in_egn_factor = sg.Input(key='egn_stretch_factor', default_text=default_params['egn_stretch_factor'], size=(10,1))

    col_egn_1 = sg.Column([[check_egn]], pad=0)
    col_egn_2 = sg.Column([[text_egn_stretch, combo_egn_stretch], [text_egn_factor, in_egn_factor]], pad=0)
    # Add to layout
    layout.append([sg.HorizontalSeparator()])
    layout.append([text_egn])
    layout.append([col_egn_1, sg.VerticalSeparator(), col_egn_2])

    #######################
    # Sonogram Tile Exports

    text_tile = sg.Text('Sonogram Tile Exports\n', font=("Helvetica", 14, "underline"))

    # Tiles
    check_wcp = sg.Checkbox('WCP (Water Column Present)', key='wcp', default=default_params['wcp'])
    check_wcm = sg.Checkbox('WCM (Water Column Masked)', key='wcm', default=default_params['wcm'])
    check_wcr = sg.Checkbox('SRC (Slant Range Corrected)', key='wcr', default=default_params['wcr'])
    check_wco = sg.Checkbox('WCO (Water Column Only)', key='wco', default=default_params['wco'])

    # Options
    text_file_type = sg.Text('Image Format:', size=(15,1))
    combo_file_type = sg.Combo(['.jpg', '.png'], key='tileFile', default_value=default_params['tileFile'])

    text_tile_color = sg.Text('Tile Colormap:', size=(15,1))
    combo_tile_color = sg.Combo(plt.colormaps(), key='sonogram_colorMap', default_value=default_params['sonogram_colorMap'])


    check_speed_cor = sg.Checkbox('Speed Correct', key='spdCor', default=default_params['spdCor'])

    check_max_crop = sg.Checkbox('Max Crop', key='maxCrop', default=default_params['maxCrop'])

    # Mask
    check_mask_shdw = sg.Checkbox('Mask Shadows', key='mask_shdw', default=default_params['mask_shdw'])
    
    # Turn into columns
    col_tile_1 = sg.Column([[check_wcp], [check_wcm], [check_wcr], [check_wco]], pad=0)
    col_tile_2 = sg.Column([[check_speed_cor], [check_mask_shdw], [check_max_crop]], pad=0)
    col_tile_3 = sg.Column([[text_file_type, combo_file_type], [text_tile_color, combo_tile_color]], pad=0)
    

    # Add to layout
    layout.append([sg.HorizontalSeparator()])
    layout.append([text_tile])
    layout.append([col_tile_1, sg.VerticalSeparator(), col_tile_2, sg.VerticalSeparator(), col_tile_3])

    ########################
    # Depth & Shadow Removal

    text_dep_shdw = sg.Text('Depth Detection and Shadow Removal\n', font=("Helvetica", 14, "underline"))

    # Shadow
    text_shdw = sg.Text('Shadow Removal', size=(15,1))
    in_shdw = sg.Combo(['False', 'Remove all shadows', 'Remove only bank shadows'], key='remShadow', default_value=default_params['remShadow'])

    # Depth
    text_dep = sg.Text('Depth Detection', size=(15,1))
    in_dep = sg.Combo(['Sensor', 'Auto'], key='detectDep', default_value=default_params['detectDep'])
    check_dep_smth = sg.Checkbox('Smooth Depth', key='smthDep', default=default_params['smthDep'])
    text_dep_adj = sg.Text('Adjust Depth [m]', size=(15,1))
    in_dep_adj = sg.Input(key='adjDep', default_text=default_params['adjDep'], size=(10,1))
    check_dep_plt = sg.Checkbox('Plot Bedpick', key='pltBedPick', default=default_params['pltBedPick'])

    col_depshdw_1 = sg.Column([[text_dep, in_dep], [text_dep_adj, in_dep_adj], [check_dep_smth], [check_dep_plt]], pad=0)
    col_depshdw_2 = sg.Column([[text_shdw, in_shdw]], pad=0)

    # Add to layout
    layout.append([sg.HorizontalSeparator()])
    layout.append([text_dep_shdw])
    layout.append([col_depshdw_1, sg.VerticalSeparator(), col_depshdw_2])

    ########################
    # Sonar Georectification

    text_rect = sg.Text('Sonar Georectification Exports\n', font=("Helvetica", 14, "underline"))

    # Pixel resolution
    text_rect_pix = sg.Text('Pixel Resolution [0==Default (~0.02m)]', size=(30,1))
    in_rect_pix = sg.Input(key='pix_res_son', default_text=default_params['pix_res_son'], size=(10,1))

    # Type
    check_rect_wcp = sg.Checkbox('WCP (Water Column Present)', key='rect_wcp', default=default_params['rect_wcp'])
    check_rect_wcr = sg.Checkbox('WCR (Water Column Removed)', key='rect_wcr', default=default_params['rect_wcr'])

    # # COG
    # check_rect_cog = sg.Checkbox('Use COG', key='cog', default=default_params['cog'])
    # Rectification Method
    check_rect_meth = sg.Checkbox('Rubber Sheeting or', key='rubberSheeting', default=default_params['rubberSheeting'], enable_events=True)
    if default_params['rubberSheeting'] == True:
        rect_meth_status = True
    else:
        rect_meth_status = False
    combo_rect_meth = sg.Combo(['Heading', 'COG'], key='rectMethod', default_value=default_params['rectMethod'], disabled=rect_meth_status)

    # Interpolation Distance
    text_rect_interp = sg.Text('Interp. Dist.', size=(10,1))
    slide_rect_interp = sg.Slider(range=(0, 200), resolution=5, orientation='h', key='rectInterpDist', default_value=default_params['rectInterpDist'], disabled=rect_meth_status)

    text_color = sg.Text('Sonar Colormap', size=(30,1))
    combo_color = sg.Combo(plt.colormaps(), key='son_colorMap', default_value=default_params['son_colorMap'])

    text_rect_mosaic = sg.Text('Export Sonar Mosaic', size=(30,1))
    combo_rect_mosaic = sg.Combo(['False', 'GTiff', 'VRT'], key='mosaic', default_value=default_params['mosaic'])

    text_rect_chunk = sg.Text('# Chunks per Mosaic [0==All Chunks]', size=(30,1))
    in_rect_chunk = sg.Input(key='mosaic_nchunk', default_text=default_params['mosaic_nchunk'], size=(10,1))
    
    col_rect_1 = sg.Column([[check_rect_wcp], [check_rect_wcr], [check_rect_meth, combo_rect_meth], [text_rect_interp, slide_rect_interp]], pad=0)
    col_rect_2 = sg.Column([[text_rect_pix, in_rect_pix], [text_color, combo_color], [text_rect_mosaic, combo_rect_mosaic], [text_rect_chunk, in_rect_chunk]], pad=0)
    
    # Add to layout
    layout.append([sg.HorizontalSeparator()])
    layout.append([text_rect])
    layout.append([col_rect_1, sg.VerticalSeparator(), col_rect_2])


    ###################s
    # Substrate Mapping

    text_substrate = sg.Text('Substrate Mapping\n', font=("Helvetica", 14, "underline"))

    check_substrate_raster = sg.Checkbox('Map Substrate [Raster]', key='map_sub', default=default_params['map_sub'])
    check_substrate_poly = sg.Checkbox('Map Substrate [Polygon]', key='export_poly', default=default_params['export_poly'])
    check_substrate_plot =  sg.Checkbox('Export Substrate Plots', key='pltSubClass', default=default_params['pltSubClass'])
        
    text_substrate_mosaic = sg.Text('Export Substrate Mosaic', size=(30,1))
    combo_substrate_mosaic = sg.Combo(['False', 'GTiff', 'VRT'], key='map_mosaic', default_value=default_params['map_mosaic'])

    # Pixel resolution
    text_substrate_pix = sg.Text('Pixel Resolution [0==Default (~0.02m)]', size=(30,1))
    in_substrate_pix = sg.Input(key='pix_res_map', default_text=default_params['pix_res_map'], size=(10,1))

    # Columns
    col_substrate_1 = sg.Column([[check_substrate_raster], [text_substrate_mosaic, combo_substrate_mosaic], [text_substrate_pix, in_substrate_pix]], pad=0)
    col_substrate_2 = sg.Column([[check_substrate_poly], [check_substrate_plot]], pad=0)
    
    # Add to layout
    layout.append([sg.HorizontalSeparator()])
    layout.append([text_substrate])
    layout.append([col_substrate_1, sg.VerticalSeparator(), col_substrate_2])

    #######################
    # Miscellaneous Exports

    text_misc = sg.Text('Miscellaneous Shapefile Exports\n', font=("Helvetica", 14, "underline"))

    check_misc_banks = sg.Checkbox('Banklines', key='banklines', default=default_params['banklines'])
    check_misc_cov = sg.Checkbox('Coverage', key='coverage', default=default_params['coverage'])

    col_misc_1 = sg.Column([[check_misc_banks], [check_misc_cov]], pad=0)

    # Add to layout
    layout.append([sg.HorizontalSeparator()])
    layout.append([text_misc])
    layout.append([col_misc_1])
        

    #####################
    # Submit/quit buttons
    layout.append([sg.HorizontalSeparator()])
    layout.append([sg.Push(), sg.Submit(), sg.Quit(), sg.Button('Save Defaults'), sg.Push()])


    layout2 =[[sg.Column(layout, scrollable=True,  vertical_scroll_only=True, size_subsample_height=4)]]

    if batch:
        window_text = 'Batch Process Sonar Logs'
    else:
        window_text = 'Process Sonar Log'
    window = sg.Window(window_text, layout2, resizable=True)

    while True:
        event, values = window.read()

        # values['humFile'] = os.path.join(values['inDir'], 'R1.DAT')

        if event == "Quit" or event == 'Submit':
            break
        if event == "Save Defaults":
            saveDefaultParams(values)

        if event == 'Edit Table':
            clip_table(filter_time_csv)

        if event == 'doc_link':
            webbrowser.open('https://cameronbodine.github.io/PINGMapper/docs/gettingstarted/Running.html')

        if event == 'handbook_link':
            webbrowser.open('https://cameronbodine.github.io/PINGMapper/docs/tutorials/Handbook.html')

        if event == 'question_link':
            webbrowser.open('https://github.com/CameronBodine/PINGMapper/discussions')

        if event == 'issue_link':
            webbrowser.open('https://github.com/CameronBodine/PINGMapper/issues')

        if event == 'doc_link_transducer_offset':
            webbrowser.open('https://cameronbodine.github.io/PINGMapper/docs/gettingstarted/Running.html#step-6')

        # Enable or disable the slider based on the selected rectification method
        if event == 'rubberSheeting':
            if values['rubberSheeting'] == True:
                window['rectMethod'].update(disabled=True)
                window['rectInterpDist'].update(disabled=True)
            else:
                window['rectMethod'].update(disabled=False)
                window['rectInterpDist'].update(disabled=False)

        

    window.close()

    # if event == "Quit":
    #     sys.exit()
    if event == "Submit":

        batch_start_time = time.time()

        for k, v in values.items():
            print(k, v, '\n\n')

        # sys.exit()

        outDir = os.path.normpath(values['proj'])

        if batch:
            inDir = os.path.normpath(values['inDir'])

        #################################
        # Convert parameters if necessary

        if values['filter_table']:
            time_table = filter_time_csv
        else:
            time_table = False

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
            # 'humFile':values[0],
            # 'projDir':os.path.join(values[1], values[2]),
            'project_mode':int(values['project_mode']),
            'tempC':float(values['tempC']),
            'nchunk':int(values['nchunk']),
            'cropRange':float(values['cropRange']),
            'exportUnknown':values['exportUnknown'],
            'fixNoDat':values['fixNoDat'],
            'threadCnt':float(values['threadCnt']),
            'aoi':aoi,
            'max_heading_deviation':float(values['max_heading_deviation']),
            'max_heading_distance':float(values['max_heading_distance']),
            'min_speed':float(values['min_speed']),
            'max_speed':float(values['max_speed']),
            'time_table':time_table,
            'pix_res_son':float(values['pix_res_son']),
            'pix_res_map':float(values['pix_res_map']),
            'x_offset':float(values['x_offset']),
            'y_offset':float(values['y_offset']),
            'egn':values['egn'],
            'egn_stretch':egn_stretch,
            'egn_stretch_factor':float(values['egn_stretch_factor']),
            'wcp':values['wcp'],
            'wcm':values['wcm'],
            'wcr':values['wcr'],
            'wco':values['wco'],
            'sonogram_colorMap':values['sonogram_colorMap'],
            'mask_shdw':values['mask_shdw'],
            'tileFile':values['tileFile'],
            'spdCor':values['spdCor'],
            'maxCrop':values['maxCrop'],
            'remShadow':remShadow,
            'detectDep':detectDep,
            'smthDep':values['smthDep'],
            'adjDep':float(values['adjDep']),
            'pltBedPick':values['pltBedPick'],
            'rect_wcp':values['rect_wcp'],
            'rect_wcr':values['rect_wcr'],
            'rubberSheeting':values['rubberSheeting'],
            'rectMethod':values['rectMethod'],
            'rectInterpDist':int(values['rectInterpDist']),
            'son_colorMap':values['son_colorMap'],
            'mosaic_nchunk':int(values['mosaic_nchunk']),
            'pred_sub':values['pred_sub'],
            'pltSubClass':values['pltSubClass'],
            'map_sub':values['map_sub'],
            'export_poly':values['export_poly'],
            'map_class_method':values['map_class_method'],
            'map_predict':map_predict,
            'mosaic':mosaic,
            'map_mosaic':map_mosaic,
            'banklines':values['banklines'],
            'coverage':values['coverage']
        }

        globals().update(params)

        from pingmapper.doWork import doWork

        doWork(
            in_file=(values['inFile'] if not batch else None),
            in_dir=(inDir if batch else None),
            out_dir=outDir,
            proj_name=(values['projName'] if not batch else None),
            prefix=(values['prefix'] if batch else ''),
            suffix=(values['suffix'] if batch else ''),
            batch=batch,
            params=params,
            script_path=os.path.abspath(__file__),
        )

        #============================================

        # if batch:
        #     # Find all DAT and SON files in all subdirectories of inDir
        #     inFiles=[]
        #     for root, dirs, files in os.walk(inDir):
        #         if '__MACOSX' not in root:
        #             for file in files:
        #                 if file.endswith('.DAT') or file.endswith('.sl2') or file.endswith('.sl3') or file.endswith('.RSD') or file.endswith('.svlog'):
        #                     inFiles.append(os.path.join(root, file))

        #     inFiles = sorted(inFiles)

        # else:
        #     inFiles = [values['inFile']]

        # for i, f in enumerate(inFiles):
        #     print(i, ":", f)

        # for datFile in inFiles:
        #     logfilename = 'log_'+time.strftime("%Y-%m-%d_%H%M")+'.txt'

        #     try:
        #         copied_script_name = os.path.basename(__file__).split('.')[0]+'_'+time.strftime("%Y-%m-%d_%H%M")+'.py'
        #         script = os.path.abspath(__file__)

        #         start_time = time.time()  

        #         inPath = os.path.dirname(datFile)
        #         inFile = datFile
        #         recName = '.'.join(os.path.basename(inFile).split('.')[:-1])


        #         # Rename for Gulf Sturgeon Project
        #         if 'GulfSturgeonProject_2025' in inPath:
        #             river = os.path.basename(inPath).split('_')[0]
        #             date = os.path.basename(inPath).split('_')[1]
        #             boat = os.path.basename(inPath).split('_')[2]

        #             upRKM = os.path.basename(recName).split('_')[0]
        #             dnRKM = os.path.basename(recName).split('_')[1]
        #             recName = os.path.basename(recName).split('_')[2]

        #             recName = ('{}_{}_{}_{}_{}_{}_{}'.format(river, upRKM, dnRKM, date, boat, recName, '2025'))

        #             # Apply boat offset
        #             xOff = 'x_offset'
        #             yOff = 'y_offset'
        #             # USM used FWS Jon boat
        #             # Using offsets kasea provided
        #             if boat == 'USM1':
        #                 params[xOff] = 3.6
        #                 params[yOff] = -0.6
                    
        #             elif boat == 'FWSA1':
        #                 if '202102' in date:
        #                     # Feb 2021 trip, Oquawka boat (chan)
        #                     params[xOff] = 5.3
        #                     params[yOff] = -0.5
        #                 elif '202103' in date:
        #                     # March 2021 trip, Oquawka boat (chan)
        #                     params[xOff] = 5.3
        #                     params[yOff] = -0.5
        #                 else:
        #                     print('Unknown scan!')
        #                     print(recName)
        #                     sys.exit()

        #             elif boat == 'FWSC1':
        #                 if '202102' in date:
        #                     # Feb 2021 trip, Whaler boat (adam)
        #                     params[xOff] = 3.5
        #                     params[yOff] = -0.2
        #                 elif '202105' in date:
        #                     # May 2021 trip, Kann boat (adam)
        #                     params[xOff] = 5.4
        #                     params[yOff] = -0.5
        #                 else:
        #                     print('Unknown scan!')
        #                     print(recName)
        #                     sys.exit()

        #             elif boat == 'FWSB1':
        #                 if '202103' in date:
        #                     # March 2021 trip, Kann boat (adam)
        #                     params[xOff] = 5.4
        #                     params[yOff] = -0.5
        #                 elif '202105' in date:
        #                     # May 2021 trip, Oquawka boat (chan)
        #                     params[xOff] = 5.3
        #                     params[yOff] = -0.5
        #                 else:
        #                     print('Unknown scan!')
        #                     print(recName)
        #                     sys.exit()

        #             else: 
        #                 print('Unknown scan!')
        #                 print(recName)
        #                 sys.exit()


        #         try:
        #             sonPath = inFile.split('.DAT')[0]
        #             sonFiles = sorted(glob(sonPath+os.sep+'*.SON'))
        #         except:
        #             sonFiles = ''

        #         if batch:
        #             recName = values['prefix'] + recName + values['suffix']

        #             projDir = os.path.join(outDir, recName)

        #         else:
        #             projDir = os.path.join(os.path.normpath(values['proj']), values['projName'])

        #         #============================================

        #         # =========================================================
        #         # Determine project_mode
        #         print(project_mode)
        #         if project_mode == 0:
        #             # Create new project
        #             if not os.path.exists(projDir):
        #                 os.mkdir(projDir)
        #             else:
        #                 projectMode_1_inval()

        #         elif project_mode == 1:
        #             # Overwrite existing project
        #             if os.path.exists(projDir):
        #                 shutil.rmtree(projDir)

        #             os.mkdir(projDir)        

        #         elif project_mode == 2:
        #             # Update project
        #             # Make sure project exists, exit if not.
                    
        #             if not os.path.exists(projDir):
        #                 projectMode_2_inval()

        #         # =========================================================
        #         # For logging the console output

        #         logdir = os.path.join(projDir, 'logs')
        #         if not os.path.exists(logdir):
        #             os.makedirs(logdir)

        #         logfilename = os.path.join(logdir, logfilename)

        #         sys.stdout = Logger(logfilename)

        #         print('\n\n', '***User Parameters***')
        #         for k,v in params.items():
        #             print("| {:<20s} : {:<10s} |".format(k, str(v)))

        #         #============================================
        #         # Add ofther params
        #         params['sonFiles'] = sonFiles
        #         params['logfilename'] = logfilename
        #         params['script'] = [script, copied_script_name]
        #         params['projDir'] = projDir
        #         params['inFile'] = inFile



        #         print('sonPath',sonPath)
        #         print('\n\n\n+++++++++++++++++++++++++++++++++++++++++++')
        #         print('+++++++++++++++++++++++++++++++++++++++++++')
        #         print('***** Working On *****')
        #         print(inFile)
        #         print('Start Time: ', datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))

        #         print('\n===========================================')
        #         print('===========================================')
        #         print('***** READING *****')
        #         ss_chan_avail  = read_master_func(**params)
        #         # read_master_func(sonFiles, humFile, projDir, t, nchunk, exportUnknown, wcp, wcr, detectDepth, smthDep, adjDep, pltBedPick, threadCnt)

        #         if ss_chan_avail:

        #             if rect_wcp or rect_wcr or banklines or coverage or pred_sub or map_sub or export_poly:
        #                 print('\n===========================================')
        #                 print('===========================================')
        #                 print('***** RECTIFYING *****')
        #                 rectify_master_func(**params)
        #                 # rectify_master_func(sonFiles, humFile, projDir, nchunk, rect_wcp, rect_wcr, mosaic, threadCnt)

        #             #==================================================
        #             #==================================================
        #             if pred_sub or map_sub or export_poly or pltSubClass:
        #                 print('\n===========================================')
        #                 print('===========================================')
        #                 print('***** MAPPING SUBSTRATE *****')
        #                 print("working on "+projDir)
        #                 map_master_func(**params)

        #         gc.collect()
        #         print("\n\nTotal Processing Time: ",datetime.timedelta(seconds = round(time.time() - start_time, ndigits=0)))

        #         sys.stdout.log.close()

        #     except Exception as Argument:
        #         unableToProcessError(logfilename)
        #         print('\n\nCould not process:', datFile)

        #     sys.stdout = oldOutput

        if batch:
            print("\n\nTotal Batch Processing Time: ",datetime.timedelta(seconds = round(time.time() - batch_start_time, ndigits=0)))


if __name__ == "__main__":
    # Default function to run
    if len(sys.argv) == 1:
        batch = False
    else:
        batch = sys.argv[1]
    gui(batch)