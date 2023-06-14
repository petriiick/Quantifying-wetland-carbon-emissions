"""
Shiny app for wetland carbon emissions.

How to use:
1. Upload your excel file
    a. The file should have sheet names as the sensor location name.
    b. The file should be in .xlsx format.
    c. The date column should be named as "Date".


"""
from shiny import *
from shiny.types import FileInfo
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns

# import plotly.graph_objects as go

# utils:
from util import Get_sheet_names, data_prep, get_coordination, create_map

app_ui = ui.page_fluid(
    ui.panel_title("Wetland carbon emissions"),
    ui.layout_sidebar(
        ui.panel_sidebar(
            ui.input_file(
                "file", "Upload Your excel file here(.xlsx)", accept=[".xlsx"]
            ),
        ),
        ui.panel_main(
            ui.output_plot("plot", "Correlation Heatmap"),
        ),
    ),
)


def sever(input, output, session) -> None:
    """Server of the app."""
    df = pd.read_excel(input.file())

    @output
    @render.plot
    def plot() -> object:
        f: FileInfo = input.file()
        df = pd.read_excel(f[0]["datapath"])
        poc = sns.heatmap(df.corr(), cbar=True, cmap="coolwarm")
        return poc


app = App(app_ui, sever)
