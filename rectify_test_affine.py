from common_funcs import *
from skimage.transform import PiecewiseAffineTransform, warp
from PIL import Image
from rasterio.transform import from_origin

np.set_printoptions(suppress=True)

imgFile = 'E:\\NAU\\Python\\PINGMapper\\procData\\SFE_20170801_R00014\\sidescan_port\\image-00010.png'
pingMeta = 'E:\\NAU\\Python\\PINGMapper\\procData\\SFE_20170801_R00014\\meta\\Range_PortSmth.csv'
xRange='port_ers'
yRange='port_nrs'
xTrk='es'
yTrk='ns'
pix_m = 0.018257221097741416
filt = 50
epsg = 'epsg:32617'

############################
# Prepare source coordinates
# Open image to rectify
img = np.asarray(Image.open(imgFile))

# Prepare src coordinates
rows, cols = img.shape[0], img.shape[1]
src_cols = np.arange(0, cols)
src_rows = np.linspace(0, rows, 2)
src_rows, src_cols = np.meshgrid(src_rows, src_cols)
srcAll = np.dstack([src_rows.flat, src_cols.flat])[0]

# Create mask for filtering array
mask = np.zeros(len(srcAll), dtype=bool)
mask[0::filt] = 1
mask[1::filt] = 1
mask[-2], mask[-1] = 1, 1

# Filter src
src = srcAll[mask]

#################################
# Prepare destination coordinates
pingMeta = pd.read_csv(pingMeta)
pingMeta = pingMeta[pingMeta['chunk_id']==10]

# Get range (outer extent) coordinates
xR, yR = pingMeta[xRange].to_numpy().T, pingMeta[yRange].to_numpy().T
xyR = np.vstack((xR, yR)).T

# Get trackline (inner extent) coordinates
xT, yT = pingMeta[xTrk].to_numpy().T, pingMeta[yTrk].to_numpy().T
xyT = np.vstack((xT, yT)).T

# Stack the coordinates (range[0,0], trk[0,0], range[1,1]...)
dstAll = np.empty([len(xyR)+len(xyT), 2])
dstAll[0::2] = xyT
dstAll[1::2] = xyR
# dstAll[0::2] = xyR
# dstAll[1::2] = xyT

# Filter dst
dst = dstAll[mask]

# Determine min/max for rescaling
xMin, xMax = dst[:,0].min(), dst[:,0].max()
yMin, yMax = dst[:,1].min(), dst[:,1].max()

# Determine output shape
outShapeM = [xMax-xMin, yMax-yMin]
outShape=[0,0]
outShape[0], outShape[1] = round(outShapeM[0]/pix_m,0), round(outShapeM[1]/pix_m,0)

# Rescale destination coordinates
# X values
xStd = (dst[:,0]-xMin) / (xMax-xMin) # Standardize
xScaled = xStd * (outShape[0] - 0) + 0 # Rescale
dst[:,0] = xScaled

# Y values
yStd = (dst[:,1]-yMin) / (yMax-yMin) # Standardize
yScaled = yStd * (outShape[1] - 0) + 0 # Rescale
dst[:,1] = yScaled

########################
# Perform transformation
# PiecewiseAffineTransform
tform = PiecewiseAffineTransform()
tform.estimate(src, dst) # Calculate H matrix

# Warp image
out = warp(img.T,
           tform.inverse,
           output_shape=(outShape[1], outShape[0]),
           mode='constant',
           cval=np.nan,
           clip=False,
           preserve_range=True)

out = np.where(out==255,np.nan,out) # Fixes extra white on curves

# Rotate 180 and flip
# https://stackoverflow.com/questions/47930428/how-to-rotate-an-array-by-%C2%B1-180-in-an-efficient-way
out = np.flip(np.flip(np.flip(out,1),0),1).astype('uint8')
# out = np.flip(np.flip(out,1),1).astype('uint8')
# out = np.flip(out,1).astype('uint8')

# Export rectified image
# imgFile = 'E:\\NAU\\Python\\PINGMapper\\procData\\delete\\sidescan_starboard\\Test-image-00000-rect.png'
# imageio.imwrite(imgFile, out)

##############
# Save Geotiff
# Determine resolution and calc affine transform matrix
xMin, xMax = dstAll[:,0].min(), dstAll[:,0].max()
yMin, yMax = dstAll[:,1].min(), dstAll[:,1].max()

xres = (xMax - xMin) / outShape[0]
yres = (yMax - yMin) / outShape[1]
# transform = Affine.translation(xMin - xres / 2, yMin - yres / 2) * Affine.scale(xres, yres)
transform = from_origin(xMin - xres/2, yMax - yres/2, xres, yres)

gtiff = 'E:\\NAU\\Python\\PINGMapper\\procData\\SFE_20170801_R00014\\sidescan_port\\image-00010-rect-prj.tif'
with rasterio.open(
    gtiff,
    'w',
    driver='GTiff',
    height=out.shape[0],
    width=out.shape[1],
    count=1,
    dtype=out.dtype,
    crs=epsg,
    transform=transform,
    compress='lzw'
    ) as dst:
        dst.nodata=np.nan
        dst.write(out,1)
