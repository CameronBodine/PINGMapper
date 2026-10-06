'''
Group tiles (recursively found under inTileDir) into mosaics by matching
components of their filenames, and combine overlapping pixels using
overlap_method ('average', 'max', or 'min').

Mosaicking uses rasterio + numpy in fixed-size blocks instead of GDAL's
BuildVRT + Python VRT pixel-function approach. VRT pixel functions invoke a
Python callback per raster block during gdal.Translate (slow), and naively
accumulating whole-mosaic numpy arrays in memory can OOM on large mosaics.
Processing/writing one block at a time keeps peak memory bounded by
blockSize regardless of mosaic extent.
'''

#########
# Imports

import os
import re
import warnings
from glob import glob

import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.transform import from_origin
from joblib import Parallel, delayed, cpu_count
from tqdm import tqdm


############
# Parameters

inTileDir = r"D:\scratch\USGS_CERC_CarpSchools_All_Tiles\All_Tiles"

# File pattern with delimiter
delimiter = "-"
filePattern = delimiter.join(["{recording}", "{tile}"]) + ".png"
mosaicMatchPattern = delimiter.join(["{recording}"]) + ".png"

outMosaicDir = r"D:\scratch\USGS_CERC_CarpSchools_All_Mosaics"
overlap_method = "average"  # Options: 'average', 'max', 'min'

outputFormat = "tif"  # Output mosaic file extension/format; independent of input tile extension

force_greyscale = True  # Force output to be greyscale (single band) if True, else keep original bands
tiles_overlap = True  # Set False when tile footprints are guaranteed not to overlap

threadCnt = cpu_count()  # Number of mosaics to build in parallel

blockSize = 2048  # Block edge (px) processed/written at a time; bounds peak memory use


###########
# Functions

# GDAL driver for each supported output extension; GTiff is the only one
# validated for windowed/blockwise writes used by buildMosaic.
_DRIVER_BY_EXT = {
    'tif': 'GTiff',
    'tiff': 'GTiff',
}


def _driverForFormat(outputFormat: str):
    ext = outputFormat.lower().lstrip('.')
    if ext not in _DRIVER_BY_EXT:
        raise ValueError("Unsupported outputFormat '{}'; supported: {}".format(outputFormat, sorted(_DRIVER_BY_EXT)))
    return ext, _DRIVER_BY_EXT[ext]


def _build_pattern_regex(filePattern: str, delimiter: str):
    '''
    Convert a delimiter-based file pattern (e.g. "{recording}_{tile}.tif")
    into a compiled regex with named capture groups.
    '''

    fieldNames = re.findall(r'\{(\w+)\}', filePattern)

    escaped = re.escape(filePattern)
    for name in fieldNames:
        placeholder = re.escape('{' + name + '}')
        group = '(?P<{}>[^{}]+)'.format(name, re.escape(delimiter))
        escaped = escaped.replace(placeholder, group)

    return re.compile('^' + escaped + '$'), fieldNames


def _findTiles(inTileDir: str, ext: str):
    '''Recursively find all tile files under inTileDir with extension ext.'''

    return sorted(glob(os.path.join(inTileDir, '**', '*' + ext), recursive=True))


def _groupTiles(tileFiles: list, regex, mosaicMatchPattern: str):
    '''
    Group tile file paths by the mosaic key derived from mosaicMatchPattern,
    using the named fields extracted from each filename via regex.
    '''

    groups = {}
    skipped = []

    for f in tileFiles:
        m = regex.match(os.path.basename(f))
        if not m:
            skipped.append(f)
            continue

        fields = m.groupdict()
        mosaicName = mosaicMatchPattern.format(**fields)
        groups.setdefault(mosaicName, []).append(f)

    return groups, skipped


def _toGrey(arr: np.ndarray) -> np.ndarray:
    '''Convert a (bands, H, W) array to single-band greyscale using luma weights.'''

    if arr.shape[0] == 1:
        return arr[0:1]

    if arr.shape[0] >= 3:
        r = arr[0].astype(np.float64)
        g = arr[1].astype(np.float64)
        b = arr[2].astype(np.float64)
        grey = 0.299 * r + 0.587 * g + 0.114 * b
        return grey[np.newaxis, ...]

    # 2-band fallback
    return arr.mean(axis=0, keepdims=True)


