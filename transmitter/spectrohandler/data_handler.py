import numpy as np
import pandas as pd

from BaselineRemoval import BaselineRemoval

import logging
import requests

transmitterUrl = 'http://localhost:5500'

#Get all series
def getAllSeries():
    return requests.get(transmitterUrl + '/series/get-all-series').json()

def getSeriesRange(dateRange, pointsRange):
    queries = []
    if dateRange[0] != None:
        queries.append(f'sdate={dateRange[0]}')
    if dateRange[1] != None:
        queries.append(f'edate={dateRange[1]}')
    if pointsRange[0] != None:
        queries.append(f'ptsLower={pointsRange[0]}')
    if pointsRange[1] != None:
        queries.append(f'ptsUpper={pointsRange[1]}')

    query = '?'
    for q in queries:
        query += q + '&'

    return requests.get(transmitterUrl + f'/series/get-series-range{query}').json()

def getSeriesAtId(id):
    return requests.get(transmitterUrl + '/series/get-series?seriesId={}'.format(id)).json()

def getSeriesDataframe(id, corrected):
    csv = ''
    if corrected:
        csv = './csv/corrected/{}.csv'.format(id)
    else:
        csv = './csv/raw/{}.csv'.format(id)
    return pd.read_csv(csv, index_col=False)

def baselineCorrection(id):
    df = getSeriesDataframe(id, False)
    df.iloc[:,2:] = df.iloc[:,2:].apply(lambda x: BaselineRemoval(x).ZhangFit(), axis=1, result_type='expand')
    df.to_csv(f'./csv/corrected/{id}.csv', index=False)

def filterCoordinates(df, coordinates):
    #Mask dataframe to XY
    df['x'] = pd.to_numeric(df['x'])
    df['y'] = pd.to_numeric(df['y'])
    mask = ((df['x'] >= coordinates['rangeX'][0]) & (df['x'] <= coordinates['rangeX'][1]) &
            (df['y'] >= coordinates['rangeY'][0]) & (df['y'] <= coordinates['rangeY'][1]))
    df = df.loc[mask]
    return df

def filterFrequencies(df_melted, frequencies):
    frequencyMask = ((df_melted['frequency'] >= frequencies[0]) & (df_melted['frequency'] <= frequencies[1]))
    return df_melted['frequency'].mask(frequencyMask)

def filterIntensity(df_melted, intensity):
    median = df_melted.loc[df_melted['intensity'] < intensity, 'intensity'].median()
    intensityMask = df_melted['intensity'] > intensity
    df_melted['intensity'] = df_melted['intensity'].mask(intensityMask, median)
    return df_melted

def filterAcquisition(id, *, corrected=False, coordRange=None, frequencies=None, intensity=5000):
    #Get series dataframe
    df = getSeriesDataframe(id, corrected)
    df = df.drop(['id'], axis=1, errors='ignore')

    #Filter coordinates
    if coordRange != None:    
        try:
            df = filterCoordinates(coordRange)
        except:
            logging.error("""coordRange: Expected Object with 
                values {'rangeX':[min,max],'rangeY':[min, max]}, 
                got """+str(coordRange)+""" instead""")

    df = pd.melt(df, id_vars=['x', 'y'], var_name='frequency',
        value_name='intensity').sort_values(['x', 'y', 'frequency'])
    df['frequency'] = pd.to_numeric(df['frequency'])
    
    #Mask intensity and frequency if not default
    if intensity < 5000:
        df = filterIntensity(df, intensity)
    if frequencies != None:
        df = filterFrequencies(df, frequencies)

    df = pd.pivot_table(df,values='intensity',index=['x','y'],columns='frequency').reset_index().reset_index(drop=True)
    
    #return dataframe
    return df