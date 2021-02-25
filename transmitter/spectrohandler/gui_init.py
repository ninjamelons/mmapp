import dash
import webview

import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from hyperspecter import Hyperspecter

FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"
class GuiInit():
    def __init__(self):
        self.dash = dash.Dash(
            external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME],
            suppress_callback_exceptions=True
        )

base_layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

def get_page(app, pages):
    @app.callback(
        Output('page-content', 'children'),
        [Input('url', 'pathname')])
    def display_page(pathname):
        page_found = False
        for page_url, page_layout in pages.items():
            if pathname == page_url:
                page_found = True
                return page_layout
        if not page_found:
            return pages['default']

def start_webview():
    window = webview.create_window('Raman Imaging', app.dash.server, width=1300, height=850)
    webview.start()

def start_dash():
    app.dash.run_server(debug=True, port=5501)

if __name__ == "__main__":
    #Init GUI
    app = GuiInit()
    pages = {}
    app.dash.layout = base_layout

    #Init pages & callbacks
    specter = Hyperspecter(app.dash)
    specter.dash_callbacks()
    
    #Append pages {'url': outerDiv}
    pages['default'] = specter.layout
    pages['ml'] = html.Div()

    #Navigation callback
    get_page(app.dash, pages)

    #Start GUI/App
    debug = True
    if debug:
        start_dash()
    else:
        start_webview()