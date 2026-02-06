## Run PINGMapper Programmatically

This guide shows how to call `doWork` from your own Python script to process a
single sonar file or a batch directory.

### Prerequisites

- PINGMapper is installed or the repo is on `PYTHONPATH`.
- You have a valid sonar file (e.g., `.DAT`, `.sl2`, `.sl3`, `.RSD`, `.svlog`).
- You have write access to the output folder.

### Minimal Single-File Example

```python
from pingmapper.doWork import doWork

params = {
	"project_mode": 0,
	"tempC": 12.0,
	"nchunk": 500,
	"cropRange": 0,
	"exportUnknown": False,
	"fixNoDat": False,
	"threadCnt": 0,
	"pix_res_son": 0,
	"pix_res_map": 0,
	"x_offset": 0.0,
	"y_offset": 0.0,
	"egn": False,
	"egn_stretch": 0,
	"egn_stretch_factor": 1.0,
	"wcp": True,
	"wcm": False,
	"wcr": False,
	"wco": False,
	"sonogram_colorMap": "Greys_r",
	"mask_shdw": False,
	"tileFile": ".png",
	"spdCor": False,
	"maxCrop": False,
	"remShadow": 0,
	"detectDep": 0,
	"smthDep": False,
	"adjDep": 0.0,
	"pltBedPick": False,
	"rect_wcp": True,
	"rect_wcr": False,
	"rubberSheeting": False,
	"rectMethod": "Heading",
	"rectInterpDist": 50,
	"son_colorMap": "Greys",
	"mosaic_nchunk": 0,
	"pred_sub": False,
	"pltSubClass": False,
	"map_sub": False,
	"export_poly": False,
	"map_class_method": "max",
	"map_predict": 0,
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

### Batch Directory Example

```python
from pingmapper.doWork import doWork

params = {"project_mode": 1
		  "nchunk": 500, 
          "tempC": 12.0,
		  "rect_wcr": True}

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
