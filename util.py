"""
This script contains utility functions for the project.

Author: Patrick Duan
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# Missing value Imputation:
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer


# Coodination of sensors:
def get_coordination(df: pd.DataFrame) -> pd.DataFrame:
    """This function returns a dataframe of sensor coordination."""
    coodi = {
        "DPW": {"lat": 28.0521, "long": -91.0521},
        "Elm": {"lat": 25.5519, "long": -80.7826},
        "Esm": {"lat": 25.4379, "long": -80.5946},
        "Hb1": {"lat": 33.3455, "long": -79.1957},
        "Ks3": {"lat": 28.7084, "long": -80.7427},
        "LA1": {"lat": 29.5013, "long": -90.4449},
        "LA2": {"lat": 29.8587, "long": -90.2869},
        "NC1": {"lat": 35.8118, "long": -76.7119},
        "NC2": {"lat": 35.8030, "long": -76.6685},
        "NC4": {"lat": 35.7879, "long": -75.9038},
        "xDL": {"lat": 32.5417, "long": -87.8039},
    }

    coodi_df = pd.DataFrame(coodi).T.reset_index()
    coodi_df.columns = ["sensor", "lat", "long"]

    return coodi_df


def Get_sheet_names(df_path: str) -> list:
    """Get sheet names from excel file.

    Args:
        df_path (str): Path to excel file.

    Returns:
        list: Sheet names.
    """
    xl = pd.ExcelFile(df_path)
    return xl.sheet_names


def data_prep(df_path: str, sheet_list: list) -> pd.DataFrame:
    """Prepare data for analysis.

    Args:
        df (pd.DataFrame): Raw data.

    Returns:
        pd.DataFrame: Cleaned data.
    """
    # Get sheet names
    # concatenate all sheets into one dataframe
    # impute missing values
    df_list = [
        pd.read_excel(df_path, sheet_name=sheet).assign(sheet_name=sheet)
        for sheet in sheet_list
    ]
    final_df = pd.concat(df_list)

    imp = IterativeImputer(max_iter=10, random_state=0)
    new_d = pd.DataFrame(np.round(imp.fit_transform(final_df), 4))
    new_d.columns = final_df.columns
    new_d["Date"] = new_d["Date"].astype(int).astype(str)
    new_d["Date"] = pd.to_datetime(new_d["Date"], format="%Y%m%d")

    return new_d


def create_map(df: pd.DataFrame):
    """
    This function creates a map of ground sensors.
    """
    fig = go.FigureWidget(
        data=[
            go.Scattermapbox(
                lat=df["lat"],
                lon=df["long"],
                mode="markers",
                marker=go.scattermapbox.Marker(
                    size=14, sizemode="diameter", color="#0d6aff", opacity=0.7
                ),
                text=df["sensor"],
                hoverinfo="text",
            )
        ],
        layout=dict(
            autosize=True,
            hovermode="closest",
            height=600,
            width=1000,
            margin=dict(l=0, r=0, b=0, t=0),
            mapbox=dict(style="open-street-map", zoom=0.5),
            showlegend=False,
        ),
    )
    return fig

# Sophia testing... creates a map using uploaded excel file
def plot_map(df: pd.DataFrame):
    
    fig = go.FigureWidget(
        data = [
            go.Scattermapbox(
                lat = df['Latitude'],
                lon = df['Longitude'],
                mode = 'markers',
                marker = go.scattermapbox.Marker(
                    size = 10,
                    sizemode = 'diameter',
                    color = '#0d6aff',
                    opacity = 0.5
                ),
                text = df['Site'],
                hoverinfo = 'text'
            )],
        layout = dict(
            autosize = True,
            hovermode = 'closest',
            height = 600,
            width = 1000,
            margin = {"r":0,"t":0,"l":0,"b":0},
            mapbox = dict(
                style = 'carto-darkmatter',
                zoom = 0.9
            ),
            showlegend = False,
        )
    )
    
    return fig