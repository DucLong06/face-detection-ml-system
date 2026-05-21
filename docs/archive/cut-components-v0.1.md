# Cut Components — v0.1 → v0.2 YAGNI Refactor

- Date: 2026-05-21
- Rationale: portfolio MLOps project (single dev, face detection use case, ~10 req/s). YAGNI audit (`plans/reports/researcher-260521-1023-yagni-tech-validation.md`) identified 60% stack overkill.
- Approach: archive (not delete) cho audit trail + interview defensibility.

## Cut Components

### RAG/LLM Stack — fully cut
- **RAGFlow** — RAG orchestration framework (irrelevant to face detection)
- **Ollama (TinyLlama 1.1B)** — on-device LLM (irrelevant)
- **Weaviate** — vector DB (irrelevant)
- **Typesense** — fast search (irrelevant)
- **Langfuse** — LLM observability (irrelevant)
- **Rationale**: face DETECTION (computer vision) ≠ LLM/RAG use case. Pure tool stacking. Removes 5 components, ~10 pods, entire `rag-ns` namespace.

### Inference Serving — consolidate to 1
- **Triton Inference Server** — redundant với KServe
- **RayServe** — redundant với KServe
- **RayTune** — redundant với Katib (HPO)
- **Rationale**: pick one framework. Keep FastAPI (L1) + optional KServe (L3 demo). 3 frameworks = over-engineering, interview red flag.

### Streaming — Spark covers
- **Apache Flink (JobManager + TaskManager)** — overlaps Spark Structured Streaming
- **Rationale**: Spark Structured Streaming handles ~10 req/s easily. Flink adds complexity without clear win for this workload.

### Orchestration — pick one boundary
- **Apache Airflow (Webserver + Scheduler + K8sExecutor)** — overlaps Kubeflow Pipelines
- **ArgoCD** — Jenkins + helm covers CD for single-cluster scope
- **deployKF** — abstraction overhead, unnecessary
- **Rationale**: Kubeflow Pipelines covers ML orchestration. ETL DAGs (if needed) can run as Kubeflow components. 4 orchestrators = decision fatigue.

### Load Testing — pick one
- **Locust** — k6 covers same scenarios
- **Rationale**: k6 modern, JS-based, single binary, better for CI integration.

### Artifact Tracking — consolidate
- **DVC** — MLflow Model Registry handles versioning
- **Rationale**: MLflow + MinIO covers experiment artifacts + dataset versioning via S3-compatible storage.

### Metadata Catalog — overkill
- **DataHub** — overkill cho 1-model project
- **Rationale**: DataHub designed cho enterprise data catalog (100s of datasets). MLflow registry sufficient cho 1 face detection model.

### Gateway — consolidate to 1
- **NGINX Ingress Controller** — Istio Gateway covers L7 routing
- **Rationale**: Istio mesh (L3) provides ingress gateway. NGINX in parallel = redundant. Pick Istio cho mTLS + traffic management story.

### Auth — trim heavy
- **Keycloak (full IdP + PostgreSQL backing)** → replaced với **Dex**
- **Rationale**: Dex is lightweight OIDC IdP, federates to GitHub/Google. Keycloak's enterprise features (user management, custom themes) unused in portfolio context. Saves 2 pods + PostgreSQL instance.

## Kept (Justified)

| Category | Component | Rationale |
|---|---|---|
| Inference | FastAPI + YOLOv11 | L1 baseline, working |
| Inference | KServe (optional L3) | Demo model serving advanced patterns |
| Streaming | Kafka + KRaft + Schema Registry + Debezium | Demo event-driven + CDC |
| Batch | Spark + Great Expectations | Demo medallion + data quality |
| Storage | MinIO + PostgreSQL DW + Redis | Object + DW + cache trio |
| ML | Kubeflow Pipelines + Katib + MLflow | Demo training orchestration + HPO + registry |
| Auth | Dex + OAuth2 Proxy | Demo OIDC SSO flow |
| Gateway | Istio | mTLS + ingress |
| Observability | Prometheus + Grafana + ELK + Jaeger + Evidently | 3 pillars + drift detection |
| DevOps | Jenkins + Terraform + Helm | CI/CD + IaC |
| Load test | k6 | Synthetic traffic gen |

**Total kept: ~22 components / 8-10 namespaces** (down from 40 / 16).

## Impact

| Metric | Before | After | Delta |
|---|---|---|---|
| Components | 40 | 22 | -18 (-45%) |
| Namespaces | 16 | 9 | -7 |
| Estimated RAM | 107 GB | 35-40 GB | -67 GB |
| Pods | ~50 | ~22 | -28 |
| GCP cost/mo (est) | $1118 | $311 | -$807 |
| Diagrams | 11 | 8 | -3 (07 RAG, 10 LLM Sec, 11 Enhanced RAG) |

## Diagrams Removed
- `full-07.png` (RAG Pipeline)
- `full-10.png` (LLM Security Architecture)
- `full-11.png` (Enhanced RAG Pipeline)

## Revival Path
If need to demo LLM/RAG skills in future iteration:
- Spin separate repo `face-detect-rag-extension` 
- Reference this archive doc to know what was cut and why
- Avoid mixing CV + LLM in same portfolio project (muddles narrative)
