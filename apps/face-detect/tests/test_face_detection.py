from fastapi.testclient import TestClient
from main import app
import os

client = TestClient(app)


def test_face_detection_endpoint():
    """
    Basic test to check if the face detection endpoint is working with a test image.
    Tests:
    1. Endpoint accessibility
    2. Response status code
    3. Response headers
    4. Response content type
    """
    # Path to test image
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_image_path = os.path.join(current_dir, "test_face.jpg")

    # Read test image
    with open(test_image_path, "rb") as image_file:
        image_bytes = image_file.read()

    # Send request to the endpoint
    response = client.post(
        "/detect/faces/image",
        files={"file": ("test_face.jpg", image_bytes, "image/jpeg")}
    )

    # Basic assertions
    assert response.status_code == 200, "API should return 200 OK"
    assert response.headers["content-type"] == "image/jpeg", "Response should be a JPEG image"
    assert "X-Total-Faces" in response.headers, "Response should include X-Total-Faces header"
    assert "X-Processing-Time" in response.headers, "Response should include X-Processing-Time header"

    # Print useful information
    print(f"Number of faces detected: {response.headers['X-Total-Faces']}")
    print(f"Processing time: {response.headers['X-Processing-Time']} seconds")


def test_health_endpoint():
    """
    Test the health check endpoint
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
