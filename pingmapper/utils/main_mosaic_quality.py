"""
Merge sonar mosaics from many recordings into one, outside the PINGMapper
pipeline. Nothing is re-decoded or re-rectified.

Each input pass is a georeferenced mosaic raster plus the ping metadata (boat
position, depth, range) for the track that made it. Transect numbers repeat in
every recording, so each pass is keyed "<project>:<transect>".

1. Batch folder - every project under ROOT with a sonar_mosaic/ folder:

    python -m pingmapper.utils.main_mosaic_quality ROOT [--kind wcr|wcp]
        [--method quality] [--out merged.tif] [--source] [--list]

2. Manifest CSV - any rasters, from any source (columns: tif, meta_csv, and
   optionally key, transect). One row per pass; meta_csv may be blank for
   methods that do not need tracks:

    python -m pingmapper.utils.main_mosaic_quality --manifest passes.csv ...

Common options: --swatch E N SIZE_M (small test area), --plateau-end,
--far-floor, --nadir-per-depth, --depth-window.

Algorithm credit: Max Schwartz IV (anchorhold-web-viewer).
"""
import argparse
import glob
import os
import re

import pandas as pd

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
                  source=False, log=print, workers=None):
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
                              method=method, source_tif=src, workers=workers)
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


def main(argv=None):
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
    print(merge_entries(entries, out, params, a.method, a.swatch, a.source, workers=a.workers))


if __name__ == '__main__':
    main()
