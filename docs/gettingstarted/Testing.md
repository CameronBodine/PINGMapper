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

Once you have [installed](./Installation.md) `PING-Mapper`, you can test the installation by processing two example datasets. The first is a [small](#small-dataset-test) dataset collected in Marble Canyon, AZ, USA. This is the fastest way to see if the software is performing as expected. A second test can be carried out on a [large](#large-dataset-test). The large dataset is included to see how the software performs on a typical sonar recording. 

## Small Dataset Test
A quick test can be made to ensure PING-Mapper is working properly.
1. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

2. Enter the following into the prompt:  
```
python test_PINGMapper.py 1
```

Outputs are found in `.\\PINGMapper\\procData\\PINGMapper-Test-Small-DS`.

{: .warning }
> If you recieve a `ModuleNotFoundError`, try the [troubleshooting steps](../faq.md/#modulenotfounderror)

## Large Dataset Test
A test on a large (~0.5 GB; 1:00:06 duration) dataset can also be made.
1. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

2. Enter the following into the prompt:  
```
python test_PINGMapper.py 2
```

Outputs are found in `.\\PINGMapper\\procData\\PINGMapper-Test-Large-DS`.
