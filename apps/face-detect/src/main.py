from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, File
import uvicorn
from my_yolo import (
    convert_bytes_to_image,
    convert_image_to_bytes,
    detect_faces_in_image,
    draw_detection_boxes
)
import time
import os
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import get_tracer_provider, set_tracer_provider
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from loguru import logger
import socket
from contextlib import closing
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from starlette.types import ASGIApp
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter as OTLPSpanExporterGRPC,
)
from opentelemetry.instrumentation.logging import LoggingInstrumentor

# Initialize FastAPI app
app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Get configuration from environment variables
OTLP_GRPC_ENDPOINT = os.environ.get("OTLP_GRPC_ENDPOINT", "jaeger-jaeger.tracing.svc.cluster.local:4317")


def setting_jaeger(app: ASGIApp, log_correlation: bool = True) -> None:
    try:
        # set the tracer provider
        tracer = TracerProvider(
            resource=Resource.create({SERVICE_NAME: "face-detection"}),
            sampler=ALWAYS_ON
        )
        trace.set_tracer_provider(tracer)

        otlp_exporter = OTLPSpanExporterGRPC(
            endpoint=OTLP_GRPC_ENDPOINT,
            insecure=True
        )

        logger.info(f"Configuring OTLP exporter with endpoint: {OTLP_GRPC_ENDPOINT}")

        # Remove the shutdown() call that was causing the issue
        tracer.add_span_processor(BatchSpanProcessor(otlp_exporter))

        if log_correlation:
            LoggingInstrumentor().instrument(set_logging_format=True)
        FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer)
        logger.info("Jaeger instrumentation completed successfully")
    except Exception as e:
        logger.error(f"Failed to set up Jaeger instrumentation: {str(e)}")
        raise  # Re-raise the exception to make setup failures visible


setting_jaeger(app)


@app.get('/health')
async def check_health():
    return {'status': 'healthy'}


@app.post("/detect/faces/image")
async def detect_faces_image(file: bytes = File(...)):
    start_time = time.time()

    input_image = convert_bytes_to_image(file)
    predictions = detect_faces_in_image(input_image)
    annotated_image = draw_detection_boxes(
        image=input_image,
        detections=predictions
    )
    image_bytes = convert_image_to_bytes(annotated_image)

    execution_time = time.time() - start_time
    logger.info(f"Processing time: {execution_time:.2f} seconds")

    return StreamingResponse(
        content=image_bytes,
        media_type="image/jpeg",
        headers={
            "X-Total-Faces": str(len(predictions)),
            "X-Processing-Time": f"{execution_time:.2f}"
        }
    )
