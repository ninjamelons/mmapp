from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import uvicorn

import json
from datetime import datetime
import sqlite3

from mmcontrols import stage_lib
from mmcontrols import position_lib

stageDevice = 'XY'

#Access row columns by name
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
db = sqlite3.connect('./raman_service.sqlite')
db.row_factory = dict_factory

api_tags = [
    {
        "name": "sequence",
        "description": "Operations to automatically acquire new data following a given path"
    },
    {
        "name": "series",
        "description": "Manual operations on the stage or acquired data through the series objects"
    }
]
app = FastAPI(
    title="Transmitter Service",
    description="""Receives requests from LabSpec to acquire spectroscopy data
         and move the microscope stage through micromanager""",
    version="1.0.0",
    openapi_tags=api_tags
)

#Series properties Radius & Interval
class SpectroscopySeries(BaseModel):
    Title: str
    Radius: int
    Interval: int

#Create a new series & Return the series ID
@app.post("/sequence/new-series", status_code=201, tags=["sequence"])
async def newSeries(series: SpectroscopySeries):
    #Get current stage position == Series Origin
    try:
        stage = stage_lib.StageLib(stageDevice)
        xyPos = stage.getCurrentPosition()
    except:
        raise HTTPException(status_code=503, detail='Micromanager is not on or ZMQ server is unavailable')
    #Create new Series
    print([series.Title, series.Radius, series.Interval, xyPos.x, xyPos.y])
    insertSeries = 'INSERT INTO Series (Title, Radius, Interval, OriginX, OriginY) VALUES (?,?,?,?,?)'
    insertId = db.execute(insertSeries, [series.Title, series.Radius, series.Interval, xyPos.x, xyPos.y]).lastrowid
    #Create Origin SeriesEntry
    insertOrigin = 'INSERT INTO SeriesEntry (SeriesId, StageX, StageY, PointNo) VALUES (?,?,?,?)'
    db.execute(insertOrigin, [insertId, 0, 0, 0])
    db.commit()

    #Return auto-incremented Series.Id
    returnSeries = {
        'seriesId': insertId
    }
    return returnSeries

#Update the filename for the last SeriesEntry entry
@app.post("/sequence/update-last-filename", status_code=200, tags=["sequence"])
async def updateFilenameLastPos(seriesId: int, fileName: str):
    updateEntry = """UPDATE SeriesEntry SET FileName = (?)
        WHERE SeriesId in (SELECT SeriesId FROM SeriesEntry
        WHERE SeriesId = (?) ORDER BY InitDatetime DESC LIMIT 1)"""
    db.execute(updateEntry, [fileName, seriesId])
    db.commit()
    
    #TODO - Notify ML program that file is accessible

    #TODO - SET PROPER RETURN VALUE
    selectEntry = """SELECT SeriesId, StageX, StageY FROM SeriesEntry
        WHERE SeriesId = (?) LIMIT 1"""
    entry = db.execute(selectEntry, [seriesId]).fetchone()
    returnSeries = {
        'seriesId': seriesId,
        'stageX': entry['StageX'],
        'stageY': entry['StageY']
    }
    return returnSeries

