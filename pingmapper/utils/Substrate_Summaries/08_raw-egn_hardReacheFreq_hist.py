
'''
***********************************************
WARNING: Not intended for general use but may 
serve as a template for creating new workflows.
***********************************************

Generate histogram comparing count of 1-km reaches
with x proportion of hard substrates
'''


#########
# Imports
import sys, os
from glob import glob
import pandas as pd
import plotnine as p9
import numpy as np


summaryLengths =[500, 1000, 5000, 10000]
# summaryLengths = [500]
riverCodes = ['BCH', 'PRL', 'BOU', 'LEA', 'PAS', 'CHI', 'CHU']
riverNames = ['Bogue Chitto R.', 'Pearl R.', 'Bouie R.', 'Leaf R.', 'Pascagoula R.', 'Chickasawhay R.', 'Chunky R.']

rivCodeName = {'PRL': 'Pearl R.',
               'BCH': 'Bogue Chitto R.',
               'PAS': 'Pascagoula R.',
               'LEA': 'Leaf R.',
               'CHI': 'Chickasawhay R.',
               'BOU': 'Bouie R.',
               'CHU': 'Chunky R.'
                }

rivBasin = {'PRL': '[PRL Basin]',
            'BCH': '[PRL Basin]',
            'PAS': '[PAS Basin]',
            'LEA': '[PAS Basin]',
            'CHI': '[PAS Basin]',
            'BOU': '[PAS Basin]',
            'CHU': '[PAS Basin]'
            }

substrateOutputs = ['Raw']
csvTopDir = '04_Substrate_Shps_Summary_All_Plots'
outDir = '08_raw-egn_hardReacheFreq_hist'

# topDir = r'E:\SynologyDrive\GulfSturgeonProject\SSS_Data_Processed\Substrate_Summaries'
# topDir = r'S:\GulfSturgeonProject\SSS_Data_Processed\Substrate_Summaries'
topDir = r'D:\redbo_science\projects\GulfSturgeonProject_2025\ProcessedData\Substrate_Summaries'
topDir = os.path.normpath(topDir)


###########
# Functions
    
def prep_df(df, k):

    # Get column names
    cols = df.columns.values

    # Get non substrate columns
    sub_cols = [f for f in cols if k in f]
    # cols_2_keep = ['river_code', 'rkm', 'sinuosity'] + sub_cols
    cols_2_keep = ['river_code', 'rkm', 'mapped_area'] + sub_cols

    # Get only the columns needed
    df = df.loc[:, cols_2_keep]

    # Update basin name
    for k, v in rivBasin.items():
        df.loc[df['river_code'] == k, 'basin'] = v

    # Update river name
    for k, v in rivCodeName.items():
        df.loc[df['river_code'] == k, 'river_code'] = v
    

    # Get Hard Proportion
    df['Hard_prop'] = df['Cobble_Boulder_prop'] + df['Hard_Bottom_prop']

    df = df.fillna(0)

    return df
    

def df_for_patch_hist(csv):

    # Open
    df = pd.read_csv(csv)

    # Prep the df
    df = prep_df(df, 'prop')

    # Only columns we need
    df = df[['river_code', 'basin', 'mapped_area', 'Hard_prop']]

    df['river_code'] =pd.Categorical(df['river_code'], riverNames)

    df['Hard_prop'] = np.around(df['Hard_prop'], 2)

    return df


def makeFreqHist(df, out, length):

    binWidth = 0.05
    xlim = (0.1, 1.0)

    if length == 500:
        title = str(np.round(length/1000, 1))
    else:
        title = str(int(np.round(length/1000, 0)))

    gg = p9.ggplot(df, p9.aes(x='Hard_prop', color = 'Model'))+\
         p9.theme_classic()+\
         p9.theme(figure_size=(4,4))+\
         p9.geom_freqpoly(binwidth = binWidth)+\
         p9.xlim(xlim)+\
         p9.scale_color_grey() +\
         p9.labels.xlab('Hard Substrate Proportion: {}'.format(xlim))+\
         p9.labels.ylab('Reach Count')+\
         p9.ggtitle(title+" km Reach")
    
    p9.ggsave(gg, out, dpi=300)

    return

