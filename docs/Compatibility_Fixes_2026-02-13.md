# Compatibility Fixes (2026-02-13)

This note summarizes compatibility hardening completed for recent pandas/numpy/joblib behavior changes.

## Core runtime fixes

- Added safe parallel worker resolution helper: `safe_n_jobs(task_count, thread_count)` in `pingmapper/funcs_common.py`.
- Replaced fragile `Parallel(n_jobs=np.min([len(...), threadCnt]))` patterns in core runtime modules.
- Fixed pandas chained assignment hotspots to direct `.loc[row_mask, col] = value` writes.
- Replaced positional-usage `loc` with `iloc` where label-based indexing could fail.
- Restored robust heading filtering and chunk reassignment logic in `pingmapper/class_sonObj.py`:
  - Heading filter now handles full-window spread and end-window coverage.
  - Empty-data guards prevent `IndexError` in chunk reassignment.

## Utility/workflow fixes

- Applied safe `n_jobs` handling to utility workflows and draft scripts.
- Updated positional `.loc[0]` usages to `.iloc[0]` in summary workflows where row-position semantics were intended.

## Key files updated

- `pingmapper/funcs_common.py`
- `pingmapper/main_readFiles.py`
- `pingmapper/main_mapSubstrate.py`
- `pingmapper/main_rectify.py`
- `pingmapper/funcs_rectify.py`
- `pingmapper/class_portstarObj.py`
- `pingmapper/class_sonObj.py`
- `pingmapper/class_sonObj_nadirgaptest.py`
- `pingmapper/utils/main_mosaic_transects.py`
- `pingmapper/utils/RawEGN_avg_predictions.py`
- `pingmapper/utils/DRAFT_Workflows/avg_predictions_Mussel_WBL.py`
- `pingmapper/utils/Substrate_Summaries/summarize_project_substrate.py`
- `pingmapper/utils/Substrate_Summaries/02_gen_summary_stamp_shps.py`

## Validation performed

- Read-stage smoke test passed on:
  - `Z:\miniforge3\envs\ping\exampleData\Test-Small-DS.DAT`
- Full end-to-end smoke test passed (read + rectify + map) on the same dataset.

## Environment note

- In this shell context, `conda run -p Z:\miniforge3\envs\ping --no-capture-output python ...` was reliable.
- Direct `Z:\miniforge3\envs\ping\python.exe` invocation showed interpreter crash behavior in this session context.