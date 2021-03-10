import dash
import webview

import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State

import json
import pandas as pd

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
        self.latestSeries = dh.getLatestSeries()

        #Default empty series
        if 'Id' not in self.latestSeries:
            self.latestSeries = {
                'Id': 0,
                'Title': "Default",
                'Radius': 0,
                'OriginX': 0,
                'OriginY': 0,
                'StartDatetime': "",
                'EndDatetime': ""
            }

        self.seriesEntries = dh.getSeriesEntries(self.latestSeries['Id'])
        series = self.seriesEntries.pop('series', None)
        if series != None:
            self.seriesEntries = series.items()[::-1]

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
                ], lg=4, width=12, style={'maxHeight': '30rem', 'overflowY': 'scroll'}),
                # Display scan estimation/data
                dbc.Col([
                    html.H2(str(self.latestSeries['Id'])+': '+self.latestSeries['Title']),
                    html.H4(f'Radius: {self.latestSeries["Radius"]}'),
                    html.H4(f'Origin [X,Y]: [{self.latestSeries["OriginX"]},{self.latestSeries["OriginY"]}]'),
                    html.H4(f'Start Datetime: {self.latestSeries["StartDatetime"]}'),
                    dbc.Card([
                        dbc.CardHeader(html.H4("Scan Estimation")),
                        dbc.CardBody([
                            html.P('N/A', id='estimation-progress-p'),
                            dbc.Progress(value=0, id="estimation-progress-bar", striped=True, animated=True),
                        ])
                    ])
                ], lg=8, width=12)
            ], style={'margin': '1rem'})
        ])
    
    def build_table(self, df):
        try:
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
        except Exception as ex:
            print(ex + ": Error Build Table")

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
            try:
                retOutput = []

                #Update table
                try:
                    entries = dh.getLatestEntry(self.latestSeries['Id'],
                        self.seriesEntries[self.seriesEntries[0]]['InitDatetime'])
                    #Concat entries InitDatetime DESC
                    self.seriesEntries = entries + self.seriesEntries

                    df = pd.Dataframe(self.seriesEntries)

                    retOutput.append(self.build_table(df))
                except Exception as ex:
                    print(str(ex) + "\nError when building table")

                #Update progress bar
                retOutput.append("10/50")
                retOutput.append(10)
                retOutput.append(50)
                retOutput.append("20%")
            except:
                print("Error Scan Interval")

            return retOutput