

'''
***********************************************
WARNING: Not intended for general use but may 
serve as a template for creating new workflows.
***********************************************

Generate summary plots from summary csv's
'''

#########
# Imports
import sys, os
from glob import glob
import pandas as pd
import plotnine as p9
import numpy as np
from scipy.interpolate import splprep, splev


############
# Parameters

summaryLengths =[500, 1000, 5000, 10000]
riverCodes = ['BCH', 'PRL', 'BOU', 'LEA', 'PAS', 'CHI', 'CHU']
riverNames = ['Bogue Chitto R.', 'Pearl R.', 'Bouie R.', 'Leaf R.', 'Pascagoula R.', 'Chickasawhay R.', 'Chunky R.']

d2m = {'PRL': 0,
       'BCH': 81500,
       'PAS': 0,
       'LEA': 131000,
       'CHI': 131000,
       'BOU': 131000+119000,
       'CHU': 131000+261000
       }

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

substrateOutput = 'Raw'
csvDir = '04_Substrate_Shps_Summary_All_Plots'
outDir = '04_Substrate_Shps_Summary_All_Plots'

# topDir = r'E:\SynologyDrive\GulfSturgeonProject\SSS_Data_Processed\Substrate_Summaries'
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
    
def prep_df(df, k):

    # Get column names
    cols = df.columns.values

    # Get non substrate columns
    sub_cols = [f for f in cols if k in f]
    # cols_2_keep = ['river_code', 'rkm', 'sinuosity'] + sub_cols
    cols_2_keep = ['river_code', 'rkm'] + sub_cols

    # Get only the columns needed
    df = df.loc[:, cols_2_keep]

    for k, v in d2m.items():
        df.loc[df['river_code'] == k, 'rkm'] = df.loc[df['river_code'] == k, 'rkm'] + v

    # Convert meters to km
    if length > 500:
        df['rkm'] = df['rkm'].div(1000).round(0).astype(int)
    else:
        df['rkm'] = df['rkm'].div(1000).round(1)

    # Update basin name
    for k, v in rivBasin.items():
        df.loc[df['river_code'] == k, 'basin'] = v

    # Update river name
    for k, v in rivCodeName.items():
        df.loc[df['river_code'] == k, 'river_code'] = v

    # # Add west to east
    # df['location'] = 'Western Extent <---------> Eastern Extent'

    return df

def df_for_wid(csv):
    # Open
    df = pd.read_csv(csv)

    # Prep the df
    df = prep_df(df, 'width')

    # Make categorical
    df['RKM'] = df['rkm'].astype('category')
    # df['river_code'] =pd.Categorical(df['river_code'], riverCodes)
    df['river_code'] =pd.Categorical(df['river_code'], riverNames)

    return df

def df_for_sin(csv):
    # Open
    df = pd.read_csv(csv)

    # Prep the df
    df = prep_df(df, 'sinuosity')

    # Make categorical
    df['RKM'] = df['rkm'].astype('category')
    # df['river_code'] =pd.Categorical(df['river_code'], riverCodes)
    df['river_code'] =pd.Categorical(df['river_code'], riverNames)

    # Set zeros to 1
    df.loc[df['sinuosity'] < 1, 'sinuosity'] = 1

    return df
    
def df_for_dep(csv):

    # Open
    df = pd.read_csv(csv)

    # Prep the df
    df = prep_df(df, 'dep')

    # Make categorical
    df['RKM'] = df['rkm'].astype('category')
    # df['river_code'] =pd.Categorical(df['river_code'], riverCodes)
    df['river_code'] =pd.Categorical(df['river_code'], riverNames)

    # Make depth negative
    dep_cols = [f for f in df.columns if 'dep' in f]
    for c in dep_cols:
        df[c] = df[c]*-1

    return df
    
def df_for_substrate(csv):

    # Open
    df = pd.read_csv(csv)

    # Prep the df
    df = prep_df(df, 'prop')

    # Melt df
    df = df.melt(id_vars=['river_code', 'rkm', 'basin'],
                 var_name='Substrate',
                 value_name='Proportion')
    
    # Update substrate name
    df['Substrate'] = df['Substrate'].apply(lambda x: x.replace('_prop', '').replace('_', ' '))

    # Make substrate/rkm categorical
    df['Substrate'] = pd.Categorical(df['Substrate'], ['Fines Ripple', 'Fines Flat', 'Cobble Boulder', 'Hard Bottom', 'Wood', 'Other'])
    df['RKM'] = df['rkm']
    
    # df['river_code'] =pd.Categorical(df['river_code'], riverCodes)
    df['river_code'] =pd.Categorical(df['river_code'], riverNames)

    return df

