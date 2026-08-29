# AquaSafe – Waterborne Disease Risk Prediction System
## Running the Application with Docker

### Prerequisites

Install Docker Desktop before running the containerized application.

### 1. Clone the Repository

```bash
git clone https://github.com/IamKevinMoses/Final_Project.git
```

Move into the project directory:

```bash
cd Final_Project
```

### 2. Build the Docker Image

```bash
docker build -t final-project .
```

### 3. Run the Docker Container

```bash
docker run -p 5000:5000 final-project
```

### 4. Access the Application

After the container starts successfully open a web browser and visit:

```text
http://localhost:5000
```

## Running Without Docker

Create and activate a Python virtual environment, install the required dependencies and run:

```bash
pip install -r requirements.txt
python run.py
```

The application can then be accessed through the local Flask server.

## Author

**Kevin Moses**

Final Project – BSc Data Science
