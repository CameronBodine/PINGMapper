"""
Re-runnable sonar-quality mosaic merge.

Works from the per-transect mosaics (``*_mosaic_<transect>.tif``) and a port
meta CSV that PINGMapper already wrote, so no sonar is re-decoded. Optionally
builds a small swatch around a point to tune parameters quickly.

    python -m pingmapper.utils.main_mosaic_quality <sonar_mosaic_dir> <port_meta.csv>
        [--out OUT.tif] [--swatch E N SIZE_M] [--plateau-end 0.6] [--far-floor 0.35]
        [--nadir-per-depth 1.0] [--depth-window 51]

Algorithm credit: Max Schwartz IV (anchorhold-web-viewer).
"""
import argparse
import glob
import os
import re

from pingmapper.utils import mosaic_quality as mq


def run(mosaic_dir, meta_csv, out_tif=None, params=None, swatch=None, method='quality', source=False,
        pattern='*_mosaic_[0-9]*.tif', log=print):
    """
    swatch: optional (easting, northing, size_m) in the mosaic CRS.
    Returns the written path.
    """
    mosaics = {}
    for p in sorted(glob.glob(os.path.join(mosaic_dir, pattern))):
        m = re.search(r'_mosaic_(\d+)\.tif$', p)
        if m:
            mosaics[int(m.group(1))] = p
    if len(mosaics) < 2:
        raise FileNotFoundError('Need at least two per-transect mosaics in ' + mosaic_dir)

    tracks = mq.transect_tracks(meta_csv, log, params)
    bounds = None
    suffix = method
    if swatch:
        e, n, size = swatch
        h = size / 2.0
        bounds = (e - h, n - h, e + h, n + h)
        suffix = method + '_swatch'

    if out_tif is None:
        first = next(iter(mosaics.values()))
        out_tif = re.sub(r'_mosaic_\d+\.tif$', '_mosaic_%s.tif' % suffix, first)
    src = out_tif.replace('.tif', '_source.tif') if source else None
    mq.merge_sonar_by_quality(mosaics, out_tif, tracks, log, bounds=bounds, method=method, source_tif=src)
    return out_tif


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('mosaic_dir')
    ap.add_argument('meta_csv')
    ap.add_argument('--out')
    ap.add_argument('--swatch', nargs=3, type=float, metavar=('E', 'N', 'SIZE_M'))
    ap.add_argument('--source', action='store_true', help='also write which-pass-won raster')
    ap.add_argument('--method', choices=mq.MERGE_METHODS, default='quality')
    for k, d in mq.DEFAULT_PARAMS.items():
        ap.add_argument('--' + k.replace('_', '-'), type=type(d), default=d)
    a = ap.parse_args(argv)
    params = {k: getattr(a, k) for k in mq.DEFAULT_PARAMS}
    print(run(a.mosaic_dir, a.meta_csv, a.out, params, a.swatch, a.method, a.source))


if __name__ == '__main__':
    main()