def makeSubRKMPlot(df, out, length):

    # Bar width
    if length == 500:
        w=1
        # Need decimals for half km
        df['RKM'] = df['RKM'].astype(float)
        title = str(np.round(length/1000, 1))
    else:
        w = length/1000
        # Don't need decimal since whole km's
        df['RKM'] = df['RKM'].astype(int)
        title = str(int(np.round(length/1000, 0)))

    # Tick labels
    maxRkm = np.max(df['RKM'].to_numpy())
    x_ticks = np.arange(0, maxRkm+10, 10)
    x_ticks_labels = x_ticks.tolist()

    subColors = {'Fines Ripple': '#DC3912', 
                 'Fines Flat': '#FF9900',
                 'Cobble Boulder': '#15C820',
                 'Hard Bottom': '#990099',
                 'Wood': '#0091BC',
                 'Other': '#DD4477'}

    gg = p9.ggplot(df, p9.aes(x='RKM', y='Proportion', fill='Substrate'))+\
         p9.theme_bw()+\
         p9.theme(figure_size=(10,12))+\
         p9.theme(axis_text_x=p9.element_text(rotation=90, hjust=0.5, vjust=1))+\
         p9.labels.xlab('In-stream Distance to Gulf of Mexico [km]')+\
         p9.scale_x_continuous(breaks=x_ticks_labels, labels=x_ticks_labels)+\
         p9.geom_col(width=w)+\
         p9.scale_fill_manual(values=subColors)+\
         p9.facet_grid('river_code+basin~.') +\
         p9.ggtitle(title+" km Reach Summary")
    
    p9.ggsave(gg, out, dpi=300)
    return

def makeSubRKMPlot2(df, out, length):

    # Bar width
    if length == 500:
        w=1
        # Need decimals for half km
        df['RKM'] = df['RKM'].astype(float)
        title = str(np.round(length/1000, 1))
    else:
        w = length/1000
        # Don't need decimal since whole km's
        df['RKM'] = df['RKM'].astype(int)
        title = str(int(np.round(length/1000, 0)))

    # Tick labels
    maxRkm = np.max(df['RKM'].to_numpy())
    x_ticks = np.arange(0, maxRkm+10, 100)
    x_ticks_labels = x_ticks.tolist()

    subColors = {'Fines Ripple': '#DC3912', 
                 'Fines Flat': '#FF9900',
                 'Cobble Boulder': '#15C820',
                 'Hard Bottom': '#990099',
                 'Wood': '#0091BC',
                 'Other': '#DD4477'}

    gg = p9.ggplot(df, p9.aes(x='RKM', y='Proportion', fill='Substrate'))+\
         p9.theme_bw()+\
         p9.theme(figure_size=(10,12))+\
         p9.theme(axis_text_x=p9.element_text(rotation=90, hjust=0.5, vjust=1))+\
         p9.labels.xlab('In-stream Distance to Gulf of Mexico [km]')+\
         p9.scale_x_continuous(breaks=x_ticks_labels, labels=x_ticks_labels)+\
         p9.geom_col(width=w)+\
         p9.scale_fill_manual(values=subColors)+\
         p9.facet_grid('Substrate~river_code+basin', scales='free') +\
         p9.ggtitle(title+" km Reach Summary")
    
    p9.ggsave(gg, out, dpi=300)
    return

