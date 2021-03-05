import dash
import webview

import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State

class MachineLearning():
    def __init__(self, dash_gui):
        self.reload()

        self.dash = dash_gui
        self.layout = self.grid_layout()
    
    def reload(self):
        pass

    def grid_layout(self):
        return html.Div()
    
    def dash_callbacks(self):
        pass