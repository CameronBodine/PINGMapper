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
