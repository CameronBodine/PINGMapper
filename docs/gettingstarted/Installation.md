---
layout: default
title: Installation
nav_order: 1
parent: Getting Started

nav_exclude: false

---

# Install PINGMapper
{: .no_toc }

Get `PINGMapper` up and running on your computer.
{: .fs-6 .fw-300 }

[![PINGMapper](https://img.shields.io/pypi/v/pingmapper?label=PINGMapper)](https://pypi.org/project/pingmapper/) [![PINGWizard](https://img.shields.io/pypi/v/pingwizard?label=PINGWizard)](https://pypi.org/project/pingwizard/) [![PINGVerter](https://img.shields.io/pypi/v/pingverter?label=PINGVerter)](https://pypi.org/project/pingverter/) [![PINGInstaller](https://img.shields.io/pypi/v/pinginstaller?label=PINGInstaller)](https://pypi.org/project/pinginstaller/)

---

{: .g2k }
> As of v4.0, the PINGMapper installation process has been dramatically improved and simplified compared to the [old version](./Installation-v1.md)

`PINGMapper` is a software (i.e. package) written in [Python](https://www.python.org/). PINGMapper uses a variety of Python packages ([NumPy](https://numpy.org/), [Pandas](https://pandas.pydata.org/), [Tensorflow](https://www.tensorflow.org/), etc.), or dependencies, that allow you to process Humminbird&reg; sonar recordings and generate a variety of GIS datasets.

{: .g2k }
> You **do not** need to know Python to use PINGMapper! After issuing a few simple commands, all interactions with PINGMapper will be point-and-click.

`PINGMapper` uses `conda` to ensure the installation is configured correctly. Specifically, `conda` is used to create a [virtual environments](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#) called `ping`, a container storing all the correct versions of of the required dependencies, that ensures `PINGMapper` runs as expected.

 `Conda` comes in several flavors, however, we will use [Miniforge](https://conda-forge.org/download/) as it is free for anyone to use.

 - [Miniforge](https://conda-forge.org/download/): *Free for all*; [License](https://github.com/conda-forge/miniforge?tab=License-1-ov-file#readme)

 {: .g2k }
 > Existing users may have previously used Miniconda or Anaconda. Due to changes is licensing, it is recommended that you transition to Miniforge, an open-source alternative.

This tutorial will demonstrate how to install and configure `PINGMapper`. After installing Miniforge, we will install and run [PINGInstaller](https://github.com/CameronBodine/PINGInstaller). `PINGInstaller` automatically creates the `ping` environment, installs the appropriate packages from the [PING Ecosystem](../PINGEcosystem.md) ([PINGMapper](https://github.com/CameronBodine/PINGMapper), [PINGWizard](https://github.com/CameronBodine/PINGWizard), [PINGVerter](https://github.com/CameronBodine/PINGVerter), etc.), and other necessary dependencies.

Let's get started!

## Step 1 - Install Miniforge

Go to the [Miniforge Website](https://conda-forge.org/download/) and download the software. Choose the appropriate installer for your computer's operation system. This tutorial was made on a Windows machine but the process should be similar on other operation systems. Click the file and it will download to your Downloads folder, or you can right-click and select "Save Link As..." and choose an alternative location to save the install file.

Double click the file to begin the installation file. This will open an installation window:

<img src="../../assets/install/miniconda_install_1.PNG"/>

Click `Next` and you will see the license agreement:

<img src="../../assets/install/miniconda_install_2.PNG"/>

After reviewing the license agreement, you must select `I Agree` to continue with the installation. After you agree, you will have an option to install Miniconda for `Just Me` or `All Users`. 

<img src="../../assets/install/miniconda_install_3.PNG"/>

You want to install Miniforge in your user folder so that you have the necessary permissions to install the Python dependencies, so select `Just Me` and click `Next`.

<img src="../../assets/install/miniconda_install_4.PNG"/>

Accept the default installation location and click `Next`. This will open the Advanced Installation Options window. 

<img src="../../assets/install/miniconda_install_5.PNG"/>

We will accept the default options, shown above, and click `Next`. Once installation is complete, you will see the following window indicating Miniconda was successfully installed:

<img src="../../assets/install/miniconda_install_6.PNG"/>

Click `Finish` to close the window.

## Step 2

Now for the scary part! We are going to open a command prompt so that we can submit a series of commands to Miniforge. If you want to gain some familiarity with navigating with the prompt, you can watch this video:

<iframe width="560" height="315" src="https://www.youtube.com/embed/9zMWXD-xoxc" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

Miniforge is a command prompt that we will use to install and run PINGMapper. On Windows, click the start button and scroll through your installed applications until you find `Miniforge Prompt`. 

<img src="../../assets/install/miniconda_run.png"/>

Click the icon to open the prompt.

<img src="../../assets/install/shell_1a.PNG"/>

## Step 2

{: .g2k }
> Installing PINGInstaller in the `base` environment will only download the PINGInstaller package and make no further changes.

A package called [PINGInstaller](https://github.com/CameronBodine/PINGInstaller) is used to install and setup PINGMapper. We will install `PINGInstaller` with the following command and pressing `Enter`:

```bash
pip install pinginstaller -U
```

<img src="../../assets/install/shell_install_pinginstaller.PNG"/>

## Step 3

By running `PINGInstaller`, a new conda environment called `ping` will be created, and all dependencies will be installed into `ping`. Add the following command and press `Enter`:

```bash
python -m pinginstaller
```

<img src="../../assets/install/shell_run_pinginstaller.PNG"/>

Installation will take approximately **5-10 minutes**. You should see something similar to:

<img src="../../assets/install/shell_pinginstaller_finish.PNG"/>

At the end of the install process, a window will prompt you where to save the `bat` or `sh` shortcut file. Browse to the desired location and click `Submit`.

<img src="../../assets/install/shortcut_gui.PNG"/>


## That's It!

PINGMapper is now ready to go. [Launch PINGWizard](./PINGWizard.md), a new interface for PINGMapper, to start processing data.
