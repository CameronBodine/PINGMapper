'''
Global empirical gain normalization (EGN) across many recordings.

Each recording normally gets its own range-wise mean intensity curve. That
makes neighbouring recordings differ in tone. This module pools sampled chunk
means from many processed recordings into one curve per channel, saved to an
.npz file. Pass that file to PINGMapper as ``egn_means_file`` and every
recording is normalised with the same curve.

Typical use (recordings already read, i.e. a ``meta`` folder exists):

    from pingmapper import global_egn
    global_egn.build('C:/proj/out', 'C:/proj/egn_global.npz', sampling='low')

then reprocess with ``egn=True``, ``egn_means_file='C:/proj/egn_global.npz'``
and ``project_mode=2``.
'''

import os
import sys
import glob
import argparse

import numpy as np

# Fraction of chunks sampled per recording
SAMPLING = {'low': 0.25, 'moderate': 0.5, 'high': 1.0}


def select_chunks(chunks, sampling='high'):
    '''Evenly spaced, repeatable subset of chunks (at least one).'''
    chunks = list(chunks)
    if isinstance(sampling, str):
        if sampling not in SAMPLING:
            raise ValueError("sampling must be one of %s" % list(SAMPLING))
        frac = SAMPLING[sampling]
    else:
        frac = float(sampling)
    n = len(chunks)
    if n == 0 or frac >= 1:
        return chunks
    k = max(1, int(round(n*frac)))
    idx = np.unique(np.linspace(0, n-1, k).round().astype(int))
    return [chunks[i] for i in idx]


def stack_means(chunk_means):
    '''Stack (bed, wc) chunk mean vectors into nan padded 2D arrays.'''
    lv = max(c[0].shape[0] for c in chunk_means)
    lw = max(c[1].shape[0] for c in chunk_means)
    bed = np.full((lv, len(chunk_means)), np.nan)
    wc = np.full((lw, len(chunk_means)), np.nan)
    for i, c in enumerate(chunk_means):
        bed[:c[0].shape[0], i] = c[0]
        wc[:c[1].shape[0], i] = c[1]
    return bed, wc


def pool(chunk_means_by_beam):
    '''
    Pool chunk means for each beam name.

    chunk_means_by_beam: {beam: [(bed_means, wc_means), ...]} with all
    sampled chunks of all recordings.
    Returns {beam: {'bed': 1D, 'wc': 1D, 'n_chunks': int}}.
    '''
    out = {}
    for beam, cms in chunk_means_by_beam.items():
        bed, wc = stack_means(cms)
        with np.errstate(all='ignore'):
            out[beam] = {'bed': np.nanmean(bed, axis=1),
                         'wc': np.nanmean(wc, axis=1),
                         'n_chunks': len(cms)}
    return out


def save(path, pooled, stats=None):
    """Write pooled means and optional global stats (min/max, histograms)."""
    arrs = {}
    for beam, d in pooled.items():
        arrs[beam + '__bed'] = d['bed']
        arrs[beam + '__wc'] = d['wc']
        arrs[beam + '__n'] = np.array(d['n_chunks'])
    for k, v in (stats or {}).items():
        arrs['stats__' + k] = np.asarray(v)
    np.savez(path, **arrs)


def load(path, beam):
    """Return (bed_means, wc_means) for a beam name such as ss_port."""
    with np.load(path) as z:
        if beam + '__bed' not in z:
            raise KeyError("%s has no EGN curve for %s" % (path, beam))
        return z[beam + '__bed'].copy(), z[beam + '__wc'].copy()


def load_stats(path):
    """Global min/max and histograms, or None if the file has none."""
    with np.load(path) as z:
        out = {k[7:]: z[k].copy() for k in z.files if k.startswith('stats__')}
    need = ('bed_min', 'bed_max', 'wc_min', 'wc_max', 'wcp_hist', 'wcr_hist')
    return out if all(k in out for k in need) else None


def fit_length(means, n):
    """Trim or pad (by repeating the last value) a curve to n bins."""
    means = np.asarray(means, dtype=float)
    if means.shape[0] >= n:
        return means[:n]
    pad = np.full(n - means.shape[0], means[~np.isnan(means)][-1])
    return np.concatenate([means, pad])


def combine_minmax(min_max):
    """Global bed/wc min and max from per-chunk _egnCalcMinMax results."""
    bmin = [m[0][0] for m in min_max]
    bmax = [m[0][1] for m in min_max]
    wmin = [m[1][0] for m in min_max]
    wmax = [m[1][1] for m in min_max]
    with np.errstate(all='ignore'):
        return {'bed_min': np.nanmin(bmin), 'bed_max': np.nanmax(bmax),
                'wc_min': np.nanmin(wmin), 'wc_max': np.nanmax(wmax)}


