from typing import List
from fastapi import FastAPI, Header, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

import os
from datetime import date
from datetime import datetime
import sqlite3
import numpy as np
import pandas as pd

import logging, sys

try:
    from .mmcontrols import stage_lib
    from .mmcontrols import position_lib
    from .spectrohandler import data_handler as dh
except:
    from mmcontrols import stage_lib
    from mmcontrols import position_lib
    from spectrohandler import data_handler as dh

stageDevice = 'XYStage'
csvPath = './csv/raw/'

#Access row columns by name
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def connect_db():
    db = sqlite3.connect('./transmitter/raman_service.sqlite')
    db.row_factory = dict_factory
    return db

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
    version="1.1.3",
    openapi_tags=api_tags
)

#Series properties Radius & Interval
class SpectroscopySeries(BaseModel):
    Title: str
    Radius: int
    Interval: float

#Create a new series & Return the series ID
@app.post("/sequence/new-series", status_code=201, tags=["sequence"])
async def newSeries(series: SpectroscopySeries):
    db = connect_db()
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
    insertOrigin = 'INSERT INTO SeriesEntry (SeriesId, StageX, StageY, PosX, PosY, PointNo) VALUES (?,?,?,?)'
    db.execute(insertOrigin, [insertId, 0, 0, xyPos.x, xyPos.y, 0])
    db.commit()

    final = False
    if series.Radius == 0:
        final = True

    #Return auto-incremented Series.Id
    returnSeries = {
        'seriesId': insertId,
        'final': final,
        'stageX': 0,
        'stageY': 0,
        'pointNo': 0
    }
    return returnSeries

#Update the filename for the last SeriesEntry entry
@app.patch("/sequence/update-last-filename", status_code=200, tags=["sequence"])
async def updateFilenameLastPos(seriesId: int, fileName: str):
    db = connect_db()

    updateEntry = """UPDATE SeriesEntry SET FileName = (?)
        WHERE SeriesId in (SELECT SeriesId FROM SeriesEntry
        WHERE SeriesId = (?) ORDER BY InitDatetime DESC LIMIT 1)"""
    db.execute(updateEntry, [fileName, seriesId])
    db.commit()
    
    selectEntry = """SELECT SeriesId, StageX, StageY FROM SeriesEntry
        WHERE SeriesId = (?) LIMIT 1"""
    entry = db.execute(selectEntry, [seriesId]).fetchone()
    returnSeries = {
        'seriesId': seriesId,
        'stageX': entry['StageX'],
        'stageY': entry['StageY']
    }
    return returnSeries 

@app.post("/sequence/post-sequence-file", status_code=200, tags=["sequence"])
async def postSequenceFile(seriesId: int, file: UploadFile = File(...)):
    db = connect_db()

    logging.debug(f'Uploaded file: {file}')
    try:
        contents = await file.read()
        contents = contents.decode(errors='ignore').splitlines()
    except Exception as ex:
        logging.error(ex)

    fnameArr = file.filename.split('[')
    id = fnameArr[0].split('_')[0] #Deprecated - Only exists for testing now
    stageX = fnameArr[1].split('_')[0]
    stageY = fnameArr[1].split('_')[1].split(']')[0]

    npArr = []
    npArr.append(['id', seriesId])
    npArr.append(['x', stageX])
    npArr.append(['y', stageY])

    logging.debug(f'File: [X:{stageX},Y:{stageY}]')

    for line in range(28, len(contents)-1):
        lineArr = contents[line].split('\t')
        npArr.append(lineArr)
    tpArr = np.transpose(np.array(npArr))
    df = pd.DataFrame([tpArr[1]], columns=tpArr[0])

    csv = csvPath + str(seriesId) + '.csv'

    retObj =  {
        'seriesId': seriesId,
        'success': True,
        'csvPath': csv
    }
    try:
        header = False
        if not os.path.isfile(csv):
            header = True
        df.to_csv(csv, mode='a', header=header, index=False)
    except:
        retObj['success'] = False
    
    logging.debug(f'Success: {retObj["success"]}')

    return retObj

#Move the stage to the next position in the series
@app.post("/sequence/move-stage-sequence", status_code=200, tags=["sequence"])
async def moveStageSequence(seriesId: int):
    db = connect_db()

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

        #Get the next position's absolute micrometer value
        expectedPosAbsolute = [nextPos[0] * interval, nextPos[1] * interval]

        #Move stage next position
        try:
            stage = stage_lib.StageLib(stageDevice)
            stage.moveStageRelative(dxdy, interval)
            stage.waitForDevice(stageDevice)
            xyPos = stage.getCurrentPosition()
        except:
            raise HTTPException(status_code=503, detail='Micromanager is not on or ZMQ server is unavailable')

        print(f"""Stage Position: [{xyPos[0]},{xyPos[1]}];\n
            Expected Position: [{expectedPosAbsolute[0]},{expectedPosAbsolute[1]}]""")

        #Insert new SeriesEntry
        insertOrigin = 'INSERT INTO SeriesEntry (SeriesId, StageX, StageY, PosX, PosY, PointNo) VALUES (?,?,?,?)'
        db.execute(insertOrigin, [seriesId, nextPos[0], nextPos[1], xyPos.x, xyPos.y, nextPos[2]])
        db.commit()

        returnSeries = {
            "seriesId": seriesId,
            "final": nextPos[3],
            "stageX": nextPos[0],
            "stageY": nextPos[1],
            "posX": xyPos.x,
            "posY": xyPos.y,
            "pointNo": nextPos[2],
        }

        logging.debug(f'Move stage: [X:{nextPos[0]},Y:{nextPos[1]}]; Points:{nextPos[2]}/{noPoints}')

        return returnSeries
    else:
        raise HTTPException(status_code=404, detail='Series does not exist')

