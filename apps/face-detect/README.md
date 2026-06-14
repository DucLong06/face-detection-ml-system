# Face Detection API

A FastAPI-based REST API for real-time face detection in images using YOLO model.

## 🌟 Features

- Real-time face detection in images
- Support for multiple image formats (JPEG, PNG)
- Interactive API documentation (Swagger UI)
- CORS support for cross-origin requests
- Health check endpoint
- Docker support with Poetry dependency management

## 🛠️ Technology Stack

- Python 3.10
- FastAPI
- YOLO (YOLOv11n) for face detection
- Poetry for dependency management
- Docker & Docker Compose
- Loguru for logging

## 📋 Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose
- Poetry for dependency management

## 🚀 Getting Started

### Local Development

1. Clone the repository:
```bash
git clone <repository-url>
cd <project-directory>
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Run the application:
```bash
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment

1. Build and run using Docker Compose:
```bash
docker-compose up -d
```

2. Check container status:
```bash
docker-compose ps
```

## 📁 Project Structure

```
├── docker-compose.yaml
├── dockerfile
├── Face-Detection/
├── models/
│   └── yolov11n-face.pt
├── notebook/
│   └── YOLO11_training.ipynb
├── poetry.lock
├── pyproject.toml
├── README.md
├── src/
│   ├── main.py
│   └── my_yolo.py
└── test/
    └── test.jpeg
```

## 🔍 API Endpoints

### 1. Health Check
```http
GET /health
```
Returns API health status.

### 2. Face Detection
```http
POST /detect/faces/image
```
Upload an image to detect faces. Returns the annotated image with detected faces highlighted.

#### Request
- Content-Type: `multipart/form-data`
- Body: Image file (JPEG, PNG)

#### Response
- Content-Type: `image/jpeg`
- Headers:
  - `X-Total-Faces`: Number of faces detected
- Body: Annotated image with detected faces

## 📝 API Documentation

Once the application is running, access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
