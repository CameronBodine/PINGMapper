## Run PINGMapper Programmatically

This guide shows how to call `doWork` from your own Python script to process a
single sonar file, a batch directory, or an explicit list of files.

### Prerequisites

- PINGMapper is installed or the repo is on `PYTHONPATH`.
- You have a valid sonar file (e.g., `.DAT`, `.sl2`, `.sl3`, `.RSD`, `.svlog`, `.jsf`, `.xtf`, `.sdf`).
- You have write access to the output folder.


### Minimal Single-File Example

```python
from pingmapper.doWork import doWork

params = {
	# Project / Runtime
	"project_mode": 0,
	"threadCnt": 0,

	# Survey / Sonar Basics
	"tempC": 12.0,
	"nchunk": 500,
	"cropRange": 0,

	# Navigation + Filtering
	"aoi": False,
	"max_heading_deviation": 0,
	"max_heading_distance": 0,
	"min_speed": 0,
	"max_speed": 0,
	"time_table": False,

	# dqLog event-state filtering
	"dq_table": False,
	"dq_time_field": False,
	"dq_flag_field": False,
	"dq_keep_values": False,
	"dq_src_utc_offset": 0.0,
	"dq_target_utc_offset": 0.0,
	"dq_time_offset": 0.0,

	# Input handling
	"exportUnknown": False,
	"fixNoDat": False,

	# Georeferencing / Resolution
	"pix_res_son": 0,
	"pix_res_map": 0,
	"x_offset": 0.0,
	"y_offset": 0.0,

	# Intensity / Tone
	"egn": False,
	"egn_stretch": 0,
	"egn_stretch_factor": 1.0,

	# Sonogram Exports
	"wcp": True,
	"wcm": False,
	"wcr": False,
	"wco": False,
	"sonogram_colorMap": "Greys_r",
	"mask_shdw": False,
	"tileFile": ".png",
	"spdCor": False,
	"maxCrop": False,

	# Waterfall Image / Video Exports
	"waterfall_ss_image": False,
	"waterfall_ss_video": False,
	"waterfall_di_image": False,
	"waterfall_di_video": False,
	"waterfall_video_fps": 10,
	"waterfall_video_resolution": "1080p",
	"waterfall_mode_selection": "auto",
	"waterfall_window_stride": 64,

	# Depth / Shadows
	"remShadow": 0,
	"detectDep": 0,
	"smthDep": False,
	"adjDep": 0.0,
	"pltBedPick": False,

	# Rectification / Mosaics
	"rect_wcp": True,
	"rect_wcr": False,
	"rubberSheeting": False,
	"rectMethod": "Heading",
	"rectInterpDist": 50,
	"son_colorMap": "Greys",
	"mosaic_nchunk": 0,

	# Substrate Mapping
	"pred_sub": False,
	"pltSubClass": False,
	"map_sub": False,
	"export_poly": False,
	"map_class_method": "max",
	"map_predict": 0,

	# Final Exports
	"mosaic": 0,
	"map_mosaic": 0,
	"banklines": False,
	"coverage": False,
}

results = doWork(
	in_file=r"Z:\path\to\Rec00002.DAT",
	out_dir=r"Z:\path\to\output_root",
	proj_name="MyProject",
	batch=False,
	params=params,
)

print(results)
```

### Waterfall Export Parameters

Use these parameters in `params` to generate waterfall images and videos from
exported non-rectified sonogram tiles.

- `waterfall_ss_image`: export a combined side-scan waterfall image.
- `waterfall_ss_video`: export a combined side-scan waterfall video.
- `waterfall_di_image`: export down-imaging waterfall images.
- `waterfall_di_video`: export down-imaging waterfall videos.
- `waterfall_video_fps`: video frame rate.
- `waterfall_video_resolution`: output video resolution preset.
- `waterfall_mode_selection`: which tile product(s) to use for waterfall generation.
- `waterfall_window_stride`: scroll step in pixels per frame.

Supported values:

- `waterfall_video_resolution`:
	- `"4K"`
	- `"1080p"`
	- `"720p"`
	- `"4xxp"`

- `waterfall_mode_selection`:
	- `"auto"`: use the tile export modes currently enabled in `wcp`, `wcm`, `wcr`, `wco`
	- `"wcp"`: use water-column-present tiles only
	- `"src"`: use slant-range-corrected tiles only
	- `"wcp+src"`: generate waterfall outputs for both WCP and SRC

Behavior:

- Side-scan waterfall generation uses the exported images from the `wcp` / `src`
	folders under the side-scan beam directories.
- Both side-scan beams are rotated 90 degrees counter-clockwise.
- Port is additionally flipped horizontally so port and star meet at the nadir.
- Side-scan waterfall video scrolls upward so new pings appear at the top and
	older pings leave the bottom.
