# System Architecture

**Project**: Face Detection ML System  
**Level**: 1 (Current production) + 2/3 (Planned overview)  
**Last Updated**: 2026-04-15  
**Architecture Style**: Microservices + Event-Driven (Level 2+)

## Level 1 Architecture (Current)

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Developer Workflow                       │
│                                                                 │
│  1. Commit to GitHub    2. Jenkins Pipeline    3. Deploy to    │
│     (main branch)          (Test → Build →        GKE          │
│                            Deploy)                             │
└────────┬──────────────────────────┬──────────────────────┬─────┘
         │                          │                      │
         ▼                          ▼                      ▼
    ┌─────────────┐          ┌─────────────┐      ┌──────────────┐
    │   GitHub    │          │   Jenkins   │      │ Docker Hub   │
    │  Repository │          │   CI/CD     │      │  Registry    │
    │             │          │             │      │              │
    │ - main code │          │ 3 stages:   │      │ longhd06/    │
    │ - Dockerfile│          │ 1. Test     │      │ face-        │
    │ - Helm      │          │ 2. Build    │      │ detection    │
    │ - Terraform │          │ 3. Deploy   │      │ :BUILD_NO    │
    └─────────────┘          └─────────────┘      └──────────────┘
                                    │                      │
                                    │                      │
         ┌──────────────────────────┴──────────────────────┘
         │
         ▼
    ┌─────────────────────────────────────────────────┐
    │        Google Cloud Platform (GCP)              │
    │                                                  │
    │  ┌──────────────────────────────────────────┐   │
    │  │      GKE Cluster (1 node: e2-medium)     │   │
    │  │                                          │   │
    │  │  ┌────────────────────────────────────┐  │   │
    │  │  │   model-serving Namespace          │  │   │
    │  │  │                                    │  │   │
    │  │  │  ┌──────────────────────────────┐ │  │   │
    │  │  │  │ face-detection Deployment    │ │  │   │
    │  │  │  │ (1 replica)                  │ │  │   │
    │  │  │  │                              │ │  │   │
    │  │  │  │ ┌────────────────────────┐  │ │  │   │
    │  │  │  │ │  FastAPI Pod (8000)    │  │ │  │   │
    │  │  │  │ │  - YOLOv11 inference   │  │ │  │   │
    │  │  │  │ │  - OpenTelemetry       │  │ │  │   │
    │  │  │  │ │  - loguru logging      │  │ │  │   │
    │  │  │  │ └────────────────────────┘  │ │  │   │
    │  │  │  └──────────────────────────────┘ │  │   │
    │  │  │                                    │  │   │
    │  │  │  ┌──────────────────────────────┐ │  │   │
    │  │  │  │ Service (LoadBalancer)       │ │  │   │
    │  │  │  │ :8000 → External IP          │ │  │   │
    │  │  │  └──────────────────────────────┘ │  │   │
    │  │  │                                    │  │   │
    │  │  │  ┌──────────────────────────────┐ │  │   │
    │  │  │  │ Ingress (NGINX)              │ │  │   │
    │  │  │  │ face-detection.local:8000    │ │  │   │
    │  │  │  └──────────────────────────────┘ │  │   │
    │  │  └────────────────────────────────────┘  │   │
    │  │                                          │   │
    │  │  ┌────────────────────────────────────┐  │   │
    │  │  │   nginx-ingress Namespace          │  │   │
    │  │  │   NGINX Ingress Controller         │  │   │
    │  │  └────────────────────────────────────┘  │   │
    │  │                                          │   │
    │  │  ┌────────────────────────────────────┐  │   │
    │  │  │   monitoring Namespace             │  │   │
    │  │  │   - Prometheus (metrics)           │  │   │
    │  │  │   - Grafana (dashboards)           │  │   │
    │  │  │   - Alert Manager                  │  │   │
    │  │  └────────────────────────────────────┘  │   │
    │  │                                          │   │
    │  │  ┌────────────────────────────────────┐  │   │
    │  │  │   elastic-system Namespace         │  │   │
    │  │  │   - Elasticsearch (logs)           │  │   │
    │  │  │   - Kibana (log search)            │  │   │
    │  │  │   - Filebeat (log shipping)        │  │   │
    │  │  └────────────────────────────────────┘  │   │
    │  │                                          │   │
    │  │  ┌────────────────────────────────────┐  │   │
    │  │  │   tracing Namespace                │  │   │
    │  │  │   - Jaeger (distributed traces)    │  │   │
    │  │  └────────────────────────────────────┘  │   │
    │  └──────────────────────────────────────────┘   │
    │                                                  │
    │  ┌──────────────────────────────────────────┐   │
    │  │  GCE VM (Jenkins)                        │   │
    │  │  - Jenkins master (port 8081)            │   │
    │  │  - Docker daemon                         │   │
    │  │  - kubectl (GKE access)                  │   │
    │  └──────────────────────────────────────────┘   │
    └─────────────────────────────────────────────────┘
