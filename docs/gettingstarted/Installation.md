---
layout: default
title: Installation
nav_order: 1
parent: Getting Started

nav_exclude: false

---

# Installation
- Install [Miniconda](https://docs.conda.io/en/latest/miniconda.html). When prompted, select the option to install for "me" insted of "all users". This will install miniconda into your user folder. 

- Open Anaconda Powershell Prompt or Anaconda Prompt.

{: .g2k }
> Windows Users: Go to the start menu and search for 'Anaconda'.

- Update conda:
```
conda update -n base conda
```

- Conda has released a new environment solver called [libmamba](https://www.anaconda.com/blog/a-faster-conda-for-a-growing-community) that is _considerably_ faster then installing environments with the classic installer. Install `libmamba` with:
```
conda install -n base conda-libmamba-solver
```

- Set `libmamba` as the default solver:
```
conda config --set solver libmamba
```

{: .g2k }
> You can revert to the classic installer by running:
> ```
> conda config --set solver classic
> ```

- Now install git with:
conda install git


- Now navigate to where you would like to save PING Mapper. Here I am saving PING-Mapper into 'MyPythonRepos', a folder inside my user folder:
```
cd C:\users\Cam\MyPythonRepos
```

{: .g2k }
> If you haven't navigated through your file system with the command prompt before, here is a video to explain how! (PING-Mapper developers did not make this video.)
> <iframe width="560" height="315" src="https://www.youtube.com/embed/9zMWXD-xoxc" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

- Clone the repo:
```
git clone --depth 1 https://github.com/CameronBodine/PINGMapper
```

- Change directory into PINGMapper folder:
```
cd PINGMapper
```

- Create a conda environment called `ping` and activate it:
```
conda env create --file conda/PINGMapper.yml
conda activate ping
```

{: .note }
> Since we installed `libmamba` and set it as the default solver, it will be used to solve the environment. This will install PING-Mapper in approximately 10 minutes (or less) compared to nearly 1 hour with the classic solver!

- Now let's run a [test](./Testing.md) to make sure everything is functioning as expected.
