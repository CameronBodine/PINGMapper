from common_funcs import *
from skimage.transform import PiecewiseAffineTransform, warp
from PIL import Image

np.set_printoptions(suppress=True)

imgFile = 'E:\\NAU\\Python\\PINGMapper\\procData\\delete\\sidescan_port\\image-00005.png'
pingMeta = 'E:\\NAU\\Python\\PINGMapper\\procData\\delete\\meta\\Range_PortSmth.csv'
xRange='port_ers'
yRange='port_nrs'
xTrk='es'
yTrk='ns'
pix_m = 0.018257221097741416
filt = 100

#################################
# Prepare destination coordinates
pingMeta = pd.read_csv(pingMeta)
pingMeta = pingMeta[pingMeta['chunk_id']==5]

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

# Filter coordinates (for speed)
dst = np.empty([int(len(dstAll)/filt)*2, 2])
dst[0::2] = dstAll[0::filt]
dst[1::2] = dstAll[1::filt]

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

############################
# Prepare source coordinates
# Open image to rectify
img = np.asarray(Image.open(imgFile))
print(img.shape)
img = rasterio.open(imgFile)
print(img.shape)

# Prepare src coordinates
rows, cols = img.shape[0], img.shape[1]
src_cols = np.arange(0, cols)
src_rows = np.linspace(0, rows, 2)
src_rows, src_cols = np.meshgrid(src_rows, src_cols)
srcAll = np.dstack([src_rows.flat, src_cols.flat])[0]

# Filter src coordinates
src = np.empty([int(len(srcAll)/filt)*2, 2])
src[0::2] = srcAll[0::filt]
src[1::2] = srcAll[1::filt]

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
           cval=0,
           preserve_range=True)

out = np.where(out==255,0,out) # Fixes extra white on curves

# Rotate 180 and flip
# https://stackoverflow.com/questions/47930428/how-to-rotate-an-array-by-%C2%B1-180-in-an-efficient-way
out = np.flip(np.flip(np.flip(out,1),0),1)
# out = np.flip(out,1)

# Export rectified image
imgFile = 'E:\\NAU\\Python\\PINGMapper\\procData\\delete\\sidescan_port\\image-00005-rect.png'
imageio.imwrite(imgFile, out.astype('uint8'))
