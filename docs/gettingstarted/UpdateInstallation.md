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

Navigate to the location where you previously installed PING-Mapper:
```
cd C:\users\Cam\MyPythonRepos
``` 

## Step 2

Stash any changes you may have made since downloading PING-Mapper (i.e. editing `main.py` script):
```
git stash
```

- Now let's run a [test](./Testing.md) to make sure everything is functioning as expected.

## Step 3

Download the latest updates:

```
git fetch
```

## Step 4

Activate the `ping` virtual environment:

```
conda activate ping
```

## Step 5

Update PING-Mapper dependencies:

```
conda env update --file conda/PINGMapper.yml --prune
```

## All Done!