def makeDepRKMAreaPlot(df, out, length):
     # Bar width
    if length == 500:
        w=1
        # Need decimals for half km
        df['RKM'] = df['RKM'].astype(float)
        title = str(np.round(length/1000, 1))
    else:
        w = length/1000
        # Don't need decimal since whole km's
        df['RKM'] = df['RKM'].astype(int)
        title = str(int(np.round(length/1000, 0)))

    # Tick labels
    minRkm = np.min(df['RKM'].to_numpy())
    maxRkm = np.max(df['RKM'].to_numpy())
    x_ticks = np.arange(0, maxRkm+10, 10)
    x_ticks_labels = x_ticks.tolist()

    # gg = p9.ggplot()+\
    #      p9.theme_bw()+\
    #      p9.theme(figure_size=(10,8))+\
    #      p9.theme(axis_text_x=p9.element_text(rotation=90, hjust=0.5, vjust=1))+\
    #      p9.labels.xlab('In-stream Distance to Gulf of Mexico [km]')+\
    #      p9.labels.ylab('Depth [m]')+\
    #      p9.scale_x_continuous(breaks=x_ticks_labels, labels=x_ticks_labels)+\
    #      p9.geom_ribbon(p9.aes(x='RKM',ymin='dep_m_whisklo', ymax='dep_m_whiskhi'), fill='royalblue', alpha= 0.35, data=df)+\
    #      p9.geom_ribbon(p9.aes(x='RKM',ymin='dep_m_q1', ymax='dep_m_q3'), fill='royalblue', alpha= 0.35, data=df)+\
    #      p9.geom_line(p9.aes(x='RKM',y='dep_m_q2'), colour='royalblue', linetype='dashed', data=df)+\
    #      p9.ylim(-10, 0)+\
    #      p9.facet_grid('river_code+basin~.') +\
    #      p9.ggtitle(title+" km Reach Summary")

    gg = p9.ggplot()+\
         p9.theme_bw()+\
         p9.theme(figure_size=(10,12))+\
         p9.theme(axis_text_x=p9.element_text(rotation=90, hjust=0.5, vjust=1))+\
         p9.labels.xlab('In-stream Distance to Gulf of Mexico [km]')+\
         p9.labels.ylab('Depth [m]')+\
         p9.scale_x_continuous(breaks=x_ticks_labels, labels=x_ticks_labels)+\
         p9.geom_ribbon(p9.aes(x='RKM',ymin='dep_m_whisklo', ymax='dep_m_whiskhi', fill="'darkgrey'"), alpha= 0.5, data=df)+\
         p9.geom_ribbon(p9.aes(x='RKM',ymin='dep_m_q1', ymax='dep_m_q3', fill="'royalblue'"), alpha= 0.5, data=df)+\
         p9.geom_line(p9.aes(x='RKM',y='dep_m_q2', colour="'midnightblue'"), linetype='dashed', data=df)+\
         p9.scale_color_identity(guide='legend', name='Median', breaks=['midnightblue'], labels=['Median'])+\
         p9.scale_fill_identity(guide='legend', name='Quantiles', breaks=['darkgrey', 'royalblue'], labels=['98% Quantile', '50% Quantile'])+\
         p9.theme(legend_title=p9.element_blank())+\
         p9.ylim(-10, 0)+\
         p9.facet_grid('river_code+basin~.') +\
         p9.ggtitle(substrateOutput+': '+title+" km Reach Summary")

    p9.ggsave(gg, out, dpi=300)
    return

def makeDepRKMBoxPlot(df, out):

    # Bar width
    if length == 500:
        w=1
        # Need decimals for half km
        df['RKM'] = df['RKM'].astype(float)
        title = str(np.round(length/1000, 1))
    else:
        w = length/1000
        # Don't need decimal since whole km's
        df['RKM'] = df['RKM'].astype(int)
        title = str(int(np.round(length/1000, 0)))

    # Tick labels
    minRkm = np.min(df['RKM'].to_numpy())
    maxRkm = np.max(df['RKM'].to_numpy())
    x_ticks = np.arange(0, maxRkm+10, 10)
    x_ticks_labels = x_ticks.tolist()

    gg = p9.ggplot()+\
         p9.theme_bw()+\
         p9.theme(figure_size=(10,12))+\
         p9.theme(axis_text_x=p9.element_text(rotation=90, hjust=0.5, vjust=1))+\
         p9.labels.xlab('In-stream Distance to Gulf of Mexico [km]')+\
         p9.labels.ylab('Depth [m]')+\
         p9.scale_x_continuous(breaks=x_ticks_labels, labels=x_ticks_labels)+\
         p9.geom_crossbar(p9.aes(x='RKM', y='dep_m_q2', ymin='dep_m_q1', ymax='dep_m_q3'), width=w, colour='royalblue', data=df)+\
         p9.geom_errorbar(p9.aes(x='RKM', ymin='dep_m_whisklo', ymax='dep_m_whiskhi'), width=w, colour='royalblue', alpha=0.75, data=df)+\
         p9.ylim(0, 10)+\
         p9.facet_grid('river_code+basin~.')+\
         p9.ggtitle(substrateOutput+': '+title+" km Reach Summary")
    
    p9.ggsave(gg, out, dpi=300)

    return

