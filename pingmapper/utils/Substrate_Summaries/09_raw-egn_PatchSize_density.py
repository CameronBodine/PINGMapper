
'''
***********************************************
WARNING: Not intended for general use but may 
serve as a template for creating new workflows.
***********************************************

Generate density curves for substrate poly patch size
faceted by substrate type (or river??)
'''

#########
# Imports
import sys, os
from glob import glob
import pandas as pd
import geopandas as gpd
import plotnine as p9
import numpy as np

############
# Parameters
# substrateShpsDir = r'S:\GulfSturgeonProject\SSS_Data_Processed\Substrate_Summaries\02_Substrate_Shps_Mosaic_Transects'
substrateShpsDir = r'D:\redbo_science\projects\GulfSturgeonProject_2025\ProcessedData\Substrate_Summaries\02_Substrate_Shps_Mosaic_Transects'
outDir = os.path.join(os.path.dirname(substrateShpsDir), '09_raw-egn_PatchSize_density')

outFolderNames = ['Raw']

classOrder = ['Fines Ripple', 'Fines Flat', 'Cobble Boulder', 'Hard Bottom', 'Wood']

rivCodeName = {'PRL': 'Pearl R.',
               'BCH': 'Bogue Chitto R.',
               'PAS': 'Pascagoula R.',
               'LEA': 'Leaf R.',
               'CHI': 'Chickasawhay R.',
               'BOU': 'Bouie R.',
               'CHU': 'Chunky R.'
                }

if not os.path.exists(outDir):
    os.makedirs(outDir)

###########
# Functions

def prep_df(f):

    # Open shapefile
    df = gpd.read_file(f)

    df = df[['Name', 'Area_m', 'geometry']]

    df = df.rename(columns={'Name': 'Substrate'})

    # Add river name
    river = os.path.basename(f).split('_')[0]
    df['River'] = rivCodeName[river]

    return df

def slicePercentile(df, by, l=0.01, u=0.99):

    dfOut = pd.DataFrame()
    col = 'Area_m'

    for name, group in df.groupby(by):
        
        # Get percentiles
        lp = np.quantile(df[col].to_numpy(), l)
        up = np.quantile(df[col].to_numpy(), u)
        
        group = group.loc[group[col] >= lp]
        group = group.loc[group[col] <= up]

        dfOut = pd.concat([dfOut, group], ignore_index=True)

    return dfOut

def sliceOutliers(df, by):
    dfOut = pd.DataFrame()
    col = 'Area_m'

    for name, group in df.groupby(by):
        
        vals = df[col].to_numpy()
        
        # # Get percentiles
        # lp = np.quantile(df[col].to_numpy(), l)
        # up = np.quantile(df[col].to_numpy(), u)

        q1, q3 = np.percentile(vals, [25,75])
        iqr = q3-q1

        l = q1 - 1.5*iqr
        u = q3 + 1.5*iqr

        group = group.loc[group[col] > l]
        group = group.loc[group[col] < u]

        dfOut = pd.concat([dfOut, group], ignore_index=True)
    
    return dfOut



def makeDensityPlot(df, out, facet, ncol=3):

    # # Slice each facet by percentage
    # df = slicePercentile(df, facet, l=0, u=0.75)

    # Remove outliers
    df = sliceOutliers(df, facet)

    gg = p9.ggplot(df, p9.aes(x='Area_m', color='Model'))+\
         p9.theme_classic()+\
         p9.theme(figure_size=(12,8))+\
         p9.geom_density()+\
         p9.scale_color_grey() +\
         p9.labels.xlab('Patch Size [m2]')+\
         p9.facet_wrap(facet, ncol=ncol)
    
    p9.ggsave(gg, out, dpi=300)


    return

def makeBoxPlot(df, out, facet):

    # # Slice each facet by percentage
    # df = slicePercentile(df, facet, l=0, u=0.75)

    # Remove outliers
    df = sliceOutliers(df, facet)

    gg = p9.ggplot(df, p9.aes(x='Model', y='Area_m'))+\
         p9.theme_bw()+\
         p9.theme(figure_size=(12,8))+\
         p9.geom_boxplot()+\
         p9.labels.ylab('Patch Size [m2]')+\
         p9.facet_wrap(facet)
    
    p9.ggsave(gg, out, dpi=300)
    return

#########
# Do Work

shpAll = gpd.GeoDataFrame()

for dir in outFolderNames:

    # Get shapefiles
    shpFiles = '*_postproc.shp'
    shpFiles = os.path.join(substrateShpsDir, dir, shpFiles)
    shpFiles = glob(shpFiles)

    for shp in shpFiles:
        shp = prep_df(shp)

        shp['Model'] = dir
        
        if 'shpAllDir' not in locals():
            shpAllDir = shp
        else:
            shpAllDir = pd.concat([shpAllDir, shp], ignore_index=True)

    shpAll = pd.concat([shpAll, shpAllDir], ignore_index=True)
    del shpAllDir

shpAllFile = os.path.join(outDir, 'All_River_Model_Maps.shp')
# shpAll.to_file(shpAllFile)

shpAllFile = os.path.join(outDir, 'All_River_Model_Maps.shp')
# shpAll = gpd.read_file(shpAllFile)

# Drop geometry column
df = shpAll.drop(columns='geometry')
del shpAll

dfFile = shpAllFile.replace('.shp', '.csv')
df.to_csv(dfFile)

dfFile = shpAllFile.replace('.shp', '.csv')
df = pd.read_csv(dfFile)

# Make density plot: substrate vs patch size
outPlot = '_'.join(['PatchSize_by_Substrate.png'])
outPlot = os.path.join(outDir, outPlot)

makeDensityPlot(df, outPlot, 'Substrate', ncol=3)


# Make density plot: substrate vs patch size
outPlot = '_'.join(['PatchSize_by_River.png'])
outPlot = os.path.join(outDir, outPlot)

makeDensityPlot(df, outPlot, 'River', ncol=3)

# Make Box and Whisker Plot
outPlot = '_'.join(['Box', 'PatchSize_by_Substrate.png'])
outPlot = os.path.join(outDir, outPlot)

makeBoxPlot(df, outPlot, 'Substrate')

# Make Box and Whisker Plot
outPlot = '_'.join(['Box', 'PatchSize_by_River.png'])
outPlot = os.path.join(outDir, outPlot)

makeBoxPlot(df, outPlot, 'River')
