import pandas as pd
import xgboost as xgb
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Union
from datetime import date

# Initialize FastAPI app
app = FastAPI(title="Energy Consumption Prediction API")

# Model and Data Loading 
reg_new = xgb.XGBRegressor()
reg_new.load_model('model.json')

# Load the historical data needed for creating lag features
try:
    df_full = pd.read_csv('PJME_hourly.csv')
    df_full = df_full.set_index('Datetime')
    df_full.index = pd.to_datetime(df_full.index)
except FileNotFoundError:
    raise RuntimeError("PJME_hourly.csv not found. Please ensure it is in the root directory.")

# Pydantic Models for Request and Response
class PredictionRequest(BaseModel):
    """Defines the structure for an incoming prediction request."""
    start_date: date
    end_date: date

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "start_date": "2018-08-03",
                "end_date": "2018-08-04"
            }
        }
    )

class PredictionResponse(BaseModel):
    """Defines the structure for a successful prediction response."""
    predictions: Dict[str, float]

class ErrorResponse(BaseModel):
    """Defines the structure for an error response."""
    error: str

# Feature Engineering Functions
def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create time series features from a datetime index."""
    df = df.copy()
    df['hour'] = df.index.hour
    df['dayofweek'] = df.index.day_of_week
    df['quarter'] = df.index.quarter
    df['month'] = df.index.month
    df['year'] = df.index.year
    df['dayofyear'] = df.index.day_of_year
    df['dayofmonth'] = df.index.day
    df['weekofyear'] = df.index.isocalendar().week.astype(int)
    return df

def add_lags(df: pd.DataFrame) -> pd.DataFrame:
    """Create lag features based on historical data."""
    target_map = df_full['PJME_MW'].to_dict()
    df['lag1'] = (df.index - pd.Timedelta('364 days')).map(target_map)
    df['lag2'] = (df.index - pd.Timedelta('728 days')).map(target_map)
    df['lag3'] = (df.index - pd.Timedelta('1092 days')).map(target_map)
    return df

# API Endpoints
@app.get("/", tags=["General"])
def read_root():
    """Root endpoint providing a welcome message."""
    return {"message": "Welcome to the Energy Consumption Prediction API!"}

@app.post("/predict",
          response_model=Union[PredictionResponse, ErrorResponse],
          tags=["Prediction"])
def predict(request: PredictionRequest):
    """
    Predict energy consumption for a given date range.
    The dates should be in 'YYYY-MM-DD' format.
    """
    try:
        future_dates = pd.date_range(str(request.start_date), str(request.end_date), freq='1h')
        future_df = pd.DataFrame(index=future_dates)
        future_df['isFuture'] = True

        df_and_future = pd.concat([df_full, future_df])
        df_and_future['isFuture'] = df_and_future['isFuture'].fillna(False)

        df_and_future = create_features(df_and_future)
        df_and_future = add_lags(df_and_future)

        future_with_features = df_and_future.query('isFuture').copy()

        FEATURES = ['hour', 'dayofweek', 'quarter', 'month', 'year', 'dayofyear', 'lag1', 'lag2', 'lag3']

        predictions = reg_new.predict(future_with_features[FEATURES])

        prediction_results = {str(date): pred for date, pred in zip(future_with_features.index, predictions)}

        return PredictionResponse(predictions=prediction_results)

    except ValueError:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid date format. Please use YYYY-MM-DD."}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

