from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_read_root():
    """Test the root endpoint to ensure it's working."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Energy Consumption Prediction API!"}

def test_predict_endpoint_success():
    """
    Test the /predict endpoint with valid start and end dates.
    It should return a 200 OK status and a dictionary of predictions.
    """
    response = client.post(
        "/predict",
        json={"start_date": "2018-08-03", "end_date": "2018-08-03"} 
    )
    assert response.status_code == 200
    data = response.json()
    assert "predictions" in data
    assert isinstance(data["predictions"], dict)
    assert "2018-08-03 00:00:00" in data["predictions"] 

def test_predict_endpoint_invalid_date():
    """
    Test the /predict endpoint with an invalid date format.
    FastAPI should automatically return a 422 Unprocessable Entity status.
    """
    response = client.post(
        "/predict",
        json={"start_date": "invalid-date", "end_date": "2018-08-04"}
    )
    assert response.status_code == 422
    assert "detail" in response.json()

