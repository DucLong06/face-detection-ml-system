FROM tiangolo/uvicorn-gunicorn:python3.10

# libgl1 (replaces obsolete libgl1-mesa-glx on Debian trixie) provides libGL.so.1 for opencv/ultralytics
RUN apt update && \
    apt install -y htop libgl1 libglib2.0-0

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# tiangolo base auto-serves /app/main.py via uvicorn-gunicorn
COPY src/ /app/
COPY models/ /app/models/
ENV MODEL_PATH=/app/models/yolov11n-face.pt
