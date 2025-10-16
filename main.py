import pandas as pd
import xgboost as xgb
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict

app = FastAPI(
    title="Energy Consumption Prediction API",
    description="An API to predict hourly PJME energy consumption using an XGBoost model."
)

# Load the trained XGBoost model
try:
    reg_model = xgb.XGBRegressor()
    reg_model.load_model('Model/model.json')
except xgb.core.XGBoostError:
    print("Warning: 'model.json' not found")
    reg_model = None


# Load historical data needed for lag features
try:
    historical_df = pd.read_csv('Model/PJME_hourly.csv')
    historical_df = historical_df.set_index('Datetime')
    historical_df.index = pd.to_datetime(historical_df.index)
    historical_df = historical_df.sort_index()
    historical_df = historical_df.query('PJME_MW > 19_000').copy()
except FileNotFoundError:
    print("Warning: 'PJME_hourly.csv' not found.")
    historical_df = None



# Creating Features and Lags

def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates time series features from a datetime index.
    """
    df = df.copy()
    df['hour'] = df.index.hour
    df['dayofweek'] = df.index.dayofweek
    df['quarter'] = df.index.quarter
    df['month'] = df.index.month
    df['year'] = df.index.year
    df['dayofyear'] = df.index.dayofyear
    df['dayofmonth'] = df.index.day
    df['weekofyear'] = df.index.isocalendar().week.astype(int)
    return df

def add_lags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds lag features to the DataFrame using historical data.
    """
    if historical_df is None:
        raise RuntimeError("Historical data not loaded, cannot create lag features.")
    
    # The target map must come from the original, historical data
    target_map = historical_df['PJME_MW'].to_dict()
    
    df['lag1'] = (df.index - pd.Timedelta('364 days')).map(target_map)
    df['lag2'] = (df.index - pd.Timedelta('728 days')).map(target_map)
    df['lag3'] = (df.index - pd.Timedelta('1092 days')).map(target_map)
    return df

class PredictionRequest(BaseModel):
    """Defines the structure for a prediction request."""
    start_date: str = '2018-08-03'
    end_date: str = '2018-08-04'
    
    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2018-08-03",
                "end_date": "2018-08-04"
            }
        }

class PredictionResponse(BaseModel):
    """Defines the structure for the prediction response."""
    predictions: Dict[str, float]

# prediction api
@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):

    if reg_model is None or historical_df is None:
        return {"error": "Model or historical data not loaded. Check server logs."}

    try:
        future_dates = pd.date_range(start=request.start_date, end=request.end_date, freq='1h')
    except ValueError:
        return {"error": "Invalid date format. Please use YYYY-MM-DD."}
        
    future_df = pd.DataFrame(index=future_dates)
    future_df['isFuture'] = True


    df_and_future = pd.concat([historical_df, future_df])
    df_and_future = create_features(df_and_future)
    df_and_future = add_lags(df_and_future)
    future_with_features = df_and_future.query('isFuture == True').copy()

    features = ['hour', 'dayofweek', 'quarter', 'month', 'year', 'dayofyear', 'lag1', 'lag2', 'lag3']
    predictions = reg_model.predict(future_with_features[features])

    prediction_results = {}
    for timestamp, pred_value in zip(future_with_features.index, predictions):
        prediction_results[timestamp.isoformat()] = round(float(pred_value), 2)
        
    return {"predictions": prediction_results}

# Root endpoint for health check
@app.get("/")
def read_root():
    return {"status": "Energy Prediction API is running."}