def makeFreqPolyRiver(df, out, length):
    binWidth = 0.05
    xlim = (0.1, 1.0)

    if length == 500:
        title = str(np.round(length/1000, 1))
    else:
        title = str(int(np.round(length/1000, 0)))

    gg = p9.ggplot(df, p9.aes(x='Hard_prop', color = 'Model'))+\
         p9.theme_classic()+\
         p9.theme(figure_size=(8,4))+\
         p9.geom_freqpoly(binwidth = binWidth)+\
         p9.xlim(xlim)+\
         p9.scale_color_grey() +\
         p9.labels.xlab('Hard Substrate Proportion: {}'.format(xlim))+\
         p9.labels.ylab('Reach Count')+\
         p9.ggtitle(title+" km Reach") +\
         p9.facet_wrap('river_code', scales='free_y', ncol=4)
    
    p9.ggsave(gg, out, dpi=300)

    return


def getStats(df, model, prop):

    reachCntTotal = len(df)
    # Calculate Area in ha
    df['Hard_Area'] = df['mapped_area'] * df['Hard_prop'] * 0.0001
    totalArea = np.around(df['Hard_Area'].sum(axis=0), 1)

    print('\nHard Substrate Stats for: {} | Proportion: {}'.format(model, prop))
    print('Total Patches > \t{}: \t{}'.format(prop, reachCntTotal))
    print('Total Area [ha] > \t{}: \t{}'.format(prop, totalArea))

    # Get rivers
    rivs = np.unique(df['river_code'].to_numpy(na_value='-'))

    for riv in rivs:
        rivdf = df.loc[df['river_code'] == riv]
        cnt = len(rivdf)
        area = np.around(rivdf['Hard_Area'].sum(axis=0), 1)

        print('\t{:20s}| Reach Count = {}\t\tArea [ha] = {}'.format(riv, cnt, area))



#########
# Do Work

# Iterate each summary length
for length in summaryLengths:

    for substrateOutput in substrateOutputs:
        csvDir = os.path.join(topDir, csvTopDir, substrateOutput)
        csvDir = os.path.normpath(csvDir)
        
        outDir = os.path.join(topDir, outDir)
        outDir = os.path.normpath(outDir)


        if not os.path.exists(outDir):
            os.makedirs(outDir)

        # Get csv
        csvFile = '_'.join([substrateOutput, 'ALL', str(length), 'summary.csv'])
        csvFile = os.path.join(csvDir, csvFile)

        # Get dataframe
        df = df_for_patch_hist(csvFile)

        # Add Model
        df['Model'] = substrateOutput

        # # Drop less then .1 (?)
        # df = df.loc[df['Hard_prop'] >= 0.05]

        if 'dfAll' not in locals():
            dfAll = df
        else:
            dfAll = pd.concat([dfAll, df], ignore_index=True)

    
    # Make fequency poly for all rivers
    outPlot = '_'.join(['ALL', str(length), 'Raw-EGN_HardReachFreq_hist.png'])
    outPlot = os.path.join(outDir, outPlot)

    makeFreqHist(dfAll, outPlot, length)

    # Make frequency poly facet wrap by river
    outPlot = '_'.join(['River', str(length), 'Raw-EGN_HardReachFreq_hist.png'])
    outPlot = os.path.join(outDir, outPlot)

    makeFreqPolyRiver(dfAll, outPlot, length)

    # Print a summary to report on

    bins = np.arange(0.2, 1, 0.2)
    for bin in bins:
        bin = np.around(bin, 1)
        print('\n\n\nHard Substrate Stats for Proportion > {}'.format(bin))
        df = dfAll.loc[dfAll['Hard_prop'] > bin]

        raw = df.loc[df['Model'] == 'Raw'].copy()
        egn = df.loc[df['Model'] == 'EGN'].copy()

        getStats(raw, 'Raw', bin)
        getStats(egn, 'EGN', bin)

    del dfAll