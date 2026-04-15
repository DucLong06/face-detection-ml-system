# Face Detection MLOps - Extended Architecture Plans

## Document Overview

This document describes the **complete architecture expansion** from MLOps Level 1 (current) to MLOps Level 2 (Data Engineering) and MLOps Level 3 (Advanced ML Platform + RAG/LLM). It covers all Kubernetes namespaces, tool selections, data flows, user roles, SSO integration, and coursework requirements (Sections 01-04).

> **Status**: Research & Design Phase (NOT implementation yet)
> **Scope**: Maximum ambition - covers both AI Track 4A (ML System) + 4B (LLM/Agent)
> **Reference Diagrams**: See `images/` folder and `architecture_detailed.html`

---

## 1. Current System (MLOps Level 1) - DONE

**Branch**: `main`

### 1.1 Components

| Component | Tool | Version | Namespace | Status |
|-----------|------|---------|-----------|--------|
| ML Model | YOLOv11 Face Detection | latest | `model-serving-ns` | Done |
| API Server | FastAPI | 0.104+ | `model-serving-ns` | Done |
| Container Registry | Docker Hub | - | external | Done |
| Orchestration | GKE (Google Kubernetes Engine) | 1.27+ | - | Done |
| IaC | [Terraform](https://www.terraform.io/) | 1.5+ | - | Done |
| Config Mgmt | [Ansible](https://www.ansible.com/) | 2.15+ | GCE VM | Done |
| CI/CD | [Jenkins](https://www.jenkins.io/) | LTS | GCE VM | Done |
| Ingress | [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/) | 4.x | `nginx-ingress-ns` | Done |
| Metrics | [Prometheus](https://prometheus.io/) + [Grafana](https://grafana.com/) | latest | `monitoring-ns` | Done |
| Logging | [ELK Stack](https://www.elastic.co/elastic-stack) (Elasticsearch + Logstash + Kibana) + Filebeat | 8.x | `logging-ns` | Done |
| Tracing | [Jaeger](https://www.jaegertracing.io/) | latest | `tracing-ns` | Done |

### 1.2 Architecture Reference

![Current MLOps 1 Architecture](images/architecture.png)

**Data Flow (MLOps 1)**:
```
Developer → Push code → GitHub → Trigger → Jenkins (GCE VM)
  → Build Docker image → Push to Docker Hub
  → Deploy via Helm → GKE cluster
  → NGINX Ingress → FastAPI service → YOLOv11 model → Response

End User → Request → NGINX Ingress → FastAPI → Inference → Response
  ├── Metrics → Prometheus → Grafana dashboard
  ├── Traces → Jaeger → Jaeger UI
  └── Logs → Filebeat → Logstash → Elasticsearch → Kibana
```

---

## 2. MLOps Level 2: Data Engineering Pipeline - WIP

**Branch**: `AddDataFlow`

### 2.1 New Kubernetes Namespaces

| Namespace | Purpose | Key Pods |
|-----------|---------|----------|
| `ingestion-ns` | Data ingestion & CDC | Kafka KRaft, Schema Registry, Debezium |
| `streaming-ns` | Stream processing | Flink (JobManager + TaskManager) |
| `processing-ns` | Batch processing | Spark (Master + Workers) |
| `storage-ns` | Data lake & warehouse | MinIO, PostgreSQL DW, Redis |
| `validation-ns` | Data quality | Great Expectations |
| `metadata-ns` | Metadata catalog & lineage | DataHub (GMS + Frontend + Actions) |
| `orchestration-ns` | Workflow scheduling | Airflow (Webserver + Scheduler + Workers) |

### 2.2 Tool Stack

#### 2.2.1 Message Queue & Event Streaming

| Tool | Link | Role | Docker Image | Port |
|------|------|------|-------------|------|
| **Apache Kafka (KRaft)** | [kafka.apache.org](https://kafka.apache.org/) | Event streaming platform (no Zookeeper) | `bitnami/kafka:3.7` | 9092, 9093 |
| **Confluent Schema Registry** | [docs.confluent.io](https://docs.confluent.io/platform/current/schema-registry/) | Schema validation (Avro/Protobuf) | `confluentinc/cp-schema-registry:7.6` | 8081 |
| **Debezium** | [debezium.io](https://debezium.io/) | CDC (Change Data Capture) from PostgreSQL | `debezium/connect:2.5` | 8083 |

**Kafka Topics Design**:
```
face-detection.raw-images        -- Raw image events from camera/API
face-detection.validated-images   -- After Flink validation
face-detection.inference-results  -- KServe/Triton output
face-detection.cdc.postgres.*     -- CDC events from application DB
face-detection.alerts             -- Data quality alerts
face-detection.drift-events       -- Drift detection alerts
```

> **[ADR FIX] Claim-Check Pattern**: Raw images are NOT sent through Kafka directly (images can be 100KB-5MB, Kafka default max is 1MB). Instead:
> 1. Producer uploads image to MinIO → gets `s3://face-detection/raw/camera-feed/{uuid}.jpg`
> 2. Producer sends **metadata event** to Kafka containing `{image_path, timestamp, camera_id, format, size_bytes}`
> 3. Consumer reads metadata → fetches image from MinIO when needed
>
> This keeps Kafka messages small (~500 bytes) and avoids `message.max.bytes` issues.

**Kafka Configuration (Required)**:
```yaml
# server.properties (via Helm values)
kafka:
  config:
    message.max.bytes: 1048576          # 1MB max message (metadata only)
    log.retention.hours: 168            # 7 days retention
    log.cleanup.policy: delete          # Delete old segments
    num.partitions: 6                   # Default partitions
    default.replication.factor: 3       # RF=3 for durability
    min.insync.replicas: 2             # At least 2 replicas in-sync
  storage:
    size: 50Gi                          # PVC for Kafka logs
    storageClass: standard-rwo
```

#### 2.2.2 Data Processing

| Tool | Link | Role | Docker Image | Port |
|------|------|------|-------------|------|
| **Apache Spark** | [spark.apache.org](https://spark.apache.org/) | Batch processing (Bronze→Silver→Gold) | `bitnami/spark:3.5` | 7077, 8080 |
| **Apache Flink** | [flink.apache.org](https://flink.apache.org/) | Stream processing & real-time validation | `flink:1.18` | 8081, 6123 |

#### 2.2.3 Data Storage

| Tool | Link | Role | Docker Image | Port |
|------|------|------|-------------|------|
| **MinIO** | [min.io](https://min.io/) | S3-compatible data lake | `minio/minio:latest` | 9000, 9001 |
| **PostgreSQL** | [postgresql.org](https://www.postgresql.org/) | Data Warehouse (Gold tables) | `postgres:16` | 5432 |
| **Redis** | [redis.io](https://redis.io/) | Cache for real-time features | `redis:7-alpine` | 6379 |

**MinIO Bucket Structure**:
```
s3://face-detection/
├── raw/                    # Bronze layer - raw images + metadata
│   ├── wider-face/         # WIDER FACE dataset
│   ├── camera-feed/        # Real-time camera captures
│   └── uploaded/           # User-uploaded images via API
├── processed/              # Silver layer - validated + cleaned
│   ├── faces-cropped/      # Extracted face regions
│   ├── annotations/        # Standardized annotations (COCO format)
│   └── metadata/           # Enriched metadata (Parquet)
├── gold/                   # Gold layer - ML-ready features
│   ├── training/           # Training datasets (versioned by DVC)
│   ├── evaluation/         # Evaluation datasets
│   └── features/           # Pre-computed feature tables
├── models/                 # Model artifacts
│   ├── yolov11/            # YOLOv11 weights (.pt, .onnx, .engine)
│   ├── tensorrt/           # TensorRT optimized models (INT8)
│   └── registry/           # MLflow model registry snapshots
└── checkpoints/            # DVC checkpoints
```

#### 2.2.4 Data Quality & Versioning

| Tool | Link | Role | Docker Image | Port |
|------|------|------|-------------|------|
| **Great Expectations** | [greatexpectations.io](https://greatexpectations.io/) | Data quality validation (expectations suites) | `greatexpectations/great_expectations:latest` | - |
| **DVC** | [dvc.org](https://dvc.org/) | Data versioning (backed by MinIO) | CLI tool in Spark/Airflow | - |

#### 2.2.5 Metadata & Orchestration

| Tool | Link | Role | Docker Image | Port |
|------|------|------|-------------|------|
| **DataHub** | [datahubproject.io](https://datahubproject.io/) | Metadata catalog + data lineage | `linkedin/datahub-gms:v0.13` | 8080 |
| **DataHub Frontend** | (same) | DataHub Web UI | `linkedin/datahub-frontend-react:v0.13` | 9002 |
| **DataHub Actions** | (same) | Event-driven metadata ingestion | `linkedin/datahub-actions:v0.1` | - |
| **Apache Airflow** | [airflow.apache.org](https://airflow.apache.org/) | Workflow orchestration (DAGs) | `apache/airflow:2.8` | 8080 |

### 2.3 Data Flows (3 paths)

#### Flow A: Batch Processing (WIDER FACE Dataset)

> **Refer to**: Diagram 1 - Data Engineering Pipeline (Batch Lane)

```
WIDER FACE Dataset (external)
  │
  ▼
[MinIO raw/wider-face/]           ← ingestion-ns: upload via Airflow DAG
  │
  ▼
[Spark Bronze Job]                ← processing-ns: parse, extract metadata
  │                                  Output: Parquet files with raw annotations
  ▼
[Great Expectations Check #1]     ← validation-ns: null checks, schema validation
  │                                  ✗ fail → alert to ELK + Kafka alerts topic
  ▼
[Spark Silver Job]                ← processing-ns: normalize bbox, augment, clean
  │                                  Output: standardized COCO format
  ▼
[Great Expectations Check #2]     ← validation-ns: distribution checks, range validation
  │
  ▼
[Spark Gold Job]                  ← processing-ns: feature engineering
  │                                  Output: training-ready features
  ├──▶ [PostgreSQL DW]           ← storage-ns: fact_detections + dim_images + dim_models
  ├──▶ [MinIO gold/training/]    ← storage-ns: versioned by DVC
  └──▶ [DataHub]                 ← metadata-ns: lineage registered automatically
```

**Data Types Flowing**: `images (JPEG/PNG)` → `Parquet` → `Parquet (cleaned)` → `Parquet (features)` + `SQL tables`

#### Flow B: Stream Processing (Real-time Camera/API)

> **Refer to**: Diagram 1 - Data Engineering Pipeline (Stream Lane)

```
Camera Feed / API Upload
  │
  ▼
[Kafka KRaft]                     ← ingestion-ns: topic face-detection.raw-images
  │                                  Format: Avro (validated by Schema Registry)
  ▼
[Flink Validation Job]            ← streaming-ns: real-time quality check
  │
  ├── VALID ──▶ [Kafka validated topic]
  │               │
  │               ├──▶ [Spark Streaming micro-batch]  ← processing-ns
  │               │       │
  │               │       ├──▶ [Redis]               ← storage-ns: cache latest features
  │               │       └──▶ [PostgreSQL DW]       ← storage-ns: append to fact tables
  │               │
  │               └──▶ [KServe + Triton]             ← serving-ns: real-time inference
  │                       │
  │                       └──▶ [Kafka inference-results topic]
  │
  └── INVALID ──▶ [Kafka alerts topic]
                    │
                    └──▶ [ELK Stack alert]           ← logging-ns: notify Data Engineer
```

**Data Types Flowing**: `raw image bytes` → `Avro events` → `validated events` → `features + inference results` → `JSON response`

#### Flow C: CDC (Change Data Capture)

> **Refer to**: Diagram 1 - Data Engineering Pipeline (CDC Lane)

```
Application PostgreSQL (face_detection DB)
  │
  ▼
[Debezium Connector]              ← ingestion-ns: WAL-based CDC
  │                                  Captures: INSERT/UPDATE/DELETE on detection results
  ▼
[Kafka CDC topics]                ← ingestion-ns: face-detection.cdc.postgres.*
  │
  ▼
[Spark Batch Merge Job]           ← processing-ns: daily merge into DW
  │
  └──▶ [PostgreSQL DW]           ← storage-ns: upsert to dimension tables
```

**Data Types Flowing**: `WAL events (JSON)` → `Kafka CDC events` → `SQL merge operations`

### 2.4 Gold Schema Design (Coursework Section 02)

#### Fact Table: `fact_detections`
```sql
CREATE TABLE gold.fact_detections (
    detection_id    BIGSERIAL PRIMARY KEY,
    image_id        BIGINT REFERENCES dim_images(image_id),
    model_id        INT REFERENCES dim_models(model_id),
    time_id         INT REFERENCES dim_time(time_id),        -- [ADR FIX] Added FK to dim_time
    timestamp       TIMESTAMP NOT NULL,
    bbox_x          FLOAT,
    bbox_y          FLOAT,
    bbox_w          FLOAT,
    bbox_h          FLOAT,
    confidence      FLOAT,
    face_count      INT,
    inference_ms    FLOAT,
    source_type     VARCHAR(20),  -- 'batch', 'stream', 'api'
    is_valid        BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (timestamp);  -- [ADR FIX] Partition by date for query performance

-- Create monthly partitions
CREATE TABLE gold.fact_detections_2026_01 PARTITION OF gold.fact_detections
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE gold.fact_detections_2026_02 PARTITION OF gold.fact_detections
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
-- ... create partitions as needed
```

#### Dimension Tables
```sql
-- dim_images: metadata about each processed image
CREATE TABLE gold.dim_images (
    image_id            BIGSERIAL PRIMARY KEY,
    file_path           TEXT NOT NULL,
    file_size_bytes     BIGINT,
    width               INT,
    height              INT,
    format              VARCHAR(10),
    source              VARCHAR(50),   -- 'wider_face', 'camera', 'api_upload'
    camera_id           VARCHAR(100),  -- [ADR FIX] For multi-camera scenarios
    processing_status   VARCHAR(20),   -- [ADR FIX] 'raw', 'bronze', 'silver', 'gold'
    upload_time         TIMESTAMP,
    dvc_version         VARCHAR(40),
    CONSTRAINT uq_file_path UNIQUE (file_path)  -- [ADR FIX] Enforce uniqueness
);

-- dim_models: model registry metadata
CREATE TABLE gold.dim_models (
    model_id                SERIAL PRIMARY KEY,
    model_name              VARCHAR(100),
    model_version           VARCHAR(50),
    framework               VARCHAR(50),  -- 'pytorch', 'onnx', 'tensorrt'
    quantization            VARCHAR(20),  -- 'fp32', 'fp16', 'int8'
    map_score               FLOAT,
    training_dataset_version VARCHAR(40), -- [ADR FIX] Link to DVC version
    deploy_date             TIMESTAMP,    -- [ADR FIX] When deployed to production
    is_active               BOOLEAN DEFAULT FALSE,  -- [ADR FIX] Currently serving?
    registered_at           TIMESTAMP
);

-- dim_time: time dimension for analytics
CREATE TABLE gold.dim_time (
    time_id         SERIAL PRIMARY KEY,
    full_timestamp  TIMESTAMP,
    date            DATE,
    hour            INT,
    day_of_week     INT,
    week_of_year    INT,
    month           INT,
    quarter         INT,
    year            INT
);
```

#### Feature Tables (for ML training)
```sql
-- feature_image_stats: pre-computed features per image
CREATE TABLE gold.feature_image_stats (
    image_id            BIGINT PRIMARY KEY REFERENCES dim_images(image_id),
    avg_brightness      FLOAT,
    contrast_ratio      FLOAT,
    blur_score          FLOAT,
    face_density        FLOAT,    -- faces_per_megapixel
    avg_face_size_ratio FLOAT,    -- avg_face_area / image_area
    has_occlusion       BOOLEAN,
    edge_density        FLOAT,    -- [ADR FIX] edge detection density
    color_histogram_entropy FLOAT, -- [ADR FIX] color distribution entropy
    aspect_ratio        FLOAT,    -- [ADR FIX] image width/height ratio
    quality_score       FLOAT     -- composite quality metric
);
```

#### SLA Definitions
```yaml
gold_table_slas:
  fact_detections:
    freshness: "< 1 hour for stream, < 24h for batch"
    completeness: "> 99.5% non-null for required columns"
    accuracy: "confidence > 0.0 AND confidence <= 1.0"
  dim_images:
    freshness: "< 24 hours"
    uniqueness: "file_path must be unique"
  feature_image_stats:
    freshness: "< 24 hours after new images ingested"
    validity: "all scores between 0.0 and 1.0"
```

---

## 3. MLOps Level 3: Advanced ML Platform - PLANNED

### 3.1 New Kubernetes Namespaces

| Namespace | Purpose | Key Pods |
|-----------|---------|----------|
| `ml-pipeline-ns` | ML training pipelines & AutoML | Kubeflow Pipelines, Katib, MLflow, Kubeflow Notebooks |
| `serving-ns` | Model serving & inference | KServe, Triton Inference Server, RayServe |
| `auth-ns` | Authentication & authorization | Keycloak, OAuth2 Proxy |
| `istio-system` | Service mesh | Istiod, Istio Ingress Gateway (Envoy) |

### 3.2 ML Training Pipeline

| Tool | Link | Role | Docker Image | Port |
|------|------|------|-------------|------|
| **Kubeflow Pipelines** | [kubeflow.org/docs/components/pipelines/](https://www.kubeflow.org/docs/components/pipelines/) | ML workflow orchestration (training DAGs) | `gcr.io/ml-pipeline/frontend:2.0` | 8888 |
| **Kubeflow Notebooks** | [kubeflow.org](https://www.kubeflow.org/) | Interactive notebook server for DS | `kubeflownotebookswg/jupyter:latest` | 8888 |
| **Katib** | [kubeflow.org/docs/components/katib/](https://www.kubeflow.org/docs/components/katib/) | AutoML hyperparameter tuning | `docker.io/kubeflowkatib/katib-controller` | 8443 |
| **Ray Tune** | [docs.ray.io/en/latest/tune/](https://docs.ray.io/en/latest/tune/) | Distributed hyperparameter search (via Katib) | `rayproject/ray:2.9` | 6379, 8265 |
| **MLflow** | [mlflow.org](https://mlflow.org/) | Experiment tracking & model registry | `ghcr.io/mlflow/mlflow:2.11` | 5000 |

**Training Flow**:
```
PostgreSQL DW (Gold tables) + MinIO (Gold features)
  │
  ▼
[Kubeflow Notebook]               ← ml-pipeline-ns: Data Scientist explores data
  │
  ▼
[Kubeflow Pipeline]               ← ml-pipeline-ns: automated training workflow
  │
  ├── Step 1: Data Loading         → Read from Gold layer
  ├── Step 2: Preprocessing        → Feature engineering
  ├── Step 3: Training             → YOLOv11 training (+ Katib/RayTune for HPO)
  ├── Step 4: Evaluation           → mAP, precision, recall metrics
  ├── Step 5: Model Registration   → MLflow model registry
  └── Step 6: Model Export         → ONNX → TensorRT INT8 optimization
  │
  ▼
[MLflow Registry]                 ← ml-pipeline-ns: version control, stage transitions
  │                                  Stages: None → Staging → Production → Archived
  ▼
[MinIO models/]                   ← storage-ns: model artifact storage
```

### 3.3 Model Serving (KServe + Triton Combined)

> **Key insight**: KServe = Kubernetes orchestration layer (autoscaling, canary, traffic routing). Triton = inference engine (dynamic batching, TensorRT, multi-model serving). **Best practice: Use KServe with Triton as runtime backend.**

| Tool | Link | Role | Docker Image | Port |
|------|------|------|-------------|------|
| **KServe** | [kserve.github.io](https://kserve.github.io/website/) | K8s-native model serving (InferenceService CRD) | `kserve/kserve-controller:v0.12` | 8080 |
| **NVIDIA Triton** | [developer.nvidia.com/triton-inference-server](https://developer.nvidia.com/triton-inference-server) | High-performance inference runtime | `nvcr.io/nvidia/tritonserver:24.01-py3` | 8000, 8001, 8002 |
| **RayServe** | [docs.ray.io/en/latest/serve/](https://docs.ray.io/en/latest/serve/) | Parallel inference & ensemble serving | `rayproject/ray:2.9` | 8000 |
| **TensorRT** | [developer.nvidia.com/tensorrt](https://developer.nvidia.com/tensorrt) | Model optimization (FP16/INT8 quantization) | included in Triton image | - |
| **KEDA** | [keda.sh](https://keda.sh/) | Event-driven autoscaling (Kafka consumer lag → scale pods) | `ghcr.io/kedacore/keda:2.13` | - |

**KServe + Triton InferenceService**:
```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: face-detection
  namespace: serving-ns
spec:
  predictor:
    triton:
      storageUri: s3://face-detection/models/tensorrt/yolov11-int8
      runtimeVersion: "24.01-py3"
      resources:
        limits:
          nvidia.com/gpu: 1
          memory: 4Gi
        requests:
          cpu: 2
          memory: 2Gi
  # Canary deployment
  canaryTrafficPercent: 10
```

**Serving Flow**:
```
End User → API Request
  │
  ▼
[Istio Ingress Gateway (Envoy)]  ← istio-system: TLS termination, rate limiting
  │
  ├── 90% traffic ──▶ [KServe v1 (Production)]
  │                     │
  │                     └──▶ [Triton: YOLOv11-TensorRT-INT8]  ← serving-ns
  │
  └── 10% traffic ──▶ [KServe v2 (Canary)]
                        │
                        └──▶ [Triton: YOLOv11-v2-TensorRT-INT8]  ← serving-ns
  │
  ▼
[RayServe]                        ← serving-ns: parallel pre/post-processing
  │
  ▼
[Response] → [Kafka inference-results topic] → [PostgreSQL DW]
```

### 3.4 Performance Testing & Drift Detection

| Tool | Link | Role | Docker Image | Port |
|------|------|------|-------------|------|
| **k6** | [k6.io](https://k6.io/) | Load testing (HTTP + gRPC) | `grafana/k6:latest` | - |
| **k6-operator** | [github.com/grafana/k6-operator](https://github.com/grafana/k6-operator) | Distributed k6 on K8s | `ghcr.io/grafana/k6-operator:latest` | - |
| **Evidently AI** | [evidentlyai.com](https://www.evidentlyai.com/) | ML monitoring & data/model drift detection | `evidentlyai/evidently-service:latest` | 8080 |
| **Iter8** | [iter8.tools](https://iter8.tools/) | A/B testing & progressive delivery | `iter8/iter8:latest` | - |

**Drift Detection Flow** (Coursework Section 03):
```
[Kafka inference-results topic]
  │
  ▼
[Evidently AI Service]            ← monitoring-ns
  │
  ├── Feature Drift Check          → PSI, KS-test on input features
  │     (image brightness, resolution, face count distribution)
  │
  ├── Prediction Drift Check       → confidence distribution shift
  │
  ├── Data Quality Check           → missing values, outliers
  │
  └── Output ──▶ [Prometheus metrics] → [Grafana drift dashboard]
        │
        ├── If drift detected ──▶ [Airflow trigger retrain DAG]
        └── Alert ──▶ [ELK Stack / Kafka alerts topic]
```

**Drift Scenarios to Implement**:
1. **Image quality shift**: Simulate degraded camera (lower resolution, blur, darkness)
2. **Face distribution shift**: Change face count distribution (crowd scenes vs. single faces)
3. **Confidence decay**: Model accuracy degradation over time
4. **Feature schema change**: New fields added to input schema

### 3.5 A/B Testing with Iter8

```
[Iter8 Experiment]
  │
  ├── Baseline: KServe v1 (90% traffic)
  │     Metrics: latency_p95, error_rate, mean_confidence
  │
  ├── Candidate: KServe v2 (10% traffic)
  │     Metrics: same as baseline
  │
  └── Decision (automatic):
        ├── Candidate wins → promote to 100%
        ├── Candidate loses → rollback to baseline
        └── Inconclusive → continue experiment
```

---

## 4. RAG/LLM Pipeline (AI Track 4B) - PLANNED

### 4.1 Namespace: `rag-ns`

| Tool | Link | Role | Docker Image | Port |
|------|------|------|-------------|------|
| **Ollama** | [ollama.ai](https://ollama.ai/) | Local LLM runtime on K8s (CPU-friendly) | `ollama/ollama:latest` | 11434 |
| **RAGFlow** | [github.com/infiniflow/ragflow](https://github.com/infiniflow/ragflow) | RAG engine (chunking, retrieval, generation) | `infiniflow/ragflow:latest` | 9380 |
| **Weaviate** | [weaviate.io](https://weaviate.io/) | Vector database for embeddings | `semitechnologies/weaviate:1.24` | 8080 |
| **Typesense** | [typesense.org](https://typesense.org/) | Fast metadata search (hybrid search) | `typesense/typesense:0.25` | 8108 |
| **Langfuse** | [langfuse.com](https://langfuse.com/) | LLM observability (traces, cost, quality) | `langfuse/langfuse:2` | 3000 |

**Helm Chart for Ollama on K8s**:
```yaml
# Using otwld/ollama-helm
helm repo add ollama-helm https://otwld.github.io/ollama-helm/
helm install ollama ollama-helm/ollama \
  --namespace rag-ns \
  --set ollama.models[0]=tinyllama:1.1b \
  --set resources.requests.memory=2Gi \
  --set resources.requests.cpu=2 \
  --set resources.limits.memory=4Gi
```

**LLM Model Options** (resource-constrained, no GPU):
| Model | Size | RAM Required | Speed (CPU) | Quality |
|-------|------|-------------|-------------|---------|
| TinyLlama 1.1B | 637MB | ~2GB | ~5 tok/s | Basic |
| Qwen2.5-0.5B | 395MB | ~1.5GB | ~8 tok/s | Good for size |
| Phi-3-mini-4k (if GPU available) | 2.3GB | ~4GB | ~15 tok/s | Excellent |

### 4.2 RAG Pipeline Flow

> **Refer to**: Diagram 3 - RAG/LLM + Monitoring + Security

```
[User Question via Chat UI]       ← e.g., "How many faces were detected today?"
  │
  ▼
[RAGFlow Engine]                  ← rag-ns: query understanding + rewriting
  │
  ├── Step 1: Query Embedding     → sentence-transformers (all-MiniLM-L6-v2)
  │
  ├── Step 2: Vector Search       → [Weaviate] semantic similarity search
  │     (searches: model docs, detection reports, system logs)
  │
  ├── Step 3: Metadata Search     → [Typesense] keyword + faceted search
  │     (searches: detection metadata, model versions, dates)
  │
  ├── Step 4: Context Assembly    → Merge vector + keyword results, rank, deduplicate
  │
  └── Step 5: LLM Generation     → [Ollama / TinyLlama 1.1B]
        │                           Prompt: system context + retrieved docs + user query
        │
        ▼
      [Langfuse]                  ← rag-ns: trace logging (latency, tokens, cost)
        │
        ▼
      [Guardrails Check]         ← rag-ns: content safety, hallucination check
        │
        ▼
      [Response to User]
```

### 4.3 Documents Indexed in RAG

```
Weaviate Collections:
├── detection_reports     # Daily/weekly detection summaries
├── model_documentation   # YOLOv11 architecture, training configs
├── system_runbooks       # Operational procedures, troubleshooting
├── api_documentation     # FastAPI endpoint docs
└── monitoring_alerts     # Historical alert summaries

Typesense Collections:
├── detections_metadata   # Structured: image_id, timestamp, face_count, confidence
├── model_versions        # Structured: version, mAP, deploy_date, status
└── incidents             # Structured: incident_id, severity, resolution
```

---

## 5. SSO & Security Architecture - PLANNED

### 5.1 Namespace: `auth-ns` + `istio-system`

| Tool | Link | Role | Docker Image | Port |
|------|------|------|-------------|------|
| **Keycloak** | [keycloak.org](https://www.keycloak.org/) | Identity Provider (OIDC/SAML) | `quay.io/keycloak/keycloak:24` | 8080 |
| **OAuth2 Proxy** | [oauth2-proxy.github.io](https://oauth2-proxy.github.io/oauth2-proxy/) | Auth proxy for tools without native OIDC | `quay.io/oauth2-proxy/oauth2-proxy:7.6` | 4180 |
| **Istio** | [istio.io](https://istio.io/) | Service mesh (mTLS, traffic management) | `istio/pilot:1.21` | 15010, 15014 |

### 5.2 SSO Login Flow (12 Steps)

```
1. User → browser → https://grafana.face-detect.dev
2. Istio Ingress Gateway (Envoy) receives request
3. EnvoyFilter checks for auth cookie → NOT FOUND
4. Redirect to OAuth2 Proxy (/oauth2/start)
5. OAuth2 Proxy redirects to Keycloak login page
6. User enters credentials (or SSO via Google/GitHub)
7. Keycloak authenticates → issues authorization code
8. OAuth2 Proxy exchanges code for JWT token
9. OAuth2 Proxy sets cookie on *.face-detect.dev domain
10. Redirect back to original URL (grafana.face-detect.dev)
11. EnvoyFilter validates JWT token → PASS
12. Request forwarded to Grafana pod (user is logged in)

Same cookie works for ALL tools under *.face-detect.dev:
  - grafana.face-detect.dev      (Grafana)
  - kibana.face-detect.dev       (Kibana)
  - jaeger.face-detect.dev       (Jaeger)
  - airflow.face-detect.dev      (Airflow)
  - datahub.face-detect.dev      (DataHub)
  - mlflow.face-detect.dev       (MLflow)
  - kubeflow.face-detect.dev     (Kubeflow)
  - langfuse.face-detect.dev     (Langfuse)
  - minio.face-detect.dev        (MinIO Console)
  - api.face-detect.dev          (FastAPI / Swagger)
```

### 5.3 Keycloak RBAC Configuration

| Role | Realm Role | Access |
|------|-----------|--------|
| **End User** | `user` | FastAPI inference API only |
| **Data Scientist** | `data-scientist` | Kubeflow Notebooks, MLflow, Grafana (ML dashboards), MinIO (models/) |
| **Data Analyst** | `data-analyst` | DataHub, Grafana (data dashboards), PostgreSQL DW (read-only), MinIO (gold/) |
| **Data Engineer** | `data-engineer` | Airflow, Flink UI, Spark UI, Kafka UI, DataHub, Great Expectations, MinIO (all) |
| **ML Engineer** | `ml-engineer` | KServe, Triton, RayServe, k6, Evidently, Iter8, MLflow, Kubeflow |
| **DevOps/Admin** | `admin` | Full access: Keycloak admin, Grafana admin, Kibana admin, all namespaces |

### 5.4 Envoy Load Balancing Configuration

Envoy (via Istio) handles load balancing at 3 layers:

| Layer | Scope | Algorithm | Config CRD |
|-------|-------|-----------|------------|
| **Ingress Gateway** | External → cluster | ROUND_ROBIN (default) | `Gateway` + `VirtualService` |
| **Sidecar Proxy** | Pod → Pod (east-west) | Per-service configured | `DestinationRule` |
| **Per-Service** | Specific tuning | Varies by service | `DestinationRule` |

**Service-specific Load Balancing**:
```yaml
# FastAPI: Round Robin (stateless, equal distribution)
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: fastapi-lb
spec:
  host: fastapi-service.model-serving-ns.svc.cluster.local
  trafficPolicy:
    loadBalancer:
      simple: ROUND_ROBIN
    connectionPool:
      http:
        h2UpgradePolicy: UPGRADE
    outlierDetection:
      consecutiveErrors: 3
      interval: 30s
      baseEjectionTime: 60s

---
# KServe/Triton: Least Request (route to least loaded GPU)
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: kserve-triton-lb
spec:
  host: face-detection-predictor.serving-ns.svc.cluster.local
  trafficPolicy:
    loadBalancer:
      simple: LEAST_REQUEST
    connectionPool:
      http:
        maxRequestsPerConnection: 100
    outlierDetection:
      consecutiveGatewayErrors: 2
      interval: 10s

---
# Ollama: Consistent Hash (session affinity for model loading)
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: ollama-lb
spec:
  host: ollama.rag-ns.svc.cluster.local
  trafficPolicy:
    loadBalancer:
      consistentHash:
        httpHeaderName: x-session-id
```

### 5.5 Network Policies & mTLS

```yaml
# Istio PeerAuthentication: enforce mTLS cluster-wide
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system
spec:
  mtls:
    mode: STRICT

# JWT validation for all requests
apiVersion: security.istio.io/v1
kind: RequestAuthentication
metadata:
  name: keycloak-jwt
  namespace: istio-system
spec:
  jwtRules:
  - issuer: "https://keycloak.face-detect.dev/realms/face-detection"
    jwksUri: "https://keycloak.face-detect.dev/realms/face-detection/protocol/openid-connect/certs"
    forwardOriginalToken: true
```

---

## 6. Data Generator Design (Coursework Section 01)

> **Required**: Custom data generator that simulates real-world data challenges

### 6.1 Generator Components

```python
# data_generator/
├── generator.py              # Main generator class
├── configs/
│   ├── base_config.yaml      # Default generation parameters
│   ├── drift_config.yaml     # Drift simulation parameters
│   └── chaos_config.yaml     # Data quality chaos scenarios
├── sources/
│   ├── image_source.py       # Image generation/augmentation
│   ├── metadata_source.py    # Metadata generation
│   └── stream_source.py      # Kafka event generation
└── challenges/
    ├── offline_challenges.py  # Batch data issues
    ├── streaming_challenges.py # Stream data issues
    └── optional_challenges.py  # Additional chaos
```

### 6.2 Configurable Data Challenges

#### Offline (Batch) Challenges
| Challenge | Description | Implementation |
|-----------|-------------|----------------|
| **Data Skew** | Imbalanced face count distribution (90% single-face, 10% multi-face) | Weighted sampling in image_source |
| **High Cardinality** | Unique metadata fields exploding dimensions | Generate 100K+ unique camera_ids |
| **Schema Evolution** | Fields added/removed between batches | v1 schema → v2 schema with new columns |

#### Streaming Challenges
| Challenge | Description | Implementation |
|-----------|-------------|----------------|
| **Bursty Traffic** | 10x spike in events for 5 minutes | k6-style load pattern via stream_source |
| **Late Arrivals** | Events with timestamps 5-30 minutes behind | Random delay injection in Kafka producer |

#### Optional Challenges
| Challenge | Description | Implementation |
|-----------|-------------|----------------|
| **Duplicate Records** | 5-15% duplicate events | Replay same event with identical key |
| **Missing Values** | Null confidence, missing bbox | Random null injection per field |
| **Out-of-Order Events** | Events arriving with shuffled sequence numbers | Shuffle event buffer before flush |

### 6.3 Generator CLI

```bash
# Generate batch data with offline challenges
python generator.py batch \
  --num-images 10000 \
  --skew-ratio 0.9 \
  --schema-version v2 \
  --output s3://face-detection/raw/generated/

# Generate streaming events with chaos
python generator.py stream \
  --kafka-broker kafka.ingestion-ns:9092 \
  --rate 100/s \
  --burst-interval 300s \
  --burst-multiplier 10 \
  --late-arrival-pct 0.05 \
  --duplicate-pct 0.1 \
  --duration 3600s
```

---

## 7. deployKF Analysis

### 7.1 What deployKF Covers

[deployKF](https://www.deploykf.org/) is a deployment tool that bundles multiple MLOps tools with ArgoCD-based GitOps.

**Covered (~40% of our stack)**:
| Tool | deployKF Component | Our Equivalent |
|------|-------------------|----------------|
| Kubeflow Pipelines | Built-in | ml-pipeline-ns |
| Kubeflow Notebooks | Built-in | ml-pipeline-ns |
| KServe | Built-in | serving-ns |
| MLflow (via plugin) | Optional | ml-pipeline-ns |
| Istio | Built-in | istio-system |
| Dex (OIDC) | Built-in | Replace with Keycloak |
| MinIO | Built-in | storage-ns |
| ArgoCD | Deployer | New addition |
| cert-manager | Built-in | istio-system |
| Kyverno | Built-in | Policy enforcement |

**NOT Covered (must deploy manually)**:
- Kafka, Schema Registry, Debezium (ingestion-ns)
- Spark, Flink (processing-ns)
- Great Expectations (validation-ns)
- DataHub (metadata-ns)
- Airflow (orchestration-ns)
- Triton, RayServe, KEDA (serving-ns)
- Ollama, RAGFlow, Weaviate, Typesense, Langfuse (rag-ns)
- ELK Stack, Jaeger (monitoring-ns)
- Prometheus, Grafana (monitoring-ns)
- k6, Evidently AI, Iter8 (testing)
- Keycloak (auth-ns) — deployKF uses Dex instead

### 7.2 Recommendation

Use deployKF for the Kubeflow ecosystem (Pipelines, Notebooks, KServe, Istio, MinIO) as a **foundation**, then layer additional tools on top via Helm charts. Replace Dex with Keycloak for more powerful RBAC.

---

## 8. Complete Namespace Map

```
GKE Cluster: face-detection-cluster
│
├── istio-system              ← Istiod, Istio Ingress Gateway, cert-manager
├── auth-ns                   ← Keycloak, OAuth2 Proxy
├── nginx-ingress-ns          ← NGINX Ingress Controller (MLOps 1 legacy, migrate to Istio)
│
├── model-serving-ns          ← FastAPI + YOLOv11 (MLOps 1)
├── serving-ns                ← KServe + Triton + RayServe + KEDA (MLOps 3)
│
├── ingestion-ns              ← Kafka KRaft, Schema Registry, Debezium
├── streaming-ns              ← Flink (JobManager + TaskManager)
├── processing-ns             ← Spark (Master + Workers)
├── storage-ns                ← MinIO, PostgreSQL DW, Redis
├── validation-ns             ← Great Expectations
├── metadata-ns               ← DataHub (GMS + Frontend + Actions)
├── orchestration-ns          ← Airflow (Webserver + Scheduler + Workers + PostgreSQL + Redis)
│
├── ml-pipeline-ns            ← Kubeflow Pipelines, Kubeflow Notebooks, Katib, MLflow
│
├── rag-ns                    ← Ollama, RAGFlow, Weaviate, Typesense, Langfuse
│
├── monitoring-ns             ← Prometheus, Grafana, Evidently AI, k6-operator
├── logging-ns                ← Elasticsearch, Logstash, Kibana, Filebeat
└── tracing-ns                ← Jaeger
```

**Total**: ~16 namespaces, ~50+ pods, ~35+ distinct tools

---

## 9. User Role → Dashboard Access Map

| Dashboard | URL | Roles | Purpose |
|-----------|-----|-------|---------|
| FastAPI Swagger | `api.face-detect.dev/docs` | End User, ML Engineer | API testing, inference |
| Grafana (System) | `grafana.face-detect.dev` | DevOps, Admin | CPU/Memory/Network metrics |
| Grafana (ML) | `grafana.face-detect.dev/d/ml` | Data Scientist, ML Engineer | Model performance, drift |
| Grafana (Data) | `grafana.face-detect.dev/d/data` | Data Analyst, Data Engineer | Pipeline throughput, quality |
| Kibana | `kibana.face-detect.dev` | DevOps, Data Engineer | Log analysis, alerts |
| Jaeger | `jaeger.face-detect.dev` | DevOps, ML Engineer | Distributed tracing |
| Airflow | `airflow.face-detect.dev` | Data Engineer | DAG management, scheduling |
| DataHub | `datahub.face-detect.dev` | Data Analyst, Data Engineer | Metadata catalog, lineage |
| MLflow | `mlflow.face-detect.dev` | Data Scientist | Experiment tracking, model registry |
| Kubeflow | `kubeflow.face-detect.dev` | Data Scientist, ML Engineer | Pipelines, Notebooks, Katib |
| MinIO Console | `minio.face-detect.dev` | Data Engineer, Admin | Object storage management |
| Spark UI | `spark.face-detect.dev` | Data Engineer | Job monitoring |
| Flink UI | `flink.face-detect.dev` | Data Engineer | Stream job monitoring |
| Langfuse | `langfuse.face-detect.dev` | ML Engineer | LLM observability |
| Evidently | `evidently.face-detect.dev` | Data Scientist, ML Engineer | Drift reports |
| Keycloak Admin | `keycloak.face-detect.dev` | Admin | User/role management |

---

## 10. Architecture Diagrams Reference

### Diagram 1: Data Engineering Pipeline (Batch + Stream + CDC)

> **File**: `images/data_engineering_pipeline.html`
> **Scope**: ingestion-ns, streaming-ns, processing-ns, storage-ns, validation-ns, metadata-ns, orchestration-ns
> **User roles**: Data Engineer (primary), Data Analyst (read)
> **Key flows**:
> - BATCH: WIDER FACE → MinIO raw → Spark (Bronze→Silver→Gold) → GE checks → PostgreSQL DW + DVC
> - STREAM: Camera → Kafka → Flink validate → Spark Streaming → Redis + PostgreSQL → KServe/Triton
> - CDC: App PostgreSQL → Debezium → Kafka CDC → Spark merge → DW

### Diagram 2: ML Training + Model Serving

> **File**: `images/ml_training_serving.html`
> **Scope**: ml-pipeline-ns, serving-ns, monitoring-ns
> **User roles**: Data Scientist (training), ML Engineer (serving), End User (inference)
> **Key flows**:
> - TRAINING: Gold data → Kubeflow Notebook → Pipeline + Katib/Ray → MLflow → Model Registry
> - SERVING: User → Istio → KServe (90/10 canary) → Triton TensorRT → RayServe → Response
> - TESTING: k6 load test → Prometheus → Grafana + Iter8 A/B + Evidently drift → retrain trigger

### Diagram 3: RAG/LLM + Monitoring + Security

> **File**: `images/rag_monitoring_security.html`
> **Scope**: rag-ns, auth-ns, istio-system, monitoring-ns, logging-ns, tracing-ns
> **User roles**: All roles (SSO), End User (RAG chat), DevOps (monitoring)
> **Key flows**:
> - RAG: User question → RAGFlow → Weaviate (vector) + Typesense (keyword) → Ollama → Langfuse → Response
> - SSO: User → Istio Gateway → EnvoyFilter → OAuth2 Proxy → Keycloak → JWT → all tools
> - MONITORING: All pods → Prometheus/ELK/Jaeger → Grafana/Kibana/Jaeger UI

### Diagram 4: Full System Overview (All Namespaces)

> **File**: `images/full_system_overview.html`
> **Scope**: All 16 namespaces
> **Shows**: High-level namespace grouping with inter-namespace data flows, user entry points, tool counts per namespace

---

## 11. Implementation Phases (Reference Only)

### Phase 1: Data Engineering Foundation (MLOps 2)
- Deploy Kafka KRaft + Schema Registry
- Deploy MinIO + PostgreSQL DW
- Deploy Spark + Flink
- Deploy Great Expectations
- Deploy Airflow + DataHub
- Implement Data Generator
- Build Batch + Stream + CDC pipelines
- Design Gold schema with SLAs

### Phase 2: Advanced ML Platform (MLOps 3)
- Deploy Kubeflow (Pipelines + Notebooks + Katib)
- Deploy MLflow
- Deploy KServe + Triton (combined)
- Deploy RayServe + KEDA
- Configure TensorRT INT8 optimization
- Deploy k6 + k6-operator
- Deploy Evidently AI + Iter8
- Build automated retrain pipeline

### Phase 3: RAG/LLM + Security + Polish
- Deploy Ollama + TinyLlama on K8s
- Deploy RAGFlow + Weaviate + Typesense
- Deploy Langfuse
- Deploy Keycloak + OAuth2 Proxy
- Configure Istio service mesh (mTLS, EnvoyFilter)
- Configure SSO for all tools
- Implement RBAC
- Final integration testing

---

## 12. Infrastructure & Resource Planning [ADR FIX — NEW SECTION]

### 12.1 GKE Node Pool Design

> **Current state**: 1x `e2-medium` (2 vCPU, 4GB RAM) — INSUFFICIENT for 50+ pods.

```hcl
# Recommended: 3 node pools for workload isolation

# Pool 1: General workloads (data pipelines, orchestration, auth)
resource "google_container_node_pool" "general" {
  name       = "general-pool"
  cluster    = google_container_cluster.gke_face.name
  location   = var.region
  node_count = 3
  node_config {
    machine_type = "e2-standard-4"  # 4 vCPU, 16GB RAM each
    disk_type    = "pd-ssd"
    disk_size_gb = 100
    labels = { "pool" = "general" }
    taint  = []
  }
}

# Pool 2: ML workloads (training, serving) — GPU optional
resource "google_container_node_pool" "ml" {
  name       = "ml-pool"
  cluster    = google_container_cluster.gke_face.name
  location   = var.region
  node_count = 1
  node_config {
    machine_type = "n1-standard-4"  # 4 vCPU, 15GB RAM
    # Uncomment when GPU available:
    # guest_accelerator {
    #   type  = "nvidia-tesla-t4"
    #   count = 1
    # }
    disk_type    = "pd-ssd"
    disk_size_gb = 100
    labels = { "pool" = "ml" }
    taint {
      key    = "workload"
      value  = "ml"
      effect = "NO_SCHEDULE"
    }
  }
}

# Pool 3: Stateful services (Kafka, PostgreSQL, Elasticsearch, MinIO)
resource "google_container_node_pool" "stateful" {
  name       = "stateful-pool"
  cluster    = google_container_cluster.gke_face.name
  location   = var.region
  node_count = 2
  node_config {
    machine_type = "e2-standard-4"
    preemptible  = false  # IMPORTANT: stateful services must NOT be preemptible
    disk_type    = "pd-ssd"
    disk_size_gb = 200    # More disk for data storage
    labels = { "pool" = "stateful" }
  }
}
```

### 12.2 Resource Estimation per Namespace

| Namespace | Est. Pods | CPU (cores) | RAM (GB) | Disk (GB) | Node Pool |
|-----------|-----------|-------------|----------|-----------|-----------|
| istio-system | 3 | 2 | 4 | 10 | general |
| auth-ns | 3 | 1.5 | 4 | 10 | general |
| model-serving-ns | 1 | 0.5 | 1 | 5 | general |
| serving-ns | 5 | 4 | 10 | 20 | ml |
| ingestion-ns | 5 | 3 | 8 | 60 | stateful |
| streaming-ns | 3 | 2 | 6 | 20 | general |
| processing-ns | 4 | 4 | 12 | 30 | general |
| storage-ns | 4 | 2 | 8 | 200 | stateful |
| validation-ns | 2 | 1 | 2 | 5 | general |
| metadata-ns | 4 | 2 | 6 | 30 | stateful |
| orchestration-ns | 4 | 2 | 6 | 20 | general |
| ml-pipeline-ns | 5 | 3 | 8 | 30 | ml |
| rag-ns | 6 | 4 | 12 | 40 | general |
| monitoring-ns | 6 | 3 | 10 | 50 | stateful |
| logging-ns | 4 | 2 | 8 | 100 | stateful |
| tracing-ns | 1 | 0.5 | 2 | 10 | general |
| **TOTAL** | **~60** | **~36** | **~107** | **~640** | — |

### 12.3 Cost Estimation (GCP us-central1)

| Configuration | Nodes | Monthly Cost (est.) | Notes |
|--------------|-------|---------------------|-------|
| **Full (with GPU)** | 3x e2-standard-4 + 1x n1-standard-4+T4 + 2x e2-standard-4 | ~$933/month | Production-like |
| **Demo (no GPU)** | 2x e2-standard-8 | ~$390/month | Shared pools, preemptible |
| **Minimal demo** | 1x e2-standard-16 | ~$350/month | Single large node |
| **Current** | 1x e2-medium | ~$25/month | Cannot run extended system |

---

## 13. Persistent Storage (PVC) Specifications [ADR FIX — NEW SECTION]

### 13.1 PersistentVolumeClaims

```yaml
# storage-ns: MinIO — Data Lake
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: minio-data
  namespace: storage-ns
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: standard-rwo
  resources:
    requests:
      storage: 100Gi

---
# storage-ns: PostgreSQL DW
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgresql-dw-data
  namespace: storage-ns
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: standard-rwo
  resources:
    requests:
      storage: 50Gi

---
# ingestion-ns: Kafka logs
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: kafka-data
  namespace: ingestion-ns
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: standard-rwo
  resources:
    requests:
      storage: 50Gi

---
# logging-ns: Elasticsearch
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: elasticsearch-data
  namespace: logging-ns
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: standard-rwo
  resources:
    requests:
      storage: 50Gi

---
# rag-ns: Weaviate vector data
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: weaviate-data
  namespace: rag-ns
spec:
  accessModes: [ReadWriteOnce]
  storageClassName: standard-rwo
  resources:
    requests:
      storage: 20Gi
```

### 13.2 PodDisruptionBudgets

```yaml
# Kafka: at least 2 of 3 brokers must be available
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: kafka-pdb
  namespace: ingestion-ns
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: kafka

---
# PostgreSQL DW: must always be available
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: postgresql-dw-pdb
  namespace: storage-ns
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: postgresql-dw

---
# Elasticsearch: at least 2 of 3 nodes
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: elasticsearch-pdb
  namespace: logging-ns
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: elasticsearch
```

---

## 14. Secrets Management [ADR FIX — NEW SECTION]

```yaml
# K8s Secret for database credentials
apiVersion: v1
kind: Secret
metadata:
  name: postgresql-dw-credentials
  namespace: storage-ns
type: Opaque
stringData:
  POSTGRES_USER: "face_detection_admin"
  POSTGRES_PASSWORD: "${GENERATED_PASSWORD}"  # Use sealed-secrets or external-secrets
  POSTGRES_DB: "face_detection"

---
# MinIO credentials
apiVersion: v1
kind: Secret
metadata:
  name: minio-credentials
  namespace: storage-ns
type: Opaque
stringData:
  MINIO_ROOT_USER: "minio-admin"
  MINIO_ROOT_PASSWORD: "${GENERATED_PASSWORD}"

---
# Keycloak admin
apiVersion: v1
kind: Secret
metadata:
  name: keycloak-admin
  namespace: auth-ns
type: Opaque
stringData:
  KEYCLOAK_ADMIN: "admin"
  KEYCLOAK_ADMIN_PASSWORD: "${GENERATED_PASSWORD}"

---
# MLflow backend store
apiVersion: v1
kind: Secret
metadata:
  name: mlflow-backend
  namespace: ml-pipeline-ns
type: Opaque
stringData:
  MLFLOW_BACKEND_STORE_URI: "postgresql://mlflow:${PASSWORD}@postgresql-dw.storage-ns:5432/mlflow"
  MLFLOW_ARTIFACT_ROOT: "s3://face-detection/models/"
  AWS_ACCESS_KEY_ID: "${MINIO_ACCESS_KEY}"
  AWS_SECRET_ACCESS_KEY: "${MINIO_SECRET_KEY}"
```

> **Recommendation**: For production, use [sealed-secrets](https://github.com/bitnami-labs/sealed-secrets) or [external-secrets-operator](https://external-secrets.io/) with GCP Secret Manager instead of plain K8s Secrets.

---

## 15. NetworkPolicy per Namespace [ADR FIX — NEW SECTION]

```yaml
# Default deny all ingress for each namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: storage-ns
spec:
  podSelector: {}
  policyTypes: [Ingress]

---
# Allow processing-ns → storage-ns (Spark → MinIO, PostgreSQL)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-processing-to-storage
  namespace: storage-ns
spec:
  podSelector: {}
  policyTypes: [Ingress]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: processing-ns
        - namespaceSelector:
            matchLabels:
              name: streaming-ns
        - namespaceSelector:
            matchLabels:
              name: serving-ns
        - namespaceSelector:
            matchLabels:
              name: orchestration-ns
        - namespaceSelector:
            matchLabels:
              name: ml-pipeline-ns

---
# Allow only ingestion-ns to access Kafka
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: kafka-access-policy
  namespace: ingestion-ns
spec:
  podSelector:
    matchLabels:
      app: kafka
  policyTypes: [Ingress]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: streaming-ns
        - namespaceSelector:
            matchLabels:
              name: processing-ns
        - namespaceSelector:
            matchLabels:
              name: serving-ns
        - namespaceSelector:
            matchLabels:
              name: monitoring-ns
      ports:
        - port: 9092
          protocol: TCP
```

---

## 16. Flink Checkpoint & State Configuration [ADR FIX — NEW SECTION]

```yaml
# flink-conf.yaml (via Helm values)
flink:
  config:
    state.backend: rocksdb
    state.checkpoints.dir: s3://face-detection/checkpoints/flink/
    state.savepoints.dir: s3://face-detection/savepoints/flink/
    execution.checkpointing.interval: 60000       # 60 seconds
    execution.checkpointing.mode: EXACTLY_ONCE
    execution.checkpointing.min-pause: 30000       # 30 seconds between checkpoints
    state.backend.rocksdb.localdir: /tmp/flink-rocksdb
    restart-strategy: fixed-delay
    restart-strategy.fixed-delay.attempts: 3
    restart-strategy.fixed-delay.delay: 10s
  s3:
    access-key: "${MINIO_ACCESS_KEY}"
    secret-key: "${MINIO_SECRET_KEY}"
    endpoint: "http://minio.storage-ns:9000"
    path-style-access: true
```

---

## 17. Airflow Executor Strategy [ADR FIX — NEW SECTION]

> **Recommendation**: Use `KubernetesExecutor` instead of `CeleryExecutor` to save resources.
> With KubernetesExecutor, each Airflow task runs in its own K8s pod — no persistent workers needed.

```yaml
# airflow values.yaml
airflow:
  executor: KubernetesExecutor
  config:
    AIRFLOW__KUBERNETES__NAMESPACE: orchestration-ns
    AIRFLOW__KUBERNETES__WORKER_CONTAINER_REPOSITORY: apache/airflow
    AIRFLOW__KUBERNETES__WORKER_CONTAINER_TAG: "2.8"
    AIRFLOW__KUBERNETES__DELETE_WORKER_PODS: "True"
    AIRFLOW__KUBERNETES__DELETE_WORKER_PODS_ON_FAILURE: "False"  # Keep failed pods for debugging
  webserver:
    replicas: 1
    resources:
      requests: { cpu: 500m, memory: 1Gi }
      limits:   { cpu: 1, memory: 2Gi }
  scheduler:
    replicas: 1
    resources:
      requests: { cpu: 500m, memory: 1Gi }
      limits:   { cpu: 1, memory: 2Gi }
  # No workers needed with KubernetesExecutor!
  # workers:
  #   replicas: 0
```

---

## 18. SSO Tool Compatibility Matrix [ADR FIX — NEW SECTION]

| Tool | Native OIDC Support | Integration Method | Config |
|------|--------------------|--------------------|--------|
| Grafana | ✅ Yes | `auth.generic_oauth` in grafana.ini | Direct Keycloak client |
| Airflow | ✅ Yes | `AUTH_TYPE = AUTH_OID` via Flask-AppBuilder | Direct Keycloak client |
| MLflow | ❌ No | OAuth2 Proxy sidecar | Proxy in front of MLflow |
| Kubeflow | ✅ Yes (via Dex/OIDC) | OIDC connector | Replace Dex with Keycloak |
| DataHub | ✅ Yes | `datahub.auth.oidc.*` config | Direct Keycloak client |
| MinIO | ✅ Yes | `MINIO_IDENTITY_OPENID_CONFIG_URL` | Direct Keycloak client |
| Kibana | ⚠️ Requires xpack | OAuth2 Proxy sidecar (free tier) | Proxy in front of Kibana |
| Jaeger | ❌ No | OAuth2 Proxy sidecar | Proxy in front of Jaeger |
| Spark UI | ❌ No | OAuth2 Proxy sidecar | Proxy in front of Spark |
| Flink UI | ❌ No | OAuth2 Proxy sidecar | Proxy in front of Flink |
| Langfuse | ✅ Yes | OIDC config built-in | Direct Keycloak client |
| Evidently | ❌ No | OAuth2 Proxy sidecar | Proxy in front of Evidently |
| Prometheus | ❌ No | OAuth2 Proxy sidecar | Proxy in front of Prometheus |
| FastAPI (Swagger) | Custom | `python-keycloak` library | JWT middleware in FastAPI |

**Summary**: 6 tools use native OIDC, 7 tools need OAuth2 Proxy sidecar, 1 tool needs custom middleware.

---

## 19. Health Probes for All Services [ADR FIX — NEW SECTION]

> **Current gap**: FastAPI deployment has `/health` endpoint but no `livenessProbe` or `readinessProbe` in the Helm template.

### FastAPI Deployment Fix:
```yaml
# charts/face-detection/templates/deployment.yaml — ADD these probes:
containers:
  - name: {{ .Release.Name }}
    image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
    ports:
      - containerPort: 8000
    livenessProbe:
      httpGet:
        path: /health
        port: 8000
      initialDelaySeconds: 30
      periodSeconds: 15
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /health
        port: 8000
      initialDelaySeconds: 10
      periodSeconds: 5
      failureThreshold: 3
    resources:
      limits:
        memory: 1Gi      # [ADR FIX] Increased from 500Mi for YOLOv11 model loading
        cpu: "1"          # [ADR FIX] Increased from 500m
      requests:
        memory: 512Mi     # [ADR FIX] Increased from 300Mi
        cpu: 500m
```

### Health Probe Standards for All New Services:

| Service | Health Endpoint | Liveness | Readiness | Startup |
|---------|----------------|----------|-----------|---------|
| FastAPI | `GET /health` | 30s init, 15s period | 10s init, 5s period | — |
| Kafka | TCP :9092 | 30s init, 10s period | 30s init, 10s period | 120s timeout |
| PostgreSQL | `pg_isready -U postgres` | 30s init, 10s period | 10s init, 5s period | 60s timeout |
| MinIO | `GET /minio/health/live` | 30s init, 15s period | 10s init, 5s period | — |
| Elasticsearch | `GET /_cluster/health` | 60s init, 30s period | 30s init, 10s period | 120s timeout |
| Airflow Webserver | `GET /health` | 30s init, 15s period | 10s init, 5s period | — |
| KServe/Triton | `GET /v2/health/ready` | 60s init, 15s period | 30s init, 5s period | 120s timeout |
| Ollama | `GET /api/tags` | 60s init, 30s period | 30s init, 10s period | 180s timeout |

---

## 20. NGINX → Istio Migration Plan [ADR FIX — NEW SECTION]

### Phase 1: Coexistence
1. Deploy Istio alongside NGINX Ingress (both active)
2. Istio handles new MLOps 2/3 services (`*.face-detect.dev`)
3. NGINX continues handling MLOps 1 services (legacy)

### Phase 2: Gradual Migration
4. Create Istio `VirtualService` for FastAPI
5. Update DNS: `api.face-detect.dev` → Istio Gateway IP
6. Test FastAPI through Istio for 1 week
7. Migrate monitoring tools (Grafana, Kibana, Jaeger) to Istio

### Phase 3: Cutover
8. All traffic flows through Istio Gateway
9. Remove NGINX Ingress Controller helm release
10. Delete `nginx-ingress-ns` namespace
11. Update Terraform to remove NGINX-related resources

### Validation Checklist:
- [ ] All URLs resolve through Istio Gateway
- [ ] mTLS active between all pods (`istioctl analyze`)
- [ ] SSO cookie works for all `*.face-detect.dev` subdomains
- [ ] Latency unchanged (compare Grafana dashboards before/after)
- [ ] Jaeger traces show Istio sidecar spans

---

## 21. LLM Security & Guardrails Architecture

> **Reference**: [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/), [LLM Engineer Toolkit](https://github.com/KalyanKS-NLP/llm-engineer-toolkit)

### 21.1 Threat Model (OWASP LLM Top 10 — 2025)

| # | Vulnerability | Risk Level | Our Mitigation |
|---|--------------|------------|----------------|
| LLM01 | **Prompt Injection** | CRITICAL | LLM Guard input scanner + NeMo Guardrails dialog control |
| LLM02 | **Sensitive Information Disclosure** | HIGH | PII scanner (LLM Guard) + output filtering + Langfuse audit |
| LLM03 | **Supply Chain Vulnerabilities** | HIGH | Model provenance tracking (MLflow) + DVC hash verification |
| LLM04 | **Data Poisoning** | HIGH | Great Expectations validation on RAG knowledge base + signed datasets |
| LLM05 | **Improper Output Handling** | MEDIUM | Guardrails AI output validators + structured output (Instructor) |
| LLM06 | **Excessive Agency** | MEDIUM | Tool sandboxing + Guardrails AI action limits |
| LLM07 | **System Prompt Leakage** | MEDIUM | NeMo Guardrails Colang rules + LLM Guard system prompt protection |
| LLM08 | **Vector & Embedding Weaknesses** | MEDIUM | Weaviate tenant isolation + query sanitization |
| LLM09 | **Misinformation** | LOW | Langfuse hallucination scoring + source citation enforcement |
| LLM10 | **Unbounded Consumption** | MEDIUM | KEDA rate limiting + Envoy circuit breaker + token budget per request |

### 21.2 Multi-Layer Defense Architecture

```
User Request
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 1: Input Screening (< 30ms)                               │
│ ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│ │ LLM Guard       │  │ Prompt Injection  │  │ PII Anonymizer │  │
│ │ Input Scanners  │  │ Detector          │  │ (presidio)     │  │
│ │ (15 scanners)   │  │ (DeBERTa model)   │  │                │  │
│ └─────────────────┘  └──────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
     │ (clean input)
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 2: Dialog Control (50-200ms)                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ NVIDIA NeMo Guardrails                                      │ │
│ │ - Colang 2.0 dialog rules                                  │ │
│ │ - Topic boundary enforcement                                │ │
│ │ - Jailbreak detection (multi-model voting)                  │ │
│ │ - Hallucination rail (fact-checking against knowledge base) │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
     │ (approved prompt)
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 3: LLM Inference                                           │
│ ┌──────────────┐  ┌──────────────────┐  ┌────────────────────┐ │
│ │ Ollama        │  │ RAGFlow          │  │ Langfuse           │ │
│ │ TinyLlama 1.1B│  │ Retrieval +      │  │ Observability      │ │
│ │               │  │ Generation       │  │ (cost, latency,    │ │
│ │               │  │                  │  │  token usage)      │ │
│ └──────────────┘  └──────────────────┘  └────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
     │ (raw LLM output)
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 4: Output Validation (< 50ms)                              │
│ ┌─────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│ │ Guardrails AI   │  │ LLM Guard        │  │ Structured      │  │
│ │ Output          │  │ Output Scanners  │  │ Output          │  │
│ │ Validators      │  │ (20 scanners)    │  │ (Instructor)    │  │
│ │ (Pydantic)      │  │ - Toxicity       │  │ (Pydantic       │  │
│ │                 │  │ - Bias detect    │  │  validation)    │  │
│ │                 │  │ - Malicious URL  │  │                 │  │
│ │                 │  │ - Data leakage   │  │                 │  │
│ └─────────────────┘  └──────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
     │ (validated output)
     ▼
┌─────────────────────────────────────────────────────────────────┐
│ LAYER 5: Audit & Monitoring                                      │
│ ┌──────────────┐  ┌──────────────────┐  ┌────────────────────┐ │
│ │ Langfuse      │  │ Prometheus       │  │ DeepTeam           │ │
│ │ Trace logs    │  │ Guardrail        │  │ (scheduled         │ │
│ │ + scoring     │  │ metrics          │  │  red-team scans)   │ │
│ └──────────────┘  └──────────────────┘  └────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### 21.3 Tool Selection & Deployment

| Tool | Docker Image | Purpose | Namespace | Port |
|------|-------------|---------|-----------|------|
| **LLM Guard** | `protectai/llm-guard-api:latest` | Input/output scanning (15+20 scanners) | `rag-ns` | 8192 |
| **NeMo Guardrails** | `nvcr.io/nvidia/nemo-guardrails:latest` | Dialog control + Colang rules | `rag-ns` | 8090 |
| **Guardrails AI** | `guardrails/guardrails-api:latest` | Output validation (50+ validators) | `rag-ns` | 8000 |
| **Instructor** | *(Python library, embedded in RAGFlow)* | Structured output with Pydantic retry | `rag-ns` | — |
| **DeepTeam** | `python:3.11-slim` + pip install | Red-teaming framework (40+ vuln classes) | `ml-pipeline-ns` | — |
| **Garak** | `python:3.11-slim` + pip install | NVIDIA LLM vulnerability scanner | `ml-pipeline-ns` | — |

### 21.4 LLM Guard Configuration

```yaml
# llm-guard-config.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-guard
  namespace: rag-ns
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: llm-guard
        image: protectai/llm-guard-api:latest
        ports:
        - containerPort: 8192
        env:
        - name: SCAN_PROMPT_ENABLED
          value: "true"
        - name: SCAN_OUTPUT_ENABLED
          value: "true"
        - name: LOG_LEVEL
          value: "INFO"
        resources:
          requests: { cpu: 500m, memory: 1Gi }
          limits:   { cpu: 1, memory: 2Gi }
        # Needs ~1.5GB for DeBERTa prompt injection model
        livenessProbe:
          httpGet: { path: /healthz, port: 8192 }
          initialDelaySeconds: 60
        readinessProbe:
          httpGet: { path: /readyz, port: 8192 }
          initialDelaySeconds: 45
```

**Input Scanners Enabled:**

| Scanner | Purpose | Performance |
|---------|---------|-------------|
| `PromptInjection` | Detect direct & indirect injection attacks | ~15ms (DeBERTa v3) |
| `Toxicity` | Block toxic/harmful prompts | ~10ms |
| `BanTopics` | Restrict off-topic requests | ~5ms |
| `InvisibleText` | Detect hidden unicode/zero-width attacks | ~1ms |
| `Secrets` | Detect API keys, passwords in prompts | ~2ms |
| `Anonymize` (PII) | Auto-redact names, emails, phone numbers | ~8ms |
| `Language` | Enforce language whitelist (en, vi) | ~3ms |
| `Regex` | Custom pattern matching | ~1ms |

**Output Scanners Enabled:**

| Scanner | Purpose | Performance |
|---------|---------|-------------|
| `Deanonymize` | Re-inject PII from vault after processing | ~2ms |
| `Toxicity` | Scan LLM output for harmful content | ~10ms |
| `MaliciousURLs` | Block malicious URLs in responses | ~5ms |
| `NoRefusal` | Detect unhelpful refusals | ~3ms |
| `Bias` | Detect biased/discriminatory outputs | ~10ms |
| `FactualConsistency` | Cross-check against retrieved documents | ~20ms |
| `Relevance` | Ensure output is relevant to query | ~8ms |
| `Sensitive` | Block sensitive data leakage | ~5ms |

### 21.5 NeMo Guardrails — Colang 2.0 Rules

```python
# config/rails.co (Colang 2.0 syntax)

# === Topic Boundaries ===
define user ask about face detection
  "How do I detect faces?"
  "What model is used?"
  "Show me detection results"

define user ask off topic
  "Write me a poem"
  "What's the weather?"
  "Tell me a joke"

define flow handle off topic
  user ask off topic
  bot refuse off topic
  "I'm a face detection assistant. I can help with face detection, model performance, and system monitoring. Let me know how I can help with those topics."

# === Prompt Injection Defense ===
define flow detect injection
  user ...
  $is_injection = execute check_prompt_injection(user_message=$last_user_message)
  if $is_injection
    bot warn injection
    "I've detected a potential prompt manipulation attempt. Your request has been logged for security review."
    stop

# === Hallucination Prevention ===
define flow check facts
  bot ...
  $is_hallucination = execute check_hallucination(bot_message=$last_bot_message)
  if $is_hallucination
    bot refuse hallucination
    "I'm not confident in that answer. Let me check the knowledge base again."
    execute generate_with_stricter_retrieval()

# === PII Protection ===
define flow block pii output
  bot ...
  $has_pii = execute scan_pii(bot_message=$last_bot_message)
  if $has_pii
    $sanitized = execute remove_pii(bot_message=$last_bot_message)
    bot say $sanitized
```

### 21.6 Red-Teaming Pipeline (DeepTeam + Garak)

```python
# red_team_pipeline.py — Scheduled via Airflow DAG (monthly)
from deepteam import red_team
from deepteam.vulnerabilities import (
    PromptInjection, PIILeakage, Hallucination,
    Toxicity, Bias, IntellectualProperty
)
from deepteam.attacks import (
    PromptInjection as PIAttack, Jailbreaking,
    ROT13Encoding, CrescendoJailbreaking
)

# Define target LLM endpoint
target_model = "http://ollama.rag-ns:11434/api/generate"

# Run red-team assessment
results = red_team(
    model=target_model,
    vulnerabilities=[
        PromptInjection(),   # OWASP LLM01
        PIILeakage(),        # OWASP LLM02
        Hallucination(),     # OWASP LLM09
        Toxicity(),
        Bias(),
        IntellectualProperty(),
    ],
    attacks=[
        PIAttack(),
        Jailbreaking(),
        ROT13Encoding(),
        CrescendoJailbreaking(),
    ],
    # OWASP + NIST compliance check
    frameworks=["owasp:llm:01", "owasp:llm:02", "nist:ai:100-2"],
)

# Export results to Langfuse for tracking
results.export_to_langfuse(
    host="http://langfuse.rag-ns:3000",
    public_key="...",
    secret_key="..."
)

# Fail pipeline if critical vulnerabilities found
assert results.critical_count == 0, f"CRITICAL: {results.critical_count} vulnerabilities found!"
```

**Airflow DAG Schedule:**
```python
# dags/red_team_scan.py
from airflow import DAG
from airflow.providers.cncf.kubernetes.operators.kubernetes_pod import KubernetesPodOperator

dag = DAG('llm_red_team_scan', schedule_interval='0 3 1 * *')  # Monthly, 3 AM

red_team_task = KubernetesPodOperator(
    task_id='run_deepteam_scan',
    namespace='ml-pipeline-ns',
    image='python:3.11-slim',
    cmds=['bash', '-c'],
    arguments=['pip install deepteam garak && python /scripts/red_team_pipeline.py'],
    resources={'requests': {'cpu': '1', 'memory': '4Gi'}},
    dag=dag,
)
```

---

## 22. Advanced LLM Engineering Stack

> **Reference**: [LLM Engineer Toolkit (150+ tools)](https://github.com/KalyanKS-NLP/llm-engineer-toolkit), [alexbobes.com](https://alexbobes.com/artificial-intelligence/the-ultimate-llm-engineer-toolkit/)

### 22.1 Enhanced RAG Pipeline Architecture

The current plan uses RAGFlow + Weaviate + Typesense. Based on the LLM Engineer Toolkit research, we add these enhancements:

| Enhancement | Tool | Purpose | Integration Point |
|-------------|------|---------|------------------|
| **Structured Output** | [Instructor](https://github.com/jxnl/instructor) | Pydantic-validated LLM responses with auto-retry | Ollama output → Pydantic model |
| **Prompt Compression** | [LLMLingua](https://github.com/microsoft/LLMLingua) | 2-5x context compression, fit more docs in context | Pre-Ollama prompt |
| **LLM Caching** | [GPTCache](https://github.com/zilliztech/GPTCache) | Semantic cache for repeated queries, reduce latency | Before Ollama inference |
| **LLM Gateway** | [LiteLLM Proxy](https://github.com/BerriAI/litellm) | Unified API for multiple models, rate limiting, logging | API gateway for Ollama |
| **Embedding Models** | [Sentence-Transformers](https://github.com/UKPLab/sentence-transformers) | Local embedding generation (all-MiniLM-L6-v2) | Weaviate vectorizer |
| **Chunking** | [Chonkie](https://github.com/bhavnicksm/chonkie) | Smart semantic chunking for RAG documents | Pre-Weaviate ingestion |
| **Reranker** | [FlashRank](https://github.com/PrithivirajDamodaran/FlashRank) | Ultra-fast reranking (~10ms, no GPU needed) | Post-retrieval, pre-generation |

### 22.2 Enhanced RAG Flow (with Security Layers)

```
User Query
    │
    ▼
[LLM Guard Input Scan] ──(block)──> 403 Rejected
    │ (clean)
    ▼
[GPTCache Check] ──(cache hit)──> Return cached response
    │ (cache miss)
    ▼
[NeMo Guardrails Dialog Control]
    │ (approved)
    ▼
[LLMLingua Prompt Compression]
    │
    ▼
[RAGFlow Retrieval]
    ├── Weaviate (vector search)
    └── Typesense (keyword BM25)
    │
    ▼
[FlashRank Reranker] ──> Top-K relevant docs
    │
    ▼
[Ollama TinyLlama 1.1B] ──> via LiteLLM Proxy
    │
    ▼
[Instructor Structured Output] ──> Pydantic validated
    │
    ▼
[LLM Guard Output Scan] ──(block)──> Sanitized response
    │ (clean)
    ▼
[Guardrails AI Final Validation]
    │
    ▼
[Langfuse Trace Logging] ──> Response to User
```

### 22.3 LLM Evaluation Framework

| Tool | Purpose | When to Run |
|------|---------|-------------|
| [DeepEval](https://github.com/confident-ai/deepeval) | RAG evaluation metrics (faithfulness, relevance, coherence) | After RAG pipeline changes |
| [Ragas](https://github.com/explodinggradients/ragas) | RAG-specific metrics (context precision, answer relevancy) | Weekly automated eval |
| [DeepTeam](https://github.com/confident-ai/deepteam) | Security red-teaming (40+ vulnerability classes) | Monthly security scan |
| [Garak](https://github.com/NVIDIA/garak) | NVIDIA LLM vulnerability probing | Monthly security scan |
| [Promptfoo](https://github.com/promptfoo/promptfoo) | Prompt testing & regression checking | On every prompt template change |

**Evaluation Pipeline (Airflow DAG):**
```python
# dags/llm_evaluation.py
# Runs weekly to assess RAG quality

evaluate_rag = KubernetesPodOperator(
    task_id='evaluate_rag_quality',
    namespace='ml-pipeline-ns',
    image='python:3.11-slim',
    cmds=['bash', '-c'],
    arguments=['''
        pip install deepeval ragas langfuse &&
        python -c "
from deepeval.metrics import (
    FaithfulnessMetric,
    AnswerRelevancyMetric,
    ContextualPrecisionMetric,
    HallucinationMetric
)
from deepeval.test_case import LLMTestCase
from deepeval import evaluate

# Load test cases from gold dataset
test_cases = load_test_cases('s3://face-detection/eval/rag_test_cases.json')

metrics = [
    FaithfulnessMetric(threshold=0.7),
    AnswerRelevancyMetric(threshold=0.8),
    ContextualPrecisionMetric(threshold=0.7),
    HallucinationMetric(threshold=0.5),
]

results = evaluate(test_cases, metrics)
# Push metrics to Prometheus
push_metrics_to_prometheus(results)
# Log to Langfuse
log_to_langfuse(results)
"
    '''],
)
```

### 22.4 LLM Observability Stack

| Layer | Tool | Metrics |
|-------|------|---------|
| **Tracing** | Langfuse | Per-request traces (prompt → retrieval → generation → validation) |
| **Cost Tracking** | Langfuse + LiteLLM | Token usage, cost per query, model comparison |
| **Quality Scoring** | Langfuse Scores | User feedback, auto-eval scores, hallucination rate |
| **Latency** | Prometheus + Grafana | P50/P95/P99 latency per component (cache, retrieval, generation, validation) |
| **Security Alerts** | LLM Guard + Prometheus | Blocked requests, injection attempts, PII detections |
| **Drift Detection** | DeepEval + Airflow | Weekly RAG quality regression detection |

**Grafana Dashboard Panels (LLM Monitoring):**

| Panel | Metric | Alert Threshold |
|-------|--------|----------------|
| Prompt Injection Rate | `llm_guard_blocked_total{scanner="PromptInjection"}` | > 10/hour |
| PII Detection Rate | `llm_guard_blocked_total{scanner="Anonymize"}` | > 5/hour |
| Response Toxicity | `llm_guard_output_blocked{scanner="Toxicity"}` | > 1/hour |
| Cache Hit Rate | `gptcache_hit_total / gptcache_total` | < 20% (investigate) |
| RAG Faithfulness | `deepeval_faithfulness_score` | < 0.7 (trigger review) |
| E2E Latency P95 | `histogram_quantile(0.95, llm_request_duration_seconds)` | > 5s |
| Token Usage | `litellm_total_tokens` | > budget/day |

### 22.5 Kubernetes Resource Additions (for LLM Security stack)

| Component | CPU Request | Memory Request | CPU Limit | Memory Limit | PVC |
|-----------|------------|----------------|-----------|-------------|-----|
| LLM Guard | 500m | 1Gi | 1 | 2Gi | — |
| NeMo Guardrails | 500m | 512Mi | 1 | 1Gi | — |
| Guardrails AI | 250m | 256Mi | 500m | 512Mi | — |
| GPTCache (Redis) | 250m | 512Mi | 500m | 1Gi | 5Gi |
| LiteLLM Proxy | 250m | 256Mi | 500m | 512Mi | — |
| **Subtotal** | **1.75 cores** | **2.5Gi** | **3.5 cores** | **5Gi** | **5Gi** |

> **Updated infrastructure total**: ~38 cores, ~110GB RAM (previously ~36 cores, ~107GB)

---

## 23. LLM Knowledge Base Management

### 23.1 RAG Knowledge Sources for Face Detection System

| Knowledge Source | Type | Update Frequency | Chunking Strategy |
|-----------------|------|------------------|-------------------|
| Face detection API docs | Markdown | On code change | Semantic (512 tokens) |
| YOLOv11 documentation | PDF | Monthly | Fixed (1000 tokens) with overlap |
| Model performance reports | JSON/CSV | Weekly (auto) | Structured extraction |
| Incident postmortems | Markdown | On creation | Semantic (768 tokens) |
| Monitoring runbooks | Markdown | On update | Semantic (512 tokens) |
| System architecture docs | Markdown + PNG | On update | Multimodal (text + image captions) |

### 23.2 Knowledge Base Pipeline

```
Source documents
    │
    ▼
[Chonkie Semantic Chunker]
    │
    ▼
[Sentence-Transformers Embedding] (all-MiniLM-L6-v2, 384 dim)
    │
    ▼
[Weaviate Vector Store]
    │
    ├── Collection: "FaceDetectionDocs" (general docs)
    ├── Collection: "IncidentReports" (postmortems)
    ├── Collection: "ModelPerformance" (metrics & reports)
    └── Collection: "Runbooks" (operational guides)

[Great Expectations] validates:
    - No duplicate documents
    - Embedding dimension consistency (384)
    - Chunk size within bounds (100-1500 tokens)
    - Source attribution present
```

### 23.3 Knowledge Base Security

| Concern | Mitigation |
|---------|-----------|
| **Data Poisoning** (OWASP LLM04) | GE validation on all ingested docs + manual approval gate |
| **Tenant Isolation** | Weaviate multi-tenancy with per-role collection access |
| **Document Provenance** | SHA-256 hash + git commit tracking for every document |
| **Stale Knowledge** | Airflow DAG checks document freshness weekly |
| **Embedding Inversion** | Weaviate API behind Istio mTLS, no direct external access |

---

*Document generated: April 2026 — Updated with ADR-001 fixes + LLM Security & Advanced LLM Engineering*
*Project: Face Detection ML System - MLOps Extended Architecture*
*Author: Long Loe (Hoang Duc Long)*
*References: [OWASP LLM Top 10](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/), [LLM Engineer Toolkit](https://github.com/KalyanKS-NLP/llm-engineer-toolkit)*
