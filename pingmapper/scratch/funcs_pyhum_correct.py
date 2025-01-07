
from funcs_common import *
from scipy.special import jv
from skimage.restoration import denoise_tv_chambolle

# Insignificant comment - disregard
# ==============================================================================
def doPyhumCorrections(sonObj, sonMeta):
    '''
    Developed from PyHum Correction Module
    '''

    mega = True # Use if data is known to come from newer mega imaging xducers

    ############
    # Parameters
    maxW = 1000 # Transducer source level power in watts
    alpha = 0 # sediment attenuation
    pix_m = sonObj.pixM # Size of 1 pixel in meters
    ft = 1/pix_m # Convert meters to pixels
    dep_m = sonMeta.dep_m.to_numpy()
    # bed = ft * (dep_m - sonObj.tvg) # Location of bed, in pixels, with tvg correction
    bed = ft * (dep_m) # Location of bed, in pixels
    dist_m = np.ediff1d(sonMeta.trk_dist.to_numpy()) # Distance between each ping

    # print('\n\n\n', sonObj, '\n\n\n\n')

    # # Get sonar data
    # sonDat_wcp = sonObj.sonDat.copy()

    # Get sonar shape
    shape = sonObj.sonDat.shape

    # Remove water column
    sonObj._WCR_SRC(sonMeta)
    sonDat_wcr = sonObj.sonDat.copy()

    # Convert to dB
    Zt = sonObj.sonDat * (10*np.log10(maxW)/255)

    # Calculate range and incident angle
    R, A = calculateRange(sonObj, sonMeta, Zt, bed, shape, dep_m, pix_m)
    del Zt

    # Set nan's to zero
    R[np.isnan(R)] = 0

    # Calculate absorption of sound in water
    f = sonMeta.f.to_numpy() # frequency
    c = sonObj.c # speed of sound
    pH = sonObj.pH # water pH
    t = sonObj.tempC # water temperature
    s = sonObj.S # water salinity
    alpha_w = water_atten(R, f, c, pH, t, s)

    # Compute tansmission losses
    TL = (40 * np.log10(R) + alpha_w + (2*alpha)*R/1000)/255
    del alpha_w

    # Set nan's, negatives to 0
    TL[np.isnan(TL)] = 0
    TL[TL<0] = 0

    # Do Lambertian Correction
    Zt = correct_scans_lambertian(sonDat_wcr, A, TL, R, c, np.nanmax(f), mega)

    avg = np.nanmedian(Zt,axis=0)

    Zt2 = Zt-avg + np.nanmean(avg)
    Zt2 = Zt2 + np.abs(np.nanmin(Zt2))

    try:
        Zt2 = median_filter(Zt2, (3,3))
    except:
        pass

    return Zt2


def correct_scans_lambertian(fp, a_fp, TL, R, c, f, mega):
    '''
    '''

    # Calculate acoustic wavelength, lambda
    lam = c/(f*1000)

    Rtmp = np.deg2rad(R.copy()) ##/2
    try:
        Rtmp[np.where(Rtmp==0)] = Rtmp[np.where(Rtmp!=0)[0][-1]]
    except:
        pass

    # # We know some things about mega xducers due to:
    # ## http://forums.sideimagingsoft.com/index.php?topic=10052.0
    # if mega:
    #     # Calculate vertical beam width at 3db
    #     L1
    #
    # sys.exit()

    alpha=59 # Vertical beam width
    theta=35 # opening angle

    #transducer radius
    a = 0.61*lam / (np.sin(alpha/2))

    M = (f*1000)/(a**4)

    # no 'M' constant of proportionality
    phi = ((M*(f*1000)*a**4) / Rtmp**2)*(2*jv(1,(2*np.pi/lam)*a*np.sin(np.deg2rad(theta))) / (2*np.pi/lam)*a*np.sin(np.deg2rad(theta)))**2

    phi = np.squeeze(phi)
    phi[phi==np.inf]=np.nan

    # fp is 1d (1 scan)
    beta = np.cos(a_fp)
    try:
        beta[np.where(beta<10e-5)] = beta[np.where(beta>10e-5)[0][-1]]
    except:
        pass
    mg = (fp / phi * beta)*(1/Rtmp)
    mg[np.isinf(mg)] = np.nan
    K = np.nansum(fp)/np.nansum(mg)
    mg = mg*K

    mg[mg<0] = np.nan

    mg = 10**np.log10(mg + TL)
    mg[fp==0] = np.nan
    mg[mg<0] = np.nan

    mask = np.isnan(mg)
    mg[np.isnan(mg)] = 0
    mg = denoise_tv_chambolle(mg.copy(), weight=.2, multichannel=False).astype('float32')
    mg[mask==True] = np.nan
    return mg

# ==============================================================================
def water_atten(H, f, c, pH, T, S):
    '''
    Calculate absorption of sound in water
    '''
    H = np.abs(H)
    P1 = 1 # cosntant
    A1 = (8.86/c)*(10**(0.78*pH - 5))
    f1 = 2.8*(S/35)**0.5 * 10**(4 - 1245/(T + 273))
    A2 = 21.44*(S/c)*(1 + 0.025*T)
    A3 = (4.937 *10**-4) - (2.59 * 10**-5)*T + (9.11* 10**-7)*T**2- (1.5 * 10**-8)*T**3
    f2 = (8.17 * 10**(8 - 1990/(T + 273))) / (1 + 0.0018*(S - 35))
    P2= 1 - (1.37*10**-4) * H + (6.2 * 10**-9)* H**2
    P3 = 1 - (3.83 * 10**-5)*H + (4.9 *10**(-10) )* H**2
    # absorption sound water dB/km
    alphaw = ( (A1*P1*f1*f**2)/(f**2 + f1**2) ) + ( (A2*P2*f2*f**2)/(f**2 + f2**2) ) + (A3*P3*f**2)
    return 2*(alphaw/1000)*H # depth(m) * dB/m = dB

# ==============================================================================
def calculateRange(sonObj, sonMeta, fp, bed, shape, dep_m, pix_m):
    '''
    Calculate pixel-wise range
    '''

    extent = shape[0]
    yvec = np.linspace(pix_m, extent*pix_m, extent)
    d = dep_m

    a = np.ones(np.shape(fp))

    for k in range(len(d)):
        a[:, [k]] = np.expand_dims(d[k]/yvec, axis=1)

    r = np.ones(np.shape(fp))

    for k in range(len(d)):
        r[:, [k]] = np.expand_dims(np.sqrt(yvec**2 - d[k]**2), axis=1)

    # Remove water column
    ## Store a, r in sonObj.sonDat, then do water column removal
    sonObj.sonDat = r
    del r
    sonObj._WCR_SRC(sonMeta, son=False)
    r = sonObj.sonDat.copy()

    sonObj.sonDat = a
    del a
    sonObj._WCR_SRC(sonMeta, son=False)
    a = sonObj.sonDat.copy()

    return r, np.pi/2 - np.arctan(a)
