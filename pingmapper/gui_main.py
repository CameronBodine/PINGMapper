
import sys, os
import webbrowser


import FreeSimpleGUI as sg
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
import textwrap
import pandas as pd

filter_time_csv = os.path.join(SCRIPT_DIR, 'clip_table.csv')
filter_time_csv = os.path.normpath(filter_time_csv)

# Global tooltip tuning to reduce flicker by moving the tooltip away from the cursor.
sg.set_options(tooltip_time=500, tooltip_offset=(18, 18))

def ml_tip(text, width=62):
    return textwrap.fill(text, width=width, break_long_words=False)


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
        # Fallback: look in environment prefix (works with both conda and pixi)
        prefix = os.environ.get('CONDA_PREFIX', '')
        if prefix:
            primary_default_params = os.path.join(prefix, 'pingmapper_config', 'default_params.json')
    
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

    tip_input = ml_tip('Sonar log file to process. Supports .DAT (Humminbird®), .sl2/.sl3 (Lowrance®), .RSD (Garmin®), .svlog (Cerulean®)')
    if batch:
        text_input = sg.Text('Parent Folder of Recordings to Process')
        in_input = sg.In(key='inDir', size=(80,1), tooltip=tip_input)
        browse_input = sg.FolderBrowse(initial_folder=(default_params['inDir']))

    else:
        text_input = sg.Text('Recording to Process')
        # in_input = sg.In(key='inFile', size=(80,1))
        in_input = sg.In(key='inFile', size=(80,1), default_text=default_params['inFile'])
        browse_input = sg.FileBrowse(
            file_types=(("Sonar File", "*.DAT *.sl2 *.sl3 *.RSD *.svlog *.jsf *.xtf *.sdf"),),
            initial_folder=os.path.dirname(default_params['inFile']),
        )
        # browse_input = sg.FileBrowse(file_types=(("Sonar File", "*.DAT *.sl2 *.sl3 *.svlog") ), initial_folder=os.path.dirname(default_params['inFile']))

    # Add to layout
    layout.append([text_io])
    layout.append([text_input])
    layout.append([in_input, browse_input])

    ###################
    # Output parameters
    tip_output = ml_tip('Destination folder for all processed outputs. Avoid cloud drives (OneDrive, Google Drive).')
    text_output = sg.Text('Output Folder')
    # in_output = sg.In(key='proj', size=(80,1))
    in_output = sg.In(key='proj', size=(80,1), default_text=os.path.dirname(default_params['projDir']), tooltip=tip_output)
    browse_output = sg.FolderBrowse(initial_folder=os.path.dirname(default_params['projDir']))

    # Add to layout
    layout.append([text_output])
    layout.append([in_output, browse_output])

    ##############
    # Project Name
    tip_project_name = ml_tip('Unique name for this processing project. Folder with this name created in output folder.')
    tip_prefix = ml_tip('Prefix for batch project names. Useful for organizing multiple batch runs.')
    tip_suffix = ml_tip('Suffix for batch project names. Useful for organizing multiple batch runs.')
    tip_overwrite = ml_tip('If checked, overwrite existing project folder with same name. If unchecked, creates new folder.')
    if batch:
        text_prefix = sg.Text('Project Name Prefix:', size=(20,1))
        in_prefix = sg.Input(key='prefix', size=(10,1), tooltip=tip_prefix)

        text_suffix = sg.Text('Project Name Suffix:', size=(20,1))
        in_suffix = sg.Input(key='suffix', size=(10,1), tooltip=tip_suffix)

        check_preserve_subdirs = sg.Checkbox(
            'Preserve Input Subdirectory Structure',
            key='preserve_subdirs',
            default=default_params.get('preserve_subdirs', False),
        )

        # Add to layout
        layout.append([text_prefix, in_prefix, sg.VerticalSeparator(), text_suffix, in_suffix])
        layout.append([check_preserve_subdirs])

    else:
        text_project = sg.Text('Project Name', size=(15,1))
        in_project = sg.InputText(key='projName', size=(50,1), default_text=default_params['projName'], tooltip=tip_project_name)

        # Add to layout
        layout.append([text_project, in_project])

    ###########
    # Overwrite
    check_overwrite = sg.Checkbox('Overwrite Existing Project', key='project_mode', default=default_params['project_mode'], tooltip=tip_overwrite)

    # Add to layout
    layout.append([check_overwrite])

    ####################
    # General Parameters
    text_general = sg.Text('General Parameters\n', font=("Helvetica", 14, "underline"))

    tip_temp = ml_tip('Water temperature in Celsius. Used for sound speed calculations for accurate sonar processing.')
    tip_chunk = ml_tip('Number of pings per exported sonar tile. Typical: 500 pings. Larger chunks = fewer, larger tiles.')
    tip_thread = ml_tip('0=all CPU threads, 0.5-0.75=safe CPU usage (prevents OOM), >1=specific thread count.')
    tip_attr = ml_tip('Export unknown/undefined ping metadata fields to output CSV files.')
    tip_missing = ml_tip('Detect missing pings in sonar log and fill with NoData values for proper indexing.')
    # Temperature
    text_temp = sg.Text('Temperature [C]', size=(30,1))
    in_temp = sg.Input(key='tempC', default_text=default_params['tempC'], size=(10,1), tooltip=tip_temp)

    # Chunk
    text_chunk = sg.Text('Chunk Size', size=(30,1))
    in_chunk = sg.Input(key='nchunk', default_text=default_params['nchunk'], size=(10,1), tooltip=tip_chunk)

    # Ping Attributes
    check_attr = sg.Checkbox('Export Unknown Ping Attributes', key='exportUnknown', default=default_params['exportUnknown'], tooltip=tip_attr)

    # Missing Pings
    check_missing = sg.Checkbox('Locate and flag missing pings', key='fixNoDat', default=default_params['fixNoDat'], tooltip=tip_missing)

    # Thread count
    text_thread = sg.Text('Thread Count [0==All Threads]', size=(30,1))
    in_thread = sg.Input(key='threadCnt', default_text=default_params['threadCnt'], size=(10,1), tooltip=tip_thread)

    col_general_1 = sg.Column([[text_temp, in_temp], [text_chunk, in_chunk], [text_thread, in_thread]], pad=0)
    col_general_2 = sg.Column([[check_attr], [check_missing]], pad=0)

    # Add to layout
    layout.append([sg.HorizontalSeparator()])
    layout.append([text_general])
    layout.append([col_general_1, sg.VerticalSeparator(), col_general_2])

    
    ###########
    # Filtering
    text_filtering = sg.Text('Filter Sonar Log\n', font=("Helvetica", 14, "underline"))

    tip_crop = ml_tip('Crop (remove) sonar returns beyond this range in meters. 0=no crop, >0=max range.')
    tip_heading = ml_tip('Filter records based on vessel heading deviation over distance. 0=no filter.')
    tip_distance = ml_tip('Distance over which heading deviation is calculated (in meters).')
    tip_speed_min = ml_tip('Minimum vessel speed filter in m/s. 0=no minimum speed filter.')
    tip_speed_max = ml_tip('Maximum vessel speed filter in m/s. 0=no maximum speed filter.')
    tip_aoi = ml_tip('Optional polygon shapefile (.shp) to spatially filter sonar records to area of interest.')
    tip_time_filter = ml_tip('Option to filter sonar records by time range using start/end seconds.')
    # Cropping
    text_crop = sg.Text('Crop Range [m]', size=(22,1))
    in_crop = sg.Input(key='cropRange', default_text=default_params['cropRange'], size=(10,1), tooltip=tip_crop)

    # Heading
    text_heading = sg.Text('Max. Heading Deviation [deg]:', size=(22,1))
    in_heading = sg.Input(key='max_heading_deviation', default_text=default_params['max_heading_deviation'], size=(10,1), tooltip=tip_heading)
    text_distance = sg.Text('Distance [m]:', size=(15,1))
    in_distance = sg.Input(key='max_heading_distance', default_text=default_params['max_heading_distance'], size=(10,1), tooltip=tip_distance)

    # Speed
    text_speed_min = sg.Text('Min. Speed [m/s]:', size=(22,1))
    in_speed_min = sg.Input(key='min_speed', default_text=default_params['min_speed'], size=(10,1), tooltip=tip_speed_min)
    text_speed_max = sg.Text('Max. Speed [m/s]:', size=(15,1))
    in_speed_max = sg.Input(key='max_speed', default_text=default_params['max_speed'], size=(10,1), tooltip=tip_speed_max)

    # AOI
    text_aoi = sg.Text('AOI')
    in_aoi = sg.In(size=(80,1), tooltip=tip_aoi)
    browse_aoi = sg.FileBrowse(key='aoi', file_types=(("Shapefile", "*.shp"), (".plan File", "*.plan")), initial_folder=os.path.dirname(default_params['aoi']))

    # Time table
    button_time_table = sg.Button('Edit Table')
    check_time_load = sg.Checkbox('Filter by Time', key='filter_table', default=default_params['filter_table'], tooltip=tip_time_filter)

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

    tip_x_offset = ml_tip('X offset in meters. Origin at control head. Positive towards bow (front), negative towards stern (rear).')
    tip_y_offset = ml_tip('Y offset in meters. Positive towards starboard (right), negative towards port (left).')
    # X offset
    text_x_offset = sg.Text('X Offset [m]:', size=(22,1))
    in_x_offset = sg.Input(key='x_offset', default_text=default_params['x_offset'], size=(10,1), tooltip=tip_x_offset)
    
    # Y offset
    text_y_offset = sg.Text('Y Offset [m]:', size=(22,1))
    in_y_offset = sg.Input(key='y_offset', default_text=default_params['y_offset'], size=(10,1), tooltip=tip_y_offset)

    # Add to layout
    layout.append([sg.HorizontalSeparator()])
    layout.append([text_position, button_help_position])
    layout.append([sg.Text('', size=(1,1))])
    layout.append([text_x_offset, in_x_offset, sg.VerticalSeparator(), text_y_offset, in_y_offset])


    #################
    # EGN Corrections

    # EGN text
    text_egn = sg.Text('Sonar Intensity Corrections\n', font=("Helvetica", 14, "underline"))

    tip_egn = ml_tip('Enable empirical gain normalization to reduce range-dependent intensity falloff before export.')
    tip_egn_stretch = ml_tip('Choose contrast stretch after EGN: None keeps native scaling, Min-Max uses full range, Percent Clip trims outliers.')
    tip_egn_factor = ml_tip('Percent clip amount used by EGN Stretch Factor when Percent Clip is selected.')
    tip_gamma = ml_tip('Tone curve control. <1 brightens mid-tones, >1 darkens mid-tones.')
    tip_gain = ml_tip('Linear brightness multiplier. >1 brightens overall intensity, <1 darkens.')
    # EGN
    check_egn = sg.Checkbox('Empiracal Gain Normalization (EGN)', key='egn', default=default_params['egn'], tooltip=tip_egn)

    # EGN options
    text_egn_stretch = sg.Text('EGN Stretch', size=(20,1))
    combo_egn_stretch = sg.Combo(['None', 'Min-Max', 'Percent Clip'], key='egn_stretch', default_value=default_params['egn_stretch'], tooltip=tip_egn_stretch)
    text_egn_factor = sg.Text('EGN Stretch Factor', size=(20,1))
    in_egn_factor = sg.Input(key='egn_stretch_factor', default_text=default_params['egn_stretch_factor'], size=(10,1), tooltip=tip_egn_factor)
    text_egn_gamma = sg.Text('Tone Gamma [0.1-3.0]', size=(20,1))
    slide_egn_gamma = sg.Slider(
        range=(0.1, 3.0),
        resolution=0.05,
        orientation='h',
        key='tone_gamma',
        default_value=float(default_params['tone_gamma']),
        tooltip=tip_gamma,
    )
    text_egn_gain = sg.Text('Tone Gain [0.0-3.0]', size=(20,1))
    slide_egn_gain = sg.Slider(
        range=(0.0, 3.0),
        resolution=0.05,
        orientation='h',
        key='tone_gain',
        default_value=float(default_params['tone_gain']),
        tooltip=tip_gain,
    )

    col_egn_1 = sg.Column([[text_egn_gamma, slide_egn_gamma], [text_egn_gain, slide_egn_gain]], pad=0)
    col_egn_2 = sg.Column([[check_egn], [text_egn_stretch, combo_egn_stretch], [text_egn_factor, in_egn_factor]], pad=0)
    # Add to layout
    layout.append([sg.HorizontalSeparator()])
    layout.append([text_egn])
    layout.append([col_egn_1, sg.VerticalSeparator(), col_egn_2])

    #######################
    # Global Export Options

    text_global_export = sg.Text('Global Export Options\n', font=("Helvetica", 14, "underline"))
    check_export_16bit = sg.Checkbox(
        'Export 16-bit TIFFs (applies to Sonogram + Rectified outputs)',
        key='export_16bit',
        default=default_params.get('export_16bit', False),
        enable_events=True,
    )
    check_export_colormap_uint8 = sg.Checkbox(
        'Colormapped RGB uses 8-bit channels (smaller files)',
        key='export_colormap_uint8',
        default=default_params.get('export_colormap_uint8', True)
    )

    layout.append([sg.HorizontalSeparator()])
    layout.append([text_global_export])
    layout.append([check_export_16bit])
    layout.append([check_export_colormap_uint8])

    #######################
    # Sonogram Tile Exports

    text_tile = sg.Text('Sonogram Tile Exports\n', font=("Helvetica", 14, "underline"))

    tip_wcp = ml_tip('Export raw (waterfall) sonograms with water column present. Quick preview of sonar.')
    tip_wcm = ml_tip('Export raw sonograms with water column masked (highlighted).')
    tip_wcr = ml_tip('Export raw sonograms with water column removed. Water column corrected to nadir slant range.')
    tip_wco = ml_tip('Export raw sonograms showing water column only, without substrate/seafloor data.')
    tip_speed_cor = ml_tip('Apply speed correction to tiles based on vessel distance traveled. Compensates for vessel motion.')
    tip_max_crop = ml_tip('Crop sonograms to minimum depth and maximum range extent.')
    tip_mask_shdw = ml_tip('Mask (hide) sonar shadows in tiles. Shadow Removal setting in Depth & Shadow Removal must be enabled.')
    tip_file_type = ml_tip('Output image format: .jpg (smaller files) or .png (lossless, larger files).')
    tip_tile_color = ml_tip('Colormap applied to tile images. Append _r to reverse colormap (e.g., viridis_r).')
    # Tiles
    check_wcp = sg.Checkbox('WCP (Water Column Present)', key='wcp', default=default_params['wcp'], tooltip=tip_wcp)
    check_wcm = sg.Checkbox('WCM (Water Column Masked)', key='wcm', default=default_params['wcm'], tooltip=tip_wcm)
    check_wcr = sg.Checkbox('SRC (Slant Range Corrected)', key='wcr', default=default_params['wcr'], tooltip=tip_wcr)
    check_wco = sg.Checkbox('WCO (Water Column Only)', key='wco', default=default_params['wco'], tooltip=tip_wco)

    # Options
    text_file_type = sg.Text('Image Format:', size=(15,1))
    combo_file_type = sg.Combo(['.jpg', '.png', '.tif'], key='tileFile', default_value=default_params['tileFile'])

    text_tile_color = sg.Text('Tile Colormap:', size=(15,1))
    tile_colormaps = ['None'] + list(plt.colormaps())
    combo_tile_color = sg.Combo(tile_colormaps, key='sonogram_colorMap', default_value=default_params.get('sonogram_colorMap', 'copper'), enable_events=True)


    check_speed_cor = sg.Checkbox('Speed Correct', key='spdCor', default=default_params['spdCor'], tooltip=tip_speed_cor)

    check_max_crop = sg.Checkbox('Max Crop', key='maxCrop', default=default_params['maxCrop'], tooltip=tip_max_crop)

    # Mask
    check_mask_shdw = sg.Checkbox('Mask Shadows', key='mask_shdw', default=default_params['mask_shdw'], tooltip=tip_mask_shdw)
    
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

    tip_depth = ml_tip('Depth detection method: Sensor=use sonar depth, Auto=ML-based water column segmentation (Zheng et al. 2021).')
    tip_shadow = ml_tip('Shadow removal strategy: False=no removal, Remove all=every shadow, Remove bank=only far-field (bank-caused) shadows.')
    tip_adj_depth = ml_tip('Additional depth adjustment in meters. Positive increases depth estimate (removes more water column), negative decreases.')
    tip_smooth = ml_tip('Smooth depth data before water column removal. Helps with noisy or inconsistent depth estimates.')
    tip_plot_bed = ml_tip('Plot detected bedpick (depth) on exported non-rectified sonograms for visual inspection and validation.')
    # Shadow
    text_shdw = sg.Text('Shadow Removal', size=(15,1))
    in_shdw = sg.Combo(['False', 'Remove all shadows', 'Remove only bank shadows'], key='remShadow', default_value=default_params['remShadow'], tooltip=tip_shadow)

    # Depth
    text_dep = sg.Text('Depth Detection', size=(15,1))
    in_dep = sg.Combo(['Sensor', 'Auto'], key='detectDep', default_value=default_params['detectDep'], tooltip=tip_depth)
    check_dep_smth = sg.Checkbox('Smooth Depth', key='smthDep', default=default_params['smthDep'], tooltip=tip_smooth)
    text_dep_adj = sg.Text('Adjust Depth [m]', size=(15,1))
    in_dep_adj = sg.Input(key='adjDep', default_text=default_params['adjDep'], size=(10,1), tooltip=tip_adj_depth)
    check_dep_plt = sg.Checkbox('Plot Bedpick', key='pltBedPick', default=default_params['pltBedPick'], tooltip=tip_plot_bed)

    col_depshdw_1 = sg.Column([[text_dep, in_dep], [text_dep_adj, in_dep_adj], [check_dep_smth], [check_dep_plt]], pad=0)
    col_depshdw_2 = sg.Column([[text_shdw, in_shdw]], pad=0)

    # Add to layout
    layout.append([sg.HorizontalSeparator()])
    layout.append([text_dep_shdw])
    layout.append([col_depshdw_1, sg.VerticalSeparator(), col_depshdw_2])

    ########################
    # Sonar Georectification

    text_rect = sg.Text('Sonar Georectification Exports\n', font=("Helvetica", 14, "underline"))

    tip_rect_wcp = ml_tip('Export georectified sonar imagery with water column present. Less accurate positionally due to water column.')
    tip_rect_wcr = ml_tip('Export georectified sonar imagery with water column removed. More accurate positional representation.')
    tip_pix_res = ml_tip('Output pixel resolution in meters. 0=default (~0.02m), >0=custom resolution. Smaller=higher resolution output.')
    tip_rubber = ml_tip('Use Rubber Sheeting (flexible warping) instead of simple rigid Heading/COG-based rectification.')
    tip_rect_method = ml_tip('Rectification method: Heading=use vessel heading, COG=use course over ground.')
    tip_interp = ml_tip('Interpolation distance in pixels for smooth georectification. Higher=smoother but slower processing.')
    tip_son_color = ml_tip('Colormap applied to georectified sonar imagery. Append _r to reverse (e.g., viridis_r).')
    tip_mosaic = ml_tip('Create mosaic of georectified tiles: False=no mosaic, GTiff=GeoTIFF format, VRT=Virtual Raster.')
    tip_nchunk = ml_tip('Number of chunks per mosaic. 0=process all chunks, >0=limit to specified count for smaller output.')
    # Pixel resolution
    text_rect_pix = sg.Text('Pixel Resolution [0==Default (~0.02m)]', size=(30,1))
    in_rect_pix = sg.Input(key='pix_res_son', default_text=default_params['pix_res_son'], size=(10,1), tooltip=tip_pix_res)

    # Type
    check_rect_wcp = sg.Checkbox('WCP (Water Column Present)', key='rect_wcp', default=default_params['rect_wcp'], tooltip=tip_rect_wcp)
    check_rect_wcr = sg.Checkbox('WCR (Water Column Removed)', key='rect_wcr', default=default_params['rect_wcr'], tooltip=tip_rect_wcr)

    # # COG
    # check_rect_cog = sg.Checkbox('Use COG', key='cog', default=default_params['cog'])
    # Rectification Method
    check_rect_meth = sg.Checkbox('Rubber Sheeting or', key='rubberSheeting', default=default_params['rubberSheeting'], enable_events=True, tooltip=tip_rubber)
    if default_params['rubberSheeting'] == True:
        rect_meth_status = True
    else:
        rect_meth_status = False
    combo_rect_meth = sg.Combo(['Heading', 'COG'], key='rectMethod', default_value=default_params['rectMethod'], disabled=rect_meth_status, tooltip=tip_rect_method)

    # Interpolation Distance
    text_rect_interp = sg.Text('Interp. Dist.', size=(10,1))
    slide_rect_interp = sg.Slider(range=(0, 200), resolution=5, orientation='h', key='rectInterpDist', default_value=default_params['rectInterpDist'], disabled=rect_meth_status, tooltip=tip_interp)

    text_color = sg.Text('Sonar Colormap', size=(30,1))
    rect_colormaps = ['None'] + list(plt.colormaps())
    combo_color = sg.Combo(rect_colormaps, key='son_colorMap', default_value=default_params.get('son_colorMap', 'Greys_r'), enable_events=True)

    text_rect_mosaic = sg.Text('Export Sonar Mosaic', size=(30,1))
    combo_rect_mosaic = sg.Combo(['False', 'GTiff', 'VRT'], key='mosaic', default_value=default_params['mosaic'], tooltip=tip_mosaic)

    text_rect_chunk = sg.Text('# Chunks per Mosaic [0==All Chunks]', size=(30,1))
    in_rect_chunk = sg.Input(key='mosaic_nchunk', default_text=default_params['mosaic_nchunk'], size=(10,1), tooltip=tip_nchunk)
    
    col_rect_1 = sg.Column([[check_rect_wcp], [check_rect_wcr], [check_rect_meth, combo_rect_meth], [text_rect_interp, slide_rect_interp]], pad=0)
    col_rect_2 = sg.Column([[text_rect_pix, in_rect_pix], [text_color, combo_color], [text_rect_mosaic, combo_rect_mosaic], [text_rect_chunk, in_rect_chunk]], pad=0)
    
    # Add to layout
    layout.append([sg.HorizontalSeparator()])
    layout.append([text_rect])
    layout.append([col_rect_1, sg.VerticalSeparator(), col_rect_2])


    ###################s
    # Substrate Mapping

    text_substrate = sg.Text('Substrate Mapping\n', font=("Helvetica", 14, "underline"))

    tip_map_raster = ml_tip('Export georectified substrate classification rasters using machine learning segmentation.')
    tip_map_mosaic = ml_tip('Create mosaic of substrate classification tiles: False=no mosaic, GTiff=GeoTIFF, VRT=Virtual Raster.')
    tip_pix_res_map = ml_tip('Output pixel resolution in meters. 0=default (~0.02m), >0=custom resolution.')
    tip_map_poly = ml_tip('Export substrate classifications as polygon shapefile for GIS use. Requires Map Substrate [Raster] to be enabled.')
    tip_map_plots = ml_tip('Export plots showing substrate classification probabilities and statistics.')
    check_substrate_raster = sg.Checkbox('Map Substrate [Raster]', key='map_sub', default=default_params['map_sub'], tooltip=tip_map_raster)
    check_substrate_poly = sg.Checkbox('Map Substrate [Polygon]', key='export_poly', default=default_params['export_poly'], tooltip=tip_map_poly)
    check_substrate_plot =  sg.Checkbox('Export Substrate Plots', key='pltSubClass', default=default_params['pltSubClass'], tooltip=tip_map_plots)
        
    text_substrate_mosaic = sg.Text('Export Substrate Mosaic', size=(30,1))
    combo_substrate_mosaic = sg.Combo(['False', 'GTiff', 'VRT'], key='map_mosaic', default_value=default_params['map_mosaic'], tooltip=tip_map_mosaic)

    # Pixel resolution
    text_substrate_pix = sg.Text('Pixel Resolution [0==Default (~0.02m)]', size=(30,1))
    in_substrate_pix = sg.Input(key='pix_res_map', default_text=default_params['pix_res_map'], size=(10,1), tooltip=tip_pix_res_map)

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

    tip_banklines = ml_tip('Export polygon shapefile outlining estimated river/channel bankline based on shadow segmentation.')
    tip_coverage = ml_tip('Export polygon shapefile of sonar coverage extent and point shapefile of vessel trackline.')
    check_misc_banks = sg.Checkbox('Banklines', key='banklines', default=default_params['banklines'], tooltip=tip_banklines)
    check_misc_cov = sg.Checkbox('Coverage', key='coverage', default=default_params['coverage'], tooltip=tip_coverage)

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
    window = sg.Window(window_text, layout2, resizable=True, finalize=True)

    def _is_cmap_selected(value):
        if value is None:
            return False
        return str(value).strip().lower() not in ['', 'none', 'false']

    def _update_colormap_depth_toggle(values_dict):
        use_16bit = bool(values_dict.get('export_16bit', False))
        tile_cmap_selected = _is_cmap_selected(values_dict.get('sonogram_colorMap'))
        rect_cmap_selected = _is_cmap_selected(values_dict.get('son_colorMap'))
        enable_toggle = use_16bit and (tile_cmap_selected or rect_cmap_selected)
        window['export_colormap_uint8'].update(disabled=not enable_toggle)

    initial_values = {
        'export_16bit': default_params.get('export_16bit', False),
        'sonogram_colorMap': default_params.get('sonogram_colorMap', 'copper'),
        'son_colorMap': default_params.get('son_colorMap', 'Greys_r'),
    }
    _update_colormap_depth_toggle(initial_values)

    while True:
        event, values = window.read()

        if event not in (None, 'Quit'):
            _update_colormap_depth_toggle(values)

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
            'tone_gamma':float(values['tone_gamma']),
            'tone_gain':float(values['tone_gain']),
            'wcp':values['wcp'],
            'wcm':values['wcm'],
            'wcr':values['wcr'],
            'wco':values['wco'],
            'sonogram_colorMap':values['sonogram_colorMap'],
            'mask_shdw':values['mask_shdw'],
            'export_16bit':values['export_16bit'],
            'export_colormap_uint8':values['export_colormap_uint8'],
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
            preserve_subdirs=(values.get('preserve_subdirs', False) if batch else False),
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

