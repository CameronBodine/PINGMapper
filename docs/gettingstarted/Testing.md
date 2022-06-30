---
layout: default
title: Testing PING-Mapper
nav_order: 2
parent: Getting Started

nav_exclude: false

---
# Testing PING-Mapper

Once you have [installed](.../docs/gettingstarted/Installation.md)  `PING-Mapper` on your computer, you can test the installation by processing two example datasets. The first is a [small](#small-dataset-test) dataset that is already downloaded into the `PING-Mapper` directory following installation. This is the fastest way to see if the software is performing as expected. A second test can be carried out on a [large](#large-dataset-test) which is automatically downloaded once you run the test. The large dataset is included to see how the software performs on a typical sonar recording.  

## Small Dataset Test
A quick test can be made to ensure PING-Mapper is working properly.
1. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

2. Enter the following into the prompt:  
```
python test_PINGMapper.py 1
```

Outputs are found in `.\\PINGMapper\\procData\\PINGMapper-Test-Small-DS`.

## Large Dataset Test
A test on a large (~0.5 GB; 1:00:06 duration) dataset can also be made.
1. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

2. Enter the following into the prompt:  
```
python test_PINGMapper.py 2
```

Outputs are found in `.\\PINGMapper\\procData\\PINGMapper-Test-Large-DS`.
