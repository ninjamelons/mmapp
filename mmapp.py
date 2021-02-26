# Main entry point for app
import time
from threading import Thread
import atexit

from transmitter.transmitter_service import init_rest_service, cleanup_on_exit
from transmitter.spectrohandler.gui_init import init_gui, start_webview

def exit_handler():
    cleanup_on_exit()

atexit.register(exit_handler)

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
    finally:
        exit_handler()