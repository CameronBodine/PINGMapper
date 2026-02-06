import os
import sys
import time
import datetime
import gc
import shutil
from glob import glob

from pingmapper.funcs_common import (
    Logger,
    projectMode_1_inval,
    projectMode_2_inval,
    unableToProcessError,
)
from pingmapper.main_readFiles import read_master_func
from pingmapper.main_rectify import rectify_master_func
from pingmapper.main_mapSubstrate import map_master_func


SUPPORTED_EXTS = ('.DAT', '.sl2', '.sl3', '.RSD', '.svlog')


def _coerce_batch(batch):
    if isinstance(batch, str):
        return batch.strip().lower() in {'true', '1', 'yes', 'y'}
    return bool(batch)


def _collect_in_files(in_files=None, in_dir=None, in_file=None, batch=False):
    if in_files:
        return [os.path.normpath(f) for f in in_files]

    if batch or in_dir:
        if not in_dir:
            raise ValueError('in_dir is required for batch processing.')
        in_files = []
        for root, _, files in os.walk(in_dir):
            if '__MACOSX' in root:
                continue
            for file in files:
                if file.endswith(SUPPORTED_EXTS):
                    in_files.append(os.path.join(root, file))
        return sorted(in_files)

    if not in_file:
        raise ValueError('in_file is required for single-file processing.')

    return [os.path.normpath(in_file)]


def _get_son_files(in_file):
    try:
        if '.DAT' in in_file:
            son_path = in_file.split('.DAT')[0]
        else:
            son_path = os.path.splitext(in_file)[0]
        return sorted(glob(son_path + os.sep + '*.SON'))
    except Exception:
        return ''


