import plotly.graph_objects as go
import dash
import webview
from threading import Thread

import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from dash.dependencies import Input, Output, State

import numpy as np
import pandas as pd
import scipy.ndimage

import data_handler as dh

FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

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
    def __init__(self):
        self.data = pd.DataFrame.from_dict(dh.getAllSeries()['series'])
        self.table_headers = self.data.iloc[:,np.r_[1:4, 8:9, 6:7]].rename(
            columns={'StartDatetime': 'Date'}).columns
        self.options = self.getDropdownOptions()
        self.title = 'title'

        self.dash = dash.Dash(
            external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME]
        )
        self.grid_layout()
    
    def grid_layout(self):
        self.dash.layout = html.Div([
            dbc.Row([
                dbc.Col(self.columnTable(), md=12, lg=5),
                dbc.Col(self.columnGraph(), md=12, lg=7)]),
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.Col([
                            dbc.Alert('Something went wrong. Selected series may not include the input frequency',
                                id='surface-alert', color='danger', className='d-none',
                                style={'marginTop': '1rem'}),
                            dbc.InputGroup([
                                dbc.InputGroupAddon('Frequency'),
                                dbc.Input(id='surface-frequency', type='number', value=1000),
                                dbc.InputGroupAddon('Smoothing', style={'marginLeft': '1rem'}),
                                dbc.Input(id='surface-smoothing', type='number', min=0, max=5, step=0.1, value=0.6),
                                dbc.Button(html.I(className='fas fa-search'),
                                    id='surface-submit', style={'marginLeft': '1rem'}),
                            ], size='lg', style={'marginTop': '1rem'}),
                            dcc.Graph(id='surface-3d-graph'),
                        ], md=5),
                        dbc.Col([
                            
                        ], md=7)
                    ]), md=12)])
        ], style={'overflowX': 'hidden', 'margin': '2rem'})

    def columnTable(self):
        return dbc.Card([
            dbc.CardHeader([
                html.H1('Available Series')
            ]),
            dbc.CardBody([
                dbc.ListGroup([
                    dbc.ListGroupItemHeading('Select series'),
                    dcc.Dropdown(id='series-selector', options=self.options,
                        value='', placeholder='Enter series title',
                        style={'marginBottom': '1rem'})
                ]),
                dbc.ListGroupItemHeading('Filter series'),
                dbc.InputGroup([
                    dcc.DatePickerRange(id='date-range',
                        className='mb-2'),
                    dbc.Button(html.I(className='fas fa-times'),
                        id='reset-date',
                        style={'height': '3rem', 'width': '3rem', 'marginLeft': '0.5rem'})
                ], size='lg'),
                dbc.InputGroup([
                    dbc.InputGroupAddon('No. Points'),
                    dbc.Input(type='number', id='points-lower',
                        style={'minWidth': '6rem', 'maxWidth': '8rem'}),
                    dbc.Input(type='number', id='points-upper',
                        style={'minWidth': '6rem', 'maxWidth': '8rem'}),
                ], size='lg'),
                dbc.InputGroup([
                ], size='lg', className='mb-2'),
                dbc.Table(id='table', bordered=True,
                    style={'textAlign': 'center'})
            ])
        ])

    def columnGraph(self):
        return dbc.Card([
            dbc.CardHeader([
                html.H1('Selected Series')
            ]),
            dbc.CardBody([
                dbc.Alert('Selected series is not valid',
                    id='volumetric-alert', color='danger', className='d-none',
                    style={'marginTop': '1rem'}),
                html.H3(self.title, style={'textAlign': 'center'}),
                dcc.Graph(id='volumetric-graph'),
                html.H3(id="volumetric-graph-click")
            ])
        ])
    
    def getSeriesTable(self, df):
        try:
            df = df.iloc[:,np.r_[1:4, 8:9, 6:7]]
        except Exception as ex:
            print(ex)

        table_header = [
            html.Thead(html.Tr([html.Th(col) for col in self.table_headers]))
        ]
        
        rows = []
        for index, row in df.iterrows():
            rows.append(html.Tr([html.Td(field) for field in row]))
        table_body = [html.Tbody(rows)]

        return table_header+table_body

    def getDropdownOptions(self):
        df_opt = self.data.loc[:, ['Id', 'Title']]
        df_opt.rename(columns={'Id': 'value', 'Title': 'label'}, inplace=True)
        dict_opt = df_opt.to_dict(orient='records')
        return dict_opt

    def volumetric_graph(self, id):
        #Dataframe
        df = dh.aggregateAcquistion(id)
        radius = df['x'].max()
        dims = radius * 2 + 1
        xy_shape = (dims, dims)
        nb_frames = df.iloc[:,2:].shape[1]
        max_intensity = df.iloc[:,2:].max(axis=1).max()
        freqs = pd.melt(df.iloc[::xy_shape[0]*xy_shape[1],2:])['frequency'].values

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
    
    def surface_3d_graph(self, id, frequency, smoothing):
        #Dataframe
        id = int(id)
        frequency = float(frequency)
        df = dh.aggregateAcquistion(id, frequencies=[frequency-5, frequency+5])

        #Input: Dataframe with e.g. columns; 'x', 'y', '1005.43'
        array = df.columns[2:]
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
        sigma = [smoothing, smoothing]
        z = scipy.ndimage.filters.gaussian_filter(z, sigma)
        
        fig = go.Figure(data=[go.Surface(z=z, x=x, y=y)])
        fig.update_layout(title=nearestFreq, autosize=False,
                          width=600, height=600,
                          margin=dict(l=65, r=50, b=65, t=90))
        return fig