```

### Component Description

#### 1. API Service Layer (`api/`)
**Purpose**: Serve face detection inference requests

**Components**:
- **FastAPI Application** (`main.py`)
  - Routes: GET `/health`, POST `/detect/faces/image`
  - CORS middleware (allow all origins)
  - OpenTelemetry instrumentation (automatic HTTP span capture)

- **Inference Engine** (`my_yolo.py`)
  - YOLOv11 model (5.5 MB, loaded at startup)
  - Image processing utilities (encode/decode)
  - Bounding box rendering

**Dependencies**:
- FastAPI 0.115.3 (HTTP framework)
- Ultralytics 8.3.21 (YOLOv11 inference)
- OpenCV (image processing)
- OpenTelemetry SDK (tracing)
- loguru (logging)

**Performance**:
- Single request latency: ~100ms (inference) + ~20ms (encode/decode) = ~120ms p95
- Throughput: ~10 requests/second per pod
- Memory: ~400 MB (with loaded model)

#### 2. Kubernetes Orchestration (`charts/`)
**Purpose**: Deploy and manage containerized services

**Deployment Strategy**:
- **face-detection Chart**
  - 1 replica (manually scaled; KEDA autoscaling planned for Level 3)
  - Resource limits: 500Mi memory, 200m CPU
  - Health checks: Liveness/readiness probes (future: implement)
  - Image pull policy: IfNotPresent

- **NGINX Ingress Controller**
  - Provides HTTP(S) ingress to GKE services
  - Hostname: `face-detection.local` (configurable)
  - External load balancer exposure

**Networking Model**:
- **ClusterIP Service**: Internal pod-to-pod communication
- **LoadBalancer Service**: External API access (port 8000)
- **Ingress**: Layer 7 routing (hostname-based)

#### 3. Infrastructure as Code (`infrastructure/`)
**Purpose**: Automate cloud resource provisioning

**Terraform Components**:
- **GKE Cluster**
  - Zone: us-central1-a
  - Node pool: 1× e2-medium (preemptible, cost-optimized)
  - Network: Auto-created VPC with subnets
  - Cluster version: Latest stable (managed by GKE)

- **GCE VM (Jenkins)**
  - Machine type: n1-standard-1 (configurable)
  - Image: Debian 10 (for Ansible provisioning)
  - Firewall: SSH (22), HTTP (8081) open to 0.0.0.0/0 (future: restrict)

**Ansible Configuration**:
- Install Docker on Jenkins VM
- Configure Jenkins agent
- Register GKE cluster credentials
- Deploy sample job

#### 4. Monitoring & Observability

**Metrics Collection (Prometheus)**:
- Scrape target: `http://face-detection:8000/metrics` (every 15s)
- Metrics exposed:
  - HTTP request count (by method, path, status)
  - Request latency (p50, p95, p99)
  - Model inference time
  - Error rates

