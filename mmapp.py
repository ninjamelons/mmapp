# Main entry point for app
import time
from threading import Thread

from transmitter.transmitter_service import init_rest_service
from transmitter.spectrohandler.gui_init import init_gui, start_webview

def run_service():
    init_rest_service()

def run_gui():
    app = init_gui()
    start_webview(app)

if __name__ == "__main__":
    try:
        service_thread = Thread(target=run_service)
        service_thread.start()

        time.sleep(2)

        run_gui()
    except Exception as ex:
        print(ex)