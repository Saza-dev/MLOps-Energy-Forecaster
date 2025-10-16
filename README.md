# Energy Consumption Prediction API

This project provides a FastAPI-based API to serve a pre-trained XGBoost model for forecasting hourly energy consumption. It includes a Dockerfile for easy containerization and a GitHub Actions workflow for automated CI/CD deployment to AWS App Runner.

---
## Project Structure

-   `main.py`: The main FastAPI application file.
-   `Model/model.json`: The pre-trained XGBoost model file.
-   `Model/PJME_hourly.csv`: The historical energy consumption data.
-   `requirements.txt`: Python dependencies.
-   `Dockerfile`: Instructions to build the Docker image for the API.
-   `.dockerignore`: Specifies files to exclude from the Docker image.
-   `.github/workflows/main.yml`: The CI/CD pipeline definition.
-   `tests/test_main.py`: Basic unit tests for the API.

---
## Automated Deployment with CI/CD (GitHub Actions + AWS App Runner)

This project is configured to automatically test and deploy to AWS App Runner every time you push a change to the `main` branch.

### 1. AWS Setup (One-Time)

You need to create the necessary resources in your AWS account.

#### a. Create an ECR Repository

This is where your Docker images will be stored.

1.  Go to the **Amazon ECR** service in the AWS Console.
2.  Click **Create repository**.
3.  Choose **Private**.
4.  Enter a **Repository name** (e.g., `energy-predictor-api`). This must match the name you set in `.github/workflows/main.yml`.
5.  Click **Create repository**.

#### b. Create an App Runner Service

This service will automatically pull images from ECR and run your application.

1.  Go to the **AWS App Runner** service in the AWS Console.
2.  Click **Create an App Runner service**.
3.  For **Source**, select **Container registry** and **Amazon ECR**.
4.  For **Container image URI**, browse and select your newly created ECR repository. For the initial deployment, App Runner might need an image to exist first, so you might need to push one manually or complete the GitHub Actions setup first.
5.  For **Deployment settings**, choose **Automatic**.
6.  Give your service a name and configure the port to **8000**.
7.  Proceed through the steps and click **Create & deploy**.
8.  Once created, copy the **Service ARN** from the service overview page. You will need this for the workflow file.

### 2. GitHub Setup (One-Time)

#### a. Add Repository Secrets

You must provide your AWS credentials to GitHub securely.

1.  In your GitHub repository, go to **Settings** > **Secrets and variables** > **Actions**.
2.  Click **New repository secret**.
3.  Create two secrets:
    -   `AWS_ACCESS_KEY_ID`: Your AWS access key.
    -   `AWS_SECRET_ACCESS_KEY`: Your AWS secret access key.

#### b. Configure the Workflow File

1.  Open the `.github/workflows/main.yml` file.
2.  Update the placeholder values in the `env` section with your actual AWS details:
    -   `AWS_REGION`: The AWS region where you created your resources (e.g., `us-east-1`).
    -   `ECR_REPOSITORY`: The name of your ECR repository.
    -   `APP_RUNNER_SERVICE_ARN`: The ARN you copied from your App Runner service.

### 3. Triggering the Workflow

Now, every time you commit and push changes to your `main` branch, the workflow will automatically run. You can view its progress under the **Actions** tab in your GitHub repository. It will run the tests, build a new Docker image, push it to ECR, and tell App Runner to deploy it.

---
## Local Development & Docker

Instructions for running the application locally or building the Docker image manually are provided below.

### 1. Prerequisites (Local)

-   Python 3.8+
-   The `model.json` and `PJME_hourly.csv` files must be in the same directory as `main.py`.

### 2. Install Dependencies (Local)

Install all the required Python packages using pip:

```bash
pip install -r requirements.txt
```

### 3. Run the API Server (Local)

You can run the application using `uvicorn`:

```bash
uvicorn main:app --reload
```

The API will be accessible at `http://127.0.0.1:8000`.

### 4. Build the Docker Image

From your terminal, navigate to the project directory and run the `docker build` command. This will create an image named `energy-predictor-api`.

```bash
docker build -t energy-predictor-api .
```

### 5\. Run the Docker Container

Once the image is built, run it as a container using the `docker run` command:

```bash
docker run -d -p 8000:8000 --name energy-api energy-predictor-api
```

  - `-d`: Runs the container in detached mode (in the background).
  - `-p 8000:8000`: Maps port 8000 on your local machine to port 8000 inside the container.
  - `--name energy-api`: Assigns a convenient name to your running container.

The API will now be running inside the container and accessible at `http://localhost:8000`.
