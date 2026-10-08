"""Script-driven sonar mosaic merge (no GUI): edit the settings, then run.

Merges the per-recording mosaics already written by PINGMapper (rect_wcr or
rect_wcp) into one GeoTIFF, choosing the best look per pixel.
Same engine as `python -m pingmapper mosaic`.
"""
from pingmapper.main_mosaic import merge_mosaics

# Folder holding the PINGMapper outputs (each <project>/sonar_mosaic is searched),
# or set MANIFEST to a CSV with columns tif, meta_csv (optional key, transect).
ROOT = r"C:\Users\cbodine\Downloads\NewRiver"
MANIFEST = None
OUT_TIF = None          # None -> <ROOT>/merged_mosaic/merged_rect_<KIND>_<METHOD>.tif

KIND = "wcr"            # "wcr" water column removed, "wcp" water column present
METHOD = "quality"      # quality, first, last, mean, median, min, max
COLORMAP = None         # matplotlib name (e.g. "Greys", "viridis") or None
WORKERS = None          # None -> min(4, CPUs)
SOURCE = False          # also write which-pass-won raster + key CSV
SWATCH = None           # (easting, northing, size_m) to merge a test area only

# Seam softening (quality method only)
FEATHER = 0.0           # 0 = hard seams; 0.05-0.2 blends passes with close scores
FEATHER_MODE = "blend"  # "blend", or "lowpass" to keep best-pass texture
FEATHER_SIGMA = 2.0     # lowpass Gaussian sigma in metres

# Quality scoring
PARAMS = {
    "plateau_end": 0.6,       # fraction of max range fully trusted
    "far_floor": 0.35,        # trust at the farthest pixels
    "nadir_per_depth": 1.0,   # untrusted strip under the boat, x depth
    "depth_window": 51,       # pings in the rolling-median depth
    "range_smooth": 1,        # pings in the rolling-median max range (1 = off)
    "edge_feather": 0.0,      # metres over which trust tapers at the far edge
}

if __name__ == "__main__":
    out = merge_mosaics(
        root=ROOT, manifest=MANIFEST, out_tif=OUT_TIF, kind=KIND, method=METHOD,
        params=PARAMS, swatch=SWATCH, source=SOURCE, workers=WORKERS,
        feather=FEATHER, colormap=COLORMAP,
        feather_mode=FEATHER_MODE, feather_sigma=FEATHER_SIGMA,
    )
    print(out)
