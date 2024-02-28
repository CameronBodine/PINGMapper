

'''
***********************************************
WARNING: Not intended for general use but may 
serve as a template for creating new workflows.
***********************************************

Bar graphs comparing raw and egn substrate quantity per class.
'''

#########
# Imports
import sys, os
from glob import glob
import pandas as pd
import plotnine as p9
import numpy as np

############
# Parameters

summaryLengths =[1000]
substrateModels = ['Raw', 'EGN']

csvDir = '04_Substrate_Shps_Summary_All_Plots'
outDir = '05_Substrate_Shps_Raw_EGN_Compare'

# topDir = r'E:\SynologyDrive\GulfSturgeonProject\SSS_Data_Processed\Substrate_Summaries'
topDir = r'S:\GulfSturgeonProject\SSS_Data_Processed\Substrate_Summaries'
outDir = os.path.join(topDir, outDir)

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

topDir = os.path.normpath(topDir)
csvDir = os.path.normpath(csvDir)
outDir = os.path.normpath(outDir)

if not os.path.exists(outDir):
    os.makedirs(outDir)


###########
# Functions
def prep_df(df, k, model):

    # Get column names
    cols = df.columns.values

    # Get non substrate columns
    sub_cols = [f for f in cols if k in f]
    # cols_2_keep = ['river_code', 'rkm', 'sinuosity'] + sub_cols
    # cols_2_keep = ['river_code', 'rkm'] + sub_cols
    cols_2_keep = ['river_code', 'mapped_area'] + sub_cols

    # Get only the columns needed
    df = df.loc[:, cols_2_keep]

    # for k, v in d2m.items():
    #     df.loc[df['river_code'] == k, 'rkm'] = df.loc[df['river_code'] == k, 'rkm'] + v

    # # Convert meters to km
    # if length > 500:
    #     df['rkm'] = df['rkm'].div(1000).round(0).astype(int)
    # else:
    #     df['rkm'] = df['rkm'].div(1000).round(1)

    # Update basin name
    for k, v in rivBasin.items():
        df.loc[df['river_code'] == k, 'basin'] = v

    # Update river name
    for k, v in rivCodeName.items():
        df.loc[df['river_code'] == k, 'river_code'] = v

    # Convert m2 to hectare
    df['mapped_area_ha'] = np.around(df['mapped_area'] * 0.0001, 2)

    # Calculate substrate hectare
    new_cols = ['river_code', 'basin', 'model']
    for col in sub_cols:
        new_col = col[:-5]
        new_col = new_col.replace('_', ' ')
        new_cols.append(new_col)
        df[new_col] = np.around(df[col] * df['mapped_area_ha'], 2)

    # Remove proportion columns
    for col in sub_cols:
        df = df.drop(col, axis=1)

    df = df.drop('mapped_area', axis=1)
    df = df.drop('mapped_area_ha', axis=1)

    # Add model to columns
    df['Model'] = model

    # Sum columns
    df = df.groupby(['river_code', 'basin', 'Model']).agg(['sum'])
    df = df.reset_index()
    df.columns = df.columns.droplevel(-1)

    return df
    
def makeSubBarComparePlot(df, out):

    subColors = {'Fines Ripple': '#DC3912', 
                 'Fines Flat': '#FF9900',
                 'Cobble Boulder': '#15C820',
                 'Hard Bottom': '#990099',
                 'Wood': '#0091BC',
                 'Other': '#DD4477'}

    gg = p9.ggplot(df, p9.aes(x='Model', y='Area [ha]', fill='Substrate')) +\
         p9.theme_bw() +\
         p9.theme(figure_size=(10,10))+\
         p9.geom_col(position='dodge') +\
         p9.labels.xlab('Substrate')+\
         p9.facet_grid('Substrate~river_code+basin', scales='free') +\
         p9.scale_fill_manual(values=subColors)+\
         p9.ggtitle("Raw and EGN Substrate Area Comparison")
    p9.ggsave(gg, out, dpi=300)
        
    
    gg = p9.ggplot(df, p9.aes(x='Model', y='Area [ha]', fill='Substrate')) +\
         p9.theme_bw() +\
         p9.theme(figure_size=(10,12))+\
         p9.geom_col(position='stack') +\
         p9.labels.xlab('Substrate')+\
         p9.facet_grid('.~river_code+basin', scales='free') +\
         p9.scale_fill_manual(values=subColors)+\
         p9.ggtitle("Raw and EGN Substrate Area Comparison")
        
    
    out = out.replace('.png', 'areacheck.png')
    p9.ggsave(gg, out, dpi=300)
    return
#########
# Do Work
    
# Iterate each summary length
for length in summaryLengths:

    # Get csvs to dataframe
    for model in substrateModels:
        csvd = os.path.join(topDir, csvDir, model)

        csvFile = '_'.join([model, 'ALL', str(length), 'summary.csv'])
        csvFile = os.path.join(csvd, csvFile)

        df = pd.read_csv(csvFile)
        df = prep_df(df, 'prop', model)

        if 'dfAll' not in locals():
            dfAll = df
        else:
            dfAll = pd.concat([dfAll, df])

    # Melt dfAll
    dfPlot = dfAll.melt(id_vars=['river_code', 'basin', 'Model'],
                       var_name='Substrate',
                       value_name='Area [ha]')
    
    # # Make substrate/rkm categorical
    dfPlot['Substrate'] = pd.Categorical(dfPlot['Substrate'], ['Fines Ripple', 'Fines Flat', 'Cobble Boulder', 'Hard Bottom', 'Wood', 'Other'])
    dfPlot['Model'] = pd.Categorical(dfPlot['Model'], ['Raw', 'EGN'])
    dfPlot['river_code'] =pd.Categorical(dfPlot['river_code'], riverNames)

    # Make bar chart for comparison
    outPlot = '_'.join([str(length), 'Raw_EGN_SubstratePerRiver.png'])
    outPlot = os.path.join(outDir, outPlot)
    makeSubBarComparePlot(dfPlot, outPlot)
    
    outFile = outPlot.replace('.png', '.csv')
    dfAll.to_csv(outFile)

    sys.exit()
    del dfAll