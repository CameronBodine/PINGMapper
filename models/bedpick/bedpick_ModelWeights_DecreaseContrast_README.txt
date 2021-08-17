Orig Model Location: Z:\toProcess\bedPicking\forModelTraining\Models\Cam_20210724_DecreaseContrast_Allds

Initial training set size: 10,360
Image masks were derived from digitized bedpicks using SonarTRX on FWC data.

Decrease Contrast (Using DecreaseContrast_01.py):
For each image and mask pair, the mask was used to isolate water and bed regions.
For water region, the standard deviation of the intensity was calculated and was added to water pixels.
For bed region, the standard deviation of the intensity was calculated and was subtracted from bed pixels.

This resulted in 20,720 image/mask pairs.

Training datasets were then pre-processed using make_datasets.py w/ 2 augmentation copies.

This resulted in 41,440 datasets for training.

All model training and ds creation parameters are in Cam_20210724_DecreaseContrast_Allds.json.

Model training took approximately 82 hours.

