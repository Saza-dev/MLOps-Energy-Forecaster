from fastapi.testclient import TestClient
from httpx import Response
from main import app

client = TestClient(app)

def test_read_root():
    """
    Test that the root endpoint returns a 200 OK status and the correct message.
    """
    response: Response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "Energy Prediction API is running."}

def test_predict_endpoint_success():
    """
    Test the /predict endpoint with a valid request.
    It should return a 200 OK status and a dictionary of predictions.
    """
    response: Response = client.post(
        "/predict",
        json={"start_date": "2018-08-03", "end_date": "2018-08-04"}
    )
    assert response.status_code == 200
    response_data = response.json()
    assert "predictions" in response_data
    assert isinstance(response_data["predictions"], dict)
    assert "2018-08-03T00:00:00" in response_data["predictions"]

def test_predict_endpoint_invalid_date():
    """
    Test the /predict endpoint with an invalid date format.
    It should return an error message.
    """
    response: Response = client.post(
        "/predict",
        json={"start_date": "invalid-date", "end_date": "2018-08-04"}
    )
    assert response.status_code == 200 
    assert "error" in response.json()
    assert "Invalid date format" in response.json()["error"]
