import sys
from pathlib import Path

# Ensure local repo package is imported when running this script directly.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pingmapper.doWork import doWork

params = {
    # ------------------------------------------------------------------
    # Project / Runtime
    # ------------------------------------------------------------------
    "project_mode": 1,
    "threadCnt": 0,

    # ------------------------------------------------------------------
    # Survey / Sonar Basics
    # ------------------------------------------------------------------
    "tempC": 12.0,
    "nchunk": 500,
    "cropRange": 0,

    # ------------------------------------------------------------------
    # Navigation + Filtering
    # ------------------------------------------------------------------
    "aoi": False,
    "max_heading_deviation": 0,
    "max_heading_distance": 0,
    "min_speed": 0,
    "max_speed": 0,
    "time_table": False,

    # dqLog event-state filtering
    # Set dq_table and field names to enable; keep values can be list or csv string.
    "dq_table": False,
    "dq_time_field": False,
    "dq_flag_field": False,
    "dq_keep_values": False,
    "dq_src_utc_offset": 0.0,
    "dq_target_utc_offset": 0.0,
    "dq_time_offset": 0.0,

    # ------------------------------------------------------------------
    # Input Handling
    # ------------------------------------------------------------------
    "exportUnknown": False,
    "fixNoDat": False,

    # ------------------------------------------------------------------
    # Georeferencing / Resolution
    # ------------------------------------------------------------------
    "pix_res_son": 0.1,
    "pix_res_map": 0,
    "x_offset": 0.0,
    "y_offset": 0.0,

    # ------------------------------------------------------------------
    # Intensity / Tone
    # ------------------------------------------------------------------
    "egn": False,
    "egn_stretch": 0,
    "egn_stretch_factor": 1.0,

    # ------------------------------------------------------------------
    # Sonogram Exports
    # ------------------------------------------------------------------
    "wcp": False,
    "wcm": False,
    "wcr": False,
    "wco": False,
    "sonogram_colorMap": "Greys_r",
    "mask_shdw": False,
    "tileFile": ".png",
    "spdCor": False,
    "maxCrop": False,

    # ------------------------------------------------------------------
    # Depth / Shadows
    # ------------------------------------------------------------------
    "remShadow": 0,
    "detectDep": 0,
    "smthDep": False,
    "adjDep": 0.0,
    "pltBedPick": False,

    # ------------------------------------------------------------------
    # Rectification / Mosaics
    # ------------------------------------------------------------------
    "rect_wcp": False,
    "rect_wcr": False,
    "rubberSheeting": False,
    "rectMethod": "Heading",
    "rectInterpDist": 50,
    "son_colorMap": "Greys",
    "mosaic_nchunk": 0,

    # ------------------------------------------------------------------
    # Substrate Mapping
    # ------------------------------------------------------------------
    "pred_sub": False,
    "pltSubClass": False,
    "map_sub": False,
    "export_poly": False,
    "map_class_method": "max",
    "map_predict": 0,

    # ------------------------------------------------------------------
    # Final Exports
    # ------------------------------------------------------------------
    "mosaic": 0,
    "map_mosaic": 0,
    "banklines": False,
    "coverage": False,
}

results = doWork(
    in_dir=r"C:\Users\cbodine\Downloads\NewRiver\SonarRecording",
    out_dir=r"C:\Users\cbodine\Downloads\NewRiver",
    proj_name=None,
    batch=True,
    preserve_subdirs=False,
    prefix="",
    suffix="",
    params=params,
)

print(results)