def _open_son(meta_file):
    from pingmapper.class_rectObj import rectObj
    son = rectObj(meta_file)
    son.egn = True
    son.tvg = False
    return son


def _sampled_chunks(son, sampling):
    chunks = son._getChunkID()
    chunks = chunks[:-1] if len(chunks) > 1 else chunks
    return select_chunks(chunks, sampling)


def _per_chunk(son, fn, chunks):
    out = []
    for c in chunks:
        son._loadSonMeta()  # the chunk routines free it
        out.append(fn(c))
    return out


def recording_chunk_means(meta_file, sampling='high', log=print):
    """Sampled chunk means for one sidescan beam of a processed recording."""
    son = _open_son(meta_file)
    chunks = _sampled_chunks(son, sampling)
    return son.beamName, _per_chunk(son, son._egnCalcChunkMeans, chunks)


def _meta_files(root):
    files = []
    for d in sorted(glob.glob(os.path.join(root, '*'))):
        if os.path.isdir(os.path.join(d, 'meta')):
            files += sorted(glob.glob(os.path.join(d, 'meta', '*_ss_*_meta.meta')))
    return files


def build(root, out_file, sampling='high', stats=True, log=print):
    """
    Pool EGN from every recording folder under root (each holding a ``meta``
    folder). Port and starboard are pooled separately.

    Stage 1 pools the range-wise means. If stats is True, stage 2 finds the
    global min/max after EGN and stage 3 sums the corrected histograms, so the
    contrast stretch is also shared by all recordings. Everything is written
    to out_file, and the pooled means dict is returned.
    """
    by_beam = {}
    good = []
    for mf in _meta_files(root):
        name = os.path.basename(os.path.dirname(os.path.dirname(mf)))
        try:
            beam, cms = recording_chunk_means(mf, sampling, log)
        except Exception as e:
            log('skip %s: %r' % (mf, e))
            continue
        by_beam.setdefault(beam, []).extend(cms)
        good.append(mf)
        log('means %s %s: %d chunks' % (name, beam, len(cms)))
    if not by_beam:
        raise RuntimeError('No processed recordings found under %s' % root)
    pooled = pool(by_beam)

    extra = None
    if stats:
        extra = _pool_stats(good, pooled, sampling, log)
    save(out_file, pooled, extra)
    log('wrote %s' % out_file)
    return pooled


def _pool_stats(meta_files, pooled, sampling, log):
    def prep(mf):
        son = _open_son(mf)
        son.egn_bed_means = pooled[son.beamName]['bed']
        son.egn_wc_means = pooled[son.beamName]['wc']
        return son

    mm = []
    for mf in meta_files:
        son = prep(mf)
        mm += _per_chunk(son, son._egnCalcMinMax, _sampled_chunks(son, sampling))
        log('min/max %s' % os.path.basename(mf))
    stats = combine_minmax(mm)

    wcp = np.zeros(255)
    wcr = np.zeros(255)
    for mf in meta_files:
        son = prep(mf)
        son.egn_bed_min, son.egn_bed_max = stats['bed_min'], stats['bed_max']
        son.egn_wc_min, son.egn_wc_max = stats['wc_min'], stats['wc_max']
        son.remShadow = getattr(son, 'remShadow', 0)
        for a, b in _per_chunk(son, son._egnCalcHist, _sampled_chunks(son, sampling)):
            wcp += a
            wcr += b
        log('histogram %s' % os.path.basename(mf))
    stats['wcp_hist'] = wcp
    stats['wcr_hist'] = wcr
    return stats


def main(argv=None):
    ap = argparse.ArgumentParser(description='Pool EGN across recordings.')
    ap.add_argument('root', help='Folder holding processed recording folders')
    ap.add_argument('out', help='Output .npz file')
    ap.add_argument('--no-stats', action='store_true',
                    help='Pool only the means (skip global min/max and stretch)')
    ap.add_argument('--sampling', default='high',
                    help='low, moderate, high or a fraction 0-1')
    a = ap.parse_args(argv)
    s = a.sampling
    try:
        s = float(s)
    except ValueError:
        pass
    build(a.root, a.out, s, stats=not a.no_stats)


if __name__ == '__main__':
    here = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if here not in sys.path:
        sys.path.insert(0, here)
    main()