#Move the stage to the next position in the series
@app.patch("/sequence/update-series-end-datetime", status_code=200, tags=["sequence"])
async def updateSeriesEndDatetime(seriesId: int, background_tasks: BackgroundTasks):
    db = connect_db()
    
    updateSeries = """UPDATE Series SET
        EndDatetime = CURRENT_TIMESTAMP WHERE Id = (?)"""
    db.execute(updateSeries, [seriesId])
    db.commit()

    selectSeries = 'SELECT * FROM Series Where Id = (?)'
    seriesTbl = db.execute(selectSeries, [seriesId]).fetchone()

    if seriesTbl == None:
        raise HTTPException(status_code=404, detail='Series does not exist')

    background_tasks.add_task(dh.baselineCorrection, seriesId)

    return {'seriesId': seriesTbl['Id'],
        'EndDatetime': seriesTbl['EndDatetime']}

@app.post("/sequence/post-multiple-sequence-files", status_code=200, tags=["sequence"])
async def postMultipleSequenceFile(seriesId: int, files: List[UploadFile] = File(...)):
    db = connect_db()
    
    for file in files:
        contents = await file.read()
        contents = contents.decode(errors='ignore').splitlines()
        fnameArr = file.filename.split('[')
        id = fnameArr[0].split('_')[0]
        stageX = fnameArr[1].split('_')[0]
        stageY = fnameArr[1].split('_')[1].split(']')[0]

        npArr = []
        npArr.append(['id', seriesId])
        npArr.append(['x', stageX])
        npArr.append(['y', stageY])

        for line in range(28, len(contents)-1):
            lineArr = contents[line].split('\t')
            npArr.append(lineArr)
        tpArr = np.transpose(np.array(npArr))
        df = pd.DataFrame([tpArr[1]], columns=tpArr[0])

        csv = csvPath + str(seriesId) + '.csv'
        retObj =  {
            'seriesId': seriesId,
            'success': True,
            'csvPath': csv
        }
        try:
            header = False
            if not os.path.isfile(csv):
                header = True
            df.to_csv(csv, mode='a', header=header, index=False)
        except:
            retObj['success'] = False
    return retObj

#Series properties Radius & Interval
class Series(BaseModel):
    SeriesId: int
    X: float
    Y: float

@app.post("/series/move-stage-origin-relative", status_code=200, tags=["series"])
async def moveStageOriginRelative(series: Series):
    db = connect_db()

    #Select series Origin, Interval
    #Calculate dx dy from origin (X * Interval), (Y * Interval)
    #Move stage relative to origin with calculated dxdy
    pass

@app.post("/series/move-stage-origin", status_code=200, tags=["series"])
async def moveStageOrigin(seriesId: int):
    db = connect_db()

    #Select series Origin
    #Move stage absolute to origin X,Y
    pass

@app.get("/series/get-series-entries", status_code=200, tags=["series"])
async def getSeriesEntries(seriesId: int):
    db = connect_db()

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

@app.get("/series/get-series", status_code=200, tags=['series'])
async def getSeries(seriesId: int):
    db = connect_db()

    selectSeries = 'SELECT * FROM Series WHERE Id = (?)'
    seriesTbl = db.execute(selectSeries, [seriesId]).fetchone()
    return seriesTbl

@app.get("/series/get-all-series", status_code=200, tags=["series"])
async def getAllSeries():
    db = connect_db()

    returnSeries = {'series': []}
    #Select series
    selectSeries = 'SELECT *, ((Radius*2+1)*(Radius*2+1)) as NoPoints FROM Series'
    seriesTbl = db.execute(selectSeries, []).fetchall()
    
    for entry in seriesTbl:
        returnSeries['series'].append(entry)
    return returnSeries

@app.get("/series/get-series-range", status_code=200, tags=["series"])
async def getSeriesRange(sdate: date = date(2021, 1, 1),
                       edate: date = date.today(),
                       ptsLower: int = 1,
                       ptsUpper: int = 1000):
    db = connect_db()

    returnSeries = {'series': []}

    edate = datetime(year=edate.year, month=edate.month, day=edate.day,
         hour=23, minute=59, second=59, microsecond=9999)
    #Select series
    selectSeries = """SELECT *, ((Radius*2+1)*(Radius*2+1)) as NoPoints
                    FROM Series
                    WHERE StartDatetime >= (?) AND
                    EndDatetime <= (?) AND
                    NoPoints >= (?) AND
                    NoPoints <= (?)"""
    seriesTbl = db.execute(selectSeries, [sdate, edate, ptsLower, ptsUpper]).fetchall()
    
    for entry in seriesTbl:
        returnSeries['series'].append(entry)
    return returnSeries

@app.get("/")
async def main():
    content = """
<body>
<form action="/sequence/post-multiple-sequence-files?seriesId=1" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)

def init_rest_service():
    uvicorn.run(app, host="0.0.0.0", port=5500, timeout_keep_alive=0)

#Start server with uvicorn
if __name__ == "__main__":
    #init_rest_service()
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    uvicorn.run("transmitter_service:app", host="0.0.0.0", port=5500, reload=True, timeout_keep_alive=0, log_level="info")