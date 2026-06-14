from PIL import Image
import io
import os
import pandas as pd
import numpy as np
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, colors
from loguru import logger

# Model path: env MODEL_PATH overrides (e.g. /app/models in container or model registry later);
# default resolves to apps/face-detect/models/ relative to this file, independent of CWD.
_DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models",
    "yolov11n-face.pt",
)
MODEL_PATH = os.environ.get("MODEL_PATH", _DEFAULT_MODEL_PATH)

# Initialize the YOLOv11 face detection model
logger.info(f"Loading YOLOv11 face detection model from {MODEL_PATH}")
face_detection_model = YOLO(MODEL_PATH)
logger.info("Face detection model loaded successfully")


def convert_bytes_to_image(image_bytes: bytes) -> Image:
    """
    Convert bytes to PIL Image object.

    Args:
        image_bytes (bytes): Raw image bytes

    Returns:
        Image: PIL Image in RGB format
    """
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")


def convert_image_to_bytes(image: Image) -> bytes:
    """
    Convert PIL Image to bytes for HTTP response.

    Args:
        image (Image): PIL Image object

    Returns:
        bytes: Image encoded as JPEG bytes
    """
    buffer = io.BytesIO()
    image.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    return buffer


def convert_yolo_predictions_to_dataframe(results: list, label_dict: dict) -> pd.DataFrame:
    """
    Convert YOLO detection results to pandas DataFrame.

    Args:
        results (list): YOLO detection results
        label_dict (dict): Dictionary mapping class IDs to labels

    Returns:
        pd.DataFrame: DataFrame containing detection results
    """
    # Extract bounding box coordinates
    bbox_df = pd.DataFrame(
        results[0].to("cpu").numpy().boxes.xyxy,
        columns=['xmin', 'ymin', 'xmax', 'ymax']
    )

    # Add detection confidence scores
    bbox_df['confidence'] = results[0].to("cpu").numpy().boxes.conf

    # Add class IDs and names
    bbox_df['class_id'] = results[0].to("cpu").numpy().boxes.cls.astype(int)
    bbox_df['class_name'] = bbox_df["class_id"].replace(label_dict)

    return bbox_df


def detect_faces(
    model: YOLO,
    image: Image,
    save_output: bool = False,
    image_size: int = 1248,
    confidence_threshold: float = 0.5,
    use_augmentation: bool = False
) -> pd.DataFrame:
    """
    Detect faces in an image using YOLO model.

    Args:
        model (YOLO): YOLO model instance
        image (Image): Input image
        save_output (bool): Whether to save detection results
        image_size (int): Input image size for the model
        confidence_threshold (float): Minimum detection confidence
        use_augmentation (bool): Whether to use data augmentation

    Returns:
        pd.DataFrame: DataFrame containing face detections
    """
    predictions = model.predict(
        source=image,
        imgsz=image_size,
        conf=confidence_threshold,
        save=save_output,
        augment=use_augmentation,
        flipud=0.0,
        fliplr=0.0,
        mosaic=0.0,
    )

    return convert_yolo_predictions_to_dataframe(predictions, model.model.names)


def draw_detection_boxes(image: Image, detections: pd.DataFrame) -> Image:
    """
    Draw bounding boxes and labels on image for detected faces.

    Args:
        image (Image): Original image
        detections (pd.DataFrame): Detection results DataFrame

    Returns:
        Image: Image with drawn detection boxes
    """
    # Create annotator object
    annotator = Annotator(np.array(image))

    # Sort detections by x-coordinate
    detections = detections.sort_values(by=['xmin'], ascending=True)

    # Draw each detection
    for _, detection in detections.iterrows():
        # Create label text with confidence percentage
        label = f"{detection['class_name']}: {int(detection['confidence']*100)}%"

        # Get bounding box coordinates
        bbox = [
            detection['xmin'],
            detection['ymin'],
            detection['xmax'],
            detection['ymax']
        ]

        # Draw box and label
        annotator.box_label(
            bbox,
            label,
            color=colors(detection['class_id'], True)
        )

    return Image.fromarray(annotator.result())


def detect_faces_in_image(input_image: Image) -> pd.DataFrame:
    """
    Main function to detect faces in an image using the loaded model.

    Args:
        input_image (Image): Input image for face detection

    Returns:
        pd.DataFrame: DataFrame containing face detection results
    """
    return detect_faces(
        model=face_detection_model,
        image=input_image,
        save_output=False,
        image_size=640,
        confidence_threshold=0.5,
        use_augmentation=False
    )
