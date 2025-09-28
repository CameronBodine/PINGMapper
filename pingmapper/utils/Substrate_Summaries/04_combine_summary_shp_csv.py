

'''
***********************************************
WARNING: Not intended for general use but may 
serve as a template for creating new workflows.
***********************************************

Combine summary csv for each river and distance into single csv
'''



#########
# Imports
import sys, os
from glob import glob
import pandas as pd

############
# Parameters
river_codes = ['BCH', 'PRL', 'PAS','BOU', 'LEA', 'CHI', 'CHU']
# river_codes = ['PRL']
summaryLengths = [500, 1000, 5000, 10000]

substrateOutput = 'Raw'
csvDir = '03_Substrate_Shps_Summary'
outDir = '04_Substrate_Shps_Summary_All_Plots'

topDir = r'D:\redbo_science\projects\GulfSturgeonProject_2025\ProcessedData\Substrate_Summaries'
csvDir = os.path.join(topDir, csvDir, substrateOutput)
outDir = os.path.join(topDir, outDir, substrateOutput)

topDir = os.path.normpath(topDir)
csvDir = os.path.normpath(csvDir)
outDir = os.path.normpath(outDir)

if not os.path.exists(outDir):
    os.makedirs(outDir)

###########
# Functions

#########
# Do Work

# Iterate each summary length
for length in summaryLengths:

    # Iterate each river
    for river in river_codes:

        # Get the csv
        csvPattern = '_'.join([substrateOutput, river, str(length), 'summary.csv'])
        csvFile = os.path.join(csvDir, csvPattern)

        # Open the csv
        csv = pd.read_csv(csvFile)

        # Add summary distance to df
        csv['summary_dist'] = length

        # Combine
        if 'csvAll' not in locals():
            csvAll = csv
        else:
            csvAll = pd.concat([csvAll, csv])

    # Save to file
    outFile = '_'.join([substrateOutput, 'ALL', str(length), 'summary.csv'])
    outFile = os.path.join(outDir, outFile)
    csvAll.to_csv(outFile, index=False)    

    del csvAll