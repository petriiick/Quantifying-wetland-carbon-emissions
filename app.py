from shiny import *
from shiny.types import FileInfo
import pandas as pd
import numpy as np
import json
import copy

# from htmltools import HTML
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from shinywidgets import output_widget, register_widget, reactive_read


# utils:
from util import Get_sheet_names, data_prep, plot_map, timeseries

# default map
# def_loc = pd.read_excel("./data/flux_site_loc_new.xlsx")
def_loc = pd.read_excel("./data/flux_site_loc_def.xlsx")

app_ui = ui.page_fluid(
    ui.panel_title("View time series' for your site"),
    ui.layout_sidebar(
        ui.panel_sidebar(
            # ui.HTML(style = "height: 90vh; overflow-y: auto;"),
            ui.input_checkbox_group(
                "var",
                "Variable(s) to Visualize:",
                {
                    "NEE": "NEE",
                    "SW_IN": "SW_IN",
                    "TA": "TA",
                    "VPD": "VPD",
                    "P": "P",
                    "SWC": "SWC",
                    "WS": "WS",
                    "TS": "TS",
                    "WTD": "WTD",
                    "WTDdiff": "WTDdiff",
                    "PDSI": "PDSI",
                    "LAI_month_max": "LAI_month_max",
                    "FAPAR_month_max": "FAPAR_month_max",
                    "NDVI": "NDVI",
                    "SIF_daily_8day": "SIF_daily_8day",
                    "SIF_month": "SIF_month",
                },
            ),
            ui.output_ui("var_chosen"),
        ),
        ui.panel_main(
            ui.row(
                ui.column(
                    5,
                    ui.input_file(
                        "file1", "Upload your site locations (.xlsx)", accept=[".xlsx"]
                    ),
                ),
                ui.column(
                    5,
                    ui.input_file(
                        "file2", "Upload your data (.xlsx)", accept=[".xlsx"]
                    ),
                ),
            ),
            # ui.output_ui("path"),
            output_widget("map"),
            ui.output_text_verbatim("loc"),
        ),
        
    ),
)


def server(input, output, session):
    
    map = plot_map(def_loc)
    
    def update_point(trace, points, selector):
        c = ['#0d6aff'] * map.data[0].lat.size
        s = [12] * map.data[0].lat.size
        for i in points.point_inds:
            c[i] = '#add8e6'
            s[i] = 20
        map.data[0].marker.color = c
        map.data[0].marker.size = s
        color.set(map.data[0].marker.color)
    
    map.data[0].on_click(update_point)
    color = reactive.Value(map.data[0].marker.color)
    register_widget("map", map)
    
    
    # Read the location and statistic data :
    @reactive.Calc
    @reactive.event(input.file1)
    def parse_map():
        file_1 = input.file1()
        if file_1 is None:
            return def_loc
        return pd.read_excel(file_1[0]["datapath"])

    @reactive.Calc
    @reactive.event(input.file2)
    def parse_sta():
        file_2 = input.file2()
        if file_2 is None:
            return pd.DataFrame()
        return pd.read_excel(file_2[0]["datapath"])
    
    @reactive.Effect()
    def _():
        new_loc = parse_map()
        nonlocal map 
        map = plot_map(new_loc)
        def update_point(trace, points, selector):
            c = ['#0d6aff'] * map.data[0].lat.size
            s = [12] * map.data[0].lat.size
            for i in points.point_inds:
                c[i] = '#add8e6'
                s[i] = 20
            map.data[0].marker.color = c
            map.data[0].marker.size = s
            color.set(map.data[0].marker.color)
        map.data[0].on_click(update_point)
        register_widget("map", map)
        
    @reactive.Calc()
    def select_loc():
        data = reactive_read(map, "data")
        loc = data[0].text
        color_set = color()
        print('changed')
        try:
            index = color_set.index('#add8e6')
        except ValueError:
            index = -1
        if index == -1:
            return ''
        else:
            return loc[index]

    @output
    @render.ui
    def var_chosen():
        req(input.var())
        return "You chose the variable(s) " + ", ".join(input.var())
    

    @output
    @render.text
    def loc():
        data = reactive_read(map, "data")
        loc = data[0].text
        color_set = color()
        print('changed')
        try:
            index = color_set.index('#add8e6')
        except ValueError:
            index = -1
        if index == -1:
            return 'Please select desired site by clicking on the corresponding marker in the map.'
        else:
            return 'You have selected location ' + loc[index]
        

    
    

    
    
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
    # @output
    # @render_widget
    # def map():
    #     # create_map(df: pd.DataFrame)
    #     # if input.file1() is None:
    #     #     return "Please upload a .xlsx file"
    #     # # loc = pd.read_excel(f[0]["datapath"])
    #     # names = Get_sheet_names(input.file())
    #     # final_def = data_prep(f[0]["datapath"], names)
    #     loc = parse_map()
    #     map = plot_map(loc)
    #     print(type(map))
    #     register_widget("map", map)
    #     return map

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
