"""
This script contains utility functions for the project.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import seaborn as sns
import copy

# Missing value Imputation:
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer

def data_prep(df_path: str, 
            # sheet_list: list,
            sensor: str) -> pd.DataFrame:

    df= pd.read_excel(df_path, sheet_name=sensor)
    imp = IterativeImputer(max_iter=10, random_state=0)
    new_d = pd.DataFrame(np.round(imp.fit_transform(df), 4))
    new_d.columns= df.columns
    new_d["Date"] = new_d["Date"].astype(int).astype(str)
    new_d["Date"] = pd.to_datetime(new_d["Date"], format="%Y%m%d")
    return new_d

def plot_map(df: pd.DataFrame):
    token = 'pk.eyJ1IjoiZGVubmlzd3UyOCIsImEiOiJjbGl6NmJ3ZDYwNDNrM2NuZW1lNmEwMzAwIn0.NupBJ_bWkbOZLy2gC6JeMg'
    fig = go.FigureWidget(
        data = [
            go.Scattermapbox(
                lat = df['Latitude'],
                lon = df['Longitude'],
                mode = 'markers',
                marker = go.scattermapbox.Marker(
                    size = [12] * df['Latitude'].size,
                    sizemode = 'diameter',
                    color = ['#0d6aff'] * df['Latitude'].size,
                    opacity = 0.7
                ),
                text = df['Site'],
                hoverinfo = 'text'
            )
        ],
        layout = dict(
            autosize = True,
            hovermode = 'closest',
            height = 400,
            width = 800,
            margin = {"r":0,"t":0,"l":0,"b":0},
            mapbox = dict(
                style = 'mapbox://styles/denniswu28/cliz6yff602nk01qp2dv668w7',
                zoom = 4.1,
                accesstoken = token,
                center=go.layout.mapbox.Center(
                    lat=31.82,
                    lon=-84.25
                ),
            ),
            showlegend = False,
        )
    )
    return fig


def timeseries(df: pd.DataFrame, variable: list[str]):
    index= 0
    fig, axes= plt.subplots(len(variable),1,squeeze= False)
    for var in variable:
        sns.lineplot(x='Date', y= var, data=df, ax= axes[index,0])
        index+=1

    return fig