"""
Quality-weighted merge of overlapping sonar mosaics ("sweet spot" mosaicking).

For each output pixel, keep the look from the pass that saw that ground best
(away from nadir, inside the plateau of the swath, before the far-range
decline) rather than whichever transect happens to be first or last.

Originally written by Max Schwartz IV for anchorhold-web-viewer
(https://github.com/maxschwartziv/anchorhold-web-viewer, pipeline/process_data.py,
PR #5, MIT licensed) following PINGMapper issue #210. Lifted here with the
algorithm unchanged; only the progress reporter was replaced.
"""

import contextlib
import math
import os
import warnings

import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import Resampling


class Progress:
    """Minimal stand-in for anchorhold-web-viewer's progress reporter."""

    def __init__(self, total, label=""):
        self.total, self.label, self.n = max(int(total), 1), label, 0

    def step(self):
        self.n += 1
        print(f"      {self.label}: {self.n}/{self.total}", flush=True)

    def finish(self):
        pass



# ── Merging overlapping mosaics by which look is the better one ──────────────

# Where side scan is worth trusting, as a fraction of the swath's own max range.
SONAR_PLATEAU_END = 0.6     # past this the return weakens and the footprint grows
SONAR_FAR_FLOOR = 0.35      # what the outermost ground range is still worth
SONAR_QUALITY_CELL_M = 1.0  # quality varies over metres, not pixels

# How wide the poor zone under the boat is, per metre of height above the
# bottom. Slant-range correction turns a sample at slant range s into ground
# range g = sqrt(s^2 - h^2), so one slant sample is stretched over 1/sin(theta)
# of ground, theta being the angle off vertical: 1.4x at g = h, 2.2x at h/2,
# 4.1x at h/4. 1.0 puts the edge at 45 degrees, where that stretch drops under
# root two. A transducer tilted further down sees texture closer in and wants
# less; one that leaves a wide dark band under the boat wants more.
SONAR_NADIR_PER_DEPTH = 1.0
# Depth sets the nadir width ping by ping, smoothed along the pass first: a
# running median over this many pings, so one bad bottom pick does not notch
# the scores.
SONAR_DEPTH_WINDOW_PINGS = 51

# Working memory the merge holds at once, however large the survey: it works
# through the output a window at a time and never holds the whole grid.
SONAR_MERGE_BUDGET_MB = 512
SONAR_MERGE_BLOCK = 512     # output tile size; windows are whole multiples of it
# What the merge holds per pixel of its window: the winning value, score and
# pass (7 bytes), one pass's read and validity (2), its score and the
# interpolation temporaries behind it (~25), and the quality grid that is
# interpolated from - at most a quarter the window's pixel count, at ~80 bytes
# a cell (20).
SONAR_MERGE_BYTES_PER_PX = 56

# Tunable weights in one place; every public function takes `params` (a dict
# with any of these keys) and falls back to these values.
DEFAULT_PARAMS = {
    "plateau_end": SONAR_PLATEAU_END,
    "far_floor": SONAR_FAR_FLOOR,
    "nadir_per_depth": SONAR_NADIR_PER_DEPTH,
    "depth_window": SONAR_DEPTH_WINDOW_PINGS,
}


def resolve_params(params=None) -> dict:
    """Merge user params over DEFAULT_PARAMS and range-check them."""
    p = dict(DEFAULT_PARAMS)
    p.update({k: v for k, v in (params or {}).items() if k in DEFAULT_PARAMS and v is not None})
    p["plateau_end"], p["far_floor"] = float(p["plateau_end"]), float(p["far_floor"])
    p["nadir_per_depth"], p["depth_window"] = float(p["nadir_per_depth"]), int(p["depth_window"])
    if not 0.0 < p["plateau_end"] < 1.0:
        raise ValueError("plateau_end must be between 0 and 1 (exclusive)")
    if not 0.0 < p["far_floor"] <= 1.0:
        raise ValueError("far_floor must be in (0, 1]")
    if p["nadir_per_depth"] < 0:
        raise ValueError("nadir_per_depth must be >= 0")
    if p["depth_window"] < 1:
        raise ValueError("depth_window must be >= 1")
    return p


