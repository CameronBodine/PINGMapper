---
layout: default
title: Running PING-Mapper
nav_order: 3
parent: Getting Started

nav_exclude: false

---

# Running `PING-Mapper`

After you have [tested](./Testing.md) `PING-Mapper` on the sample datasets, you are ready to process your own sonar recordings! Two scripts have been included with `PING-Mapper` and are found in the top-level directory. The first is `main.py` which allows you to process a single sonar recording. It is recommended that you start with this script when first processing sonar recordings with the software. A second script called `main_batchDirectory.py` provides an example of how to batch process many sonar recordings at once. Both approaches are covered below.

## Process single sonar recording

1. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

2. Open `main.py` in a text editor/IDE (I use [Atom](https://atom.io/)).

3. Enter paths to DAT, SON, and output directory:

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L45-L48

Windows users: Make sure your filepaths are structured in one of the three following file formats:
- (Double backslashes): `humFile = “C:\\Users\\cam\\Documents\\Programs\\PINGMapper\\Rec00012.DAT”`
- (Path preceded by `r`): `humFile = r“C:\Users\cam\Documents\Programs\PINGMapper\Rec00012.DAT”`
- (Single forward slash): `humFile = “C:/Users/cam/Documents/Programs/PINGMapper/Rec00012.DAT”`

4. Update temperature `t=10` with average temperature during scan.

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L50

5. Choose the number of pings to export per sonar tile.  This can be any value but all testing has been performed on chunk sizes of 500.

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L51

6. Option to export unknown ping metadata fields.

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L52

7. Export un-rectified sonar tiles with water column present AND/OR water column removed.

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L53-L54

<!-- 8. Line 37: Option to use Humminbird depth (`detectDepth=0`), automatically detect depth through thresholding (`detectDepth=1`), automatically detect depth with Residual U-Net (`detectDepth=2`), or do both automatic depth picking methods (`detectDepth=3`).  NOTE: this will soon be updated with a new method, stay tuned... -->

8. Smooth the depth data before removing water column.  This may help with any strange issues or noisy depth data.

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L55

9. Additional depth adjustment in number of pixels for water column removal.

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L56

10. Plot bedick(s) on non-rectified sonogram for visual inspection.

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L57

11. Export georectified sonar imagery (water-column-present AND/OR water-column-removed/slant-range-corrected) for use in GIS.

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L59-L60

12. Option to mosaic georectified sonar imagery (exported from step 12).

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L62

13. Number of compute threads to use for processing in parallel.

https://github.com/CameronBodine/PINGMapper/blob/a45db3039d13ab5e1c317002f17050f10600f035/main.py#L64

14. Run the program by entering the following in the command prompt:
```
python main.py
```

## Batch process multiple sonar recordings

PING-Mapper includes a script which will find all sonar recordings in a directory (even subdirectories!) and batch process them. This is useful if you have spent a day on the water collecting multiple sonar recordings. Just point this script at the top-most folder, provide an output directory for processed files, and PING-Mapper will do the rest!

1. Ensure your Anaconda prompt is in the top level of `PINGMapper` directory.

2. Open `main_batchDirectory.py` in a text editor/IDE (I use [Atom](https://atom.io/)).

3. Enter paths to input and output directory:

https://github.com/CameronBodine/PINGMapper/blob/ab77cdf0a5a4fc06d3833700e638777a0b1ec7fa/main_batchDirectory.py#L39-L40

4. Edit parameters as necessary (Note: supplied parameters will be applied to all sonar recordings):

https://github.com/CameronBodine/PINGMapper/blob/dd74f508e689ace132bdf304e28e8561cb0e100f/main_batchDirectory.py#L42-L58

5. Run the program by entering the following in the command prompt:
```
python main_batchDirectory.py
```
