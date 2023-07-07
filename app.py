from shiny import *
from shiny.types import FileInfo
import pandas as pd
import numpy as np
import json 
import copy
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
from shinywidgets import output_widget, register_widget, reactive_read, render_widget

from util import data_prep, plot_map, timeseries

# default map
def_loc = pd.read_excel('./data/flux_site_loc_def.xlsx')

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
                        "file1", "#1 Upload your site locations (.xlsx)", accept=[".xlsx"]
                    )),
                ui.column(5, ui.input_file(
                    "file2", "#2 Upload your data (.xlsx)", accept=[".xlsx"]
                ))
            ),
            ui.output_text_verbatim("loc"),
            output_widget("map"),
        )
    ),
    ui.output_plot("show_timeseries")    
)

def server(input, output, session):
    map = plot_map(def_loc)

    # makes map reactive
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

    # also helps make map reactive
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

    # returns the site chosen
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

    # outputs text about map
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
            return '#3 Please select desired site by clicking on the corresponding marker in the map.'
        else:
            return 'You have selected location ' + loc[index]
    
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
        return timeseries(data_prep(parse_sta(),select_loc()), variable())

app = App(app_ui, server)
