from shiny import *
from shiny.types import FileInfo
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from shinywidgets import output_widget, register_widget, render_widget

from util import data_prep, plot_map, timeseries

# default map
loc = pd.read_excel('./data/flux_site_loc.xlsx')

app_ui = ui.page_fluid(
    ui.panel_title("View time series' for your site"),
    ui.layout_sidebar(
        ui.panel_sidebar(
            ui.input_checkbox_group("var", "Variable(s) to Visualize:", 
                {
                    "NEE" : "NEE",
                    "SW_IN" : "SW_IN",
                    "TA" : "TA",
                    "VPD" : "VPD",
                    "P" : "P",
                    "SWC" : "SWC",
                    "WS" : "WS",
                    "TS" : "TS",
                    "WTD" : "WTD",
                    "WTDdiff" : "WTDdiff",
                    "PDSI" : "PDSI",
                    "LAI_month_max" : "LAI_month_max",
                    "FAPAR_month_max" : "FAPAR_month_max",
                    "NDVI" : "NDVI",
                    "SIF_daily_8day" : "SIF_daily_8day",
                    "SIF_month" : "SIF_month"
                }),
        ),
        ui.panel_main(
            ui.row(
                ui.column(5,
                    ui.input_file(
                        "file1", "Upload your site locations (.xlsx)", accept=[".xlsx"]
                    )),
                ui.column(5, ui.input_file(
                    "file2", "Upload your data (.xlsx)", accept=[".xlsx"]
                ))
            ),
            output_widget("map")
        )
    ),
    ui.output_plot("show_timeseries")    
)

def server(input, output, session):
    # Read the location data
    @reactive.Calc
    @reactive.event(input.file1)
    def parse_map():
        file_1 = input.file1()
        if file_1 is None:
            return pd.DataFrame()
        return pd.read_excel(file_1[0]["datapath"])

    # Read sensor data
    @reactive.Calc
    @reactive.event(input.file2)
    def parse_sta():
        file_2 = input.file2()
        if file_2 is None:
            return pd.DataFrame()
        return file_2[0]["datapath"]

    # when location data is uploaded, update the map output
    @output
    @render_widget
    def map():
        loc = parse_map()
        map = plot_map(loc)
        register_widget("map", map)
        return map
    
    # returns the list of variables the user checked
    @reactive.event(input.var)
    def variable():
        return input.var()
        
    # displays the timeseries
    @output
    @render.plot
    def show_timeseries():
        # TO DO make fig size interactive based on len(variable())
        sns.set(rc={'figure.figsize':(8.27,11.7)})
        return timeseries(data_prep(parse_sta(),'DPW'), variable())

app = App(app_ui, server)
