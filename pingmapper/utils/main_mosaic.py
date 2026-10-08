"""
Merge sonar mosaics from many recordings into one, outside the PINGMapper
pipeline. Nothing is re-decoded or re-rectified.

Each input pass is a georeferenced mosaic raster plus the ping metadata (boat
position, depth, range) for the track that made it. Transect numbers repeat in
every recording, so each pass is keyed "<project>:<transect>".

1. Batch folder - every project under ROOT with a sonar_mosaic/ folder:

    python -m pingmapper.utils.main_mosaic ROOT [--kind wcr|wcp]
        [--method quality] [--out merged.tif] [--source] [--list]

2. Manifest CSV - any rasters, from any source (columns: tif, meta_csv, and
   optionally key, transect). One row per pass; meta_csv may be blank for
   methods that do not need tracks:

    python -m pingmapper.utils.main_mosaic --manifest passes.csv ...

From Python: merge_mosaics(root=..., method=...) (see below).
With no arguments, a FreeSimpleGUI window opens (python -m pingmapper.utils.main_mosaic).

Common options: --swatch E N SIZE_M (small test area), --plateau-end,
--far-floor, --nadir-per-depth, --depth-window.

Algorithm credit: Max Schwartz IV (anchorhold-web-viewer).
"""
import argparse
import glob
import os
import re
import sys

import pandas as pd
# Prefer this checkout over any installed pingmapper (repo root = 3 levels up).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pingmapper.utils import mosaic_quality as mq


def discover_batch(root, kind='wcr', log=print):
    """
    Find passes under `root`: any <project>/sonar_mosaic/*_rect_<kind>_mosaic_<n>.tif
    with a port meta CSV in <project>/meta/. Returns a list of dicts
    (key, tif, meta_csv, transect).
    """
    entries = []
    for mosaic_dir in sorted(glob.glob(os.path.join(root, '**', 'sonar_mosaic'), recursive=True)):
        proj_dir = os.path.dirname(mosaic_dir)
        project = os.path.basename(proj_dir)
        tifs = {}
        for p in glob.glob(os.path.join(mosaic_dir, '*_rect_%s_mosaic_*.tif' % kind)):
            m = re.search(r'_mosaic_(\d+)\.tif$', p)
            if m:
                tifs[int(m.group(1))] = p
        if not tifs:
            continue
        metas = sorted(glob.glob(os.path.join(proj_dir, 'meta', '*_port_meta.csv')))
        if not metas:
            log('  skip %s: no port meta CSV' % project)
            continue
        if len(metas) > 1:
            log('  %s: %d port meta CSVs, using %s' % (project, len(metas), os.path.basename(metas[0])))
        for tid, p in sorted(tifs.items()):
            entries.append(dict(key='%s:%d' % (project, tid), tif=p,
                                meta_csv=metas[0], transect=tid))
    return entries


def read_manifest(path):
    df = pd.read_csv(path)
    if 'tif' not in df.columns:
        raise KeyError("manifest needs a 'tif' column")
    base = os.path.dirname(os.path.abspath(path))

    def full(v):
        return v if os.path.isabs(v) else os.path.join(base, v)

    entries = []
    for _, r in df.iterrows():
        meta = r.get('meta_csv')
        meta = full(meta) if isinstance(meta, str) and meta.strip() else None
        tid = int(r['transect']) if 'transect' in df.columns and pd.notna(r['transect']) else 0
        key = r['key'] if 'key' in df.columns and pd.notna(r['key']) else '%s:%d' % (
            os.path.splitext(os.path.basename(r['tif']))[0], tid)
        entries.append(dict(key=str(key), tif=full(r['tif']), meta_csv=meta, transect=tid))
    return entries


def merge_entries(entries, out_tif, params=None, method='quality', swatch=None,
                  source=False, log=print, workers=None, feather=0.0):
    """
    Merge passes described by entries (key, tif, meta_csv, transect).
    swatch: optional (easting, northing, size_m) in the mosaic CRS.
    """
    if len(entries) < 2:
        raise FileNotFoundError('need at least two passes, found %d' % len(entries))

    tracks, cache = {}, {}
    for e in entries:
        if not e.get('meta_csv'):
            continue
        if e['meta_csv'] not in cache:
            cache[e['meta_csv']] = mq.transect_tracks(e['meta_csv'], log, params)
        track = cache[e['meta_csv']].get(int(e['transect']))
        if track is not None:
            tracks[e['key']] = track
    if method == 'quality' and not tracks:
        raise ValueError('method quality needs ping metadata (meta_csv) for the passes')

    bounds = None
    if swatch:
        x, y, size = swatch
        h = size / 2.0
        bounds = (x - h, y - h, x + h, y + h)

    os.makedirs(os.path.dirname(os.path.abspath(out_tif)), exist_ok=True)
    mapping = {e['key']: e['tif'] for e in entries}
    log('Merging %d passes (%s) -> %s' % (len(mapping), method, out_tif))
    src = out_tif.replace('.tif', '_source.tif') if source else None
    mq.merge_sonar_by_quality(mapping, out_tif, tracks, log, bounds=bounds,
                              method=method, source_tif=src, workers=workers, feather=feather)
    if src and method in mq.SELECTING_METHODS:
        # source_id n in the raster is the n-th pass here (position + 1).
        pd.DataFrame({'source_id': range(1, len(mapping) + 1),
                      'key': list(mapping), 'tif': list(mapping.values())}
                     ).to_csv(src.replace('.tif', '.csv'), index=False)
    return out_tif


