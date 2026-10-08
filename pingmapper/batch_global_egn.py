"""Batch processing with one global EGN correction shared by all recordings.

Phase 1  read every recording without EGN or exports (nav, depth, chunks)
Phase 2  pool range-wise means, min/max and histograms across recordings
Phase 3  re-open each project (project_mode=2) with EGN from the pooled file
         and run the requested exports/rectification
Phase 4  optionally merge the resulting mosaics

Usage:
    from pingmapper.batch_global_egn import process_with_global_egn
    process_with_global_egn(in_dir, out_dir, params, sampling='moderate')
"""

import os

from pingmapper.doWork import doWork
from pingmapper import global_egn

# Output-producing steps that are deferred until the global EGN is ready.
_DEFERRED_OFF = {
    'egn': False, 'wcp': False, 'wcm': False, 'wcr': False, 'wco': False,
    'rect_wcp': False, 'rect_wcr': False, 'pred_sub': False, 'map_sub': False,
    'export_poly': False, 'pltSubClass': False, 'banklines': False,
    'coverage': False, 'mosaic_quality': False,
}


def process_with_global_egn(in_dir=None, out_dir=None, params=None, sampling='moderate',
                            in_files=None, prefix='', suffix='', preserve_subdirs=False,
                            means_file=None, merge=False, merge_kw=None, log=print):
    """Process recordings with a single EGN curve pooled across all of them.

    ``params`` are the normal doWork parameters (egn is forced on in phase 3).
    ``sampling`` is 'low', 'moderate' or 'high' (share of chunks used to build
    the curve). Returns {'phase1', 'phase3', 'means_file', 'mosaic'}.
    """
    if not out_dir:
        raise ValueError('out_dir is required.')
    params = dict(params or {})
    common = dict(in_dir=in_dir, in_files=in_files, out_dir=out_dir, batch=True,
                  prefix=prefix, suffix=suffix, preserve_subdirs=preserve_subdirs)

    log('Phase 1/3: reading recordings (no EGN, no exports)')
    p1 = dict(params, **_DEFERRED_OFF)
    r1 = doWork(params=p1, **common)
    ok = [r['inFile'] for r in r1 if r['success']]
    if not ok:
        raise RuntimeError('No recordings were read successfully.')

    means_file = means_file or os.path.join(out_dir, 'global_egn.npz')
    log('Phase 2/3: pooling EGN across %d recordings (%s sampling)' % (len(ok), sampling))
    global_egn.build(out_dir, means_file, sampling, log=log)

    log('Phase 3/3: applying global EGN and exporting')
    p3 = dict(params, project_mode=2, egn=True, egn_means_file=means_file)
    kw = dict(common, in_files=ok)
    r3 = doWork(params=p3, **kw)

    mosaic = None
    if merge:
        from pingmapper import main_mosaic
        kw = dict(colormap=params.get('son_colorMap'), **(merge_kw or {}))
        mosaic = main_mosaic.merge_mosaics(root=out_dir, **kw)

    return {'phase1': r1, 'phase3': r3, 'means_file': means_file, 'mosaic': mosaic}