def makeWidRKMAreaPlot(df, out, length):
     # Bar width
    if length == 500:
        w=1
        # Need decimals for half km
        df['RKM'] = df['RKM'].astype(float)
        title = str(np.round(length/1000, 1))
    else:
        w = length/1000
        # Don't need decimal since whole km's
        df['RKM'] = df['RKM'].astype(int)
        title = str(int(np.round(length/1000, 0)))

    # Tick labels
    minRkm = np.min(df['RKM'].to_numpy())
    maxRkm = np.max(df['RKM'].to_numpy())
    x_ticks = np.arange(0, maxRkm+10, 10)
    x_ticks_labels = x_ticks.tolist()

    gg = p9.ggplot()+\
         p9.theme_bw()+\
         p9.theme(figure_size=(10,12))+\
         p9.theme(axis_text_x=p9.element_text(rotation=90, hjust=0.5, vjust=1))+\
         p9.labels.xlab('In-stream Distance to Gulf of Mexico [km]')+\
         p9.labels.ylab('Width [m]')+\
         p9.scale_x_continuous(breaks=x_ticks_labels, labels=x_ticks_labels)+\
         p9.geom_ribbon(p9.aes(x='RKM',ymin='width_whisklo', ymax='width_whiskhi', fill="'darkgrey'"), alpha= 0.5, data=df)+\
         p9.geom_ribbon(p9.aes(x='RKM',ymin='width_q1', ymax='width_q3', fill="'olivedrab'"), alpha= 0.35, data=df)+\
         p9.geom_line(p9.aes(x='RKM', y='width_q2', colour="'olive'"), linetype='dashed', data=df)+\
         p9.scale_color_identity(guide='legend', name='Median', breaks=['olive'], labels=['Median'])+\
         p9.scale_fill_identity(guide='legend', name='Quantiles', breaks=['darkgrey', 'olivedrab'], labels=['98% Quantile', '50% Quantile'])+\
         p9.theme(legend_title=p9.element_blank())+\
         p9.facet_grid('river_code+basin~.') +\
         p9.ggtitle(substrateOutput+': '+title+" km Reach Summary")

    p9.ggsave(gg, out, dpi=300)
    return

def makeWidRKMBoxPlot(df, out, length):

    # Bar width
    if length == 500:
        w=1
        # Need decimals for half km
        df['RKM'] = df['RKM'].astype(float)
        title = str(np.round(length/1000, 1))
    else:
        w = length/1000
        # Don't need decimal since whole km's
        df['RKM'] = df['RKM'].astype(int)
        title = str(int(np.round(length/1000, 0)))

    # Tick labels
    minRkm = np.min(df['RKM'].to_numpy())
    maxRkm = np.max(df['RKM'].to_numpy())
    x_ticks = np.arange(0, maxRkm+10, 10)
    x_ticks_labels = x_ticks.tolist()

    gg = p9.ggplot()+\
         p9.theme_bw()+\
         p9.theme(figure_size=(10,12))+\
         p9.theme(axis_text_x=p9.element_text(rotation=90, hjust=0.5, vjust=1))+\
         p9.labels.xlab('In-stream Distance to Gulf of Mexico [km]')+\
         p9.labels.ylab('Mapped Width [m]')+\
         p9.geom_crossbar(p9.aes(x='RKM', y='width_q2', ymin='width_q1', ymax='width_q3'), width=w, colour='olivedrab', data=df)+\
         p9.geom_errorbar(p9.aes(x='RKM', ymin='width_whisklo', ymax='width_whiskhi'), width=w, colour='olivedrab', alpha=0.75, data=df)+\
         p9.facet_grid('river_code+basin~.')+\
         p9.ggtitle(substrateOutput+': '+title+" km Reach Summary")
    
    p9.ggsave(gg, out, dpi=300)

    return

