"""
This script contains utility functions for the project.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import seaborn as sns
import copy
# modeling
from sklearn.metrics import mean_squared_error,r2_score
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import sklearn.ensemble
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import KFold
from sklearn.linear_model import LinearRegression
from sklearn.inspection import partial_dependence


import warnings
warnings.filterwarnings('ignore')



def data_prep(df_path: str, 
            # sheet_list: list,
            sensor: str) -> pd.DataFrame:
    if sensor == '':
        return None
    else:
        data = pd.read_excel(df_path, sheet_name = sensor)
        data= data.loc[:, ['Date','NEE', 'SW_IN', 'TA', 'VPD', 'P', \
                            'SWC', 'WS', 'TS', 'WTD', 'WTDdiff', 'PDSI', \
                            'LAI_month_max', 'FAPAR_month_max', 'NDVI', \
                            'SIF_daily_8day', 'SIF_month']]
        data.set_index('Date', inplace=True)
        data.index = pd.to_datetime(data.index, format='%Y%m%d')
        for columns in data.columns:
            data[columns] = data[columns].replace(-9999, np.nan)
            data[columns] = data.groupby(data.index.dayofyear)[columns].transform(lambda x: x.fillna(x.mean()))
        return data

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
    if len(variable) == 0:
        return None
    else:
        index= 0
        fig, axes= plt.subplots(len(variable),1,squeeze= False)
        for var in variable:
            sns.lineplot(x='Date', y= var, data=df, ax= axes[index,0])
            index+=1
        return fig

def data_prep_model(df_path: str) -> pd.DataFrame:
    # concat data
    sheet_names = pd.ExcelFile(df_path).sheet_names
    df_list = [
        pd.read_excel(df_path, sheet_name=sheet).assign(sheet_name=sheet)
        for sheet in sheet_names
    ]
    data = pd.concat(df_list)
    data.pop()
    # data imputation
    data.set_index('Date', inplace=True)
    data.index = pd.to_datetime(data.index, format='%Y%m%d')
    for columns in data.columns:
        data[columns] = data[columns].replace(-9999, np.nan)
        data[columns] = data.groupby(data.index.dayofyear)[columns].transform(lambda x: x.fillna(x.mean()))
    # feature engineering
    data['season'] = data['Month'] 
    data['season'] = data['season'].replace([2,12], 1)
    data['season'] = data['season'].replace([3,4,5], 2)
    data['season'] = data['season'].replace([6,7,8], 3)
    data['season'] = data['season'].replace([9,10,11], 4)
    # one hot encoding
    onehotcols = ['Month','season']
    onehot_enc = OneHotEncoder(handle_unknown='ignore')
    onehot_enc.fit(data[onehotcols])
    colnames = columns=list(onehot_enc.get_feature_names(input_features=onehotcols))
    onehot_vals = onehot_enc.transform(data[onehotcols]).toarray()
    enc_df = pd.DataFrame(onehot_vals,columns=colnames,index=data.index)
    data = pd.concat([data,enc_df],axis=1).drop(onehotcols,axis=1)
    return data


def rf(df: pd.DataFrame):
    
    # Labels are the values we "want to predict
    labels = np.array(df['NEE'])
    # Remove the labels from the features
    # axis 1 refers to the columns
    df_upsampled= df.drop('NEE', axis = 1)
    # Saving feature names for later use
    feature_list = list(df_upsampled.columns)
    # Convert to numpy array
    features = np.array(df_upsampled)
    train_features, test_features, train_labels, test_labels = train_test_split(features, labels, test_size = 0.25, random_state = 42)
    scaler = StandardScaler()
    train_features = scaler.fit_transform(train_features)
    test_features = scaler.transform(test_features)
    clf = sklearn.ensemble.RandomForestRegressor(random_state=21)
    param_grid = {'bootstrap': [True, False],
              'min_samples_split': [2, 5, 10],
              'max_depth': [2, 8, 16],
              'max_features': ['auto', 'sqrt','log2'],
              'n_estimators': [10,50,100,500,1000,2000,5000,10000],
              'min_samples_leaf': [1, 2, 4]}
    gd_sr = GridSearchCV(estimator=clf,
                     param_grid=param_grid,
                     scoring='r2',
                     cv=KFold(n_splits=3, shuffle=True, random_state=21),
                     error_score="raise")
    gd_sr.fit(train_features, train_labels)

    # new _model with best params
    clf = sklearn.ensemble.RandomForestRegressor(gd_sr.best_params_, random_state=21)
    clf = clf.fit(train_features, train_labels)
    
    # Prediction
    predictions = clf.predict(test_features)

    # actual vs. prediction:
    reg = LinearRegression().fit(test_labels.reshape((-1, 1)), predictions)
    a = reg.coef_
    b = reg.intercept_
    fig1, ax = plt.subplots(1,1,figsize=(9,9))
    plt.scatter(test_labels, predictions)
    plt.plot([-15,15],[-15,15],color = 'k')
    plt.plot(test_labels, a * test_labels + b,color = 'r')
    plt.xlim([-15, 15])
    plt.ylim([-15, 15])
    ax.set_xlabel("NEE")
    ax.set_ylabel("NEE Estimated")
  
    # feature importance
    importances = list(clf.feature_importances_)
    # List of tuples with variable and importance
    feature_importances = [(feature, round(importance, 4)) for feature, importance in zip(feature_list, importances)]
    # Sort the feature importances by most important first
    feature_importances = sorted(feature_importances, key = lambda x: x[1], reverse = True)
    # Set the style
    plt.style.use('fivethirtyeight')
    # list of x locations for plotting
    x_values = list(range(len(importances)))
    # Make a bar chart
    fig2 = plt.bar(x_values, importances, orientation = 'vertical')
    # Tick labels for x axis
    plt.xticks(x_values, feature_list, rotation='vertical')
    # Axis labels and title
    plt.ylabel('Importance'); plt.xlabel('Variable'); plt.title('Variable Importances');

    return gd_sr.best_params_, clf.score(test_features,test_labels),fig1, fig2, clf
    # returns best parameters, score, actual vs pred plot, feature importance, model

def rf_partialdep(df,model,variable):
    sk_data0 = partial_dependence(model, X = df, features = variable, percentiles=[0,1])
    f, axs = plt.subplots(1,1,figsize=(9,9))
    ax2 = plt.subplot(111)
    plt.plot(sk_data0["values"][0], sk_data0["average"][0])
    ax2.set_title("SW_IN")
    ax2.set_xlabel("SW_IN")
    ax2.set_ylabel("Partial dependence")
    plt.subplots_adjust(hspace = 0.3)
    return f