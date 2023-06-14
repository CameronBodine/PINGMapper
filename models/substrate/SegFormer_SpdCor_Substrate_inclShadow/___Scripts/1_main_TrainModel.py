
'''
Cross validation modeling
By: Cameron Bodine
'''

# Imports
import sys, os, gc
from joblib import Parallel, delayed, cpu_count
import itertools
import json
import pandas as pd
from glob import glob

gymDir = '/mnt/md0/SynologyDrive/Modeling/segmentation_gym'
sys.path.insert(0, gymDir)
# import train_model

############
# Parameters
os.chdir('../') # Move out of ___Scripts dir
outDir = os.getcwd()
os.chdir('../../') # Move to Modeling dir
dataset_path = [
                os.path.join(os.getcwd(), '03_TrainDatasets/1500Ping_Substrate_inclShadow'),
                os.path.join(os.getcwd(), '03_TrainDatasets/SpdCor_Substrate_inclShadow')
               ]

# Hyperparameters
# For testing multiple params, add items to list with a comma [i1, i2, ...]
config = {
    "TARGET_SIZE": [512,512],
    "MODEL": 'segformer',
    "NCLASSES": 8,
    "BATCH_SIZE": 20,
    "N_DATA_BANDS": 1,
    "DO_TRAIN": True,
    "PATIENCE": 10,
    "MAX_EPOCHS": 100,
    "VALIDATION_SPLIT": 0.6,
    "FILTERS": 6,
    "KERNEL":9,
    "STRIDE":2,
    "LOSS": 'dice',
    "DROPOUT":0.1,
    "DROPOUT_CHANGE_PER_LAYER":0.0,
    "DROPOUT_TYPE":"standard",
    "USE_DROPOUT_ON_UPSAMPLING":False,
    "ROOT_STRING": 'Substrate_inclShadow',
    "FILTER_VALUE": 3,
    "DOPLOT": True,
    "USEMASK": True,
    "RAMPUP_EPOCHS": 10,
    "SUSTAIN_EPOCHS": 0.0,
    "EXP_DECAY": 0.9,
    "START_LR":  1e-7,
    "MIN_LR": 1e-7,
    "MAX_LR": 1e-4,
    "AUG_ROT": 0,
    "AUG_ZOOM": 0.0,
    "AUG_WIDTHSHIFT": 0.05,
    "AUG_HEIGHTSHIFT": 0.05,
    "AUG_HFLIP": True,
    "AUG_VFLIP": False,
    "AUG_LOOPS": 3,
    "AUG_COPIES": 3,
    "TESTTIMEAUG": False,
    "SET_GPU": '0',
    "DO_CRF": False,
    "SET_PCI_BUS_ID": True,
    "TESTTIMEAUG": False,
    "WRITE_MODELMETADATA": True,
    "OTSU_THRESHOLD": True,
    "MODE": 'all',
    "REMAP_CLASSES": {
        "0": 0,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 0
    },
    "MY_CLASS_NAMES": {
        "0": "NoData",
        "1": "Fines Ripple",
        "2": "Fines Flat",
        "3": "Cobble Boulder",
        "4": "Hard Bottom",
        "5": "Wood",
        "6": "Other",
        "7": "Shadow",
        "8": "Water - NoData"
    }
    }

###########
# Functions

# def doWork(d, c, f, train, test):
def doWork(mDir, c, dataset_path):
    # Set output directory
    os.chdir(mDir)

    # Save configuration to file
    ## Create config file dir
    configfile = os.path.join(mDir, 'config')
    if not os.path.exists(configfile):
        os.mkdir(configfile)

    # Set config file name
    configfile = os.path.join(configfile, os.path.split(mDir)[-1]+'.json')

    # Save configuration file
    with open(configfile, 'w') as f:
        json.dump(c, f, indent=4)
        f.close()

    # Use MODE to specify aug, non aug, all files
    if 'MODE' not in c.keys():
        c['MODE'] = 'all'

    if c['MODE'] == 'all':
        npSuffix = '*.npz'

    elif c['MODE'] == 'noaug':
        npSuffix = '*noaug*.npz'

    else:
        npSuffix = '*_aug*.npz'

    # Get npzs
    npzs = []
    for d in dataset_path:
        np = glob(os.path.join(d, npSuffix))
        npzs += np

    # npzs = npzs[:300] # For testing

    # Save to csv
    # Create dataset path
    data_path = os.path.join(mDir, 'datasets')
    if not os.path.exists(data_path):
        os.mkdir(data_path)

    # Convert list to dataframe and save
    df = pd.DataFrame(npzs, columns=['Files'])

    npzCsv = os.path.join(data_path, 'datasets.csv')
    df.to_csv(npzCsv, index=False)


    # Train model
    # doModelTrain(configfile, train)
    model_file = '/mnt/md0/SynologyDrive/Modeling/segmentation_gym/train_model.py'
    os.system("python "+model_file+" "+configfile+" "+npzCsv)
    gc.collect()


######
# Main

doWork(outDir, config, dataset_path)