def _as_mapping(tif_paths) -> dict:
    """Accept {transect_id: path} or a list (transect id = list index)."""
    if isinstance(tif_paths, dict):
        return dict(tif_paths)
    return {i: p for i, p in enumerate(tif_paths)}


# Blending is off. The reasoning below is kept because the idea is sound and
# the implementation worked; what failed was the premise.
#
# The claim was that averaging two passes sheds speckle, the way multi-look
# averaging has always worked in radar and sonar. Measured over the whole
# overlap of an 8-pass Indian Hills survey, it does not:
#
#                      native (0.019 m)   0.15 m    stdev
#   first-file-wins            21.419     26.291     65.1
#   best look wins             21.411     26.024     65.2
#   blended                    18.862     22.161     57.5
#   blended vs order           -11.9%     -15.7%    -11.7%
#
# Shedding speckle means pixel-scale variation falling FASTER than texture.
# It fell slower: the high-to-low ratio went from 0.815 to 0.851, up 4.5%.
# Everything dropped together, so what the blend did was flatten contrast,
# and it took slightly more texture than noise with it.
#
# The likely reason is in the note at the end of merge_sonar_by_quality: the
# residual registration error between passes is one to four metres, which at
# 0.0188 m/px is 53 to 213 pixels. Two views of the same ground offset by
# that much do not average into a cleaner look at it; they blur.
#
# What would make it worth revisiting is registration. Cross-correlate the
# overlap and shift one pass onto the other before averaging, and the premise
# becomes true again - the looks would then actually be of the same ground.
# Until then the merge keeps the single best look, which the same measurement
# shows is where the real win is: quality picks a different pass from file
# order on 76.4% of the overlap, by 54 of 255 on average.
#
# SONAR_BLEND_POWER = 3.0   # cubed, a nadir look at 0.2 carried 0.008


def transect_tracks(meta_csv: str, log=print, params=None) -> dict:
    """
    Where the boat was on each pass, and what each ping could see, from
    PINGMapper's own ping metadata.

    With any track filter set, PINGMapper mosaics per transect - one file per
    continuous run of pings that survived the filter - and numbers the transects
    in the order it writes the mosaics. So transect i's ping positions are the
    trackline of mosaic i, which is what lets a pixel be turned back into a
    ground range from the boat that recorded it.

    Nadir and range are kept per ping rather than as one figure for the pass. A
    pass that runs from 3 m of water into 12 m has a nadir zone four times as
    wide at one end as the other, and a range changed mid-pass moves where the
    far field starts; a pass-wide median got both wrong for most of the pass.
    Each pixel takes the figures of the ping its ground range is measured from.

    max_range is the slant range the unit was set to. The mosaics have the
    water column removed and are in ground range, where that reach is
    sqrt(range^2 - depth^2).

    Returns {transect: {points (N,2) in the mosaic CRS, tree over them,
    nadir (N,) and far (N,) in metres, reach - the furthest far}}.
    """
    return transect_tracks_from_df(pd.read_csv(meta_csv), log=log, params=params,
                                   name=os.path.basename(meta_csv))


