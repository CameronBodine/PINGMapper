---
layout: default
title: Update Installation
nav_order: 3
parent: Getting Started

nav_exclude: false

---

# Update PINGMapper
{: .no_toc }

Update `PINGMapper` & dependencies to the latest version.
{: .fs-6 .fw-300 }

[![PINGMapper](https://img.shields.io/pypi/v/pingmapper?label=PINGMapper)](https://pypi.org/project/pingmapper/) [![PINGWizard](https://img.shields.io/pypi/v/pingwizard?label=PINGWizard)](https://pypi.org/project/pingwizard/) [![PINGVerter](https://img.shields.io/pypi/v/pingverter?label=PINGVerter)](https://pypi.org/project/pingverter/) [![PINGInstaller](https://img.shields.io/pypi/v/pinginstaller?label=PINGInstaller)](https://pypi.org/project/pinginstaller/)

---

{: .g2k }
> As of v4.0, the updating PINGMapper process has been dramatically improved and simplified compared to the [old version](./UpdateInstallation_v1.md)

{: .warning }
> If you have not installed PINGInstaller previously and used a version of PINGMapper < 4.0, you will want to follow the [installation](./Installation.md) instructions.

If you have installed a previous version of PING-Mapper (>=4.0), follow these instructions to update to the latest version.

## Option 1

Launch PINGWizard *([Click here to learn how](./PINGWizard.md))*:

<img src="../../assets/running/PINGWizard_gui.PNG"/>

Press `Update`:

<img src="../../assets/install/pingwizard_update.PNG"/>

## Option 2

Open the Anaconda Powershell prompt and run the following:

```bash
conda activate ping
python -m pinginstaller
```

Alternatively run as a single command:

```base
cond run -n ping python -m pinginstaller
```

## All Done!

It is recommended that you [run the tests](./Testing.md) to make sure everything is working correctly.