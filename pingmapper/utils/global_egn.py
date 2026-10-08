'''
Global empirical gain normalization (EGN) across many recordings.

Each recording normally gets its own range-wise mean intensity curve. That
makes neighbouring recordings differ in tone. This module pools sampled chunk
means from many processed recordings into one curve per channel, saved to an
.npz file. Pass that file to PINGMapper as ``egn_means_file`` and every
recording is normalised with the same curve.

Typical use (recordings already read, i.e. a ``meta`` folder exists):

    from pingmapper.utils import global_egn
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


def save(path, pooled):
    arrs = {}
    for beam, d in pooled.items():
        arrs[beam + '__bed'] = d['bed']
        arrs[beam + '__wc'] = d['wc']
        arrs[beam + '__n'] = np.array(d['n_chunks'])
    np.savez(path, **arrs)


def load(path, beam):
    '''Return (bed_means, wc_means) for a beam name such as ss_port.'''
    with np.load(path) as z:
        if beam + '__bed' not in z:
            raise KeyError("%s has no EGN curve for %s" % (path, beam))
        return z[beam + '__bed'].copy(), z[beam + '__wc'].copy()


def fit_length(means, n):
    '''Trim or pad (by repeating the last value) a curve to n bins.'''
    means = np.asarray(means, dtype=float)
    if means.shape[0] >= n:
        return means[:n]
    pad = np.full(n - means.shape[0], means[~np.isnan(means)][-1])
    return np.concatenate([means, pad])


def recording_chunk_means(meta_file, sampling='high', log=print):
    '''Sampled chunk means for one sidescan beam of a processed recording.'''
    from pingmapper.class_rectObj import rectObj
    son = rectObj(meta_file)
    chunks = son._getChunkID()
    chunks = chunks[:-1] if len(chunks) > 1 else chunks
    chunks = select_chunks(chunks, sampling)
    son.egn = True
    son.tvg = False
    out = []
    for c in chunks:
        son._loadSonMeta()  # the chunk routine frees it
        out.append(son._egnCalcChunkMeans(c))
    return son.beamName, out


def build(root, out_file, sampling='high', log=print):
    '''
    Pool EGN means from every recording folder under root (each holding a
    ``meta`` folder). Port and starboard are pooled separately. Returns
    the pooled dict and writes out_file.
    '''
    by_beam = {}
    dirs = sorted(d for d in glob.glob(os.path.join(root, '*'))
                  if os.path.isdir(os.path.join(d, 'meta')))
    for d in dirs:
        for mf in sorted(glob.glob(os.path.join(d, 'meta', '*_ss_*_meta.meta'))):
            try:
                beam, cms = recording_chunk_means(mf, sampling, log)
            except Exception as e:
                log('skip %s: %r' % (mf, e))
                continue
            by_beam.setdefault(beam, []).extend(cms)
            log('%s %s: %d chunks' % (os.path.basename(d), beam, len(cms)))
    if not by_beam:
        raise RuntimeError('No processed recordings found under %s' % root)
    pooled = pool(by_beam)
    save(out_file, pooled)
    log('wrote %s' % out_file)
    return pooled


def main(argv=None):
    ap = argparse.ArgumentParser(description='Pool EGN across recordings.')
    ap.add_argument('root', help='Folder holding processed recording folders')
    ap.add_argument('out', help='Output .npz file')
    ap.add_argument('--sampling', default='high',
                    help='low, moderate, high or a fraction 0-1')
    a = ap.parse_args(argv)
    s = a.sampling
    try:
        s = float(s)
    except ValueError:
        pass
    build(a.root, a.out, s)


if __name__ == '__main__':
    here = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if here not in sys.path:
        sys.path.insert(0, here)
    main()