def transect_tracks_from_df(df, log=print, params=None, name="metadata") -> dict:
    """
    As transect_tracks, from an in-memory ping metadata DataFrame (for example
    PINGMapper's sonMetaDF, port and star concatenated) rather than a CSV. The
    transect column is optional: without it every ping is one transect, id 0.
    """
    from scipy.spatial import cKDTree

    p = resolve_params(params)
    df = df.copy()
    if "transect" not in df.columns:
        df["transect"] = 0
    df["transect"] = df["transect"].fillna(0)
    missing = {"e", "n", "max_range"} - set(df.columns)
    if missing:
        raise KeyError(f"{name} has no {sorted(missing)} column(s)")
    # PINGMapper's own bottom pick where it made one, the unit's otherwise.
    depth_col = next((c for c in ("dep_m", "inst_dep_m") if c in df.columns), None)
    order = next((c for c in ("time_s", "record_num") if c in df.columns), None)

    tracks, summary = {}, []
    for transect, group in df.groupby("transect"):
        group = group.dropna(subset=["e", "n"])
        if group.empty:
            continue
        if order:
            group = group.sort_values(order)
        if depth_col:
            # 0 and below are failed picks, not depths: the median steps over
            # them, and a run too long for it is filled from either side.
            depth = group[depth_col].where(group[depth_col] > 0)
            depth = (depth.rolling(p["depth_window"], center=True, min_periods=1)
                     .median().interpolate(limit_direction="both")
                     .fillna(0.0).to_numpy(dtype=float))
        else:
            depth = np.zeros(len(group))
        slant = group["max_range"].fillna(group["max_range"].median()).to_numpy(dtype=float)
        far = np.nan_to_num(np.sqrt(np.maximum(slant ** 2 - depth ** 2, 0.0)))
        points = np.column_stack((group["e"].to_numpy(dtype=float),
                                  group["n"].to_numpy(dtype=float)))
        tracks[int(transect)] = {
            "points": points,
            "tree": cKDTree(points),
            "nadir": depth * p["nadir_per_depth"],
            "far": far,
            "plateau_end": p["plateau_end"],
            "far_floor": p["far_floor"],
            "reach": float(far.max()),
        }
        summary.append(f"#{int(transect)} {len(points):,} pings "
                       f"{depth.min():.1f}-{depth.max():.1f} m deep "
                       f"@{np.nanmax(slant):.0f} m")
    log(f"      {len(tracks)} transect(s): {', '.join(summary[:4])}"
        + (" ..." if len(summary) > 4 else ""))
    return tracks


def sonar_quality(ground_range, nadir_m, max_range_m,
                  plateau_end=SONAR_PLATEAU_END, far_floor=SONAR_FAR_FLOOR):
    """
    How far to trust a side-scan pixel sitting `ground_range` metres off its own
    trackline. Near 0 = only if nothing else covers this ground, 1 = the good
    part.

    Side scan is poor under the boat and poor at the far edge and good in
    between, so this is a ramp, a plateau and a decline:

      below nadir_m     The nadir zone. With the water column removed, the few
                        near-vertical samples get stretched over the widest
                        patch of ground in the swath, and the return is
                        specular rather than textural. Scored 0..1 across the
                        zone rather than 0 outright, because it is poor data
                        and not absent data: it still has to be able to win
                        where no other pass covers that ground at all - which
                        is also why right under the boat scores just above 0
                        rather than at it.
      to 0.6 of range   The good part - grazing angle low enough to throw
                        readable shadows, footprint still small.
      beyond that       Declines to SONAR_FAR_FLOOR at max range: weaker
                        return, bigger footprint, more noise.

    nadir_m and max_range_m are each a number or an array matching
    ground_range, so every pixel can carry the figures of its own ping. See
    SONAR_NADIR_PER_DEPTH for how depth becomes a nadir width.
    """
    r = np.asarray(ground_range, dtype="float32")
    nadir = np.maximum(np.asarray(nadir_m, dtype="float32"), 0.5)
    far = np.maximum(np.asarray(max_range_m, dtype="float32"), nadir * 2.0)
    plateau = far * plateau_end

    # far is at least twice nadir, so the plateau starts past the nadir zone
    # and the ramp and the decline never overlap: the lower of the two is
    # whichever one applies.
    ramp = np.clip(r / nadir, 1e-3, 1.0)
    decline = 1.0 - (1.0 - far_floor) * np.clip(
        (r - plateau) / np.maximum(far - plateau, 1e-3), 0.0, 1.0)
    return np.minimum(ramp, decline).astype("float32")


def quality_cell(res_m: float) -> float:
    """
    The quality grid's cell for a mosaic of res_m metres a pixel.

    A metre, unless the mosaic is coarser than half that: the grid then follows
    the pixels, so it is never more than a quarter their count and its memory
    stays inside what SONAR_MERGE_BYTES_PER_PX allows for it.
    """
    return max(SONAR_QUALITY_CELL_M, 2.0 * float(res_m))


