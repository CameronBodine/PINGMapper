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
cd C:\users\Cam\MyPythonRepos
``` 

## Step 3

Stash any changes you may have made since downloading PING-Mapper (i.e. editing `main.py` script):
```
git stash
```

## Step 4

Download the latest updates:

```
git fetch
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
