import plotly.graph_objects as go
import dash
import webview
from threading import Thread

import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html


import numpy as np
import pandas as pd

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
    def __init__(self):
        self.data = pd.DataFrame.from_dict(dh.getAllSeries()['series'])
        self.title = 'title'

        self.dash = dash.Dash(
            external_stylesheets=[dbc.themes.BOOTSTRAP]
        )
        self.grid_layout()
    
    def grid_layout(self):
        self.dash.layout = html.Div([
            dbc.Row([dbc.Col(self.seriesTable(), width=4), dbc.Col(self.seriesGraph(), width=8)])
        ], style={'overflowX': 'hidden'})

    def seriesTable(self):
        self.data['No. Points'] = (self.data['Radius'] * 2 + 1)**2
        return dbc.Card([
            dbc.CardHeader([
                html.H1('Available Series')
            ]),
            dbc.CardBody([
                dbc.Table.from_dataframe(self.data.iloc[:,np.r_[1:4, 8:9, 6:8]],
                    bordered=True,
                    responsive=True
                )
            ], style={'textAlign': 'center'})
        ], style={'height': '52rem', 'margin': '2rem 0rem 2rem 2rem'})

    def seriesGraph(self):
        return dbc.Card([
            dbc.CardHeader([
                html.H1('Selected Series')
            ]),
            dbc.CardBody([
                html.H3(self.title, style={'textAlign': 'center'}),
                dcc.Graph(figure=self.show_graph(), style={'height': '95%'})
            ])
        ], style={'height': '52rem', 'margin': '2rem 2rem 2rem 0rem'})

    def show_graph(self):
        #Dataframe
        df = dh.aggregateAcquistion(self.title)
        dims = df['x'].max() * 2 + 1
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

        #Plotly figure
        frames = list()
        for nb in range(nb_frames):
            frame = go.Frame(
                data=go.Surface(
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

def start_webview():
    app = Hyperspecter()

    window = webview.create_window('Raman Imaging', app.dash.server)
    webview.start()

if __name__ == "__main__":
    start_webview()