from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets
import plotly.graph_objects as go

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

class Hyperspecter(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title = QtWidgets.QLineEdit(self)
        self.button = QtWidgets.QPushButton('Plot', self)
        self.browser = QtWebEngineWidgets.QWebEngineView(self)

        vlayout = QtWidgets.QVBoxLayout(self)
        vlayout.addWidget(self.button, alignment=QtCore.Qt.AlignHCenter)
        vlayout.addWidget(self.title, alignment=QtCore.Qt.AlignHCenter)
        vlayout.addWidget(self.browser)

        self.button.clicked.connect(self.show_graph)
        self.resize(1000,800)

    def show_graph(self):
        #Dataframe
        df = dh.aggregateAcquistion(self.title.text())
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
            z=freqs.max() * np.ones(xy_shape),
            surfacecolor=np.flipud(df[40]),
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
            "x": 1,
            "y": 0,
            "steps": [{
                "args": [[f.name], frame_args(0)],
                "label": str(k),
                "method": "animate",
            } for k, f in enumerate(fig.frames)],
        }]
        # Layout
        fig.update_layout(
            title='Slices in volumetric data',
            width=800,
            height=600,
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
                "x": 1,
                "y": 0,
            }], sliders=sliders
        )
        self.browser.setHtml(fig.to_html(include_plotlyjs='cdn'))

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    specter = Hyperspecter()
    specter.show()
    app.exec()