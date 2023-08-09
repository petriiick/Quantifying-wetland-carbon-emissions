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
    # drop sheet name
    data.drop(data.columns[-1], axis=1, inplace=True)
    # drop unnamed columns
    data.drop(data.filter(regex='Unnamed').columns, axis=1, inplace=True)
    # check missingness
    data = data.replace(-9999, np.nan)
    data = data.dropna(subset=["NEE"])
    percent_missing = data.isnull().sum() * 100 / len(data)
    print(percent_missing)
    columns_to_drop = percent_missing[percent_missing > 50].index
    data = data.drop(columns=columns_to_drop)
    # data imputation
    data.set_index('Date', inplace=True)
    data.index = pd.to_datetime(data.index, format='%Y%m%d')
    for columns in data.columns:
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
    colnames = columns=list(onehot_enc.get_feature_names_out(input_features=onehotcols))
    onehot_vals = onehot_enc.transform(data[onehotcols]).toarray()
    enc_df = pd.DataFrame(onehot_vals,columns=colnames,index=data.index)
    data = pd.concat([data,enc_df],axis=1).drop(onehotcols,axis=1)
    # data.pop('Date')
    # data.to_excel("data/output.xlsx")  
    return data


def rf(df: pd.DataFrame):
    
    df = df.dropna()
    
    # Labels are the values we "want to predict
    labels = np.array(df['NEE'])
    # Remove the labels from the features
    # axis 1 refers to the columns
    df_upsampled= df.drop('NEE', axis = 1)

    print(np.isnan(df_upsampled).any())
    # Saving feature names for later use
    feature_list = list(df_upsampled.columns)
    # Convert to numpy array
    features = np.array(df_upsampled)

    train_features, test_features, train_labels, test_labels = train_test_split(features, labels, test_size = 0.25, random_state = 42)
    scaler = StandardScaler()

    train_features = scaler.fit_transform(train_features)
    test_features = scaler.transform(test_features)
    
    # Grid Search
    # clf = sklearn.ensemble.RandomForestRegressor(random_state=21)
    # param_grid = {'bootstrap': [False],
    #             'min_samples_split': [2, 5, 10],
    #             'max_depth': [8, 16, None],
    #             'max_features': ['sqrt'],
    #             'n_estimators': [3,5,10,20,30,40,50,60,70,80,90,100,200,300,500],
    #             'min_samples_leaf': [1, 2, 4]}
    # gd_sr = GridSearchCV(estimator=clf,
    #                  param_grid=param_grid,
    #                  scoring='r2',
    #                  cv=KFold(n_splits=3, shuffle=True, random_state=21),
    #                  error_score="raise")
    # print("success 0!")
    # import warnings
    # warnings.filterwarnings('ignore')
    # gd_sr.fit(train_features, train_labels)
    # print(gd_sr.best_params_)
    # print("success 0!")

    # new model with best params
    clf = sklearn.ensemble.RandomForestRegressor(bootstrap = False, min_samples_split = 2, min_samples_leaf =1, n_estimators = 100, max_features = 'sqrt', random_state=21)
    clf = clf.fit(train_features, train_labels)
    best_param = {'bootstrap': False, 'min_samples_split': 3, 'min_samples_leaf': 2, 'n_estimators': 40, 'max_features': 'sqrt', 'random_state': 21}
    # Prediction
    predictions = clf.predict(test_features)

    # actual vs. prediction:
    reg = LinearRegression().fit(test_labels.reshape((-1, 1)), predictions)
    a = reg.coef_
    b = reg.intercept_
    fig, (ax1, ax2)= plt.subplots(2,1,squeeze= True, figsize=(12,12))
    ax1.scatter(test_labels, predictions)
    ax1.plot([-15,15],[-15,15],color = 'k')
    ax1.plot(test_labels, a * test_labels + b,color = 'r')
    ax1.set_xlim([-15, 15])
    ax1.set_ylim([-15, 15])
    ax1.set_xlabel("NEE")
    ax1.set_ylabel("NEE Estimated")
    ax1.set_title('NEE Estimated vs Actual')
    print("success 1!")
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
    ax2.bar(x_values, importances, orientation = 'vertical')
    # Tick labels for x axis
    ax2.set_xticks(x_values, feature_list, rotation='vertical')
    # Axis labels and title
    ax2.set_ylabel('Importance')
    ax2.set_xlabel('Variable')
    ax2.set_title('Variable Importances')
    print("success 2!")
    return best_param, clf.score(test_features,test_labels), fig, clf
    # returns score, actual vs pred plot, feature importance, model

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