from shiny import *
from shiny.types import FileInfo
import pandas as pd
import numpy as np
# from htmltools import HTML
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from shinywidgets import output_widget, register_widget, render_widget


# utils:
from util import data_prep, plot_map, timeseries, plot_better_map
# default map
loc = pd.read_excel('./data/flux_site_loc.xlsx')

app_ui = ui.page_fluid(
    ui.panel_title("View time series' for your site"),
    ui.layout_sidebar(
        ui.panel_sidebar(
            # ui.HTML(style = "height: 90vh; overflow-y: auto;"), 
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
                ui.output_ui("var_chosen"),
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
            # ui.output_ui("path"),
            output_widget("map")
        )
    ),
    ui.output_plot("show_timeseries")    
)

def server(input, output, session):
    # Read the location and statistic data :
    @reactive.Calc
    @reactive.event(input.file1)
    def parse_map():
        file_1 = input.file1()
        if file_1 is None:
            return pd.DataFrame()
        return pd.read_excel(file_1[0]["datapath"])

    @reactive.Calc
    @reactive.event(input.file2)
    def parse_sta():
        file_2 = input.file2()
        if file_2 is None:
            return pd.DataFrame()
        # df= file_2[0]["datapath"]
        return file_2[0]["datapath"]
    
    @output
    @render.ui
    def var_chosen():
        req(input.var())
        return "You chose the variable(s) " + ", ".join(input.var())
    
    # @output
    # @render.ui
    # def path():
    #     # create_map(df: pd.DataFrame)
    #     if input.file1() is None:
    #         return "Please upload a .xlsx file"
    #     f: list[FileInfo] = input.file1()
    #     df = pd.read_excel(f[0]["datapath"])
    #     return ui.HTML(df.to_html(classes="table table-striped"))

    # when a .xlsx file is uploaded, update the map output
    # gives error @render.plot doesn't know to render objects of type class str
    @output
    @render_widget
    def map():
        # create_map(df: pd.DataFrame)
        # if input.file1() is None:
        #     return "Please upload a .xlsx file"
        # # loc = pd.read_excel(f[0]["datapath"])
        # names = Get_sheet_names(input.file())
        # final_def = data_prep(f[0]["datapath"], names)
        loc = parse_map()
        map = plot_better_map(loc)
        register_widget("map", map)
        return map
    
    @reactive.Effect
    @reactive.event(input.var)
    def variable():
        # var_choose= input.var()
        return input.var()
        

    @output
    @render.plot
    def show_timeseries():
        # variable= variable()
        # sheet_name= Get_sheet_names(df)
        return timeseries(data_prep(parse_sta(),'DPW'),'NEE')




    # when checkboxes change, update timeseries
    # @reactive.Effect
    # @reactive.event(input.var)
    # def _timeseries():
    #     variables = input.var()
    #     for variable in variables:
    #         make_timeseries(variable)

    # # function to make a timeseries plot given a variable to show
    # @reactive.Effect
    # def make_timeseries(variable: str):
    #     timeseries(f: pd.DataFrame, sensor: str, variable: str)
    #     # display plot
    #     ui.insert_ui(
    #         ui.output_plot("timeseries"),
    #         selector = "var",
    #         where = "afterEnd"
    #     )


app = App(app_ui, server)


