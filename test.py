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
    ui.h1("HI")

)


def server(input, output, session) -> None:
    """Server of the app."""





app = App(app_ui, server)




    # ui.panel_title("Wetland carbon emissions"),
    # ui.layout_sidebar(
    #     ui.panel_sidebar(
    #         ui.input_file(
    #             "file1", "Upload Your excel file here (.xlsx)", accept=[".xlsx"]
    #         ),
    #     ),
    #     ui.panel_main(
    #         ui.output_plot("plot", "Correlation Heatmap"),
    #     ),
    # )




    # @output
    # @render.plot
    # def plot() -> object:
    #     if input.file1() is None:
    #         return "Please upload a .xlsx file"
    #     f: FileInfo = input.file1()

    #     df = pd.read_excel(input.file())
    #     # df = pd.read_excel(f[0]["datapath"])
    #     names = Get_sheet_names(input.file())
    #     final_def = data_prep(f[0]["datapath"], names)
    #     map = create_map(df)
    #     return map