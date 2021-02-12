#Read .txt file
#Write to db
#Read from db

import logging
import requests

import sqlite3
import numpy as np
import pandas as pd

# DO NOT USE - USE CSV INSTEAD
#Access row columns by name
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
db = sqlite3.connect('./spectroscopy.sqlite')
db.row_factory = dict_factory

#Can aggregate by None, Frequencies, Coordinate Range, Coordinate Range AND Frequencies
def aggregateAcquistion(seriesId, *, frequencies, coordRange):
    #Set default variables
    series = requests.get('http://localhost:5500/series/get-series?seriesId='+str(seriesId))
    radius = series['Radius']
    frequency = [0, 2000]
    range = {'rangeX': [-radius, radius],
            'rangeY': [-radius, radius]}
    #Set parameter variables
    if frequencies != None:
        frequency = frequencies
    if coordRange != None:    
        try:
            range.rangeX[0] = min(coordRange.rangeX)
            range.rangeX[1] = max(coordRange.rangeX)
            range.rangeY[0] = min(coordRange.rangeY)
            range.rangeY[1] = max(coordRange.rangeY)
        except:
            range = {'rangeX': [-radius, radius],
                    'rangeY': [-radius, radius]}
            logging.error("""coordRange: Expected Object with 
                values {'rangeX':[min,max],'rangeY':[min, max]}, 
                got """+str(coordRange)+""" instead""")
    
    #Aggregate by range,frequency
    selectAggregate = """SELECT * FROM Acquisition WHERE
        (CoordX > (?) AND CoordX < (?)) AND
        (CoordY > (?) AND CoordY < (?)) AND
        (Frequency > (?) AND Frequency < (?)) AND
        (SeriesId = (?))
        ORDER BY Frequency ASC, CoordX ASC, CoordY ASC"""
    aggrTbl = db.execute(selectAggregate, [range.rangeX[0], range.rangeX[1],
                                 range.rangeY[0], range.rangeY[1],
                                 frequency[0], frequency[1],
                                 seriesId]).fetchall()
    #Create [][] for rows, [str] for column names
    aggrArr = []
    aggrCols = ['x','y']
    for row in aggrTbl:
        isInObj = False
        for coord in aggrArr:
            if coord[0] == row['CoordX'] and coord[1] == row['CoordY']:
                aggrObj[coord][row['Frequency']] = row['Intensity']
                isInObj = True
        if row['Frequency'] not in aggrCols:
            aggrCols.append(row['Frequency'])
        if not isInObj:
            aggrArr.append([row['CoordX'], row['CoordY'], row['Intensity']])
    #Create DF from rows and column names
    return pd.DataFrame(np.array(aggrArr, columns=aggrCols))