**Log Aggregation (ELK Stack)**:
- **Elasticsearch**: Stores logs in indices (logstash-*)
- **Filebeat**: Ships container stdout/stderr to Elasticsearch
- **Kibana**: Provides log search and visualization UI

**Distributed Tracing (Jaeger)**:
- **Endpoint**: OTLP gRPC (port 4317, in-cluster)
- **Sampler**: ALWAYS_ON (100% sampling, for development)
- **Exporter**: BatchSpanProcessor (flushes every 5s)
- **Traces captured**:
  - HTTP request entry/exit
  - Model inference call
  - Image encoding/decoding

**Visualization (Grafana)**:
- Dashboards: Request rate, latency, error rate (auto-generated)
- Data source: Prometheus
- UI: NodePort (port 30000)

### Data Flow Diagram (Request Path)

```
Client Request → NGINX Ingress → LoadBalancer Service → Pod
    │                                                      │
    │  HTTP POST /detect/faces/image                      │
    │  + file (image bytes)                               │
    │                                                      │
    └──────────────────────────────────────────────────────→
                                                            │
                                                      FastAPI App
                                                            │
                                    ┌─────────────────────┬─┴────────┬──────────────────┐
                                    │                     │          │                  │
                            OpenTelemetry         Image Decode  YOLOv11          Encode
                            (start span)             (CV2)      Inference        Result
                                    │                     │          │                  │
                                    └─────────────────────┴──────────┴──────────────────┘
                                    │
                                    ├→ Jaeger (trace export, async)
                                    ├→ Prometheus (metrics, in-memory)
                                    └→ loguru (stderr → Filebeat → Elasticsearch)
                                    │
                                    ▼
                        StreamingResponse
                        (image/jpeg + headers)
                                    │
    ┌───────────────────────────────┘
    │
    ▼
Client Response
  - Content: Annotated JPEG image
  - Headers:
    - X-Total-Faces: <count>
    - X-Processing-Time: <seconds>
```

## Level 2 Architecture (Planned)

### Data Engineering Layer

**New Components**:
- **Kafka KRaft** (data pipeline ingestion)
  - 3 brokers, KRaft mode (no Zookeeper)
  - Topics: raw-images (claims), metadata
  - Claim-check pattern: Images → MinIO, metadata → Kafka

- **Apache Spark** (batch processing)
  - Spark cluster: 1 Master + 2 Workers
  - Medallion architecture: Bronze (raw) → Silver (cleaned) → Gold (curated)
  - Great Expectations: Data quality validation

- **Apache Flink** (stream processing, optional)
  - Low-latency real-time inference augmentation
  - Parallel to Spark Streaming

- **MinIO** (object storage)
  - S3-compatible API
  - Stores raw/processed images and models

- **Airflow** (workflow orchestration)
  - DAGs: Daily batch inference, weekly retraining prep
  - KubernetesExecutor pods

**Data Flow**:
```
Batch: Images → MinIO Bronze → Spark Bronze → Silver → Gold → Data Warehouse
Stream: Kafka → Flink → Enrichment → Serving Layer
CDC: PostgreSQL WAL → Debezium → Kafka → Spark Merge
```

See [NEW_PLANS.md](../NEW_PLANS.md) Sections 1–3 for detailed Level 2 specifications.

## Level 3 Architecture (Planned)

### Advanced ML Platform

**New Components (post-cut)**:
- **Kubeflow Pipelines** (ML training orchestration)
  - DAG-based experiments, hyperparameter tuning via Katib
  - Artifact tracking, model versioning

- **MLflow** (model registry and experiment tracking)
  - Track training metrics, compare models
  - Model registry with versioning and staging

- **KServe** (optional model serving demo)
  - Canary deployments, autoscale to zero
  - Replaces Triton + RayServe (cut as redundant)

