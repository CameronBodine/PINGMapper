'''
Create georeferenced GeoTIFF mosaics from SonarTRX-style KML files.

The KML supplies each image tile's WGS84 LatLonBox. A VRT is generated
directly from that information, referencing the original image tiles, and
GDAL translates the VRT once to the final GeoTIFF. No per-tile conversion or
Python pixel compositing is performed.
'''

import os
import xml.etree.ElementTree as ET
from glob import glob

from osgeo import gdal
from joblib import Parallel, delayed
from tqdm import tqdm


inKmlDir = r"D:\scratch\USGS_CERC_CarpSchools_All_Tiles\All_Tiles"
inTileDir = inKmlDir
outMosaicDir = r"D:\scratch\USGS_CERC_CarpSchools_All_Mosaics"
outputFormat = 'tif'
threadCnt = 16

_KML_NS = '{http://www.opengis.net/kml/2.2}'


def _findKmls(inKmlDir: str):
    return sorted(glob(os.path.join(inKmlDir, '**', '*.kml'), recursive=True))


def _parseKmlTiles(kmlPath: str, tileDir: str):
    tree = ET.parse(kmlPath)
    root = tree.getroot()
    tiles = []

    for overlay in root.iter('{}GroundOverlay'.format(_KML_NS)):
        icon = overlay.find('{}Icon'.format(_KML_NS))
        box = overlay.find('{}LatLonBox'.format(_KML_NS))
        if icon is None or box is None:
            continue

        href = icon.find('{}href'.format(_KML_NS))
        if href is None or not href.text:
            continue

        fileName = os.path.basename(href.text.replace('\\', '/'))
        tilePath = os.path.join(tileDir, fileName)
        if not os.path.isfile(tilePath):
            continue

        try:
            north = float(box.find('{}north'.format(_KML_NS)).text)
            south = float(box.find('{}south'.format(_KML_NS)).text)
            east = float(box.find('{}east'.format(_KML_NS)).text)
            west = float(box.find('{}west'.format(_KML_NS)).text)
        except (AttributeError, TypeError, ValueError):
            continue

        if east <= west or north <= south:
            continue

        tiles.append({
            'path': os.path.abspath(tilePath),
            'north': north,
            'south': south,
            'east': east,
            'west': west,
        })

    return tiles


def _sourceInfo(tiles):
    sources = []
    for tile in tiles:
        source = gdal.Open(tile['path'], gdal.GA_ReadOnly)
        if source is None:
            raise RuntimeError('GDAL could not open {}'.format(tile['path']))

        sources.append({
            **tile,
            'width': source.RasterXSize,
            'height': source.RasterYSize,
            'bands': source.RasterCount,
            'dataType': gdal.GetDataTypeName(source.GetRasterBand(1).DataType),
        })
        source = None

    return sources


def _sourceElement(source, bandNumber, colOff, rowOff):
    sourceElement = ET.Element('ComplexSource')
    ET.SubElement(sourceElement, 'SourceFilename', {'relativeToVRT': '0'}).text = source['path']
    ET.SubElement(sourceElement, 'SourceBand').text = str(bandNumber)
    ET.SubElement(sourceElement, 'SourceProperties', {
        'RasterXSize': str(source['width']),
        'RasterYSize': str(source['height']),
        'DataType': source['dataType'],
        'BlockXSize': str(source['width']),
        'BlockYSize': '1',
    })
    ET.SubElement(sourceElement, 'SrcRect', {
        'xOff': '0',
        'yOff': '0',
        'xSize': str(source['width']),
        'ySize': str(source['height']),
    })
    ET.SubElement(sourceElement, 'DstRect', {
        'xOff': str(colOff),
        'yOff': str(rowOff),
        'xSize': str(source['width']),
        'ySize': str(source['height']),
    })
    ET.SubElement(sourceElement, 'NODATA').text = '0'
    return sourceElement


def _writeVrt(vrtPath: str, sources):
    minx = min(source['west'] for source in sources)
    maxx = max(source['east'] for source in sources)
    miny = min(source['south'] for source in sources)
    maxy = max(source['north'] for source in sources)

    resX = (sources[0]['east'] - sources[0]['west']) / sources[0]['width']
    resY = (sources[0]['north'] - sources[0]['south']) / sources[0]['height']
    width = max(1, int(round((maxx - minx) / resX)))
    height = max(1, int(round((maxy - miny) / resY)))
    bandCount = max(source['bands'] for source in sources)

    vrt = ET.Element('VRTDataset', {
        'rasterXSize': str(width),
        'rasterYSize': str(height),
    })
    ET.SubElement(vrt, 'SRS').text = 'EPSG:4326'
    ET.SubElement(vrt, 'GeoTransform').text = '{}, {}, 0, {}, 0, -{}'.format(minx, resX, maxy, resY)

    for bandNumber in range(1, bandCount + 1):
        band = ET.SubElement(vrt, 'VRTRasterBand', {
            'dataType': sources[0]['dataType'],
            'band': str(bandNumber),
        })
        ET.SubElement(band, 'NoDataValue').text = '0'
        if bandCount == 4 and bandNumber == 4:
            ET.SubElement(band, 'ColorInterp').text = 'Alpha'

        for source in sources:
            if bandNumber > source['bands']:
                continue
            colOff = int(round((source['west'] - minx) / resX))
            rowOff = int(round((maxy - source['north']) / resY))
            band.append(_sourceElement(source, bandNumber, colOff, rowOff))

    ET.ElementTree(vrt).write(vrtPath, encoding='UTF-8', xml_declaration=True)


def buildMosaicFromKml(kmlPath: str, tileDir: str, outDir: str, outputFormat: str = 'tif'):
    if outputFormat.lower().lstrip('.') not in ('tif', 'tiff'):
        raise ValueError('Only GeoTIFF output is supported')

    tiles = _parseKmlTiles(kmlPath, tileDir)
    if not tiles:
        return None

    sources = _sourceInfo(tiles)
    os.makedirs(outDir, exist_ok=True)
    outPath = os.path.join(outDir, os.path.splitext(os.path.basename(kmlPath))[0] + '.tif')
    vrtPath = os.path.splitext(outPath)[0] + '.vrt'

    gdal.UseExceptions()
    try:
        _writeVrt(vrtPath, sources)
        translated = gdal.Translate(
            outPath,
            vrtPath,
            format='GTiff',
            creationOptions=['TILED=YES', 'COMPRESS=LZW', 'BIGTIFF=IF_SAFER', 'NUM_THREADS=ALL_CPUS'],
        )
        if translated is None:
            raise RuntimeError('GDAL failed to translate {}'.format(vrtPath))
        translated = None
        return outPath
    finally:
        if os.path.exists(vrtPath):
            os.remove(vrtPath)


def doWork():
    os.makedirs(outMosaicDir, exist_ok=True)
    kmlFiles = _findKmls(inKmlDir)
    print('Found {} KML(s) under {}'.format(len(kmlFiles), inKmlDir))
    results = list(Parallel(n_jobs=threadCnt)(
        delayed(buildMosaicFromKml)(kmlPath, inTileDir, outMosaicDir, outputFormat)
        for kmlPath in tqdm(kmlFiles)
    ))
    results = [result for result in results if result]
    print('Wrote {} mosaic(s) to {}'.format(len(results), outMosaicDir))
    return results


if __name__ == '__main__':
    doWork()
