"""Synthetic checks for pingmapper.mosaic_quality (run with pytest or directly)."""
import os
import tempfile

import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin

from pingmapper import mosaic_quality as mq

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


def test_other_methods():
    with tempfile.TemporaryDirectory() as d:
        paths = _setup(d)  # transect 1 -> 200, transect 0 -> 10; overlap in rows 30..70
        def run(method, **kw):
            out = os.path.join(d, method + ".tif")
            mq.merge_sonar_by_quality(paths, out, {}, method=method, **kw, **QUIET)
            with rasterio.open(out) as r:
                return r.read(1)[50, 50]
        # dict order is {1: b(200), 0: a(10)}, so "first" is b and "last" is a
        assert run("first") == 200 and run("last") == 10
        assert run("max") == 200 and run("min") == 10
        assert run("mean") == 105 and run("median") == 105
        src = os.path.join(d, "src.tif")
        run("quality", source_tif=src)
        with rasterio.open(src) as r:
            assert set(np.unique(r.read(1))) <= {0, 1, 2}
        try:
            run("bogus")
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError")


def test_batch_and_manifest():
    import shutil
    from pingmapper import main_mosaic as bm
    with tempfile.TemporaryDirectory() as root:
        # Two recordings, each with transect 0 only; transect ids collide.
        for name, y, val in (("recA", 30.0, 10), ("recB", 70.0, 200)):
            proj = os.path.join(root, name)
            os.makedirs(os.path.join(proj, "sonar_mosaic")); os.makedirs(os.path.join(proj, "meta"))
            _write(os.path.join(proj, "sonar_mosaic", name + "_x_rect_wcr_mosaic_0.tif"),
                   np.full((1, 100, 100), val, dtype="uint8"), 0, 100)
            df = _meta(); df = df[df.transect == (0 if y == 30.0 else 1)].copy(); df["transect"] = 0
            df.to_csv(os.path.join(proj, "meta", "B002_ss_port_meta.csv"), index=False)
        entries = bm.discover_batch(root, "wcr", **QUIET)
        assert [e["key"] for e in entries] == ["recA:0", "recB:0"]
        out = bm.run(root, "wcr", source=True, **QUIET)
        with rasterio.open(out) as r:
            m = r.read(1)
        assert m[60, 50] == 10 and m[30, 50] == 200
        assert os.path.exists(out.replace(".tif", "_source.csv"))
        # Manifest, no metadata, any method that needs none.
        man = os.path.join(root, "m.csv")
        pd.DataFrame({"tif": [e["tif"] for e in entries]}).to_csv(man, index=False)
        out2 = bm.merge_entries(bm.read_manifest(man), os.path.join(root, "o.tif"), method="max", **QUIET)
        with rasterio.open(out2) as r:
            assert r.read(1)[50, 50] == 200


def test_range_smooth_and_edge_feather():
    import numpy as np
    import pandas as pd
    n = 200
    df = pd.DataFrame({"e": np.arange(n, dtype=float), "n": np.zeros(n),
                       "max_range": np.where(np.arange(n) % 5 == 0, 30.0, 20.0)})
    raw = mq.transect_tracks_from_df(df, log=lambda *a, **k: None)[0]["far"]
    sm = mq.transect_tracks_from_df(df, log=lambda *a, **k: None,
                                    params={"range_smooth": 9})[0]["far"]
    assert np.ptp(sm[10:-10]) < np.ptp(raw[10:-10])
    r = np.array([5.0, 19.0, 19.9])
    a = mq.sonar_quality(r, 1.0, 20.0)
    b = mq.sonar_quality(r, 1.0, 20.0, edge_feather=5.0)
    assert b[0] == a[0] and b[2] < a[2] * 0.2 and (b > 0).all()
    for bad in ({"range_smooth": 0}, {"edge_feather": -1}):
        try:
            mq.resolve_params(bad)
            raise AssertionError
        except ValueError:
            pass




def test_global_egn_pooling():
    import numpy as np, tempfile, os
    from pingmapper import global_egn as g
    assert g.select_chunks(range(10),'high')==list(range(10))
    assert g.select_chunks(range(10),'low')==[0,9] and g.select_chunks(range(1),'low')==[0]
    cms=[(np.array([1.,2,3]),np.array([1.,1,1])),(np.array([3.,4]),np.array([3.,3]))]
    p=g.pool({'ss_port':cms})['ss_port']
    assert list(p['bed'])==[2,3,3] and p['n_chunks']==2
    f=os.path.join(tempfile.mkdtemp(),'e.npz'); g.save(f,g.pool({'ss_port':cms}))
    b,w=g.load(f,'ss_port'); assert list(b)==[2,3,3]
    assert len(g.fit_length(b,5))==5
    mm=g.combine_minmax([((0.,2.),(1.,3.)),((-1.,1.),(0.5,4.))])
    assert float(mm['bed_min'])==-1. and float(mm['wc_max'])==4.
    assert g.load_stats(f) is None
    st=dict(mm,wcp_hist=np.ones(255),wcr_hist=np.ones(255))
    g.save(f,g.pool({'ss_port':cms}),st)
    ls=g.load_stats(f); assert float(ls['bed_max'])==2. and ls['wcp_hist'].sum()==255
    print('ok')
    

if __name__ == "__main__":
    test_range_smooth_and_edge_feather()
    test_batch_and_manifest()
    test_other_methods()
    test_best_look_wins_and_mapping_is_explicit()
    test_multiband_uint16_and_swatch()
    test_params_and_mask()
    test_global_egn_pooling()
    print("ok")
