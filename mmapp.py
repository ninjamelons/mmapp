#Monkey patch flask-compress
#*********************************************#
import sys
from collections import namedtuple

import pkg_resources

IS_FROZEN = hasattr(sys, '_MEIPASS')

# backup true function
_true_get_distribution = pkg_resources.get_distribution
# create small placeholder for the dash call
# _flask_compress_version = parse_version(get_distribution("flask-compress").version)
_Dist = namedtuple('_Dist', ['version'])

def _get_distribution(dist):
    if IS_FROZEN and dist == 'flask-compress':
        return _Dist('1.5.0')
    else:
        return _true_get_distribution(dist)

# monkey patch the function so it can work once frozen and pkg_resources is of
# no help
pkg_resources.get_distribution = _get_distribution
#**********************************************#

# Main entry point for app
import time
from threading import Thread

from transmitter.transmitter_service import init_rest_service
from transmitter.spectrohandler.gui_init import init_gui, start_webview, start_dash

def run_service():
    init_rest_service()
    

def run_gui():
    app = init_gui()

    debug = False
    if debug:
        start_dash(app)
    else:
        start_webview(app)

if __name__ == "__main__":
    try:
        service_thread = Thread(target=run_service)
        service_thread.start()

        time.sleep(2)

        run_gui()
    except Exception as ex:
        print(ex)