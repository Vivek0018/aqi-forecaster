from sktime.forecasting.base import ForecastingHorizon
from sktime.forecasting.model_selection import temporal_train_test_split
from sktime.forecasting.theta import ThetaForecaster
from sktime.forecasting.naive import NaiveForecaster

import pandas as pd
import sys
from sktime.forecasting.arima import AutoARIMA
from sktime.forecasting.fbprophet import Prophet
from datetime import timedelta

from datetime import datetime


sys.path.append("..")
# import src.utility.plot_settings

# dataset = pd.read_csv("Data/TempNewDelhiData.csv", parse_dates=[0], index_col=[0])


def sktime_forecast(dataset, horizon=30, forecaster=Prophet(yearly_seasonality=True, weekly_seasonality=True), validation=False, confidence=0.9, frequency="D"):
    """Loop over a time series dataframe, train an sktime forecasting model, and visualize the results.

    Args:
        dataset (pd.DataFrame): Input time series DataFrame with datetime index
        horizon (int): Forecast horizon
        forecaster (sktime.forecasting): Configured forecaster
        validation (bool, optional): . Defaults to False.
        confidence (float, optional): Confidence level. Defaults to 0.9.
        frequency (str, optional): . Defaults to "D".
    """
    # Adjust frequency
    forecast_df = dataset.resample(rule=frequency).sum()
    # Interpolate missing periods (if any)
    forecast_df = forecast_df.interpolate(method="time")

    all_parameters_values = {}
    for col in dataset.columns:
        # Use train/test split to validate forecaster
        if validation:
            df = forecast_df[col]

            y_train = df[:-horizon]
            y_test = df.tail(horizon)

            forecaster.fit(y_train)
            fh = ForecastingHorizon(y_test.index, is_relative=False)
            y_pred = forecaster.predict(fh)
            ci = forecaster.predict_interval(fh, coverage=confidence).astype("float")
            y_true = df.tail(horizon)

            # mae = mean_absolute_error(y_true, y_pred)

        # Make predictions beyond the dataset
        if not validation:
            df = forecast_df[col].dropna()
          
            forecaster.fit(df)

            #for present date            
            present_date = datetime.now().date()
            #to start predictions from tomorrow
            present_date = str(present_date + timedelta(days=1)).split(' ')[0]
            fh = ForecastingHorizon(
                pd.date_range(str(present_date), periods=horizon, freq=frequency),
                is_relative=False,
            )

            y_pred = forecaster.predict(fh)
            ci = forecaster.predict_interval(fh, coverage=confidence).astype("float")
            # mae = np.nan

        # Visualize results
        # plt.plot(
        #     df.tail(horizon * 3),
        #     label="Actual",
        #     color="black",
        # )
        # plt.gca().fill_between(
        #     ci.index, (ci.iloc[:, 0]), (ci.iloc[:, 1]), color="b", alpha=0.1
        # )
        # # print(y_pred)
        # plt.plot(y_pred, label="Predicted")
        # plt.xticks(rotation=45, ha='right')
        # # plt.title(
        # #     f"{horizon} day forecast for {col} (mae: {round(mae, 2)}, confidence: {confidence*100}%)"
        # # )
        # plt.ylim(bottom=0)
        # # plt.legend()
        # plt.grid(False)
        # plt.show()
        # print("Mean Absolute Error : ", mae)

        # try :
        #     temp = all_parameters_values['date']
        # except:
        #     all_parameters_values['date'] = [i.strftime("%d-%m-%Y") for i in fh]

        all_parameters_values[col] = y_pred.values
    

    
    dates = [i.strftime("%d-%m-%Y") for i in fh]

    predicted_data = {}
    for date in range(len(dates)):
        temp = {}
        for param in all_parameters_values:
            temp[param] = all_parameters_values[param][date]
        predicted_data[dates[date]] = temp
    
    return predicted_data


def getForecastData(data):
    forecaster = Prophet(yearly_seasonality=True, weekly_seasonality=True)

    finalOut = {}
    if data != 404:

        dates = [i for i in data[0].index]
        for i in range(len(dates)):
            if(dates[i].date() > datetime.now().date()):
                data[0].drop(index=dates[i].date(), inplace=True)

        dataset = data[0]
        dataset = dataset.dropna()

        #saving the file locally without index
        # dataset.to_csv(f"Data/{city_name}_data.csv", index=False)

        #reading the file while parsing the dates
        # dataset = pd.read_csv(f"Data/{city_name}_data.csv", parse_dates=[0], index_col=[0])
        # print(dataset)
        #remove future dates in the dateset

        predicted_data = sktime_forecast(dataset=dataset,forecaster=forecaster, horizon=30, validation=False)


        #for present day data
        presentDayData = {}
        for i in data[0]:
            if str(data[0][i][0]) != 'nan':
                presentDayData[i] = data[0][i][0]
        
        # print(predicted_data)


        finalOut = {
            'code' : 200,
            'response' : {
                "predicted_data" : predicted_data,
                "presentDayData" : presentDayData,
                "city_name" : data[1],
                "city_station" : data[2],
                "country_code" : data[3]
            }
        }

    else:
        finalOut = {
            'code' : 404
        }

    return finalOut