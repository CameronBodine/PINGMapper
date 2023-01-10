---
layout: default
title: Installation
nav_order: 1
parent: Getting Started

nav_exclude: false

---

# Installation
1. Install [Anaconda](https://www.anaconda.com) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html).

2. Open Anaconda Prompt and navigate to where you would like to save PING Mapper:
```
cd C:\users\Cam\MyPythonRepos
```

3. Clone the repo:
```
git clone --depth 1 https://github.com/CameronBodine/PINGMapper
```

4. Change directory into PINGMapper folder:
```
cd PINGMapper
```

5. Create a conda environment called `ping` and activate it:
```
conda env create --file conda/PINGMapper.yml
conda activate ping
```

**NOTE:** *Installation may take some time (up to an hour!), please be patient. As an alternative, see the note below.*

{: .note }
> `conda` takes a long time to solve environmental dependencies, largely due to the installation of `gdal`. [libmamba](https://www.anaconda.com/blog/a-faster-conda-for-a-growing-community) is an alternative to installing with `conda` and can solve package dependencies much faster, as noted in [this issue](https://github.com/CameronBodine/PINGMapper/issues/47#issuecomment-1376246401). PING-Mapper developers have not tested this installation method, but this will likely become the recommended approach.
>
> First, update `conda`'s base environment:
> ```
> conda update -n base conda
> ```
> Second, install `libmamba` and set as the new solver:
> ```
> conda install -n base conda-libmamba-solver
> conda config --set solver libmamba
>```
> Then install and activate `PING-Mapper`:
> ```
> conda env create --file conda/PINGMapper.yml
> conda activate ping
> ```