def buildMosaic(mosaicName: str,
                 tileList: list,
                 outDir: str,
                 overlap_method: str,
                 force_greyscale: bool,
                 outputFormat: str = 'tif',
                 blockSize: int = 2048,
                 tiles_overlap: bool = True):
    '''
    Merge tileList into a single mosaic GeoTIFF, combining overlapping
    pixels per overlap_method. Processed and written one block at a time
    (rasterio/numpy only, no GDAL VRT/pixel functions) so peak memory is
    bounded by blockSize instead of the full mosaic extent.
    '''

    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=rasterio.errors.NotGeoreferencedWarning)
        srcs = [rasterio.open(f) for f in tileList]

    try:
        ref = srcs[0]
        resX, resY = ref.res
        crs = ref.crs
        dtype = ref.dtypes[0]
        nodata = ref.nodata if ref.nodata is not None else 0
        bandCnt = 1 if force_greyscale else ref.count

        lefts, bottoms, rights, tops = zip(*(s.bounds for s in srcs))
        minx, miny, maxx, maxy = min(lefts), min(bottoms), max(rights), max(tops)

        width = max(1, int(round((maxx - minx) / resX)))
        height = max(1, int(round((maxy - miny) / resY)))
        outTransform = from_origin(minx, maxy, resX, resY)

        if overlap_method not in ('average', 'max', 'min'):
            raise ValueError("overlap_method must be 'average', 'max', or 'min'; got '{}'".format(overlap_method))

        # Precompute each src's pixel offset/size within the full output grid
        srcInfo = []
        for s in srcs:
            colOff = int(round((s.bounds.left - minx) / resX))
            rowOff = int(round((maxy - s.bounds.top) / resY))
            srcInfo.append((s, colOff, rowOff, s.width, s.height))

        blockCols = (width + blockSize - 1) // blockSize
        blockRows = (height + blockSize - 1) // blockSize
        blockSources = [[] for _ in range(blockRows * blockCols)]
        for sourceIndex, (_, colOff, rowOff, sWidth, sHeight) in enumerate(srcInfo):
            firstBlockRow = max(0, rowOff // blockSize)
            lastBlockRow = min(blockRows - 1, (rowOff + sHeight - 1) // blockSize)
            firstBlockCol = max(0, colOff // blockSize)
            lastBlockCol = min(blockCols - 1, (colOff + sWidth - 1) // blockSize)
            for blockRow in range(firstBlockRow, lastBlockRow + 1):
                for blockCol in range(firstBlockCol, lastBlockCol + 1):
                    blockSources[blockRow * blockCols + blockCol].append(sourceIndex)

        # Internal GTiff block size must be a multiple of 16 and not exceed raster dims
        def _tiffBlockDim(dimSize):
            dim = min(blockSize, dimSize)
            dim = max(16, (dim // 16) * 16)
            return dim

        outExt, outDriver = _driverForFormat(outputFormat)
        outName = os.path.splitext(mosaicName)[0] + '.' + outExt
        outPath = os.path.join(outDir, outName)
        profile = {
            'driver': outDriver,
            'height': height,
            'width': width,
            'count': bandCnt,
            'dtype': dtype,
            'crs': crs,
            'transform': outTransform,
            'nodata': nodata,
            'compress': 'lzw',
            'tiled': True,
            'blockxsize': _tiffBlockDim(width),
            'blockysize': _tiffBlockDim(height),
            'BIGTIFF': 'IF_SAFER',
        }

        with rasterio.open(outPath, 'w', **profile) as dst:
            if not tiles_overlap:
                for s, colOff, rowOff, sWidth, sHeight in srcInfo:
                    data = s.read()
                    if force_greyscale:
                        data = _toGrey(data.astype(np.float64))
                    dst.write(
                        data.astype(dtype),
                        window=Window(col_off=colOff, row_off=rowOff, width=sWidth, height=sHeight),
                    )
                return outPath

            for rowStart in range(0, height, blockSize):
                bh = min(blockSize, height - rowStart)
                for colStart in range(0, width, blockSize):
                    bw = min(blockSize, width - colStart)

                    if overlap_method == 'average':
                        sumBlock = np.zeros((bandCnt, bh, bw), dtype=np.float64)
                        cntBlock = np.zeros((bandCnt, bh, bw), dtype=np.uint32)
                    else:
                        outBlock = np.full((bandCnt, bh, bw), nodata, dtype=np.float64)
                        hasBlock = np.zeros((bandCnt, bh, bw), dtype=bool)

                    blockIndex = (rowStart // blockSize) * blockCols + (colStart // blockSize)
                    for sourceIndex in blockSources[blockIndex]:
                        s, colOff, rowOff, sWidth, sHeight = srcInfo[sourceIndex]
                        # Intersection of this output block with the src's footprint
                        interRow0 = max(rowStart, rowOff)
                        interRow1 = min(rowStart + bh, rowOff + sHeight)
                        interCol0 = max(colStart, colOff)
                        interCol1 = min(colStart + bw, colOff + sWidth)

                        if interRow0 >= interRow1 or interCol0 >= interCol1:
                            continue

                        srcWin = Window(
                            col_off=interCol0 - colOff,
                            row_off=interRow0 - rowOff,
                            width=interCol1 - interCol0,
                            height=interRow1 - interRow0,
                        )
                        data = s.read(window=srcWin, masked=True)

                        if force_greyscale:
                            filled = data.filled(nodata).astype(np.float64)
                            grey = _toGrey(filled)
                            validMask = np.any(~np.ma.getmaskarray(data), axis=0, keepdims=True)
                            validMask &= np.any(data.data != nodata, axis=0, keepdims=True)
                            filled = grey
                            valid = np.broadcast_to(validMask, grey.shape)
                        else:
                            filled = data.filled(nodata).astype(np.float64)
                            valid = (~np.ma.getmaskarray(data) & (data.data != nodata))

                        bRow0 = interRow0 - rowStart
                        bCol0 = interCol0 - colStart
                        h, w = filled.shape[1], filled.shape[2]

                        if overlap_method == 'average':
                            sumBlock[:, bRow0:bRow0 + h, bCol0:bCol0 + w] += np.where(valid, filled, 0)
                            cntBlock[:, bRow0:bRow0 + h, bCol0:bCol0 + w] += valid.astype(np.uint32)
                        else:
                            region = outBlock[:, bRow0:bRow0 + h, bCol0:bCol0 + w]
                            regionHas = hasBlock[:, bRow0:bRow0 + h, bCol0:bCol0 + w]

                            if overlap_method == 'max':
                                take = valid & (~regionHas | (filled > region))
                            else:  # min
                                take = valid & (~regionHas | (filled < region))

                            region[take] = filled[take]
                            regionHas |= valid

                    if overlap_method == 'average':
                        with np.errstate(invalid='ignore', divide='ignore'):
                            outBlock = np.where(cntBlock > 0, sumBlock / np.maximum(cntBlock, 1), nodata)

                    dst.write(
                        outBlock.astype(dtype),
                        window=Window(col_off=colStart, row_off=rowStart, width=bw, height=bh),
                    )

        return outPath

    finally:
        for s in srcs:
            if not s.closed:
                s.close()


def doWork():

    os.makedirs(outMosaicDir, exist_ok=True)

    ext = os.path.splitext(filePattern)[-1]
    regex, _ = _build_pattern_regex(filePattern, delimiter)

    tileFiles = _findTiles(inTileDir, ext)
    print('Found {} tile(s) under {}'.format(len(tileFiles), inTileDir))

    groups, skipped = _groupTiles(tileFiles, regex, mosaicMatchPattern)
    if skipped:
        print('Skipped {} file(s) not matching filePattern.'.format(len(skipped)))

    print('Grouped into {} mosaic(s).'.format(len(groups)))

    results = list(Parallel(n_jobs=threadCnt)(
        delayed(buildMosaic)(mosaicName, tileList, outMosaicDir, overlap_method, force_greyscale, outputFormat, blockSize, tiles_overlap)
        for mosaicName, tileList in tqdm(groups.items(), total=len(groups))
    ))

    print('Wrote {} mosaic(s) to {}'.format(len(results), outMosaicDir))

    return results


#########
# Do Work

if __name__ == '__main__':
    doWork()