def quality_for(track, xs, ys, cell: float):
    """
    Quality of every pixel centred at xs (columns) by ys (rows) for one pass.

    Solved on a coarse grid and interpolated per pixel rather than solved per
    pixel: a KD-tree query for each of a hundred million pixels costs minutes
    and buys nothing, because ground range does not change appreciably within
    a metre. Each grid cell takes the nadir and range of the ping nearest it,
    the same ping its ground range is measured from.

    The grid is anchored at the CRS origin rather than at any raster's corner,
    so a pixel scores the same whichever window it is read in. The merge works
    a window at a time, and a grid that moved with the windows would put a
    seam at every window edge.

    Interpolating rather than taking the nearest cell is what keeps the seam
    between two passes smooth. The chart is 0.019 m/px, so rounding to the
    nearest 1 m cell quantises the boundary into 53-pixel treads - and a pixel
    one tread over gets handed to the worse pass for no reason but the
    rounding. Interpolating moves no pixel value and averages no look: the
    winner is still one pass's sample, untouched. It only puts the boundary
    where the two scores genuinely cross.
    """
    fx = np.asarray(xs, dtype=float) / cell - 0.5
    fy = np.asarray(ys, dtype=float) / cell - 0.5
    i0, j0 = int(np.floor(fx.min())), int(np.floor(fy.min()))
    # One cell past the last floor on each axis, so every pixel has a cell on
    # both sides of it and nothing is clamped at the edge of the grid.
    gx = (np.arange(i0, int(np.floor(fx.max())) + 2) + 0.5) * cell
    gy = (np.arange(j0, int(np.floor(fy.max())) + 2) + 0.5) * cell
    mesh_x, mesh_y = np.meshgrid(gx, gy)
    # Cells beyond the swath score the floor whichever ping is nearest, so the
    # tree can give up on them early. Those misses come back as distance inf
    # and an index one past the end.
    distance, nearest = track["tree"].query(
        np.column_stack((mesh_x.ravel(), mesh_y.ravel())), k=1,
        distance_upper_bound=track["reach"] + 2.0 * cell)
    nearest = np.minimum(nearest, len(track["nadir"]) - 1)
    grid = sonar_quality(distance, track["nadir"][nearest],
                         track["far"][nearest],
                         track.get("plateau_end", SONAR_PLATEAU_END),
                         track.get("far_floor", SONAR_FAR_FLOOR)).reshape(len(gy), len(gx))

    # The grid is separable - one row index per row, one column index per
    # column - so this is four outer-product gathers rather than a resample.
    fr, fc = fy - j0, fx - i0
    r0, c0 = np.floor(fr).astype(int), np.floor(fc).astype(int)
    wr = (fr - r0).astype("float32")[:, None]
    wc = (fc - c0).astype("float32")[None, :]
    return ((1 - wr) * (1 - wc) * grid[np.ix_(r0, c0)]
            + (1 - wr) * wc * grid[np.ix_(r0, c0 + 1)]
            + wr * (1 - wc) * grid[np.ix_(r0 + 1, c0)]
            + wr * wc * grid[np.ix_(r0 + 1, c0 + 1)]).astype("float32")


def _valid_mask(data, nodata=0):
    """(rows, cols) mask of pixels holding data in a (bands, rows, cols) block."""
    if nodata is None:
        return np.ones(data.shape[1:], dtype=bool)
    if isinstance(nodata, float) and np.isnan(nodata):
        return ~np.isnan(data).all(axis=0)
    return (data != nodata).any(axis=0)