def makeSinRKMLinePlot(df, out, length):

    # Bar width
    if length == 500:
        w=1
        # Need decimals for half km
        df['RKM'] = df['RKM'].astype(float)
        title = str(np.round(length/1000, 1))
    else:
        w = length/1000
        # Don't need decimal since whole km's
        df['RKM'] = df['RKM'].astype(int)
        title = str(int(np.round(length/1000, 0)))

    # Tick labels
    minRkm = np.min(df['RKM'].to_numpy())
    maxRkm = np.max(df['RKM'].to_numpy())
    x_ticks = np.arange(0, maxRkm+10, 10)
    x_ticks_labels = x_ticks.tolist()

    gg = p9.ggplot()+\
         p9.theme_bw()+\
         p9.theme(figure_size=(10,12))+\
         p9.theme(axis_text_x=p9.element_text(rotation=90, hjust=0.5, vjust=1))+\
         p9.labels.xlab('In-stream Distance to Gulf of Mexico [km]')+\
         p9.labels.ylab('Sinuosity')+\
         p9.geom_line(p9.aes(x='RKM', y='sinuosity'), colour='darkorchid', data=df)+\
         p9.facet_grid('river_code+basin~.')+\
         p9.ggtitle(substrateOutput+': '+title+" km Reach Summary")
    
    p9.ggsave(gg, out, dpi=300)

    return


#########
# Do Work

# Iterate each summary length
for length in summaryLengths:

    # In order to keep the summaries at whole numbers (500, 1000, 1500, etc.), find the next whole value downstream
    # based on summary distance
    for k, v in d2m.items():
        v = length * round(v/length)
        d2m[k] = v

    # Get csv
    csvFile = '_'.join([substrateOutput, 'ALL', str(length), 'summary.csv'])
    csvFile = os.path.join(csvDir, csvFile)


    ###############
    # Substrate RKM

    # Get substrate dataframe
    dfSub = df_for_substrate(csvFile)

    # Make RKM summary
    outPlot = '_'.join([substrateOutput, 'ALL', str(length), 'Substrate_RKM_Summary.png'])
    outPlot = os.path.join(outDir, outPlot)

    makeSubRKMPlot(dfSub, outPlot, length)

    # Make RKM summary
    outPlot = '_'.join([substrateOutput, 'ALL', str(length), 'Substrate_RKM_Summary2.png'])
    outPlot = os.path.join(outDir, outPlot)

    makeSubRKMPlot2(dfSub, outPlot, length)

    del dfSub

    #############################
    # Depth RKM

    dfDep = df_for_dep(csvFile)

    # # Make RKM summary Boxplot
    # outPlot = '_'.join([substrateOutput, 'ALL', str(length), 'Depth_Box_RKM_Summary.png'])
    # outPlot = os.path.join(outDir, outPlot)
    # makeDepRKMBoxPlot(dfDep, outPlot)

    # Make RKM summary Boxplot
    outPlot = '_'.join([substrateOutput, 'ALL', str(length), 'Depth_Area_RKM_Summary.png'])
    outPlot = os.path.join(outDir, outPlot)
    makeDepRKMAreaPlot(dfDep, outPlot, length)

    del dfDep

    # sys.exit()

    #############################
    # Width RKM

    dfWid = df_for_wid(csvFile)

    # # Make RKM summary Boxplot
    # outPlot = '_'.join([substrateOutput, 'ALL', str(length), 'Width_Box_RKM_Summary.png'])
    # outPlot = os.path.join(outDir, outPlot)
    # makeWidRKMBoxPlot(dfWid, outPlot, length)

    # Make RKM summary Area
    outPlot = '_'.join([substrateOutput, 'ALL', str(length), 'Width_Area_RKM_Summary.png'])
    outPlot = os.path.join(outDir, outPlot)
    makeWidRKMAreaPlot(dfWid, outPlot, length)

    del dfWid

    ###############
    # Sinuosity RKM

    dfSin = df_for_sin(csvFile)

    # Make RKM summary Line
    outPlot = '_'.join([substrateOutput, 'ALL', str(length), 'Sinuosity_Line_RKM_Summary.png'])
    outPlot = os.path.join(outDir, outPlot)
    makeSinRKMLinePlot(dfSin, outPlot, length)


    # sys.exit()