def dash_callbacks(app):
    #Fallback figure - Empty figure for default
    fig = go.Figure(data=[go.Scatter(x=[], y=[])])

    @app.dash.callback(
        Output('volumetric-graph', 'figure'),
        Output('volumetric-alert', 'className'),
        [Input('series-selector', 'value')])
    def update_volumetric_graph(id):
        if id == '':
            return fig, 'd-none'
        try:
            volumetric_fig = app.volumetric_graph(id)
        except:
            return fig, 'd-block'
        return volumetric_fig, 'd-none'

    @app.dash.callback(
        Output('surface-3d-graph', 'figure'),
        Output('surface-alert', 'className'),
        [Input('surface-submit', 'n_clicks'),
        Input('series-selector', 'value')],
        [State('surface-frequency', 'value'),
        State('surface-smoothing', 'value')])
    def update_surface_graph(n_clicks, id, frequency, smoothing):
        if id == '':
            return fig, 'd-none'
        try:
            surface_fig = app.surface_3d_graph(id, frequency, smoothing)
        except:
            return fig, 'd-block'
        return surface_fig, 'd-none'
    
    @app.dash.callback(
        Output('table', 'children'),
        [Input('date-range', 'start_date'),
        Input('date-range', 'end_date'),
        Input('points-lower', 'value'),
        Input('points-upper', 'value')])
    def update_table_df(start_date, end_date, points_lower, points_upper):
        if start_date == None and end_date == None and points_lower == None and points_upper == None:
            return app.getSeriesTable(app.data)
        df = pd.DataFrame.from_dict(dh.getSeriesRange([start_date, end_date], [points_lower, points_upper])['series'])
        return app.getSeriesTable(df)

    @app.dash.callback(
        [Output('date-range', 'start_date'),
        Output('date-range', 'end_date')],
        [Input('reset-date', 'n_clicks')])
    def reset_date_range(nclick):
        return None, None
    
    @app.dash.callback(
        Output('volumetric-graph-click', 'children'),
        [Input('volumetric-graph', 'clickData')],
        [State('volumetric-graph', 'figure')])
    def volumetric_onclick(clickData, fig):
        trigger = dash.callback_context.triggered[0]["prop_id"]
        if trigger == 'volumetric-graph.clickData':
            return str(clickData['points'])

def start_webview():
    app = Hyperspecter()

    dash_callbacks(app)

    window = webview.create_window('Raman Imaging', app.dash.server, width=1300, height=850)
    webview.start()

def start_dash():
    app = Hyperspecter()

    dash_callbacks(app)

    app.dash.run_server(debug=True, port=5501)

if __name__ == "__main__":
    start_dash()
    #start_webview()