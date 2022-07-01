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

**NOTE:** *Installation may take some time, please be patient.*
