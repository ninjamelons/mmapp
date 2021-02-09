# Main entry point for app
import uvicorn

from transmitter.transmitter_service import app

uvicorn.run(app, host="0.0.0.0", port=8000)