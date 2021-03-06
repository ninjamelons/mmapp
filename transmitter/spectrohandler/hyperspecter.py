import plotly.graph_objects as go
#import plotly.express as px
import dash
import webview

import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

import numpy as np
import pandas as pd
#import scipy.ndimage

import traceback
import sys
import os

try:
    from . import data_handler as dh
except:
    import data_handler as dh

def rearrange_df(df, nb_frames):
    z_arr = list()
    for i in range(nb_frames):
        arr_at = list()
        for j, multi in enumerate(df):
            arr_at.append(multi[i])
        z_arr.append(arr_at)
    z_arr = np.array(z_arr)
    return z_arr

class Hyperspecter():
    def __init__(self, dash_gui):
        self.reload()

        self.dash = dash_gui
        self.layout = self.grid_layout()
    
    def reload(self):
        self.data = pd.DataFrame.from_dict(dh.getAllSeries()['series'])
        try:
            #Select first 5 columns, and 6-9
            self.table_headers = self.data.iloc[:,np.r_[0:4, 6:9]].rename(
                columns={'StartDatetime': 'Date'}).columns
        except:
            self.table_headers = self.data
        self.title = 'title'
    
    def grid_layout(self):
        return html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H3('Available Series')
                        ]),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.ListGroup([
                                        dbc.ListGroupItemHeading('Select series'),
                                        dbc.InputGroup([
                                            dcc.Dropdown(id='series-selector', options=[],
                                                value='', placeholder='Enter series title',
                                                style={'marginBottom': '0.5rem', 'minWidth': '80%'}),
                                            dbc.Button('Refresh', id='refresh-selector'),
                                        ]),
                                        dbc.InputGroup([
                                            dbc.InputGroupAddon('Max Intensity'),
                                            dbc.Input(type='number', id='series-intensity', value=5000,
                                                style={'minWidth': '6rem', 'maxWidth': '8rem'}),
                                        ], style={'marginBottom': '1rem'}),
                                        dbc.InputGroup([
                                            dbc.InputGroupAddon('Baseline Correction', className="mr-2 mb-2"),
                                            dbc.RadioItems(
                                                options=[
                                                    {"label": "Raw Data", "value": 1},
                                                    {"label": "Zhang fit", "value": 2},
                                                ],
                                                value=1,
                                                id="series-corrected",
                                                inline=True,
                                                style={'marginTop': '0.5rem'}
                                            ),
                                        ]),
                                        dbc.InputGroup([
                                            dbc.Button("Baseline Correct", id='correct-series',
                                                style={'minWidth': '6rem', 'maxWidth': '12rem'}),
                                                dbc.Alert("Applied Zhang Fit correction", color="success",
                                                    is_open=False, dismissable=True, id='correction-alert',
                                                    style={'margin': '0'})
                                        ], style={'marginBottom': '1rem'}),
                                    ]),
                                    dbc.ListGroup([
                                        dbc.ListGroupItemHeading('Filter table by:'),
                                        dbc.InputGroup([
                                            dcc.DatePickerRange(id='date-range',
                                                className='mb-2'),
                                            dbc.Button(html.I(className='fas fa-times'),
                                                id='reset-date',
                                                style={'height': '3rem', 'width': '3rem', 'marginLeft': '0.5rem'})
                                        ], size='md'),
                                        dbc.InputGroup([
                                            dbc.InputGroupAddon('No. Points'),
                                            dbc.Input(type='number', id='points-lower',
                                                style={'minWidth': '6rem', 'maxWidth': '8rem'}),
                                            dbc.Input(type='number', id='points-upper',
                                                style={'minWidth': '6rem', 'maxWidth': '8rem'}),
                                        ]),
                                        dbc.InputGroup([
                                        ], className='mb-2'),
                                    ])
                                ], md=6, lg=5,),
                                dbc.Col([
                                    dbc.Table(id='table', bordered=True,
                                        style={'textAlign': 'center'})
                                ], md=6, lg=7, style={'maxHeight': '30rem', 'overflowY': 'scroll'})
                            ])
                        ])
                    ])
                ])
            ], style={'marginBottom': '1rem'}),
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader([
                            html.H3('Selected Series')
                        ]),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Alert('Selected series is not valid',
                                        id='volumetric-alert', color='danger', className='d-none',
                                        style={'marginTop': '1rem'}),
                                    dbc.InputGroup([
                                        dbc.InputGroupAddon('Min Wavelength'),
                                        dbc.Input(id='volumetric-minlambda', type='number', value=975),
                                        dbc.InputGroupAddon('Max Wavelength.', style={'marginLeft': '1rem'}),
                                        dbc.Input(id='volumetric-maxlambda', type='number', value=1025),
                                    ], size='lg', style={'marginTop': '1rem'}),
                                    dcc.Graph(id='volumetric-graph'),
                                    html.H3(id="volumetric-graph-click")
                                ], lg=12, xl=6),
                                dbc.Col([
                                    dbc.Alert('Something went wrong. Selected series may not include the input frequency',
                                        id='surface-alert', color='danger', className='d-none',
                                        style={'marginTop': '1rem'}),
                                    dbc.Alert('Downloaded surface chart csv',
                                        id='download-alert', color='success', dismissable=True, is_open=False,
                                        style={'marginTop': '1rem'}),
                                    dbc.InputGroup([
                                        dbc.InputGroupAddon('Frequency'),
                                        dbc.Input(id='surface-frequency', type='number', value=1000),
                                        dbc.InputGroupAddon('Smoothing', style={'marginLeft': '1rem'}),
                                        dbc.Input(id='surface-smoothing', type='number', min=0, max=5, step=0.1, value=0.6),
                                        dbc.Button(html.I(className='fas fa-download'),
                                            id='surface-download', style={'marginLeft': '1rem'}),
                                    ], size='lg', style={'marginTop': '1rem'}),
                                    dcc.Graph(id='surface-3d-graph'),
                                ], lg=12, xl=6)
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    dbc.Alert('X/Y coordinates may not exist on series',
                                        id='frequency-line-alert', color='danger', className='d-none',
                                        style={'marginTop': '1rem'}),
                                    dcc.Graph(id='frequency-line-chart'),
                                ],)
                            ])
                        ])
                    ])
                )
            ])
        ], style={'overflowX': 'hidden', 'margin': '1rem'})
    
    def getSeriesTable(self, df):
        try:
            #Select first 5 columns, and 6-9
            df = df.iloc[:,np.r_[0:4, 6:9]]
        except Exception as ex:
            traceback.print_exception(sys.exc_info())
    
        table_header = [
            html.Thead(html.Tr([html.Th(col) for col in self.table_headers]))
        ]
        
        rows = []
        for index, row in df.iterrows():
            rows.append(html.Tr([html.Td(field) for field in row]))
        table_body = [html.Tbody(rows)]

        return table_header+table_body

    def getDropdownOptions(self):
        try:
            df_opt = self.data.loc[:, ['Id', 'Title']]
            df_opt.rename(columns={'Id': 'value', 'Title': 'label'}, inplace=True)
            dict_opt = df_opt.to_dict(orient='records')
        except:
            dict_opt = []
        return dict_opt

    def volumetric_graph(self, id, intensity, corrected, minlbd, maxlbd):
        max_lambda = maxlbd

        if maxlbd > (minlbd + 100):
            max_lambda = minlbd + 100
        elif maxlbd < minlbd:
            max_lambda = minlbd + 10
        
        #Dataframe
        df = dh.filterAcquisition(id, intensity=intensity, corrected=corrected, frequencies=[minlbd, max_lambda])

        #Expected shape
        radius = df['x'].max()
        dims = radius * 2 + 1
        #Check if terminated early (less than expected shape)
        # no. of rows is not divisible by dims
        isComplete = False
        if len(df) % dims == 0:
            isComplete = True

        #Get termination point from radius
        # Then set new radius and dims
        if not isComplete:
            xMax = radius
            xMin = abs(df['x'].min())
            yMax = df['y'].max()
            yMin = abs(df['y'].min())
            radius = min([xMax, xMin, yMax, yMin])
        
            df = df.loc[((df['x'] <= radius) & (df['y'] <= radius) &
                (df['x'] >= (-1*radius)) & (df['y'] >= (-1*radius)))]
            
            dims = radius * 2 + 1

        xy_shape = (dims, dims)
        nb_frames = df.iloc[:,2:].shape[1]
        max_intensity = df.iloc[:,2:].max(axis=1).max()
        df_melted = pd.melt(df.iloc[::xy_shape[0]*xy_shape[1],2:],
            var_name='frequency', value_name='intensity')
        freqs = df_melted['frequency'].values

        #Multi Index
        df = df.set_index(['x','y'])
        df = df.values.reshape(
            len(df.index.levels[0]),
            len(df.index.levels[1]),
            -1).swapaxes(1,2)
        df = rearrange_df(df, nb_frames)

        x = np.linspace(radius, -1*radius, xy_shape[0])
        y = np.linspace(-1*radius, radius, xy_shape[1])

        #Plotly figure
        frames = list()
        for nb in range(nb_frames):
            frame = go.Frame(
                data=go.Surface(
                    x=x,
                    y=y,
                    z=freqs[nb] * np.ones(xy_shape),
                    surfacecolor=np.flipud(df[nb]),
                    cmin=0,
                    cmax=max_intensity,
                    colorscale='oxy'
                ),
                name=str(freqs[nb]))
            frames.append(frame)
        fig = go.Figure(frames=frames)

        #Animation Data
        fig.add_trace(go.Surface(
            x=x,
            y=y,
            z=freqs[0] * np.ones(xy_shape),
            surfacecolor=np.flipud(df[0]),
            colorscale='oxy',
            cmin=0, cmax=max_intensity,
            colorbar=dict(thickness=20, ticklen=50)
            ))

        def frame_args(duration):
            return {
                    "frame": {"duration": duration},
                    "mode": "immediate",
                    "fromcurrent": True,
                    "transition": {"duration": duration, "easing": "linear"},
                }

        sliders = [{
            "pad": {"b": 10, "t": 60},
            "len": 0.9,
            "x": 0.1,
            "y": 0,
            "steps": [{
                "args": [[f.name], frame_args(0)],
                "label": str(k),
                "method": "animate",
            } for k, f in enumerate(fig.frames)],
        }]
        # Layout
        fig.update_layout(
            height=700,
            scene=dict(
                zaxis=dict(range=[freqs.min()-1, freqs.max()+1], autorange=False),
                aspectratio=dict(x=1, y=1, z=1),
            ),
            updatemenus = [{
                "buttons": [{
                        "args": [None, frame_args(50)],
                        "label": "&#9654;", # play symbol
                        "method": "animate",
                    },
                    {
                        "args": [[None], frame_args(0)],
                        "label": "&#9724;", # pause symbol
                        "method": "animate",
                    },
                ],
                "direction": "left",
                "pad": {"r": 10, "t": 70},
                "type": "buttons",
                "x": 0.1,
                "y": 0,
            }], sliders=sliders
        )
        return fig
    
    def surface_3d_graph(self, id, frequency, smoothing, intensity, corrected):
        #Dataframe
        id = int(id)
        intensity = int(intensity)
        frequency = float(frequency)
        df = dh.filterAcquisition(id, intensity=intensity, corrected=corrected)

        #Input: Dataframe with e.g. columns; 'x', 'y', '1005.43'
        array = df.columns[2:].astype('float64')
        idx = (np.abs(array - frequency)).argmin()
        nearestFreq = array[idx]

        df = df.loc[:,['x','y',nearestFreq]]

        #Convert 3 column df to rows = x, columns = y, values = intensity
        df = df.pivot(index='x', columns='y', values=df.columns[len(df.columns)-1])

        #Present dataframe
        z = df.values
        sh_0, sh_1 = z.shape
        x, y = np.linspace(sh_0, -1*sh_0, sh_0), np.linspace(-1*sh_1, sh_1, sh_1)

        #Smooth z-values
        #sigma = [smoothing, smoothing]
        #z = scipy.ndimage.filters.gaussian_filter(z, sigma)
        
        fig = go.Figure(data=[go.Surface(z=z, x=x, y=y)])
        fig.update_layout(title=nearestFreq, autosize=False,
                          width=600, height=600,
                          margin=dict(l=65, r=50, b=65, t=90))
        return fig
    
    def frequency_line_chart(self, id, intensity, corrected):
        #Dataframe
        id = int(id)
        intensity = int(intensity)
        df = dh.filterAcquisition(id, intensity=intensity, corrected=corrected)

        df = pd.melt(df, id_vars=['x', 'y'], var_name='frequency',
            value_name='intensity').sort_values(['x', 'y', 'frequency'])
        df['xy'] = df.x.astype(str) + ',' + df.y.astype(str)

        group = df.groupby('xy')
        frequencies = group.frequency.apply(list)
        intensities = group.intensity.apply(list)

        fig = go.Figure()
        for group, values in frequencies.items():
            fig.add_trace(go.Scatter(x=values, y=intensities[group], mode='lines', name=group))

        return fig

    def dash_callbacks(self):
        #Fallback figure - Empty figure for default
        fig = go.Figure(data=[go.Scatter(x=[], y=[])])

        @self.dash.callback(
            [Output('volumetric-graph', 'figure'),
            Output('volumetric-alert', 'className')],
            [Input('series-selector', 'value'),
            Input('series-intensity', 'value'),
            Input('series-corrected', 'value'),
            Input('volumetric-minlambda', 'value'),
            Input('volumetric-maxlambda', 'value')])
        def update_volumetric_graph(id, intensity, corrected, minlbd, maxlbd):
            if id == '':
                return fig, 'd-none'
            try:
                volumetric_fig = self.volumetric_graph(id, intensity, corrected, minlbd, maxlbd)
            except Exception as ex:
                traceback.print_exception(sys.exc_info())
                return fig, 'd-block'
            return volumetric_fig, 'd-none'

        @self.dash.callback(
            [Output('surface-3d-graph', 'figure'),
            Output('surface-alert', 'className')],
            [Input('series-selector', 'value'),
            Input('surface-frequency', 'value'),
            Input('surface-smoothing', 'value'),
            Input('series-intensity', 'value'),
            Input('series-corrected', 'value')])
        def update_surface_graph(id, frequency, smoothing, intensity, corrected):
            if id == '':
                return fig, 'd-none'
            try:
                surface_fig = self.surface_3d_graph(id, frequency, smoothing, intensity, corrected)
            except Exception as ex:
                traceback.print_exception(sys.exc_info())
                return fig, 'd-block'
            return surface_fig, 'd-none'

        @self.dash.callback(
            [Output('correction-alert', 'children'),
            Output('correction-alert', 'color'),
            Output('correction-alert', 'is_open'),],
            [Input('correct-series', 'n_clicks')],
            [State('series-selector', 'value')])
        def correct_baseline(n_clicks, id):
            try:
                trigger = dash.callback_context.triggered[0]["prop_id"]
                if trigger == 'correct-series.n_clicks':
                    dh.baselineCorrection(id)
                    return "Applied Zhang Fit correction", "success", True
            except:
                return "None", "warning", False
            return "None", "warning", False

        @self.dash.callback(
            [Output('frequency-line-chart', 'figure'),
            Output('frequency-line-alert', 'className')],
            [Input('series-selector', 'value'),
            Input('series-intensity', 'value'),
            Input('series-corrected', 'value')])
        def update_frequency_chart(id, intensity, corrected):
            if id == '':
                return fig, 'd-none'
            try:
                line_fig = self.frequency_line_chart(id, intensity, corrected)
            except Exception as ex:
                traceback.print_exception(sys.exc_info())
                return fig, 'd-block'
            return line_fig, 'd-none'

        @self.dash.callback(
            Output('table', 'children'),
            [Input('date-range', 'start_date'),
            Input('date-range', 'end_date'),
            Input('points-lower', 'value'),
            Input('points-upper', 'value'),
            Input('refresh-selector', 'n_clicks')])
        def update_table_df(start_date, end_date, points_lower, points_upper, n_clicks):
            returnDf = None
            if start_date == None and end_date == None and points_lower == None and points_upper == None:
                returnDf = pd.DataFrame.from_dict(dh.getAllSeries()['series'])
            else:
                returnDf = pd.DataFrame.from_dict(dh.getSeriesRange([start_date, end_date], [points_lower, points_upper])['series'])
            self.data = returnDf
            return self.getSeriesTable(returnDf)
        
        @self.dash.callback(
            Output('series-selector', 'options'),
            [Input('series-selector', 'search_value')])
        def update_series_selector(search_value):
            if not search_value:
                raise PreventUpdate
            options = self.getDropdownOptions()
            retOptions = []
            for o in options:
                if search_value in o["label"]:
                    retOptions.append(o)
            return retOptions

        @self.dash.callback(
            [Output('date-range', 'start_date'),
            Output('date-range', 'end_date')],
            [Input('reset-date', 'n_clicks')])
        def reset_date_range(nclick):
            return None, None

        @self.dash.callback(
            Output('volumetric-graph-click', 'children'),
            [Input('volumetric-graph', 'clickData')],
            [State('volumetric-graph', 'figure')])
        def volumetric_onclick(clickData, fig):
            try:
                trigger = dash.callback_context.triggered[0]["prop_id"]
                if trigger == 'volumetric-graph.clickData':
                    return str(clickData['points'])
            except:
                pass

        @self.dash.callback(
            Output('download-alert', 'is_open'),
            [Input('surface-download', 'n_clicks')],
            [State('series-selector', 'value'),
            State('surface-frequency', 'value'),
            State('series-intensity', 'value'),
            State('series-corrected', 'value')])
        def surfaceDownload(nclicks, id, frequency, intensity, corrected):
            if id == '':
                return False
            #Dataframe
            id = int(id)
            intensity = int(intensity)
            frequency = float(frequency)
            df = dh.filterAcquisition(id, intensity=intensity, corrected=corrected)

            array = df.columns[2:].astype('float64')
            idx = (np.abs(array - frequency)).argmin()
            nearestFreq = array[idx]

            df = df.loc[:,['x','y',nearestFreq]]

            #Title
            series = dh.getSeriesAtId(id)
            title = series['Title']

            current_directory = os.getcwd()
            final_directory = os.path.join(current_directory, r'downloads')
            if not os.path.exists(final_directory):
                os.makedirs(final_directory)

            #Write to csv
            df.to_csv('./downloads/{}_{}_{:.2f}.csv'.format(id, title, nearestFreq))

            return True

#Implement basic javascript-like functions in python
#Instead of callback
class API():
    pass

#Debug single page
if __name__ == "__main__":
    app = Hyperspecter()
    app.dash_callbacks()
    app.dash.run_server(debug=True, port=5501)