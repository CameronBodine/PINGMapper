













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
