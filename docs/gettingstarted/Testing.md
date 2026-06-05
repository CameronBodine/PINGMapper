---
layout: default
title: Test PINGMapper
nav_order: 4
parent: Getting Started

nav_exclude: false

---

# Test PINGMapper
{: .no_toc }

Test PINGMapper on sample datasets.
{: .fs-6 .fw-300 }

---

Once you have [installed](./Installation.md) `PING-Mapper`, the recommended way to verify the installation is to use `PINGWizard` to process the included example datasets. The first is a [small](#small-dataset-test) dataset collected in Marble Canyon, AZ, USA. This is the fastest way to see if the software is performing as expected. A second test can be carried out on a [large](#large-dataset-test). The large dataset is included to see how the software performs on a typical sonar recording. 

## Small Dataset Test

### Step 1
The first step is to launch `PING Wizard` - *[Click here to learn how](./PINGWizard.md).* This will open the `PING Wizard` window:

<img src="../../assets/running/PINGWizard_gui.PNG"/>

### Step 2
Press the `Small Dataset` button:

<img src="../../assets/running/pingwizard_test.PNG"/>

### Step 3
Once complete, explore the outputs in the `Test-Small-DS` folder created by `PINGWizard`, typically on your desktop or in your user folder.

{: .warning }
> If you receive a `ModuleNotFoundError`, try the [troubleshooting steps](../Troubleshooting.md#modulenotfounderror)

{: .g2k }
> Advanced users can also run tests from the prompt if needed, but `PINGWizard` remains the recommended workflow for routine verification.

{: .warning }
> If you receive an error, check [Troubleshooting](../Troubleshooting.md) first, then the [FAQ](../faq.md). If neither page addresses your issue, please [submit a new issue](https://github.com/CameronBodine/PINGMapper/issues/new/choose). 
> 
> [Submit Issue](https://github.com/CameronBodine/PINGMapper/issues/new/choose){: .btn .btn-red }

## Large Dataset Test

### Step 1
The first step is to launch `PING Wizard` - *[Click here to learn how](./PINGWizard.md).* This will open the `PING Wizard` window:

<img src="../../assets/running/PINGWizard_gui.PNG"/>

### Step 2
Press the `Large Dataset` button:

<img src="../../assets/running/pingwizard_test_large.PNG"/>

### Step 3
Once complete, explore the outputs in the `Test-Large-DS` folder created by `PINGWizard`, typically on your desktop or in your user folder.

{: .warning }
> If you receive a `ModuleNotFoundError`, try the [troubleshooting steps](../Troubleshooting.md#modulenotfounderror)

{: .warning }
> If you receive an error, check [Troubleshooting](../Troubleshooting.md) first, then the [FAQ](../faq.md). If neither page addresses your issue, please [submit a new issue](https://github.com/CameronBodine/PINGMapper/issues/new/choose). 
> 
> [Submit Issue](https://github.com/CameronBodine/PINGMapper/issues/new/choose){: .btn .btn-red }

## All Done!

You can now run `PINGMapper` on your [own datasets](./Running.md).