- **Istio** (service mesh + gateway)
  - mTLS encryption, traffic management, L7 ingress
  - Replaces NGINX Ingress (cut as redundant with Istio Gateway)

- **Dex** (identity provider)
  - Lightweight OIDC IdP, federates GitHub/Google
  - Replaces Keycloak (cut for footprint)

- **OAuth2 Proxy** (session check)
  - Cookie session, JWT validation for apps without native OIDC

- **Evidently AI** (model monitoring)
  - Detect data/model drift
  - Trigger automated retraining pipelines

**Cut from original plan** (see [archive](./archive/cut-components-v0.1.md)):
- RAG stack entirely (RAGFlow, Ollama, Weaviate, Typesense, Langfuse) — irrelevant
- Triton + RayServe + RayTune — serving redundancy
- Flink — Spark Structured Streaming sufficient
- Airflow — Kubeflow covers ML orchestration
- ArgoCD + deployKF — Jenkins + helm sufficient
- DVC — MLflow covers versioning
- DataHub — overkill for 1 model
- Locust — k6 sufficient
- NGINX Ingress — Istio Gateway covers
- Keycloak → Dex (trim)

**Deployment**:
- 1-zone GKE cluster (~3× e2-medium → e2-standard-4, ~12 cores, ~40GB RAM)
- 9 Kubernetes namespaces (model-serving, data-platform, ml-platform, iam, istio-system, monitoring, logging, tracing, system)
- Resource management: ResourceQuotas, PodDisruptionBudgets, NetworkPolicies (see Phase 03 L1 hardening)

See [NEW_PLANS.md](../NEW_PLANS.md) Sections 4–8 and 21–23 for detailed Level 3 specifications.

## Architecture Patterns

### Design Patterns Applied

**1. Microservices Pattern**
- Decoupled services: API, monitoring, infrastructure
- Separate concerns: FastAPI only handles inference
- Independent scaling and deployment

**2. Sidecar Pattern** (Future: Level 3)
- Istio proxy sidecars for traffic management
- Envoy for advanced routing, retry logic, circuit breakers

**3. Strangler Fig Pattern** (Migration strategy)
- Phase 1: FastAPI (current)
- Phase 2: Introduce Kafka ingestion layer (gradual)
- Phase 3: Replace with KServe + Triton (greenfield deployment)

**4. Command Query Responsibility Segregation (CQRS)** (Future: Level 2)
- Command: Inference requests → Kafka (write-once)
- Query: Model versions → Model registry (read-heavy)

**5. Event-Driven Architecture** (Future: Level 2)
- Events: Image received, inference complete, drift detected
- Event bus: Kafka topics
- Event handlers: Spark, Airflow, monitoring

### Scalability Design

**Current (Level 1)**:
- Horizontal: Manual replica scaling via `kubectl scale`
- Vertical: Increase resource limits for heavier models

**Planned (Level 3)**:
- **Horizontal Pod Autoscaling (HPA)**: Based on CPU/memory
- **KEDA**: Custom metrics (request queue depth, inference latency)
- **Node autoscaling**: GKE Cluster Autoscaler (add/remove nodes)
- **Multi-region**: Replicate cluster to multiple zones (future)

### Resilience & Fault Tolerance

**Current (Level 1)**:
- Single node: Manual failover via pod restart
- Liveness probe: Restart unhealthy pod (future: implement)
- Readiness probe: Remove pod from load balancer if not ready (future)

**Planned (Level 3)**:
- **Pod Disruption Budgets (PDB)**: Ensure minimum availability
- **Network Policies**: Restrict traffic by default, allow specific routes
- **Service Mesh (Istio)**: Automatic retry, timeout, circuit breaker
- **Multi-zone nodes**: Spread across availability zones

## Technology Stack Summary

> **2026-05-21 update**: scope cut per YAGNI audit. See [docs/archive/cut-components-v0.1.md](./archive/cut-components-v0.1.md) for what was removed and why.

