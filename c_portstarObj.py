from funcs_common import *
from rasterio.merge import merge
from rasterio.enums import Resampling
import gdal

class portstarObj(object):
    '''

    '''
    #=======================================================================
    def __init__(self, objs):
        '''
        '''
        for obj in objs:
            if obj.beamName == 'ss_port':
                self.port = obj
            elif obj.beamName == 'ss_star':
                self.star = obj
            else:
                print("Object is unknown...")
        return

    ############################################################################
    # Mosaic                                                                   #
    ############################################################################

    #=======================================================================
    def _createMosaic(self, mosaic, overview):
        self.imgsToMosaic = []
        imgDirs = [self.port.outDir, self.star.outDir]

        if self.port.rect_wcp:
            wrcToMosaic = []
            for path in imgDirs:
                path = os.path.join(path, 'rect_wcp')
                imgs = glob(os.path.join(path, '*.tif'))
                for img in imgs:
                    wrcToMosaic.append(img)
            self.imgsToMosaic.append(wrcToMosaic)

        if self.port.rect_src:
            srcToMosaic = []
            for path in imgDirs:
                path = os.path.join(path, 'rect_src')
                imgs = glob(os.path.join(path, '*.tif'))
                for img in imgs:
                    srcToMosaic.append(img)
            self.imgsToMosaic.append(srcToMosaic)

        if mosaic == 1:
            self._mosaicGtiff(overview)
        elif mosaic == 2:
            self._mosaicVRT(overview)


    #=======================================================================
    def _mosaicGtiff(self, overview):
        for imgs in self.imgsToMosaic:

            filePrefix = os.path.split(self.port.projDir)[-1]
            fileSuffix = os.path.split(os.path.dirname(imgs[0]))[-1] + '_mosaic.vrt'
            outVRT = os.path.join(self.port.projDir, filePrefix+'_'+fileSuffix)
            outTIF = outVRT.replace('.vrt', '.tif')

            vrt_options = gdal.BuildVRTOptions(resampleAlg='nearest')
            gdal.BuildVRT(outVRT, imgs, options=vrt_options)

            ds = gdal.Open(outVRT)

            kwargs = {'format': 'GTiff',
                      'creationOptions': ['NUM_THREADS=ALL_CPUS', 'COMPRESS=LZW']
                      }
            gdal.Translate(outTIF, ds, **kwargs)
            if overview:
                dest = gdal.Open(outTIF, 1)
                gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
                dest.BuildOverviews('nearest', [2 ** j for j in range(1,10)])

            os.remove(outVRT)

        return self

    #=======================================================================
    def _mosaicVRT(self, overview):
        for imgs in self.imgsToMosaic:

            filePrefix = os.path.split(self.port.projDir)[-1]
            fileSuffix = os.path.split(os.path.dirname(imgs[0]))[-1] + '_mosaic.vrt'
            outFile = os.path.join(self.port.projDir, filePrefix+'_'+fileSuffix)

            vrt_options = gdal.BuildVRTOptions(resampleAlg='nearest')
            gdal.BuildVRT(outFile, imgs, options=vrt_options)

            if overview:
                dest = gdal.Open(outFile)
                gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
                dest.BuildOverviews('nearest', [2 ** j for j in range(1,10)])

    # #=======================================================================
    # def _mosaicGtiffRasterIO(self, overview):
    #     '''
    #     '''
    #
    #     for imgs in self.imgsToMosaic:
    #         filesToMosaic = []
    #         for img in imgs:
    #             open = rasterio.open(img)
    #             filesToMosaic.append(open)
    #
    #         filePrefix = os.path.split(self.port.projDir)[-1]
    #         fileSuffix = os.path.split(os.path.dirname(imgs[0]))[-1] + '_mosaic.tif'
    #         outFile = os.path.join(self.port.projDir, filePrefix+'_'+fileSuffix)
    #
    #         outMosaic, outTrans = merge(filesToMosaic, method='max')
    #         outMeta = open.meta.copy()
    #         outMeta.update({'height': outMosaic.shape[1],
    #                         'width': outMosaic.shape[2],
    #                         'transform': outTrans})
    #         with rasterio.open(outFile, 'w', **outMeta) as dest:
    #             dest.write(outMosaic)
    #             if overview:
    #                 dest.build_overviews([2 ** j for j in range(1,10)], Resampling.nearest)
    #                 dest.update_tags(ns='rio_overview', resampling='nearest')
    #                 dest.close()












# if mosaic > 0:
#     print("\nMosaicing GeoTiffs...")
#     imgDirs = []
#     for son in portstar:
#         imgDirs.append(son.outDir)
#         projDir = son.projDir
#         filePrefix = os.path.split(projDir)[-1]
#         print(filePrefix)
#
#     imgsToMosaic = []
#     if rect_wcp:
#         wrcToMosaic = []
#         for path in imgDirs:
#             path = os.path.join(path, 'rect_wcp')
#             imgs = glob(os.path.join(path, '*.tif'))
#             for img in imgs:
#                 wrcToMosaic.append(img)
#         imgsToMosaic.append(wrcToMosaic)
#     if rect_src:
#         srcToMosaic = []
#         for path in imgDirs:
#             path = os.path.join(path, 'rect_src')
#             imgs = glob(os.path.join(path, '*.tif'))
#             for img in imgs:
#                 srcToMosaic.append(img)
#         imgsToMosaic.append(srcToMosaic)
#
#     for imgs in imgsToMosaic:
#         srcFilesToMosaic = []
#         for img in imgs:
#             src = rasterio.open(img)
#             srcFilesToMosaic.append(src)
#
#         fileSuffix = os.path.split(os.path.dirname(imgs[0]))[-1] + '_mosaic.tif'
#         print(fileSuffix)
#         outFile = os.path.join(projDir, filePrefix+'_'+fileSuffix)
#
#         outMosaic, outTrans = merge(srcFilesToMosaic, method='max')
#         outMeta = src.meta.copy()
#         outMeta.update({'height': outMosaic.shape[1],
#                         'width': outMosaic.shape[2],
#                         'transform': outTrans})
#         with rasterio.open(outFile, 'w', **outMeta) as dest:
#             dest.write(outMosaic)
