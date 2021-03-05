import dash
import webview

import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State

import json

try:
    from . import data_handler as dh
except:
    import data_handler as dh

#**************#
# Show:
#   Estimated scan time
#   Current scan time
#   Current point / Total points
#   Table:
#       Current X/Y
#       Current Absolute X/Y
#       Expected Absolute X/Y
#**************#

class Scanning():
    def __init__(self, dash_gui):
        self.reload()

        self.dash = dash_gui
        self.layout = self.grid_layout()
    
    def reload(self):
        self.latestSeries = json.loads(dh.getLatestSeries())
        self.points_table_headers = [
            'X','Y','Abs. X','Abs. Y','Exp. X','Exp. Y', 'X Diff.', 'Y Diff.'
        ]
        pass

    def grid_layout(self):
        return html.Div([
            dcc.Interval(
                id='interval-component',
                interval=1*1000, # in milliseconds
                n_intervals=0
            ),
            dbc.Row([
                # Display vertical Table
                dbc.Col([
                    html.P("""Live table displays the stage's indexed X/Y, current absolute X/Y,
                        expected absolute X/Y, and the difference between current and expected absolute X/Y"""),
                    html.P("Newer entries appear at the top of the table."),
                    dbc.Table(id='table-points', bordered=True,
                        style={'textAlign': 'center'})
                ], md=4, size=12, style={'maxHeight': '30rem', 'overflowY': 'scroll'}),
                # Display scan estimation/data
                dbc.Col([
                    html.H2(self.latestSeries['Id']+': '+self.latestSeries['Title']),
                    html.H4(f'Radius: {self.latestSeries["Radius"]}'),
                    html.H4(f'Origin [X,Y]: [{self.latestSeries["OriginX"]},{self.latestSeries["OriginY"]}]'),
                    html.H4(f'Start Datetime: {self.latestSeries["StartDatetime"]}'),
                    dbc.Card([
                        dbc.CardHeader(html.H2("Scan Estimation")),
                        dbc.CardBody([
                            html.P('N/A', id='estimation-progress-p'),
                            dbc.Progress(value=0, id="estimation-progress-bar", striped=True, animated=True),
                        ])
                    ])
                ], md=8, size=12)
            ])
        ])
    
    def build_table(self, df):
        table_header = [
            html.Thead(html.Tr(
                [html.Th(col) for col in self.points_table_headers]
            ))
        ]
        
        #Loop through df rows in reverse index order
        rows = []
        for index, row in df.iloc[::-1].iterrows():
            rows.append(html.Tr([html.Td(field) for field in row]))
        table_body = [html.Tbody(rows)]

        return table_header+table_body
    
    def dash_callbacks(self):
        # Update all interval outputs in single function
        # less calls to get all series entries
        @self.dash.callback(
            [Output('table-points', 'children'),
            Output('estimation-progress-p', 'value'),
            Output('estimation-progress-bar', 'value'),
            Output('estimation-progress-bar', 'max'),
            Output('estimation-progress-bar', 'children')],
            [Input('interval-component', 'n_intervals')])
        def update_scan_interval(n_intervals):
            retOutput = []

            #Update table
            retOutput.append(self.build_table())
            
            #Update progress bar
            retOutput.append("10/50")
            retOutput.append(10)
            retOutput.append(50)
            retOutput.append("20%")

            return retOutput