#Move the stage to the next position in the series
@app.post("/sequence/move-stage-sequence", status_code=200, tags=["sequence"])
async def moveStageSequence(seriesId: int):
    #Get accessed series & Current position
    selectSeries = """SELECT Series.Id, Series.Radius, Series.Interval, SeriesEntry.StageX, SeriesEntry.StageY
        FROM Series INNER JOIN SeriesEntry ON Series.Id = SeriesEntry.SeriesId
        WHERE Series.Id = (?) ORDER BY SeriesEntry.InitDatetime DESC,
        SeriesEntry.PointNo DESC LIMIT 1"""
    previousEntry = db.execute(selectSeries, [seriesId]).fetchone()

    #If no entries then series does not exist
    if previousEntry != None:
        radius = previousEntry['Radius']
        interval = previousEntry['Interval']
        curr_xPos = previousEntry['StageX']
        curr_yPos = previousEntry['StageY']
        noPoints = (int(radius)*2 + 1)**2

        #Calc next position
        nextPos = position_lib.GetNextPosition(curr_xPos, curr_yPos, noPoints)
        if nextPos == None:
            raise HTTPException(status_code=403, detail='Stage at last position already')
        dxdy = position_lib.GetDxDy(curr_xPos, curr_yPos, nextPos[0], nextPos[1])

        #Move stage next position
        try:
            stage = stage_lib.StageLib(stageDevice)
            stage.moveStageRelative(dxdy, interval)
            stage.waitForDevice(stageDevice)
        except:
            raise HTTPException(status_code=503, detail='Micromanager is not on or ZMQ server is unavailable')

        #Insert new SeriesEntry
        insertOrigin = 'INSERT INTO SeriesEntry (SeriesId, StageX, StageY, PointNo) VALUES (?,?,?,?)'
        db.execute(insertOrigin, [seriesId, nextPos[0], nextPos[1], nextPos[2]])
        db.commit()

        returnSeries = {
            "seriesId": seriesId,
            "final": nextPos[3],
            "pointNo": nextPos[2]
        }
        return returnSeries
    else:
        raise HTTPException(status_code=404, detail='Series does not exist')

#Move the stage to the next position in the series
@app.post("/sequence/update-series-end-datetime", status_code=200, tags=["sequence"])
async def updateSeriesEndDatetime(seriesId: int):
    updateSeries = """UPDATE Series SET
        EndDatetime = CURRENT_TIMESTAMP WHERE Id = (?)"""
    db.execute(updateSeries, [seriesId])
    db.commit()

    selectSeries = 'SELECT * FROM Series Where Id = (?)'
    seriesTbl = db.execute(selectSeries, [seriesId]).fetchone()

    if seriesTbl == None:
        raise HTTPException(status_code=404, detail='Series does not exist')

    return {'seriesId': seriesTbl['Id'],
        'EndDatetime': seriesTbl['EndDatetime']}

#Series properties Radius & Interval
class Series(BaseModel):
    SeriesId: int
    X: float
    Y: float

@app.post("/series/move-stage-origin-relative", status_code=200, tags=["series"])
async def moveStageOriginRelative(series: Series):
    #Select series Origin, Interval
    #Calculate dx dy from origin (X * Interval), (Y * Interval)
    #Move stage relative to origin with calculated dxdy
    pass

@app.post("/series/move-stage-origin", status_code=200, tags=["series"])
async def moveStageOrigin(seriesId: int):
    #Select series Origin
    #Move stage absolute to origin X,Y
    pass

@app.get("/series/get-series-entries", status_code=200, tags=["series"])
async def getSeriesEntries(seriesId: int):
    returnSeries = {}
    #Select series
    selectSeries = 'SELECT * FROM Series WHERE Id = (?)'
    seriesTbl = db.execute(selectSeries, [seriesId]).fetchone()

    if seriesTbl == None:
        raise HTTPException(status_code=404, detail='Series does not exist')

    returnSeries['series'] = seriesTbl

    #select all seriesentries
    selectEntries = 'SELECT * FROM SeriesEntry WHERE SeriesId = (?)'
    entriesTbl = db.execute(selectEntries, [seriesId]).fetchall()

    for i, entry in enumerate(entriesTbl):
        returnSeries[i] = entry

    return returnSeries

@app.get("/series/get-all-series", status_code=200, tags=["series"])
async def getAllSeries():
    returnSeries = {'series': []}
    #Select series
    selectSeries = 'SELECT * FROM Series'
    seriesTbl = db.execute(selectSeries, []).fetchall()
    
    for entry in seriesTbl:
        returnSeries['series'].append(entry)
    return returnSeries

#Start server with uvicorn
if __name__ == "__main__":
    #uvicorn.run(app, host="127.0.0.1", port=5500, timeout_keep_alive=0)
    uvicorn.run("transmitter_service:app", host="127.0.0.1", port=5500, reload=True, timeout_keep_alive=0, log_level="info")