| Layer | Level 1 | Level 2 | Level 3 |
|-------|---------|---------|---------|
| **Inference** | FastAPI + YOLOv11 | FastAPI + YOLOv11 | + KServe (optional canary) |
| **Data** | None | Kafka + Spark + MinIO + Great Expectations | + Debezium CDC |
| **ML Ops** | Manual | + Kubeflow Pipelines + Katib | + MLflow Registry + Evidently |
| **Service Mesh** | None | None | Istio + mTLS |
| **Security** | Basic RBAC | + K8s Secrets | + Dex OIDC + OAuth2 Proxy + NetworkPolicies |
| **LLM/RAG** | — | — | — (cut: irrelevant to face detection) |

## Deployment Topology

### Level 1 (Current)
```
GKE Cluster (1 zone, 1 node)
├── model-serving (1 pod)
├── monitoring (Prometheus + Grafana)
├── elastic-system (Elasticsearch + Kibana + Filebeat)
└── tracing (Jaeger)

GCE VM (separate)
└── Jenkins (external CI/CD)
```

### Level 3 (Planned, post-cut)
```
GKE Cluster (1-3 zones, 3-6 nodes ~12-24 cores)
├── model-serving (FastAPI + optional KServe)
├── data-platform (Kafka KRaft, Schema Registry, MinIO, Spark, Debezium)
├── ml-platform (Kubeflow Pipelines, Katib, MLflow)
├── monitoring (Prometheus, Grafana, Evidently)
├── logging (Elasticsearch, Kibana, Filebeat)
├── tracing (Jaeger, 10% sampling)
├── iam (Dex, OAuth2 Proxy)
├── istio-system (Istio Gateway + control plane + mTLS)
└── system (kube-system, kube-node-lease, default)
```
**Total: 9 namespaces** (down from planned 16 — RAG/orchestration namespaces cut per YAGNI).

## Cross-Cutting Concerns

### Observability (Three Pillars)

**Metrics**:
- Prometheus scraping every 15s
- Grafana dashboards for visualization
- Alert thresholds: Latency > 150ms, error rate > 1%

**Logs**:
- Filebeat ships container logs to Elasticsearch
- Kibana enables full-text search and drill-down
- Retention: 7 days (configurable via Elasticsearch policy)

**Traces**:
- Jaeger OTLP gRPC receiver (port 4317)
- Automatic HTTP instrumentation (FastAPI)
- Manual span annotations for business logic (future)

### Security (Defense in Depth)

**Current (Level 1)**:
- Secrets: Kubernetes Secrets for credentials
- RBAC: Service account for Jenkins (model-serving-sa)
- Firewall: GCP firewall rules (Jenkins SSH/HTTP open)

**Planned (Level 3)**:
- mTLS: Istio enforces mutual TLS between services
- OIDC: Keycloak provides single sign-on
- Network Policies: Deny-all by default, whitelist routes
- Secret rotation: Automated via external-secrets operator

See [ADR_ARCHITECTURE_REVIEW.md](../ADR_ARCHITECTURE_REVIEW.md) for comprehensive architecture review (22 action items, 7.8/10 score).

## Related Documentation

- **Project Overview**: [docs/project-overview-pdr.md](./project-overview-pdr.md)
- **Code Standards**: [docs/code-standards.md](./code-standards.md)
- **Codebase Summary**: [docs/codebase-summary.md](./codebase-summary.md)
- **Deployment Guide**: [docs/deployment-guide.md](./deployment-guide.md)
- **Project Roadmap**: [docs/project-roadmap.md](./project-roadmap.md)
- **Level 2/3 Specs**: [NEW_PLANS.md](../NEW_PLANS.md)
- **Architecture Review**: [ADR_ARCHITECTURE_REVIEW.md](../ADR_ARCHITECTURE_REVIEW.md)