def work_windows(width: int, height: int, budget_mb: float = SONAR_MERGE_BUDGET_MB):
    """
    Cover a width x height grid in windows that fit the memory budget.

    Full-width bands wherever a band one block high fits, because a GeoTIFF
    stored in strips - the default - decompresses a whole strip to read any
    part of it, and a full-width band reads each strip once where narrower
    windows would read it once per window across. Narrower windows only when
    the survey is too wide for that. Either way the edges fall on whole
    blocks, so no output tile is written twice.
    """
    from rasterio.windows import Window

    block = SONAR_MERGE_BLOCK
    pixels = max(int(budget_mb * 2 ** 20) // SONAR_MERGE_BYTES_PER_PX, block * block)
    if width * block <= pixels:
        cols, rows = width, pixels // width // block * block
    else:
        cols, rows = pixels // block // block * block, block
    for row in range(0, height, rows):
        for col in range(0, width, cols):
            yield Window(col, row, min(cols, width - col), min(rows, height - row))


def mask_mosaics_to_plateau(tif_paths: list, out_dir: str, tracks: dict,
                            min_quality: float = 1.0, log=print, nodata=0) -> list:
    """
    Copy each mosaic with everything outside the quality plateau blanked.

    Habitat models - RockMapper, and PINGMapper's own substrate prediction -
    read a folder of mosaics and never see the ping metadata, so they have no
    idea where the boat was. That matters more than it sounds: measured on
    Indian Hills, RockMapper's "Bedrock" class spikes to 22.8% in the 20-30 ft
    across-track band and falls to 1.5% beyond 49 ft, and PINGMapper's "Hard
    Bottom" peaks at 47.7% in that same band. A lake bed does not change
    composition according to how far the boat was from it; both models are
    reading the sonar's own brightness falloff as substrate.

    Neither tool can filter that itself - RockMapper's whole parameter set is
    window size, stride, patch-size cleanup and smoothing, none of which touch
    a stripe tens of feet wide. So it has to be done to the input: hand them
    only the band where the imagery is radiometrically consistent, which is the
    same plateau the mosaic merge already scores at 1.0.

    The cost is coverage from any single pass, but at plateau-width line
    spacing a neighbouring line covers what this one loses.
    """
    import shutil

    os.makedirs(out_dir, exist_ok=True)
    out_paths, kept_total, seen_total = [], 0, 0
    mapping = _as_mapping(tif_paths)
    for n, (index, path) in enumerate(mapping.items()):
        track = tracks.get(index)
        out_path = os.path.join(out_dir, os.path.basename(path))
        if track is None:
            log(f"      [{n+1}/{len(mapping)}] no transect {index} - copied unmasked")
            shutil.copy2(path, out_path)
            out_paths.append(out_path)
            continue

        with rasterio.open(path) as src:
            profile = src.profile.copy()
            res_x, res_y = src.res
            cell = quality_cell(max(res_x, res_y))
            with rasterio.open(out_path, "w", **profile) as dst:
                for window in work_windows(src.width, src.height):
                    data = src.read(window=window)
                    valid = _valid_mask(data, nodata)
                    if not valid.any():
                        dst.write(data, window=window)
                        continue
                    ys = src.bounds.top - (np.arange(
                        window.row_off, window.row_off + data.shape[1]) + 0.5) * res_y
                    xs = src.bounds.left + (np.arange(
                        window.col_off, window.col_off + data.shape[2]) + 0.5) * res_x
                    keep = valid & (quality_for(track, xs, ys, cell) >= min_quality)
                    seen_total += int(valid.sum())
                    kept_total += int(keep.sum())
                    dst.write(np.where(keep[None], data, nodata).astype(data.dtype),
                              window=window)
        out_paths.append(out_path)
        log(f"      [{n+1}/{len(mapping)}] {os.path.basename(path)} masked", flush=True)

    share = kept_total / max(seen_total, 1) * 100
    log(f"      kept {kept_total:,} of {seen_total:,} px ({share:.0f}%) at "
        f"quality >= {min_quality}")
    return out_paths


MERGE_METHODS = ("quality", "first", "last", "mean", "median", "min", "max")
SELECTING_METHODS = ("quality", "first", "last")


def merge_sonar_by_quality(tif_paths, out_tif: str, tracks: dict,
                           log=print, budget_mb: float = SONAR_MERGE_BUDGET_MB,
                           nodata=0, bounds=None, method="quality", source_tif=None,
                           window_index=True):
    """
    Passes are never all open at once. Each pass's header is read once to get
    its footprint, the output grid is cut into windows, and every window is
    matched to the passes whose footprint touches it. A window then opens one
    pass at a time, reads the part it needs and closes it, so the open-handle
    count stays at one however many recordings are merged.
    window_index: True writes <out>_windows.csv (window geometry and the keys
    of every pass overlapping it), a path writes it there, False/None skips.

    method: one of MERGE_METHODS. "quality" (default) is described below;
    "first"/"last" take the first/last pass in id order that holds data;
    "mean", "median", "min", "max" combine all overlapping passes per pixel.
    source_tif: optional path for a uint16 raster of which pass won each pixel
    (transect position + 1, 0 = none); only for quality/first/last.

    Merge overlapping mosaics by quality: at each pixel, keep the look from
    the pass that saw that ground best.

    What this replaces is rasterio's default, where the first file in the list
    that happens to hold data wins. That settles a real question - which pass
    saw this ground better - by reference to a sort order, which is no answer
    at all.

    This is where the win is, and it is a large one: over an 8-pass Indian
    Hills survey, 54.4% of the charted ground is seen by two or more passes,
    and on 76.4% of that overlap the best-scoring pass is not the one file
    order would have picked - differing by 54 of 255 on average.

    A pass with no track in `tracks` scores 0.5 everywhere. With no tracks at
    all every pass scores the same, the strict comparison hands each pixel to
    the first file holding data, and that is rasterio's merge exactly - so a
    survey without ping metadata comes through here too, rather than through
    rasterio.merge, which builds the whole mosaic in memory.

    Memory is budget_mb whatever the size of the survey. The output is worked
    through a window at a time (see work_windows), each window written as it
    is finished, so nothing ever spans the whole grid. Holding the winning
    value and score for the whole grid at once costs five bytes a pixel of the
    survey's bounding box: 27 GB for 2 km by 1 km at 0.019 m.

    Each pass is read through a WarpedVRT on the output grid. Where the passes
    share a CRS and pixel size that is a straight copy; where one does not, it
    is still put in the right place, which placing it by rounded offset - the
    way this used to work - did not do.

    There was a second mode that averaged the overlapping looks together,
    weighted by score. It is commented out above and below rather than
    deleted: the idea is sound, the code worked, and only the premise failed.
    See the note on SONAR_BLEND_POWER for the measurement that retired it.

    The residual registration error between passes is around one to four metres
    (from the coarse-scale correlation above, and consistent with the metadata's
    own e_err_m/n_err_m of up to 1.2 m). That is fine for seabed texture, which
    has no fixed phase to smear, and it is the reason this is not carried any
    further: a discrete target seen twice will thicken slightly rather than
    sharpen.
    """
    from rasterio.vrt import WarpedVRT
    from rasterio.warp import transform_bounds
    from rasterio.windows import Window

    # tif_paths is {transect_id: path} or a list (transect id = position).
    # Keys select each pass's track, so a transect skipped for lack of chunks
    # cannot shift the others onto the wrong trackline.
    if method not in MERGE_METHODS:
        raise ValueError(f"method must be one of {MERGE_METHODS}, got {method!r}")
    if source_tif and method not in SELECTING_METHODS:
        raise ValueError("source_tif needs method quality, first or last")
    combine = method not in SELECTING_METHODS
    mapping = _as_mapping(tif_paths)
    ids, tif_list = list(mapping.keys()), list(mapping.values())
    heads = []
    for p in tif_list:
        with rasterio.open(p) as s:
            heads.append((s.res, s.crs, s.count, s.dtypes[0], tuple(s.bounds)))
    nsrc = len(tif_list)
    try:
        res_x, res_y = heads[0][0]
        crs, count, dtype = heads[0][1], heads[0][2], heads[0][3]
        pass_bounds = [h[4] if h[1] == crs else transform_bounds(h[1], crs, *h[4])
                       for h in heads]
        # bounds=(west, south, east, north) in the mosaic CRS restricts the
        # output to a swatch; passes are only read where they overlap it.
        extent = bounds if bounds is not None else (
            min(b[0] for b in pass_bounds), min(b[1] for b in pass_bounds),
            max(b[2] for b in pass_bounds), max(b[3] for b in pass_bounds))
        west, north = extent[0], extent[3]
        width = int(round((extent[2] - west) / res_x))
        height = int(round((north - extent[1]) / res_y))
        if width <= 0 or height <= 0:
            raise ValueError("merge extent is empty")
        bounds = pass_bounds
        transform = rasterio.transform.from_origin(west, north, res_x, res_y)
        cell = quality_cell(max(res_x, res_y))
        windows = list(work_windows(width, height, budget_mb))
        log(f"      Output grid {width:,} x {height:,} px at {res_x:.4f} m, "
            f"in {len(windows):,} window(s) of at most "
            f"{windows[0].width:,} x {windows[0].height:,}", flush=True)
        if method != "quality":
            log(f"      method: {method}", flush=True)
        elif tracks:
            log("      best look wins", flush=True)
            for index in ids:
                if index not in tracks:
                    log(f"      transect {index} not in the "
                        f"metadata - scoring it flat")
        else:
            log("      nothing to judge the passes by - first file wins", flush=True)

        def read_pass(index, win):
            with rasterio.open(tif_list[index]) as s, \
                 WarpedVRT(s, crs=crs, transform=transform, width=width,
                           height=height, resampling=Resampling.nearest,
                           src_nodata=nodata, nodata=nodata) as vrt:
                return vrt.read(window=win)

        overlap = []
        for win in windows:
            w0 = west + win.col_off * res_x
            w1 = w0 + win.width * res_x
            n1 = north - win.row_off * res_y
            n0 = n1 - win.height * res_y
            overlap.append([i for i, b in enumerate(bounds)
                            if b[0] < w1 and b[2] > w0 and b[1] < n1 and b[3] > n0])
        if window_index:
            idx_path = (window_index if isinstance(window_index, str)
                        else os.path.splitext(out_tif)[0] + "_windows.csv")
            import csv
            with open(idx_path, "w", newline="") as fh:
                wr = csv.writer(fh)
                wr.writerow(["window", "col_off", "row_off", "width", "height",
                             "west", "south", "east", "north", "n_passes", "passes"])
                for k, (win, ov) in enumerate(zip(windows, overlap)):
                    w0 = west + win.col_off * res_x
                    n1 = north - win.row_off * res_y
                    wr.writerow([k, int(win.col_off), int(win.row_off),
                                 int(win.width), int(win.height), w0,
                                 n1 - win.height * res_y, w0 + win.width * res_x, n1,
                                 len(ov), ";".join(str(ids[i]) for i in ov)])
            log(f"      Window index: {idx_path}", flush=True)

        won = np.zeros(nsrc, dtype=np.int64)
        pulse = Progress(len(windows), "merge windows")
        out_nodata = 0 if nodata is None else nodata
        with rasterio.open(out_tif, "w", driver="GTiff", height=height, width=width,
                           count=count, dtype=dtype, crs=crs, transform=transform,
                           nodata=nodata, compress="lzw", tiled=True,
                           blockxsize=SONAR_MERGE_BLOCK, blockysize=SONAR_MERGE_BLOCK,
                           BIGTIFF="IF_SAFER", sparse_ok=True) as dst, \
             (rasterio.open(source_tif, "w", driver="GTiff", height=height, width=width,
                            count=1, dtype="uint16", crs=crs, transform=transform,
                            nodata=0, compress="lzw", tiled=True,
                            blockxsize=SONAR_MERGE_BLOCK, blockysize=SONAR_MERGE_BLOCK,
                            BIGTIFF="IF_SAFER", sparse_ok=True)
              if source_tif else contextlib.nullcontext()) as src_dst:
            for wi, window in enumerate(windows):
                top, left = int(window.row_off), int(window.col_off)
                # The running best value, the score that won it, and which
                # pass it came from - for this window only.
                shape = (int(window.height), int(window.width))
                best = np.full((count,) + shape, out_nodata, dtype=dtype)
                best_q = np.zeros(shape, dtype="float32")
                who = np.zeros(shape, dtype="uint16")
                stack = []
                if method in ("mean", "median"):
                    acc = np.zeros((count,) + shape, dtype="float64")
                    n_acc = np.zeros(shape, dtype="int32")
                xs = west + (np.arange(left, left + shape[1]) + 0.5) * res_x
                ys = north - (np.arange(top, top + shape[0]) + 0.5) * res_y

                for index in overlap[wi]:
                    b = bounds[index]
                    # Only the part of the window this pass reaches: a narrow
                    # pass crossing a wide window costs its own area, not the
                    # window's.
                    c0 = max(left, int(math.floor((b[0] - west) / res_x)))
                    c1 = min(left + shape[1], int(math.ceil((b[2] - west) / res_x)))
                    r0 = max(top, int(math.floor((north - b[3]) / res_y)))
                    r1 = min(top + shape[0], int(math.ceil((north - b[1]) / res_y)))
                    if c0 >= c1 or r0 >= r1:
                        continue
                    data = read_pass(index, Window(c0, r0, c1 - c0, r1 - r0))
                    valid = _valid_mask(data, nodata)
                    if not valid.any():
                        continue
                    rows = slice(r0 - top, r1 - top)
                    cols = slice(c0 - left, c1 - left)

                    if combine:
                        if method == "mean":
                            n_acc[rows, cols] += valid
                            acc[:, rows, cols] += np.where(valid, data, 0)
                        elif method == "median":
                            full = np.full((count,) + shape, np.nan, dtype="float32")
                            full[:, rows, cols] = np.where(valid, data, np.nan)
                            stack.append(full)
                        else:
                            view_v = best[:, rows, cols]
                            seen = best_q[rows, cols] > 0
                            # Multi-band: compare the band sum so a pixel keeps one pass's bands.
                            new_s = data.astype("float64").sum(axis=0)
                            old_s = view_v.astype("float64").sum(axis=0)
                            better = new_s > old_s if method == "max" else new_s < old_s
                            take = valid & (~seen | better)
                            view_v[:, take] = data[:, take]
                            best_q[rows, cols] = np.maximum(best_q[rows, cols], valid)
                        continue

                    if method == "first":
                        q = np.full(valid.shape, nsrc - index, dtype="float32")
                    elif method == "last":
                        q = np.full(valid.shape, index + 1, dtype="float32")
                    elif tracks.get(ids[index]) is None:
                        q = np.full(valid.shape, 0.5, dtype="float32")
                    else:
                        q = quality_for(tracks[ids[index]], xs[cols], ys[rows], cell)

                    view_v = best[:, rows, cols]
                    view_q = best_q[rows, cols]
                    view_w = who[rows, cols]
                    wins = valid & (q > view_q)
                    view_v[:, wins] = data[:, wins]
                    view_q[wins] = q[wins]
                    view_w[wins] = index

                # Blending divided the weighted sum by its weight here. 0 is
                # the nodata value, so an uncovered pixel had to stay 0 and a
                # covered one had to stay off it - rounding up into 1 rather
                # than down to nothing, or the faintest real backscatter reads
                # as no survey at all:
                #
                #   with np.errstate(invalid="ignore", divide="ignore"):
                #       best = np.where(best_q > 0, best / np.maximum(best_q, 1e-6), 0.0)
                #   best = np.where(best_q > 0, np.maximum(np.rint(best), 1), 0).astype("uint8")

                if method == "mean":
                    n_pix = np.maximum(n_acc, 1)
                    best = np.where(n_acc > 0, np.rint(acc / n_pix) if np.issubdtype(np.dtype(dtype), np.integer)
                                    else acc / n_pix, out_nodata).astype(dtype)
                    best_q = n_acc.astype("float32")
                elif method == "median" and stack:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", RuntimeWarning)
                        med = np.nanmedian(np.stack(stack), axis=0)
                    ok = ~np.isnan(med)
                    best = np.where(ok, np.rint(med) if np.issubdtype(np.dtype(dtype), np.integer)
                                    else med, out_nodata).astype(dtype)
                    best_q = ok.any(axis=0).astype("float32")
                covered = best_q > 0
                # A window no pass reaches is left unwritten; the file is
                # sparse and reads it back as 0.
                if covered.any():
                    dst.write(best, window=window)
                    if method in SELECTING_METHODS:
                        won += np.bincount(who[covered], minlength=nsrc)
                        if src_dst is not None:
                            src_dst.write(np.where(covered, who + 1, 0).astype("uint16"),
                                          1, window=window)
                pulse.step()
        pulse.finish()
    finally:
        pass

    if method in SELECTING_METHODS:
        for index, path in enumerate(tif_list):
            log(f"      [{ids[index]}] {os.path.basename(path)}: "
                f"{int(won[index]):,} px kept")
    if method in SELECTING_METHODS:
        how = "quality" if (tracks and method == "quality") else \
            ("file order" if method == "quality" else method)
        log(f"      {int(won.sum()):,} px carry data, decided by {how}")
    log(f"      Saved: {out_tif}  ({os.path.getsize(out_tif) / 1e6:,.0f} MB)")


