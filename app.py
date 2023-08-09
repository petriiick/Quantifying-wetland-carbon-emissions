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

from util import data_prep, plot_map, timeseries, rf, rf_partialdep, data_prep_model

# default map
def_loc = pd.read_excel('./data/flux_site_loc_def.xlsx')

app_ui = ui.page_fluid(
    ui.navset_tab_card(
        ## data visualization tab ##
        ui.nav("Site Data Visualization",
            ui.panel_title("View time series' for your site"),
            ui.h6("Please complete steps in order to avoid errors!"),
            ui.layout_sidebar(
                ui.panel_sidebar(
                    ui.input_checkbox_group("var", "#4 Variable(s) to Visualize:", 
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
                    ui.output_text("error")
                ),
                ui.panel_main(
                    ui.row(
                        ui.column(5,
                            ui.input_file(
                                "file1", "#1 Upload your site locations (.xlsx)", accept=[".xlsx"]
                            )),
                        ui.column(5, 
                            ui.input_file(
                                "file2", "#2 Upload your data (.xlsx)", accept=[".xlsx"]
                            ))
                    ),
                    ui.output_text("loc"),
                    output_widget("map"),
                )
            ),   
            ui.output_ui("timeseries_container") 
        ),

        ## ML tab ##
        ui.nav("Predicting NEE",
            ui.panel_title("Predict NEE for your data"),
            ui.row(
                ui.column(5,
                    ui.input_file(
                        "file3", "#1 Upload your data to predict on (.xlsx)", accept=[".xlsx"]
                    ),
                    ui.input_file(
                        "file4", "#2 Upload your data to train on (.xlsx)", accept=[".xlsx"]
                    )),
                ui.column(5, 
                    ui.input_radio_buttons(
                        "model",
                        "#2 Select a machine learning model",
                        {
                            "rf": "Random Forest",
                            "svm": "Support Vector Machine",
                            "ann" : "Artificial Neural Network"
                        },
                        inline=True
                    ))
            ),
            ui.output_text("params"),
            ui.output_ui("NEE_container"),
            ui.layout_sidebar(
                ui.panel_sidebar(
                    ui.input_checkbox_group("var2", "Partial Dependence(s):", 
                        {                                   
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
                    ui.output_text("error2"),
                ),
                ui.panel_main(
                    ui.output_plot("partial_dep_container")
                )
            ),
        )
    )
)

def server(input, output, session):
    ###### Data Viz #######
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
            return '#3 Please select desired site by clicking on the corresponding marker in the map!!!'
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
        data_train = file_2[0]["datapath"]
        return file_2[0]["datapath"]
    
    # returns height of figure in px as string
    @reactive.event(input.var)
    def height_timeseries():
        return str(len(input.var()) * 200) + "px"
    
    # creates the timeseries
    @output
    @render.plot
    def show_timeseries():
        return timeseries(data_prep(parse_sta(),select_loc()), input.var())

    # outputs timeseries graphs with dynamic height
    @output
    @render.ui
    def timeseries_container():
        return (ui.output_plot("show_timeseries", height = height_timeseries()),)
    
    # warns user when no variables are selected
    @output
    @render.text
    def error():
        if len(input.var()) == 0:
            return 'Please select at least one variable to visualize!!!'
        else:
            return ''
    
    ###### ML ######
    best_parameters, score, subplots, model = None, None, None, None

    # Read data to train model on
    @reactive.Calc
    @reactive.event(input.file3)
    def parse_train():
        file_3 = input.file3()
        if file_3 is None:
            return pd.DataFrame()
        # best_parameters, score, subplots, model= rf(data_prep_model(file_3[0]["datapath"]))
        return file_3[0]["datapath"]
    
    # Read data to make predictions on
    @reactive.Calc
    @reactive.event(input.file4)
    def parse_pred():
        file_4 = input.file4()
        if file_4 is None:
            return pd.DataFrame()
        return pd.read_excel(file_4[0]["datapath"])

    # returns the model the user selected
    @reactive.event(input.model)
    def model():
        return input.model()
    
    # displays model parameters
    @output
    @render.text
    def params():
        df = data_prep_model(parse_train())
        return rf(df)[:2]
        # return best_parameters, score
        
    # creates the NEE and importance plots
    @output
    @render.plot
    def show_NEE():
        return rf(data_prep_model(parse_train()))[2]

    # outputs timeseries graphs with dynamic height
    @output
    @render.ui
    def NEE_container():
        return (ui.output_plot("show_NEE", height = '1200px'),)
    

    # returns height of figure in px as string
    @reactive.event(input.var)
    def height_partial_dep():
        return str(len(input.var()) * 200) + "px"

    # creates partial dependency plots
    @output
    @render.plot
    def show_partial_dep():
        return rf_partialdep(parse_train(), model, input.var2())
    
    # outputs partial dependency plots with dynamic height
    @output
    @render.ui
    def partial_dep_container():
        return (ui.output_plot("show_partial_dep", height = height_partial_dep()),)
    
    # warns user when no variables are selected
    @output
    @render.text
    def error2():
        if len(input.var2()) == 0:
            return 'Please select at least one variable to visualize!!!'
        else:
            return ''
        
app = App(app_ui, server)