- Down-imaging waterfall videos scroll horizontally using the configured stride.
- Chunk images are range-aware: tile size is rescaled using per-chunk range
	metadata before stitching.

### Waterfall Example

```python
from pingmapper.doWork import doWork

params = {
	"project_mode": 1,
	"tempC": 12.0,
	"nchunk": 500,

	# Export source sonogram products used by waterfall generation
	"wcp": True,
	"wcm": False,
	"wcr": True,
	"wco": False,
	"tileFile": ".png",
	"spdCor": False,
	"maxCrop": False,

	# Waterfall exports
	"waterfall_ss_image": True,
	"waterfall_ss_video": True,
	"waterfall_di_image": True,
	"waterfall_di_video": True,
	"waterfall_video_fps": 10,
	"waterfall_video_resolution": "1080p",
	"waterfall_mode_selection": "wcp+src",
	"waterfall_window_stride": 64,
}

results = doWork(
	in_file=r"Z:\path\to\Rec00002.DAT",
	out_dir=r"Z:\path\to\output_root",
	proj_name="WaterfallDemo",
	batch=False,
	params=params,
)

print(results)
```

### Waterfall Output Layout

Waterfall outputs are written inside the project folder:

- `waterfall_exports/sidescan/<mode>/`
- `waterfall_exports/down_imaging/<mode>/`

Files:

- Side-scan:
	- `waterfall.png`
	- `waterfall_scroll_t2b.mp4`
- Down-imaging:
	- `<beam>_waterfall.png`
	- `<beam>_waterfall_scroll.mp4`

Notes:

- Side-scan exports are combined across port and star into one waterfall per mode.
- Down-imaging exports are beam-specific to avoid overwriting when two down-looking
	channels are present.

### dqLog Filtering Parameters

Use these parameters in `params` to filter sonar records from a data-quality log.

- `dq_table`: Path to dqLog CSV file.
- `dq_time_field`: Timestamp column name in dqLog.
- `dq_flag_field`: Flag/status column name in dqLog.
- `dq_keep_values`: List of values to keep (for example `['good', 'ok', 'use']`).
- `dq_src_utc_offset`: UTC offset (hours) for dqLog timestamps.
- `dq_target_utc_offset`: UTC offset (hours) for sonar metadata timestamps.
- `dq_time_offset`: Additional manual time offset in seconds applied to sonar timestamps.

Behavior:

- dqLog rows are treated as event-state updates over time (not exact timestamp matches).
- State is carried forward from each dqLog event until the next event.
- dqLog filtering runs first, before heading/speed/AOI/time-table filters.


### Batch Script (Recommended)

For repeatable batch runs, use the ready-to-edit script at
`pingmapper/nonGUI_batch_main.py`.

Start by updating these values:

- `in_dir`: root folder that contains your sonar recordings.
- `out_dir`: output root where project folders will be created.
- `project_mode`: usually `1` to overwrite existing batch outputs.
- `prefix` / `suffix`: optional naming controls for generated project folders.
- `preserve_subdirs`: set `True` to mirror input folder structure under `out_dir`.
- dq settings (`dq_table`, `dq_time_field`, `dq_flag_field`, `dq_keep_values`, offsets) if using dq filtering.

Then run:

```python
python pingmapper/nonGUI_batch_main.py
```


### Batch Directory Example
### Explicit List of Files Example

```python
from pingmapper.doWork import doWork

params = {"project_mode": 1, "nchunk": 500}
file_list = [r"Z:\path\to\file1.DAT", r"Z:\path\to\file2.sl2"]

results = doWork(
	in_files=file_list,
	out_dir=r"Z:\path\to\output_root",
	batch=True,
	params=params,
)

print(results)
```

```python
from pingmapper.doWork import doWork

params = {
	"project_mode": 1,
	"nchunk": 500,
	"tempC": 12.0,
	"rect_wcr": True,
}

results = doWork(
	in_dir=r"Z:\path\to\survey_folder",
	out_dir=r"Z:\path\to\output_root",
	prefix="Survey_",
	suffix="_2025",
	batch=True,
	params=params,
)

print(results)
```


### Notes

- `project_mode`:
	- `0` = create new project (fails if it already exists)
	- `1` = overwrite existing project
	- `2` = update existing project
- Output logs are written to `projDir\logs\log_YYYY-MM-DD_HHMM.txt`.
- `doWork` returns a list of dicts with `inFile`, `projDir`, `logfilename`, and `success`.
- You can use `in_file` (single file), `in_dir` (batch directory), or `in_files` (explicit list) as input. For batch or list processing, set `batch=True`.
- The `params` dictionary accepts many additional keys for advanced processing. See the `doWork` docstring for all supported options.
