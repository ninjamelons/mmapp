from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
import uvicorn

import win32com.client

app = FastAPI()

#Parameters for running acquisition
class Acquisition(BaseModel):
    Spectro: float
    RangeMin: int
    RangeMax: int
    AcqTime: int

#Start spectroscopy acquisition with parameters
@app.post('/spectroscopy/acquire', status_code=200)
async def acquirePoint(seriesId: int, acq: Acquisition):
    #Connect to LabSpec ActiveX object
    #Start acquistion with given parameters
    pass

def tryConnectLabspec():
    ls = win32com.client.Dispatch("NGSACTIVEX.NGSActiveXCtrl.1")
    print(ls.AboutBox)


#Start server with uvicorn
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5501, timeout_keep_alive=0, log_level="info")