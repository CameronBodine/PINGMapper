---
layout: default
title: Troubleshooting
nav_order: 5
---

# Troubleshooting
{: .no_toc }

Use this page when `PINGMapper`, `PINGInstaller`, or `PINGWizard` is not behaving as expected. If you cannot resolve the problem here, please submit an [Issue](https://github.com/CameronBodine/PINGMapper/issues/new/choose).
{: .fs-6 .fw-300 }

<details open markdown="block">
  <summary>
    Table of contents
  </summary>
  {: .text-delta }
1. TOC
{:toc}
</details>

## Start Here

Before digging into a specific problem, confirm the recommended workflow:

1. Install [Miniforge](./gettingstarted/Installation.md).
2. Run [PINGInstaller](./gettingstarted/Installation.md#step-4---run-pinginstaller).
3. Launch [PINGWizard](./gettingstarted/PINGWizard.md).
4. Run the [small dataset test](./gettingstarted/Testing.md#small-dataset-test).

If the small dataset test passes, your installation is usually healthy and the problem is more likely tied to a specific sonar file, processing setting, or output location.

## PINGInstaller or PINGWizard Will Not Launch

### Symptom

- `python -m pinginstaller` does nothing or fails.
- The PINGWizard shortcut does not open.
- `conda run -n ping python -m pingwizard` fails.

### What to try

1. Re-open `Miniforge Prompt` and rerun the installation steps from [Installation](./gettingstarted/Installation.md).
2. Reinstall `PINGInstaller` in `base`:

```bash
pip install pinginstaller -U
```

3. Rerun the installer:

```bash
python -m pinginstaller
```

4. If the shortcut fails, try launching directly from the prompt:

```bash
conda run -n ping python -m pingwizard
```

### If that fails

Run the [small dataset test](./gettingstarted/Testing.md#small-dataset-test) if you can reach PINGWizard. If you cannot, open an issue and include the full terminal output.

## ModuleNotFoundError

### Symptom

You receive a `ModuleNotFoundError` during installation, launch, or while running the included tests.

### Likely cause

The `ping` environment is missing a dependency, or the wrong Python environment is being used.

### What to try

1. Make sure you are using the `ping` environment created by `PINGInstaller`.
2. If the error names a specific package, install that package into `ping`.

Example:

```bash
conda activate ping
conda install sympy
```

If `conda install` fails, try:

```bash
pip install sympy
```

3. Rerun the [small dataset test](./gettingstarted/Testing.md#small-dataset-test).

### Example error

One previously reported example is shown [here](https://github.com/CameronBodine/PINGMapper/issues/105#issue-2093782805).

### If that fails

Submit an issue and include the full traceback, your operating system, and whether you installed with Miniforge + PINGInstaller.

## The Small Dataset Test Fails

### Symptom

The `Small Dataset` button in `PINGWizard` fails, closes early, or does not create outputs.

### What to try

1. Rerun the test from [Testing](./gettingstarted/Testing.md).
2. Confirm the output folder was created on a local drive.
3. If the failure mentions a missing package, follow [ModuleNotFoundError](#modulenotfounderror).
4. If the failure happens only on the large dataset test, reduce other concurrent load on your computer and rerun the small test first.

### If that fails

Open an issue and include whether the small test, large test, or both are failing.

## My Sonar File Does Not Load

### Symptom

- The selected recording does not appear in the GUI as expected.
- Processing starts but immediately fails.
- A Humminbird recording appears incomplete.

### What to try

1. Confirm the file type is supported.
2. For Humminbird recordings, make sure the `.DAT` file has a same-named folder beside it containing the `SON` and `IDX` files. See [Running](./gettingstarted/Running.md#note-on-sonar-file-structure).
3. Try the same workflow on the included test data first to confirm the installation is healthy.
4. If the file came from a cloud-synced folder, copy it to a fully local folder before processing.

### If that fails

Open an issue and include the sonar format, manufacturer, and a screenshot of the input folder structure.

## No Outputs Were Created

### Symptom

Processing ran, but the expected project folder or exported files are missing.

### What to try

1. Verify the selected `Output Folder` and `Project Name` in `PINGWizard`.
2. Check whether `Overwrite Existing Project` was enabled when rerunning a project.
3. Confirm you are writing to a local drive rather than OneDrive, Google Drive, or another cloud-synced path.
4. Look in the generated project `logs` folder for the latest log file.

### If that fails

Submit an issue and attach the log file from the project `logs` directory.

## Processing Freezes or Runs Out of Memory

### Symptom

`PINGMapper` becomes very slow, freezes, or crashes during processing.

### Likely cause

Thread count is too aggressive for the available RAM or the dataset is large.

### What to try

1. Lower `Thread Count` in the GUI.
2. Start with `0.5` to `0.75` of available CPU threads, as suggested in [Running](./gettingstarted/Running.md#step-4).
3. Close other memory-intensive applications.
4. Run the small test first to verify the installation before processing a large survey.

### If that fails

Open an issue and include dataset size, thread count used, and when the freeze occurs.

## Exports Fail on OneDrive or Other Cloud Folders

### Symptom

Processing appears to fail during export, or outputs are incomplete when writing to a synced folder.

### What to try

Write outputs to a local folder instead. This is already noted in [Running](./gettingstarted/Running.md#step-3).

### If that fails

Try a simple local path such as `C:\PINGMapper_Outputs` and rerun the workflow.

## What to Include in an Issue Report

To make troubleshooting faster, include:

- Operating system.
- Sonar file format and manufacturer.
- Whether installation was done with Miniforge + PINGInstaller.
- Whether the small dataset test passes.
- The exact error message or traceback.
- The relevant log file from the project `logs` directory.
- Screenshots of the GUI settings or input folder structure when relevant.