def run(root, kind='wcr', out_tif=None, **kw):
    """Batch entry point: discover passes under root and merge them."""
    entries = discover_batch(root, kind, kw.get('log', print))
    if out_tif is None:
        suffix = kw.get('method', 'quality') + ('_swatch' if kw.get('swatch') else '')
        out_tif = os.path.join(root, 'merged_mosaic',
                               'merged_rect_%s_%s.tif' % (kind, suffix))
    return merge_entries(entries, out_tif, **kw)


def merge_mosaics(root=None, manifest=None, out_tif=None, kind='wcr', method='quality',
                  params=None, swatch=None, source=False, workers=None, log=print, feather=0.0):
    """
    Programmatic entry point. Give a batch folder `root` or a `manifest` CSV;
    returns the merged TIF path.

        from pingmapper.utils.main_mosaic import merge_mosaics
        merge_mosaics(root='Z:/outputs', method='quality', workers=4)
    """
    if not root and not manifest:
        raise ValueError('give root or manifest')
    entries = read_manifest(manifest) if manifest else discover_batch(root, kind, log)
    if out_tif is None:
        base = root or os.path.dirname(os.path.abspath(manifest))
        out_tif = os.path.join(base, 'merged_mosaic', 'merged_%s.tif' % method)
    return merge_entries(entries, out_tif, params, method, swatch, source,
                         log=log, workers=workers, feather=feather)


def gui():
    """FreeSimpleGUI front end for the batch / manifest merge."""
    import threading
    import FreeSimpleGUI as sg

    d = mq.DEFAULT_PARAMS
    tips = {
        'plateau_end': "Fraction (0-1) of a ping's max range out to which a pixel is fully trusted. Past it, trust declines toward far_floor.",
        'far_floor': 'Trust (0-1] given to the very farthest pixels. Lower = far-range pixels yield more readily to another pass.',
        'nadir_per_depth': 'Width of the untrusted strip under the boat, in multiples of water depth. Trust ramps from 0 at the track to full at depth x this value. 0 disables it.',
        'depth_window': 'Number of pings in the rolling median used to smooth depth. Larger = steadier depth, slower response to real depth changes.',
    }
    tip_root = 'Folder holding the PINGMapper outputs; every <project>/sonar_mosaic is searched.'
    tip_manifest = 'CSV with columns tif, meta_csv (optional key, transect). Used instead of the batch folder.'
    tip_out = 'Merged GeoTIFF to write. Blank = merged_mosaic/merged_<method>.tif in the batch folder.'
    tip_kind = 'wcr = water column removed; wcp = water column present.'
    tip_method = 'quality = best look per pixel (needs meta CSVs); first/last = pass order; mean/median/min/max = per-pixel statistic.'
    tip_workers = 'Output windows processed at once. More is faster; the memory budget is shared among them.'
    tip_source = 'Also write a raster (and CSV key table) recording which pass supplied each pixel.'
    tip_feather = 'Seam softening. 0 = one best pass per pixel (hard seams). 0.05-0.2 blends passes whose quality scores are close; quality method only.'
    tip_swatch = 'Merge only a square test area centred on E, N (mosaic CRS units) with this side length in metres.'
    pk = [k for k in d]
    layout = [
        [sg.Text('Batch folder'), sg.In(key='root', size=(60, 1), tooltip=tip_root), sg.FolderBrowse(tooltip=tip_root)],
        [sg.Text('or Manifest CSV'), sg.In(key='manifest', size=(57, 1), tooltip=tip_manifest),
         sg.FileBrowse(file_types=(('CSV', '*.csv'),))],
        [sg.Text('Output TIF'), sg.In(key='out', size=(61, 1), tooltip=tip_out),
         sg.SaveAs(file_types=(('GeoTIFF', '*.tif'),), default_extension='.tif')],
        [sg.Text('Mosaic kind'), sg.Combo(['wcr', 'wcp'], 'wcr', key='kind', readonly=True, tooltip=tip_kind),
         sg.Text('Method'), sg.Combo(list(mq.MERGE_METHODS), 'quality', key='method', readonly=True, tooltip=tip_method),
         sg.Text('Workers'), sg.Spin(list(range(1, 33)), min(4, os.cpu_count() or 1), key='workers', size=(4, 1), tooltip=tip_workers),
         sg.Text('Feather'), sg.In('0', key='feather', size=(5, 1), tooltip=tip_feather),
         sg.Checkbox('Write source raster', key='source', tooltip=tip_source)],
        [sg.Text('Swatch (optional): E'), sg.In(key='sw_e', size=(10, 1), tooltip=tip_swatch), sg.Text('N'),
         sg.In(key='sw_n', size=(10, 1), tooltip=tip_swatch), sg.Text('Size m'), sg.In(key='sw_s', size=(8, 1), tooltip=tip_swatch)],
        [sg.Frame('Quality parameters', [[sg.Text(k, tooltip=tips[k]), sg.In(str(d[k]), key='p_' + k, size=(8, 1), tooltip=tips[k])]
                                         for k in pk])],
        [sg.Multiline(size=(90, 12), key='log', disabled=True, autoscroll=True)],
        [sg.Button('List passes'), sg.Button('Run'), sg.Button('Quit')],
    ]
    win = sg.Window('PINGMapper Mosaic Merge', layout, finalize=True)
    busy = False

    def collect(v):
        params = {k: type(d[k])(v['p_' + k]) for k in pk}
        if v['manifest']:
            entries = read_manifest(v['manifest'])
            base = os.path.dirname(os.path.abspath(v['manifest']))
        elif v['root']:
            entries = discover_batch(v['root'], v['kind'], lambda m, **_: win.write_event_value('-LOG-', str(m)))
            base = v['root']
        else:
            raise ValueError('choose a batch folder or a manifest')
        out = v['out'] or os.path.join(base, 'merged_mosaic', 'merged_%s.tif' % v['method'])
        sw = None
        if v['sw_e'] and v['sw_n'] and v['sw_s']:
            sw = (float(v['sw_e']), float(v['sw_n']), float(v['sw_s']))
        return entries, out, params, sw

    def work(v):
        try:
            entries, out, params, sw = collect(v)
            log = lambda m, **_: win.write_event_value('-LOG-', str(m))
            merge_entries(entries, out, params, v['method'], sw, v['source'],
                          log=log, workers=int(v['workers']),
                          feather=float(v['feather'] or 0))
            win.write_event_value('-DONE-', 'Done: ' + out)
        except Exception as e:
            win.write_event_value('-DONE-', 'Error: %s' % e)

    while True:
        ev, v = win.read()
        if ev in (sg.WIN_CLOSED, 'Quit'):
            break
        if ev == '-LOG-':
            win['log'].print(v[ev])
        elif ev == '-DONE-':
            win['log'].print(v[ev])
            busy = False
        elif ev == 'List passes' and not busy:
            try:
                entries = read_manifest(v['manifest']) if v['manifest'] else discover_batch(
                    v['root'], v['kind'], lambda m, **_: win['log'].print(m))
                for e in entries:
                    win['log'].print(e['key'], e['tif'])
                win['log'].print('%d passes' % len(entries))
            except Exception as e:
                win['log'].print('Error: %s' % e)
        elif ev == 'Run' and not busy:
            busy = True
            threading.Thread(target=work, args=(dict(v),), daemon=True).start()
    win.close()