def doWork(
    in_file=None,
    in_dir=None,
    in_files=None,
    out_dir=None,
    proj_name=None,
    prefix='',
    suffix='',
    batch=False,
    params=None,
    script_path=None,
):
    """Programmatic entry point for PINGMapper processing.

    Input selection (choose one):
        - Single file: set ``in_file``
        - Batch directory: set ``in_dir`` and ``batch=True``
        - Explicit list: set ``in_files``

    Args:
        in_file (str | None): Path to a single sonar file (.DAT/.sl2/.sl3/.RSD/.svlog).
        in_dir (str | None): Parent directory to search recursively when batch=True.
        in_files (list[str] | None): Explicit list of sonar files to process.
        out_dir (str): Output project root folder.
        proj_name (str | None): Project name for single-file runs (default: derived from file name).
        prefix (str): Batch project name prefix.
        suffix (str): Batch project name suffix.
        batch (bool | str): True/False or "true"/"false"; controls batch logic.
        params (dict | None): Processing parameters (see below).
        script_path (str | None): Source script path saved into processing_scripts (default: doWork.py).

    Params dictionary (common keys):
        project_mode (int): 0=create new, 1=overwrite, 2=update.
        tempC (float), nchunk (int), cropRange (float)
        exportUnknown (bool), fixNoDat (bool), threadCnt (int | float)
        aoi (str | False), max_heading_deviation (float), max_heading_distance (float)
        min_speed (float), max_speed (float), time_table (str | False)
        pix_res_son (float), pix_res_map (float)
        x_offset (float), y_offset (float)
        egn (bool), egn_stretch (int: 0/1/2), egn_stretch_factor (float)
        wcp/wcm/wcr/wco (bool)
        sonogram_colorMap (str), mask_shdw (bool), tileFile (str)
        spdCor (bool), maxCrop (bool)
        remShadow (int: 0/1/2), detectDep (int: 0/1), smthDep (bool), adjDep (float), pltBedPick (bool)
        rect_wcp/rect_wcr (bool), rubberSheeting (bool), rectMethod (str), rectInterpDist (int)
        son_colorMap (str), mosaic_nchunk (int), mosaic (int: 0/1/2)
        pred_sub (bool), map_sub (bool), export_poly (bool), pltSubClass (bool)
        map_class_method (str), map_predict (int), map_mosaic (int: 0/1/2)
        banklines (bool), coverage (bool)

    Returns:
        list[dict]: Each item includes inFile, projDir, logfilename, success.
    """

    batch = _coerce_batch(batch)
    params = {} if params is None else dict(params)

    project_mode = int(params.get('project_mode', 0))

    if not out_dir:
        raise ValueError('out_dir is required.')

    if not script_path:
        script_path = os.path.abspath(__file__)

    out_dir = os.path.normpath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    in_files = _collect_in_files(in_files=in_files, in_dir=in_dir, in_file=in_file, batch=batch)

    if not in_files:
        raise ValueError('No input files found. Check in_file/in_dir/in_files.')

    results = []

    for dat_file in in_files:
        logfilename_base = f"log_{time.strftime('%Y-%m-%d_%H%M')}.txt"
        logfilename = logfilename_base
        proj_dir = None
        old_output = sys.stdout

        if not os.path.exists(dat_file):
            print(f"Input file not found: {dat_file}", file=old_output)
            results.append({
                'inFile': dat_file,
                'projDir': None,
                'logfilename': None,
                'success': False,
            })
            continue

        try:
            print(f"Processing: {dat_file}", file=old_output)
            copied_script_name = os.path.basename(script_path).split('.')[0] + '_' + time.strftime('%Y-%m-%d_%H%M') + '.py'
            script = [script_path, copied_script_name]

            start_time = time.time()

            in_path = os.path.dirname(dat_file)
            in_file = dat_file
            rec_name = '.'.join(os.path.basename(in_file).split('.')[:-1])

            run_params = dict(params)

            # Rename for Gulf Sturgeon Project
            if 'GulfSturgeonProject_2025' in in_path:
                river = os.path.basename(in_path).split('_')[0]
                date = os.path.basename(in_path).split('_')[1]
                boat = os.path.basename(in_path).split('_')[2]

                up_rkm = os.path.basename(rec_name).split('_')[0]
                dn_rkm = os.path.basename(rec_name).split('_')[1]
                rec_name = os.path.basename(rec_name).split('_')[2]

                rec_name = ('{}_{}_{}_{}_{}_{}_{}'.format(river, up_rkm, dn_rkm, date, boat, rec_name, '2025'))

                if boat == 'USM1':
                    run_params['x_offset'] = 3.6
                    run_params['y_offset'] = -0.6

                elif boat == 'FWSA1':
                    if '202102' in date or '202103' in date:
                        run_params['x_offset'] = 5.3
                        run_params['y_offset'] = -0.5
                    else:
                        print('Unknown scan!')
                        print(rec_name)
                        sys.exit()

                elif boat == 'FWSC1':
                    if '202102' in date:
                        run_params['x_offset'] = 3.5
                        run_params['y_offset'] = -0.2
                    elif '202105' in date:
                        run_params['x_offset'] = 5.4
                        run_params['y_offset'] = -0.5
                    else:
                        print('Unknown scan!')
                        print(rec_name)
                        sys.exit()

                elif boat == 'FWSB1':
                    if '202103' in date:
                        run_params['x_offset'] = 5.4
                        run_params['y_offset'] = -0.5
                    elif '202105' in date:
                        run_params['x_offset'] = 5.3
                        run_params['y_offset'] = -0.5
                    else:
                        print('Unknown scan!')
                        print(rec_name)
                        sys.exit()

                else:
                    print('Unknown scan!')
                    print(rec_name)
                    sys.exit()

            son_files = _get_son_files(in_file)

            if batch:
                proj_name_final = f"{prefix}{rec_name}{suffix}"
            else:
                proj_name_final = proj_name or rec_name

            proj_dir = os.path.join(out_dir, proj_name_final)

            if project_mode == 0:
                if not os.path.exists(proj_dir):
                    os.mkdir(proj_dir)
                else:
                    projectMode_1_inval()

            elif project_mode == 1:
                if os.path.exists(proj_dir):
                    shutil.rmtree(proj_dir)
                os.mkdir(proj_dir)

            elif project_mode == 2:
                if not os.path.exists(proj_dir):
                    projectMode_2_inval()

            logdir = os.path.join(proj_dir, 'logs')
            if not os.path.exists(logdir):
                os.makedirs(logdir)

            logfilename = os.path.join(logdir, logfilename_base)
            sys.stdout = Logger(logfilename)

            run_params.update({
                'logfilename': logfilename,
                'project_mode': project_mode,
                'script': script,
                'inFile': in_file,
                'sonFiles': son_files,
                'projDir': proj_dir,
            })

            print('\n\n', '***User Parameters***')
            for k, v in run_params.items():
                print("| {:<20s} : {:<10s} |".format(k, str(v)))

            print('\n\n\n+++++++++++++++++++++++++++++++++++++++++++')
            print('+++++++++++++++++++++++++++++++++++++++++++')
            print('***** Working On *****')
            print(in_file)
            print('Start Time: ', datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))

            print('\n===========================================')
            print('===========================================')
            print('***** READING *****')
            ss_chan_avail = read_master_func(**run_params)

            if ss_chan_avail:
                rect_wcp = run_params.get('rect_wcp', False)
                rect_wcr = run_params.get('rect_wcr', False)
                banklines = run_params.get('banklines', False)
                coverage = run_params.get('coverage', False)
                pred_sub = run_params.get('pred_sub', False)
                map_sub = run_params.get('map_sub', False)
                export_poly = run_params.get('export_poly', False)
                plt_subclass = run_params.get('pltSubClass', False)

                if rect_wcp or rect_wcr or banklines or coverage or pred_sub or map_sub or export_poly:
                    print('\n===========================================')
                    print('===========================================')
                    print('***** RECTIFYING *****')
                    rectify_master_func(**run_params)

                if pred_sub or map_sub or export_poly or plt_subclass:
                    print('\n===========================================')
                    print('===========================================')
                    print('***** MAPPING SUBSTRATE *****')
                    print('working on ' + proj_dir)
                    map_master_func(**run_params)

            gc.collect()
            print("\n\nTotal Processing Time: ", datetime.timedelta(seconds=round(time.time() - start_time, ndigits=0)))

            sys.stdout.log.close()
            success = True

        except Exception:
            if logfilename and os.path.dirname(logfilename):
                try:
                    unableToProcessError(logfilename)
                except Exception:
                    pass
            print('\n\nCould not process:', dat_file)
            success = False

        sys.stdout = old_output

        results.append({
            'inFile': in_file,
            'projDir': proj_dir,
            'logfilename': logfilename,
            'success': success,
        })

    return results
