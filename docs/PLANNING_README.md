<!-- omit in toc -->
# 📋 Planning: MLOps Level 2 & Level 3 — Face Detection ML System
<!-- omit in toc -->

> **Branch:** `planning/mlops-level2-level3`
> **Status:** Research & Design Phase — NO implementation yet
> **Scope:** AI Track 4A (ML System) + 4B (LLM/Agent)
> **Author:** Hoàng Đức Long

---

## Table of Contents

- [What Is This Branch?](#what-is-this-branch)
- [Quick Navigation](#quick-navigation)
- [System Evolution Overview](#system-evolution-overview)
- [Architecture Diagrams](#architecture-diagrams)
  - [1. Full System Overview](#1-full-system-overview)
  - [2. Batch Data Flow (Medallion Architecture)](#2-batch-data-flow-medallion-architecture)
  - [3. Stream Data Flow (Real-time)](#3-stream-data-flow-real-time)
  - [4. Change Data Capture (CDC)](#4-change-data-capture-cdc)
  - [5. ML Training Pipeline](#5-ml-training-pipeline)
  - [6. Model Serving (KServe + Triton)](#6-model-serving-kserve--triton)
  - [7. RAG / LLM Pipeline](#7-rag--llm-pipeline)
  - [8. SSO & Security Flow](#8-sso--security-flow)
  - [9. Drift Detection & Auto-Retrain](#9-drift-detection--auto-retrain)
- [Technology Stack Summary](#technology-stack-summary)
- [Kubernetes Namespace Map (16 Namespaces)](#kubernetes-namespace-map-16-namespaces)
- [Documents Index](#documents-index)
- [Architecture Decision Record (ADR) Highlights](#architecture-decision-record-adr-highlights)
- [Implementation Phases](#implementation-phases)
- [Related Branches](#related-branches)

---

## What Is This Branch?

This branch contains **all planning documents, architecture diagrams, and design decisions** for extending the Face Detection ML System from:

| Level | Description | Status |
|-------|-------------|--------|
| **MLOps Level 1** | YOLOv11 + FastAPI + GKE + Jenkins + Prometheus/Grafana + ELK + Jaeger | ✅ Done (`main` branch) |
| **MLOps Level 2** | Data Engineering — Kafka, Spark, Flink, MinIO, Great Expectations, DataHub, Airflow | 📐 Planned |
| **MLOps Level 3** | Advanced ML Platform — KServe + Triton, Kubeflow, Katib, TensorRT, Istio, Keycloak | 📐 Planned |
| **RAG/LLM** | RAGFlow + Weaviate + Typesense + Ollama (TinyLlama 1.1B) + Langfuse + Guardrails | 📐 Planned |

**No code changes are made in this branch** — only documentation, diagrams, and architecture reviews.

---

## Quick Navigation

| Document | Description | Size |
|----------|-------------|------|
| 📄 [NEW_PLANS.md](../NEW_PLANS.md) | Complete architecture specification — 20 sections covering all tools, data flows, schemas, YAML specs, infrastructure sizing | ~56K |
| 📄 [README_EXTENDED.md](../README_EXTENDED.md) | Step-by-step README with embedded diagrams, code examples, and deployment commands | ~38K |
| 📄 [ADR_ARCHITECTURE_REVIEW.md](../ADR_ARCHITECTURE_REVIEW.md) | Full architecture review (13 dimensions) — score 7.8/10, 22 action items | ~25K |
| 🌐 [architecture_detailed.html](../architecture_detailed.html) | Interactive 6-tab HTML viewer (namespaces, data flows, roles, SSO, deployKF, roadmap) | ~56K |

---

## System Evolution Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CURRENT (main branch)                          │
│                                                                        │
│   Developer → GitHub → Jenkins → Docker Hub → GKE → NGINX → FastAPI   │
│                                                    → YOLOv11 inference │
│   Monitoring: Prometheus + Grafana | ELK Stack | Jaeger                │
│                                                                        │
│   Infrastructure: 1x e2-medium (GKE) + 1x GCE VM (Jenkins)           │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      PLANNED (this branch docs)                       │
│                                                                        │
│   35+ tools │ 16 namespaces │ 6 user roles │ 3 data flows            │
│                                                                        │
│   Data Layer:  Kafka KRaft → Spark/Flink → MinIO (Medallion) → DW    │
│   ML Platform: Kubeflow → Katib → MLflow → TensorRT → KServe+Triton  │
│   RAG/LLM:    RAGFlow → Weaviate+Typesense → Ollama → Langfuse      │
│   Security:   Istio mTLS → Keycloak SSO → OAuth2 Proxy → RBAC       │
│   Infra:      Multi-node GKE (~36 cores, ~107GB RAM)                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Architecture Diagrams

### 1. Full System Overview

All 16 Kubernetes namespaces, 6 user roles, and 35+ tools in one view.

![Full System Overview](../images/01_full_system_overview.png)

---

### 2. Batch Data Flow (Medallion Architecture)

WIDER FACE dataset → MinIO → Spark (Bronze → Silver → Gold) → Great Expectations → Data Warehouse

![Batch Data Flow](../images/02_batch_data_flow.png)

**Key Design Decisions:**
- Medallion Architecture (Bronze/Silver/Gold) for data quality progression
- Great Expectations validation checkpoints between each layer
- DVC for dataset versioning

---

### 3. Stream Data Flow (Real-time)

Camera feed → Kafka → Flink processing → Spark Streaming + KServe/Triton inference

![Stream Data Flow](../images/03_stream_data_flow.png)

**Key Design Decisions:**
- **Claim-Check Pattern**: Images stored in MinIO, only metadata paths sent through Kafka
- Flink for low-latency stream processing, Spark Streaming for enrichment
- Avro serialization via Schema Registry

---

### 4. Change Data Capture (CDC)

Application PostgreSQL → Debezium → Kafka → Spark Merge → Data Warehouse

![CDC Data Flow](../images/04_cdc_data_flow.png)

**Key Design Decisions:**
- Debezium captures row-level changes from PostgreSQL WAL
- Spark performs upsert/merge into the analytical data warehouse
- Enables near-real-time sync between OLTP and OLAP

---

### 5. ML Training Pipeline

Gold data → Kubeflow Pipelines → Katib (AutoML/HPO) → MLflow → TensorRT optimization

![ML Training Pipeline](../images/05_ml_training_pipeline.png)

**Key Design Decisions:**
- Kubeflow Pipelines for reproducible ML workflows
- Katib for hyperparameter optimization (Bayesian, Random, Grid)
- TensorRT INT8 quantization for 3-5x inference speedup

---

### 6. Model Serving (KServe + Triton)

KServe InferenceService → Triton Inference Server → canary deployment (90/10) → monitoring

![Model Serving](../images/06_model_serving.png)

**Key Design Decisions:**
- **KServe** = Kubernetes orchestration (autoscaling, canary, traffic split)
- **Triton** = Inference engine (dynamic batching, TensorRT, model ensemble)
- Combined via `InferenceService` CRD with `runtime: triton`
- Iter8 for A/B testing with statistical significance

---

### 7. RAG / LLM Pipeline

User query → RAGFlow → Weaviate (vector) + Typesense (keyword) → Ollama (TinyLlama 1.1B) → Langfuse tracing

![RAG Pipeline](../images/07_rag_pipeline.png)

**Key Design Decisions:**
- Hybrid search: Weaviate (semantic/vector) + Typesense (keyword/BM25)
- Ollama with TinyLlama 1.1B — runs on CPU, no GPU required
- Langfuse for LLM observability (cost, latency, quality scoring)
- Guardrails AI for input/output validation

---

### 8. SSO & Security Flow

12-step Keycloak SSO flow with Istio EnvoyFilter + OAuth2 Proxy

![SSO Security Flow](../images/08_sso_security_flow.png)

**Key Design Decisions:**
- Keycloak as central identity provider (OIDC)
- OAuth2 Proxy for tools without native OIDC support
- Istio mTLS for service-to-service encryption
- Wildcard cookie on `*.face-detect.dev` for seamless SSO

---

### 9. Drift Detection & Auto-Retrain

Evidently AI monitors → Prometheus alerts → Airflow triggers retraining pipeline

![Drift Detection](../images/09_drift_detection.png)

**Key Design Decisions:**
- Evidently AI for data drift + model performance drift detection
- Prometheus AlertManager triggers Airflow DAG on threshold breach
- Automated retraining with human-in-the-loop approval gate

---

## Technology Stack Summary

### Data Engineering (MLOps Level 2)

| Category | Tool | Purpose |
|----------|------|---------|
| Message Broker | Kafka KRaft + Schema Registry | Event streaming with Avro schemas |
| Stream Processing | Apache Flink | Low-latency real-time processing |
| Batch Processing | Apache Spark | Bronze → Silver → Gold transformations |
| Object Storage | MinIO | S3-compatible data lake |
| Data Quality | Great Expectations | Automated data validation |
| Metadata | DataHub | Data catalog & lineage tracking |
| Orchestration | Apache Airflow | Workflow scheduling & DAG management |
| CDC | Debezium | PostgreSQL change data capture |
| Data Versioning | DVC | Dataset version control |

### ML Platform (MLOps Level 3)

| Category | Tool | Purpose |
|----------|------|---------|
| ML Pipelines | Kubeflow Pipelines | Reproducible ML workflows |
| AutoML/HPO | Katib | Hyperparameter optimization |
| Experiment Tracking | MLflow | Model registry & experiment comparison |
| Model Optimization | TensorRT | INT8 quantization, 3-5x speedup |
| Model Serving | KServe + Triton | Autoscaling inference with dynamic batching |
| Load Testing | k6 + Iter8 | Performance testing & A/B experiments |
| Service Mesh | Istio | mTLS, traffic management, observability |
| Autoscaling | KEDA | Event-driven pod autoscaling |

### RAG / LLM (AI Track 4B)

| Category | Tool | Purpose |
|----------|------|---------|
| RAG Framework | RAGFlow | End-to-end RAG orchestration |
| Vector DB | Weaviate | Semantic/vector search |
| Search Engine | Typesense | Keyword/BM25 search |
| LLM Runtime | Ollama (TinyLlama 1.1B) | Local LLM inference on CPU |
| LLM Observability | Langfuse | Cost, latency, quality tracking |
| Safety | Guardrails AI | Input/output validation |

### Security & Auth

| Category | Tool | Purpose |
|----------|------|---------|
| Identity Provider | Keycloak | Central SSO with OIDC |
| Auth Proxy | OAuth2 Proxy | SSO for non-OIDC tools |
| Service Mesh | Istio + Envoy | mTLS, load balancing, traffic policies |
| Secrets | Kubernetes Secrets + SealedSecrets | Encrypted secret management |

---

## Kubernetes Namespace Map (16 Namespaces)

```
┌─────────────────────────────────────────────────────────────────┐
│                     GKE Cluster                                  │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │ istio-system │  │   auth-ns    │  │   nginx-ingress-ns     │  │
│  │ Istio+Envoy  │  │  Keycloak    │  │   NGINX (→ migrate     │  │
│  │              │  │  OAuth2Proxy │  │    to Istio Gateway)   │  │
│  └─────────────┘  └──────────────┘  └────────────────────────┘  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │ ingestion-ns │  │ streaming-ns │  │   processing-ns       │  │
│  │ Kafka KRaft  │  │ Flink        │  │   Spark               │  │
│  │ SchemaReg    │  │              │  │                       │  │
│  │ Debezium     │  │              │  │                       │  │
│  └──────────────┘  └──────────────┘  └───────────────────────┘  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  storage-ns  │  │validation-ns │  │   metadata-ns         │  │
│  │  MinIO       │  │ Great Expect │  │   DataHub             │  │
│  │  PostgreSQL  │  │              │  │                       │  │
│  └──────────────┘  └──────────────┘  └───────────────────────┘  │
│                                                                  │
│  ┌───────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │orchestration-ns│  │ml-pipeline  │  │  model-serving-ns    │  │
│  │  Airflow       │  │ Kubeflow    │  │  FastAPI + YOLOv11   │  │
│  │               │  │ Katib       │  │                      │  │
│  │               │  │ MLflow      │  │                      │  │
│  └───────────────┘  └─────────────┘  └──────────────────────┘  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│  │  serving-ns  │  │   rag-ns     │  │   monitoring-ns       │  │
│  │ KServe+Triton│  │ RAGFlow      │  │   Prometheus+Grafana  │  │
│  │ RayServe     │  │ Weaviate     │  │   Evidently AI        │  │
│  │ KEDA         │  │ Typesense    │  │                       │  │
│  │              │  │ Ollama       │  │                       │  │
│  │              │  │ Langfuse     │  │                       │  │
│  └──────────────┘  └──────────────┘  └───────────────────────┘  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │  logging-ns  │  │  tracing-ns  │                             │
│  │  ELK Stack   │  │  Jaeger      │                             │
│  └──────────────┘  └──────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Documents Index

### Core Planning Documents

| # | File | Description |
|---|------|-------------|
| 1 | [NEW_PLANS.md](../NEW_PLANS.md) | **Master architecture specification** — Complete tool selections with Docker images/ports, 3 data flow designs, Gold schema SQL, Kafka topic design, KServe YAML, SSO flow, namespace map, implementation phases. Includes ADR fixes: infrastructure sizing (Terraform HCL), resource estimation (~36 cores, ~107GB RAM), PVC/PDB specs, Secrets management, NetworkPolicy, health probes. |
| 2 | [README_EXTENDED.md](../README_EXTENDED.md) | **Step-by-step deployment README** — Follows the project's existing README style with embedded diagrams, code blocks, tables, and command examples for every component. |
| 3 | [ADR_ARCHITECTURE_REVIEW.md](../ADR_ARCHITECTURE_REVIEW.md) | **Architecture Decision Record** — 13-dimension review covering MLOps 1 code issues, data engineering gaps, ML training assessment, model serving, RAG/LLM, security, infrastructure sizing. Score: 7.8/10 with 22 prioritized action items. |

### Interactive Viewers

| # | File | Description |
|---|------|-------------|
| 4 | [architecture_detailed.html](../architecture_detailed.html) | 6-tab interactive HTML: Namespaces, Data Flows, User Roles, SSO, deployKF analysis, Roadmap |
| 5 | [images/data_engineering_pipeline.html](../images/data_engineering_pipeline.html) | Interactive data engineering pipeline diagram |
| 6 | [MLOps_Full_Architecture_Analysis.html](../MLOps_Full_Architecture_Analysis.html) | Full MLOps architecture analysis viewer |
| 7 | [architecture_design.html](../architecture_design.html) | Architecture design interactive viewer |

### Architecture Diagrams (PNG)

| # | File | Description |
|---|------|-------------|
| D1 | [01_full_system_overview.png](../images/01_full_system_overview.png) | All 16 namespaces, 6 user roles, 35+ tools |
| D2 | [02_batch_data_flow.png](../images/02_batch_data_flow.png) | WIDER FACE → MinIO → Spark Medallion → DW |
| D3 | [03_stream_data_flow.png](../images/03_stream_data_flow.png) | Camera → Kafka → Flink → KServe/Triton |
| D4 | [04_cdc_data_flow.png](../images/04_cdc_data_flow.png) | PostgreSQL → Debezium → Kafka → DW |
| D5 | [05_ml_training_pipeline.png](../images/05_ml_training_pipeline.png) | Gold data → Kubeflow → Katib → MLflow → TensorRT |
| D6 | [06_model_serving.png](../images/06_model_serving.png) | KServe canary 90/10 → Triton → monitoring |
| D7 | [07_rag_pipeline.png](../images/07_rag_pipeline.png) | RAGFlow → Weaviate + Typesense → Ollama |
| D8 | [08_sso_security_flow.png](../images/08_sso_security_flow.png) | 12-step Keycloak SSO flow |
| D9 | [09_drift_detection.png](../images/09_drift_detection.png) | Evidently AI → Prometheus → Airflow retrain |

---

## Architecture Decision Record (ADR) Highlights

The ADR review scored the overall architecture **7.8/10** with the following key findings:

### Strengths
- Well-designed data engineering pipeline with Medallion Architecture
- Strong tool selections (Kafka KRaft, KServe+Triton, Keycloak)
- Comprehensive observability stack (Prometheus, ELK, Jaeger, Langfuse)
- Clear namespace separation and RBAC role design

### Critical Issues Identified & Fixed
1. **Infrastructure undersized** → Added multi-node pool Terraform spec (~36 cores, ~107GB RAM)
2. **No persistent storage specs** → Added PVC definitions for all stateful services
3. **Kafka carrying raw images** → Added Claim-Check Pattern (images in MinIO, metadata in Kafka)
4. **Missing health probes** → Added liveness/readiness probe standards for all services
5. **Firewall 0.0.0.0/0 on Jenkins** → Documented fix to restrict to specific IPs
6. **No PodDisruptionBudgets** → Added PDB specs for critical services
7. **No NetworkPolicy** → Added namespace isolation policies

> Full details: [ADR_ARCHITECTURE_REVIEW.md](../ADR_ARCHITECTURE_REVIEW.md)

---

## Implementation Phases

| Phase | Focus | Key Components | Estimated Duration |
|-------|-------|----------------|-------------------|
| **Phase 1** | Infrastructure Upgrade | GKE multi-node, Istio, Keycloak, PVC/PDB | 2-3 weeks |
| **Phase 2** | Data Engineering Core | Kafka, MinIO, Spark, Great Expectations | 3-4 weeks |
| **Phase 3** | Data Engineering Extended | Flink, Debezium CDC, Airflow, DataHub | 2-3 weeks |
| **Phase 4** | ML Training Platform | Kubeflow, Katib, MLflow, TensorRT | 2-3 weeks |
| **Phase 5** | Model Serving | KServe + Triton, KEDA, k6, Iter8 | 2 weeks |
| **Phase 6** | RAG/LLM Pipeline | RAGFlow, Weaviate, Typesense, Ollama, Langfuse | 2-3 weeks |
| **Phase 7** | Drift & Auto-Retrain | Evidently AI, Prometheus alerts, Airflow DAG | 1-2 weeks |
| **Phase 8** | Polish & Documentation | Coursework sections 01-04, final report | 1-2 weeks |

---

## Related Branches

| Branch | Purpose | Status |
|--------|---------|--------|
| `main` | MLOps Level 1 — Production system | ✅ Done |
| `AddDataFlow` | Initial data flow exploration | 🔬 Experimental |
| `planning/mlops-level2-level3` | **This branch** — All planning docs & architecture | 📐 Active |

---

> **Next Steps:** After reviewing all planning documents, implementation will begin on feature branches branched from `main`, following the phased approach above. Each phase will have its own PR with detailed implementation notes.
