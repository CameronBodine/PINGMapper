"""Synthetic checks for pingmapper.utils.mosaic_quality (run with pytest or directly)."""
import os
import tempfile

import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin

from pingmapper.utils import mosaic_quality as mq

QUIET = dict(log=lambda *a, **k: None)


def _write(path, arr, west, north, res=1.0, nodata=0):
    with rasterio.open(path, "w", driver="GTiff", height=arr.shape[-2], width=arr.shape[-1],
                       count=arr.shape[0], dtype=arr.dtype, crs="EPSG:32618",
                       transform=from_origin(west, north, res, res), nodata=nodata) as d:
        d.write(arr)


def _meta():
    # Pass 0 runs along y=30, pass 1 along y=70; 30 m range, 2 m deep.
    rows = []
    for t, y in ((0, 30.0), (1, 70.0)):
        for i in range(100):
            rows.append(dict(transect=t, e=float(i), n=y, max_range=30.0,
                             dep_m=2.0, record_num=i))
    return pd.DataFrame(rows)


def _setup(d, bands=1, dtype="uint8"):
    a = np.full((bands, 100, 100), 10, dtype=dtype)
    b = np.full((bands, 100, 100), 200, dtype=dtype)
    _write(os.path.join(d, "a.tif"), a, 0, 100)
    _write(os.path.join(d, "b.tif"), b, 0, 100)
    # dict order deliberately reversed: keys, not order, pick the trackline
    return {1: os.path.join(d, "b.tif"), 0: os.path.join(d, "a.tif")}


def test_best_look_wins_and_mapping_is_explicit():
    tracks = mq.transect_tracks_from_df(_meta(), **QUIET)
    with tempfile.TemporaryDirectory() as d:
        paths = _setup(d)
        out = os.path.join(d, "m.tif")
        mq.merge_sonar_by_quality(paths, out, tracks, **QUIET)
        with rasterio.open(out) as r:
            m = r.read(1)
        # row = 100 - y. Pass 0 at y=30 is 10 m from y=40 (plateau);
        # pass 1 at y=70 is 30 m from it (far edge).
        assert m[60, 50] == 10
        assert m[30, 50] == 200


def test_multiband_uint16_and_swatch():
    tracks = mq.transect_tracks_from_df(_meta(), **QUIET)
    with tempfile.TemporaryDirectory() as d:
        paths = _setup(d, bands=3, dtype="uint16")
        out = os.path.join(d, "m.tif")
        mq.merge_sonar_by_quality(paths, out, tracks, bounds=(20, 40, 60, 80), **QUIET)
        with rasterio.open(out) as r:
            assert (r.count, r.dtypes[0], r.width, r.height) == (3, "uint16", 40, 40)
            assert set(np.unique(r.read())) <= {10, 200}


def test_params_and_mask():
    p = mq.resolve_params({"plateau_end": 0.5})
    assert p["plateau_end"] == 0.5 and p["far_floor"] == mq.SONAR_FAR_FLOOR
    try:
        mq.resolve_params({"plateau_end": 2})
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
    tracks = mq.transect_tracks_from_df(_meta(), **QUIET)
    with tempfile.TemporaryDirectory() as d:
        paths = _setup(d)
        out = mq.mask_mosaics_to_plateau(paths, os.path.join(d, "o"), tracks, **QUIET)
        with rasterio.open(out[0]) as r:
            m = r.read(1)
        assert (m == 0).any() and (m > 0).any()


if __name__ == "__main__":
    test_best_look_wins_and_mapping_is_explicit()
    test_multiband_uint16_and_swatch()
    test_params_and_mask()
    print("ok")
