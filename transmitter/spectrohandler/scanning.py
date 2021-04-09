import dash
import webview

import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State

import traceback
import sys

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

        # Number of seconds between refresh/update
        # updateInterval needs to be large enough to allow calculations
        #  and presentation before next update is issued - 5 is safe
        self.updateInterval = 5

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

        #Get series entries in reversed order
        self.seriesEntries = dh.getSeriesEntries(self.latestSeries['Id'])
        series = self.seriesEntries.pop('series', None)
        if series != None:
            self.seriesEntries = list(reversed(self.seriesEntries.values()))

        self.points_table_headers = [
            'X','Y','Abs. X','Abs. Y','Exp. X','Exp. Y', 'X Diff.', 'Y Diff.'
        ]

    def grid_layout(self):
        return html.Div([
            dcc.Interval(
                id='interval-component',
                interval=self.updateInterval*1000, # in milliseconds
                n_intervals=0
            ),
            dbc.Row([
                # Display vertical Table
                dbc.Col([
                    html.P("""Live table displays the stage's indexed X/Y, current absolute X/Y stage position,
                        expected absolute X/Y stage position, and the difference between current and expected absolute X/Y stage position"""),
                    html.P("Newer entries appear at the top of the table."),
                    dbc.Table(id='table-points', bordered=True,
                        style={'textAlign': 'center'})
                ], xl=5, width=12, style={'maxHeight': '30rem', 'overflowY': 'scroll', 'marginBottom': '1rem'}),
                # Display scan estimation/data
                dbc.Col([
                    html.Div(self.getTitleAttributes(), id='title-attributes'),
                    dbc.Card([
                        dbc.CardHeader(html.H4("Scan Estimation")),
                        dbc.CardBody([
                            html.P('N/A', id='estimation-progress-p'),
                            dbc.Progress(value=0, id="estimation-progress-bar", striped=True, animated=True),
                        ])
                    ])
                ], xl=7, width=12)
            ], style={'margin': '1rem'})
        ])
    
    def build_table(self, df):
        try:
            table_header = [
                html.Thead(html.Tr(
                    [html.Th(col) for col in self.points_table_headers]
                ))
            ]

            #Loop through df rows
            rows = []
            for index, row in df.iterrows():
                rows.append(html.Tr([html.Td('{:0.2f}'.format(field)) for field in row]))
            table_body = [html.Tbody(rows)]
        except Exception as ex:
            traceback.print_exception(sys.exc_info())

        return table_header+table_body
    
    def getTitleAttributes(self):
        return [html.Span('ID: '+str(self.latestSeries['Id']), style={'color':'grey'}),
            html.H2(self.latestSeries['Title']),
            html.Span('Points radius', style={'color':'grey'}),
            html.H4(self.latestSeries["Radius"]),
            html.Span('Origin [X,Y]', style={'color':'grey'}),
            html.H4(f'[{self.latestSeries["OriginX"]},{self.latestSeries["OriginY"]}]'),
            html.Span('Start Datetime', style={'color':'grey'}),
            html.H4(self.latestSeries["StartDatetime"])]
    
    def dash_callbacks(self):
        # Update all interval outputs in single function
        # less calls to get all series entries
        @self.dash.callback(
            [Output('table-points', 'children'),
            Output('title-attributes', 'children'),
            Output('estimation-progress-p', 'children'),
            Output('estimation-progress-bar', 'value'),
            Output('estimation-progress-bar', 'max'),
            Output('estimation-progress-bar', 'children')],
            [Input('interval-component', 'n_intervals')])
        def update_scan_interval(n_intervals):
            try:
                retOutput = []

                #Check if reload required
                latestSeries = dh.getLatestSeries()
                if latestSeries['Id'] != self.latestSeries['Id']:
                    self.reload()

                #Update table
                try:
                    entries = dh.getLatestEntry(self.latestSeries['Id'],
                        self.seriesEntries[0]['InitDatetime'],
                        self.seriesEntries[0]['PointNo'])
                    #Concat entries InitDatetime DESC
                    if len(entries) > 0:
                        self.seriesEntries = entries + self.seriesEntries
                except:
                    pass
                
                try:
                    #Update dataframe for table
                    df = pd.DataFrame(self.seriesEntries)
                    df = df.iloc[:,1:5]
                    df['ExpX'] = df['StageX'] * self.latestSeries['Interval'] + self.latestSeries['OriginX']
                    df['ExpY'] = df['StageY'] * self.latestSeries['Interval'] + self.latestSeries['OriginY']
                    df['DiffX'] = df['PosX'] - df['ExpX']
                    df['DiffY'] = df['PosY'] - df['ExpY']
                    #Drop duplicate rows
                    df.drop_duplicates(subset=['StageX', 'StageY'], inplace=True)
                except:
                    pass
                retOutput.append(self.build_table(df))

                #Update title attributes
                retOutput.append(self.getTitleAttributes())

                #Update progress bar
                currPoints = len(self.seriesEntries)
                maxPoints = self.latestSeries['NoPoints']
                retOutput.append('No. Scans: '+str(currPoints)+'/'+str(maxPoints))
                retOutput.append(currPoints)
                retOutput.append(maxPoints)
                retOutput.append(str(round(currPoints/maxPoints * 100, 2))+'%')
            except Exception as ex:
                traceback.print_exception(sys.exc_info())

            return retOutput