def main(argv=None):
    if argv is None and len(sys.argv) == 1:
        return gui()
    ap = argparse.ArgumentParser(description='Merge sonar mosaics from many recordings.')
    ap.add_argument('root', nargs='?', help='batch output folder containing projects')
    ap.add_argument('--manifest', help='CSV of passes instead of folder discovery')
    ap.add_argument('--kind', choices=['wcr', 'wcp'], default='wcr')
    ap.add_argument('--out')
    ap.add_argument('--method', choices=mq.MERGE_METHODS, default='quality')
    ap.add_argument('--source', action='store_true',
                    help='also write which-pass-won raster (+ key table CSV)')
    ap.add_argument('--swatch', nargs=3, type=float, metavar=('E', 'N', 'SIZE_M'))
    ap.add_argument('--workers', type=int, default=None, help='windows processed at once')
    ap.add_argument('--feather', type=float, default=0.0,
                    help='blend passes with close scores (0 = hard seams; try 0.1)')
    ap.add_argument('--list', action='store_true', help='list passes found and exit')
    for k, d in mq.DEFAULT_PARAMS.items():
        ap.add_argument('--' + k.replace('_', '-'), type=type(d), default=d)
    a = ap.parse_args(argv)
    if not a.root and not a.manifest:
        ap.error('give a batch folder or --manifest')

    params = {k: getattr(a, k) for k in mq.DEFAULT_PARAMS}
    entries = read_manifest(a.manifest) if a.manifest else discover_batch(a.root, a.kind)
    if a.list:
        for e in entries:
            print(e['key'], e['tif'], e['meta_csv'])
        print('%d passes' % len(entries))
        return
    out = a.out or os.path.join(a.root or os.path.dirname(os.path.abspath(a.manifest)),
                                'merged_mosaic', 'merged_%s.tif' % a.method)
    print(merge_entries(entries, out, params, a.method, a.swatch, a.source, workers=a.workers, feather=a.feather))


if __name__ == '__main__':
    main()
