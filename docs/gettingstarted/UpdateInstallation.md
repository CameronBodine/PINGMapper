---
layout: default
title: Update Installation
nav_order: 2
parent: Getting Started

nav_exclude: false

---

# Updating PING-Mapper Installation to Latest Version

If you have installed a previous version of PING-Mapper, follow these instructions to update to the latest version.

## Step 1

Open the Anaconda Powershell prompt and run the following:
```
conda update -n base conda
conda clean --all
python.exe -m pip install --upgrade pip
```

## Step 2

Navigate to the location where you previously installed PING-Mapper:
```
cd C:\users\Cam\MyPythonRepos\PINGMapper
``` 

## Step 3

Stash any changes you may have made since downloading PING-Mapper (i.e. editing `main.py` script):
```
git stash
```

## Step 4

Download the latest updates:

```
git pull
```

If PINGMapper has new updates, you should see an indication of that in the console outpute:
```
(base) PS E:\Python\PINGMapper> git pull
Updating 0dce260..e5ac226
Fast-forward
 gui_main.py                         |  12 +-
 gui_main_batchDirectory.py          | 168 ++++++-------
 main.py                             |  56 ++---
 main_batchDirectory.py              | 257 ++++++++++----------
 src/class_rectObj.py                |  11 +-
 src/class_sonObj.py                 | 382 ++++++++++++++++--------------
 src/funcs_common.py                 |  29 +++
 src/main_readFiles.py               | 142 +++++------
 test_PINGMapper.py                  |  42 ++--
 utils/avg_predictions_Mussel_WBL.py | 454 ++++++++++++++++++++++++++++++++++++
 10 files changed, 1044 insertions(+), 509 deletions(-)
 create mode 100644 utils/avg_predictions_Mussel_WBL.py
 ```

 If there weren't any updates, you should see:
 ```
(base) PS E:\Python\PINGMapper> git pull
Already up to date.
 ```


## Step 5

Activate the `ping` virtual environment:

```
conda activate ping
```

## Step 6

Update PING-Mapper dependencies:

```
conda env update --file conda/PINGMapper.yml --prune
```

## All Done!
