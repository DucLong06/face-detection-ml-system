# ADR-001: Full Architecture Review — Face Detection MLOps Extended System

**Status:** Proposed
**Date:** 2026-04-12
**Reviewer:** Architecture Review Agent
**Author:** Hoàng Đức Long (longloe.draft@gmail.com)

---

## Context

This project extends a working MLOps Level 1 system (YOLOv11 face detection on GKE) into a comprehensive MLOps Level 2 (Data Engineering) and Level 3 (Advanced ML Platform + RAG/LLM) architecture. The expansion covers 35+ tools across 16 Kubernetes namespaces for an academic coursework project (AI Track 4A ML System + 4B LLM/Agent).

This ADR reviews the **entire proposed architecture** for correctness, completeness, feasibility, and identifies gaps, risks, and recommendations.

---

## 1. MLOps Level 1 (Current) — Assessment: SOLID ✅

### What exists (verified from code):

| Component | Implementation | Assessment |
|-----------|---------------|------------|
| **FastAPI + YOLOv11** | `api/main.py` — proper OpenTelemetry instrumentation, Jaeger tracing, CORS configured | ✅ Good |
| **Helm chart** | `charts/face-detection/` — deployment, service, ingress templates | ⚠️ Minimal (no HPA, no PDB, no resource tuning) |
| **Terraform** | `infrastructure/terraform/main.tf` — GKE cluster + GCE for Jenkins | ⚠️ Several issues (see below) |
| **Jenkins CI/CD** | `Jenkinsfile` — Test → Build → Deploy pipeline | ✅ Functional |
| **Monitoring** | `helmfile.yaml` — Prometheus, ELK, Jaeger with proper dependency ordering | ✅ Good |
| **Docker image** | `Dockerfile` — based on `tiangolo/uvicorn-gunicorn:python3.10` | ⚠️ Improvable |

### Issues Found in MLOps 1:

**CRITICAL:**

1. **Terraform `google` provider v4.80.0 is outdated** — Current stable is v5.x+. The `google_container_cluster` resource syntax may need updates for newer GKE features (Istio, GPU node pools, etc.). When extending to MLOps 2/3, you will need provider v5+ for features like `google_container_node_pool` GPU accelerators, Workload Identity, and GKE Autopilot support.

2. **GKE cluster has only 1 node (`node_count = 1`) with `e2-medium` (2 vCPU, 4GB RAM)** — This is absolutely insufficient for the planned 50+ pods. Even MLOps 1 with Prometheus + ELK + Jaeger already pushes this limit. You need to plan multi-node pools with different machine types.

3. **Preemptible nodes (`preemptible = true`)** — Fine for cost savings but preemptible VMs can be terminated at any time. For a demo, this is acceptable, but for production-like behavior (especially Kafka, PostgreSQL), you need at least some non-preemptible nodes.

4. **Firewall rule `source_ranges = ["0.0.0.0/0"]`** — Jenkins is exposed to the entire internet on ports 8080 and 50000. This is a significant security risk.

**MEDIUM:**

5. **Deployment has hardcoded `namespace: model-serving`** in the template — Should use `{{ .Release.Namespace }}` for flexibility.

6. **No resource requests/limits tuning** — FastAPI pod is limited to 500Mi/500m which may be tight for YOLOv11 inference on CPU (the model loads into memory).

7. **Docker image uses `tiangolo/uvicorn-gunicorn:python3.10`** — This base image is heavy (~900MB). Consider `python:3.11-slim` with manual uvicorn for smaller size.

8. **No health check probes** in the deployment template (no `livenessProbe`, no `readinessProbe`) — despite having a `/health` endpoint in the API.

9. **CORS `allow_origins=["*"]`** — Overly permissive. Should be restricted when SSO is implemented.

---

## 2. Data Engineering Pipeline (MLOps 2) — Assessment: WELL-DESIGNED ✅ with GAPS ⚠️

### Architecture Strengths:

| Aspect | Assessment | Details |
|--------|-----------|---------|
| **Medallion architecture (Bronze/Silver/Gold)** | ✅ Excellent | Industry standard, clear data quality progression |
| **Kafka KRaft (no Zookeeper)** | ✅ Modern choice | Simplified operations, fewer pods |
| **Schema Registry with Avro** | ✅ Best practice | Prevents schema-related data quality issues |
| **Debezium CDC** | ✅ Correct pattern | WAL-based CDC is reliable and low-overhead |
| **Great Expectations at 2 checkpoints** | ✅ Good design | Validates at Bronze→Silver and Silver→Gold boundaries |
| **DVC + MinIO** | ✅ Good combination | Proper data versioning with S3 backend |
| **DataHub for lineage** | ✅ Strong choice | Auto-ingestion from Spark + Airflow is well thought out |
| **3 distinct data flows** | ✅ Comprehensive | Batch, Stream, and CDC cover all major patterns |

### Gold Schema Assessment:

| Table | Assessment | Issues |
|-------|-----------|--------|
| `fact_detections` | ✅ Good star schema | Missing: `time_id` foreign key to `dim_time`. Also needs partitioning strategy (by date) for query performance. |
| `dim_images` | ✅ Adequate | Missing: `camera_id` column for multi-camera scenarios, `processing_status` (raw/bronze/silver/gold) |
| `dim_models` | ✅ Good | Missing: `training_dataset_version` (link to DVC), `deploy_date`, `is_active` |
| `dim_time` | ✅ Standard | OK as-is, but consider materializing this as a static table (pre-generate 10 years) |
| `feature_image_stats` | ✅ Good ML features | Consider adding: `edge_density`, `color_histogram_entropy`, `aspect_ratio` |

### Gaps & Issues:

**GAP 1: Kafka topic retention and partitioning not specified**
- `face-detection.raw-images` — images are large (100KB-5MB). Kafka is not ideal for large binary payloads. **Recommendation**: Store images in MinIO, send only metadata + MinIO path via Kafka. This is a common pattern called "claim check".
- Missing: retention policy (how long to keep events), cleanup policy (compact vs delete), max message size configuration.

**GAP 2: Spark on Kubernetes resource planning missing**
- Spark Master + 3 Workers requires significant memory. Each Spark worker typically needs 2-4GB RAM minimum. With only 1x `e2-medium` node, this won't run.
- Missing: `spark.kubernetes.executor.request.cores`, `spark.executor.memory` configuration.

**GAP 3: Flink checkpoint storage not defined**
- Flink needs checkpoint storage (MinIO/S3) for exactly-once semantics. Without this, stream processing jobs will lose state on failure.
- Missing: `state.checkpoints.dir`, `state.savepoints.dir` configuration.

**GAP 4: PostgreSQL DW has no backup strategy**
- No `pg_dump` schedule, no WAL archiving, no point-in-time recovery plan.
- For academic demo this is acceptable, but should be documented as a known limitation.

**GAP 5: MinIO has no erasure coding or replication configured**
- Single-node MinIO has no data redundancy. Loss of the pod = loss of all data.
- **Recommendation**: At minimum, document this risk. For demo, use `MINIO_STORAGE_CLASS_STANDARD=EC:0` (no erasure coding) explicitly.

**GAP 6: Airflow executor type not specified**
- The plan mentions "Workers" suggesting CeleryExecutor, but this requires Redis/RabbitMQ as a broker.
- **Recommendation**: For a K8s-native setup, use `KubernetesExecutor` — each task runs in its own pod, no persistent workers needed. This saves resources significantly.

---

## 3. ML Training Pipeline (MLOps 3) — Assessment: AMBITIOUS BUT SOUND ✅

### Architecture Strengths:

| Aspect | Assessment | Details |
|--------|-----------|---------|
| **Kubeflow Pipelines** | ✅ Industry standard | Proper ML workflow orchestration |
| **Katib + RayTune for HPO** | ✅ Powerful combo | Katib orchestrates, RayTune distributes |
| **MLflow for experiment tracking** | ✅ Correct choice | Better than W&B for self-hosted setups |
| **TensorRT INT8 export** | ✅ Optimal for inference | Significant speedup (3-5x over PyTorch) |
| **Model staging workflow** | ✅ Best practice | None→Staging→Production→Archived lifecycle |

### Issues:

**ISSUE 1: Kubeflow + Airflow overlap**
- Both Kubeflow Pipelines and Airflow are workflow orchestrators. This creates confusion about which orchestrator to use for what.
- **Recommendation**: Use Airflow for **data pipelines** (ETL, CDC, data quality) and Kubeflow Pipelines for **ML training workflows** only. Document this boundary clearly.

**ISSUE 2: TensorRT requires NVIDIA GPU**
- The plan acknowledges "GPU hiện tại chưa có" (no GPU yet). TensorRT INT8 calibration and inference require CUDA-capable hardware.
- **Workaround**: Use ONNX Runtime as CPU fallback for demo. Keep TensorRT in the architecture for when GPU is available.
- **Recommendation**: Add a `trt_fallback` flag: if no GPU detected, serve ONNX model via KServe's sklearn/pytorch runtime instead of Triton.

**ISSUE 3: Katib resource requirements**
- Katib spawns multiple trial pods simultaneously (default: 3 parallel). Each trial trains a YOLOv11 model. On CPU, this requires significant resources.
- **Recommendation**: Set `maxTrialCount: 10`, `parallelTrialCount: 1` for resource-constrained environments.

---

## 4. Model Serving (KServe + Triton) — Assessment: CORRECT ARCHITECTURE ✅

### Architecture Strengths:

| Aspect | Assessment | Details |
|--------|-----------|---------|
| **KServe + Triton combined** | ✅ Best practice | KServe for orchestration, Triton for engine |
| **Canary 90/10 split** | ✅ Proper progressive delivery | With Iter8 for auto-promotion |
| **KEDA for autoscaling** | ✅ Good choice | Event-driven scaling based on Kafka lag |
| **RayServe for parallel processing** | ⚠️ May be overkill | See issue below |

### Issues:

**ISSUE 1: RayServe adds significant complexity**
- RayServe requires Ray cluster (head + workers), which is resource-heavy. For pre/post-processing (image decode, NMS), a simpler approach would be a FastAPI sidecar or Triton's built-in ensemble pipeline.
- **Recommendation**: Start without RayServe. Use Triton's ensemble model feature for pre/post-processing. Add RayServe only if you need multi-model ensemble (e.g., face detection → face recognition → attribute extraction).

**ISSUE 2: Triton + KServe version compatibility**
- KServe v0.12 has specific Triton runtime requirements. Ensure `nvcr.io/nvidia/tritonserver:24.01-py3` is compatible with `kserve/kserve-controller:v0.12`.
- **Recommendation**: Pin exact versions and test compatibility before deployment.

**ISSUE 3: k6 load testing needs realistic test data**
- The k6 test script sends requests to the inference endpoint but the `payload` variable is undefined in the example.
- Need to prepare a set of test images in various sizes for realistic load testing.

---

## 5. RAG / LLM Pipeline (AI Track 4B) — Assessment: FEASIBLE WITH CAVEATS ⚠️

### Architecture Strengths:

| Aspect | Assessment | Details |
|--------|-----------|---------|
| **Ollama for local LLM** | ✅ Practical choice | CPU-friendly, easy K8s deployment |
| **RAGFlow as RAG engine** | ✅ Good for demo | Handles chunking, retrieval, generation |
| **Weaviate + Typesense hybrid search** | ✅ Smart design | Vector + keyword for better retrieval |
| **Langfuse for LLM observability** | ✅ Essential | Traces every step of the RAG pipeline |
| **Guardrails for safety** | ✅ Forward-thinking | Important for production LLM systems |

### Issues:

**CRITICAL ISSUE 1: RAGFlow has heavy dependencies**
- RAGFlow requires: Elasticsearch (for document storage), Redis (for task queue), MySQL (for metadata), MinIO (for file storage). This is 4 additional services beyond what's shown.
- **Impact**: Massive resource increase in `rag-ns`.
- **Recommendation**: Consider simpler alternatives: **LangChain + custom FastAPI** or **Haystack** — these have fewer infrastructure dependencies and give you more control. If RAGFlow is used, share existing Elasticsearch and Redis instances from other namespaces.

**CRITICAL ISSUE 2: TinyLlama 1.1B quality for production use**
- At ~5 tokens/second on CPU, TinyLlama will produce 1-2 sentences per 10 seconds. The quality is also limited for complex questions like "analyze drift patterns".
- **Recommendation**: For demo purposes, TinyLlama is fine. But clearly document that this is a placeholder, and in production you would use a larger model (7B+) with GPU or an API-based model.

**ISSUE 3: Embedding model deployment not specified**
- `all-MiniLM-L6-v2` needs to run somewhere — is it inside RAGFlow, a separate pod, or using Weaviate's built-in vectorizer?
- **Recommendation**: Use Weaviate's `text2vec-transformers` module to run the embedding model as a sidecar. This avoids a separate deployment.

**ISSUE 4: What documents to index?**
- The collections listed (detection_reports, model_docs, runbooks) don't exist yet. Need a document generation pipeline to create and update these.
- **Recommendation**: Create an Airflow DAG that generates daily detection reports from PostgreSQL DW and indexes them into Weaviate.

---

## 6. SSO & Security — Assessment: WELL-DESIGNED ✅

### Architecture Strengths:

| Aspect | Assessment | Details |
|--------|-----------|---------|
| **12-step SSO flow** | ✅ Comprehensive | Correct OIDC flow via OAuth2 Proxy |
| **Wildcard cookie on *.face-detect.dev** | ✅ Smart approach | Single login for all tools |
| **Istio mTLS (STRICT)** | ✅ Security best practice | Encrypted pod-to-pod communication |
| **Envoy load balancing per service** | ✅ Well-considered | Different algorithms for different workloads |
| **RBAC with 6 roles** | ✅ Appropriate | Matches the user personas well |

### Issues:

**ISSUE 1: Keycloak is resource-heavy**
- Keycloak requires its own PostgreSQL database, 1-2GB RAM minimum.
- **Alternative**: For academic demo, consider **Dex** (lighter weight, used by deployKF) or **Authentik** as a simpler alternative. But Keycloak is the correct choice for full-featured RBAC.

**ISSUE 2: NGINX Ingress → Istio migration path not defined**
- MLOps 1 uses NGINX Ingress Controller. MLOps 3 uses Istio Ingress Gateway. Both cannot serve the same external IPs simultaneously without planning.
- **Recommendation**: Phase this migration:
  1. Deploy Istio alongside NGINX
  2. Migrate services one-by-one to Istio VirtualServices
  3. Decommission NGINX Ingress last
  4. Update DNS records to point to Istio Gateway IP

**ISSUE 3: Tools with native OIDC vs. requiring OAuth2 Proxy not documented**
- Tools with **native OIDC support** (can directly integrate with Keycloak): Grafana, Airflow, MLflow, Kubeflow, DataHub, MinIO.
- Tools **requiring OAuth2 Proxy**: Kibana, Jaeger, Spark UI, Flink UI, Langfuse, Evidently.
- **Recommendation**: Document this mapping and configure native OIDC where possible (reduces latency and complexity).

---

## 7. Infrastructure & Resource Planning — Assessment: MAJOR GAP 🔴

### The Biggest Risk in This Architecture:

**The current GKE cluster (1x `e2-medium` node, 2 vCPU, 4GB RAM) cannot run even 10% of the planned architecture.**

Resource estimation for the full system:

| Namespace | Est. Pods | Est. CPU (cores) | Est. RAM (GB) |
|-----------|-----------|-------------------|---------------|
| istio-system | 3 | 2 | 4 |
| auth-ns | 3 | 1.5 | 4 |
| model-serving-ns | 1 | 0.5 | 1 |
| serving-ns | 5 | 4 | 10 |
| ingestion-ns | 5 | 3 | 8 |
| streaming-ns | 3 | 2 | 6 |
| processing-ns | 4 | 4 | 12 |
| storage-ns | 4 | 2 | 8 |
| validation-ns | 2 | 1 | 2 |
| metadata-ns | 4 | 2 | 6 |
| orchestration-ns | 4 | 2 | 6 |
| ml-pipeline-ns | 5 | 3 | 8 |
| rag-ns | 6 | 4 | 12 |
| monitoring-ns | 6 | 3 | 10 |
| logging-ns | 4 | 2 | 8 |
| tracing-ns | 1 | 0.5 | 2 |
| **TOTAL** | **~60** | **~36 cores** | **~107 GB** |

**Recommendation for GKE node pools:**

```hcl
# Node pool 1: General workloads (data engineering, orchestration)
resource "google_container_node_pool" "general" {
  name       = "general-pool"
  node_count = 3
  node_config {
    machine_type = "e2-standard-4"  # 4 vCPU, 16GB RAM
    disk_size_gb = 100
  }
}

# Node pool 2: ML workloads (training, serving) — if GPU available
resource "google_container_node_pool" "ml" {
  name       = "ml-pool"
  node_count = 1
  node_config {
    machine_type = "n1-standard-4"  # 4 vCPU, 15GB RAM
    guest_accelerator {
      type  = "nvidia-tesla-t4"
      count = 1
    }
    disk_size_gb = 100
  }
}

# Node pool 3: Stateful services (Kafka, PostgreSQL, Elasticsearch)
resource "google_container_node_pool" "stateful" {
  name       = "stateful-pool"
  node_count = 2
  node_config {
    machine_type = "e2-standard-4"
    disk_size_gb = 200  # More disk for data storage
    preemptible  = false  # Stateful services should NOT be preemptible
  }
}
```

**Estimated monthly cost** (GCP us-central1):
- 3x e2-standard-4 (general): ~$290/month
- 1x n1-standard-4 + T4 GPU (ml): ~$450/month
- 2x e2-standard-4 (stateful): ~$193/month
- **Total: ~$933/month** (or ~$310/month without GPU)

**For academic demo** — scale down approach:
- Use 2x `e2-standard-8` (8 vCPU, 32GB) nodes: ~$390/month
- Deploy services incrementally, not all at once
- Use preemptible nodes where possible

---

## 8. Coursework Completeness Check

| Section | Requirement | Status | Assessment |
|---------|------------|--------|------------|
| **01: Data Generator** | Custom generator with configurable data issues | ⚠️ Designed, not implemented | Generator CLI spec is good. Need implementation: `generator.py`, `challenges/`, `configs/`. |
| **02: Gold Schema** | Fact/dimension tables + SLAs + feature tables | ✅ Designed | Schema is solid. Add `time_id` FK, partitioning, and `camera_id` column. |
| **03: Drift Detection** | Feature drift scenarios + detection pipeline | ✅ Designed | 4 scenarios defined. Evidently AI integration clear. Need: actual drift thresholds and Grafana dashboard JSON. |
| **04A: ML System** | End-to-end ML pipeline | ✅ Comprehensive | Training → Serving → Monitoring → Retrain loop is complete. |
| **04B: LLM/Agent** | RAG pipeline with local LLM | ✅ Designed | RAGFlow + Ollama + Weaviate architecture is sound. Quality limitations documented. |
| **Offline challenges** | Data skew, high cardinality, schema evolution | ✅ Designed | All 3 covered in generator spec. |
| **Streaming challenges** | Bursty traffic, late arrivals | ✅ Designed | Both covered with specific parameters. |
| **Optional challenges** | Duplicates, missing values, out-of-order | ✅ Designed | All 3 covered as optional flags. |

---

## 9. Tool Overlap & Redundancy Analysis

| Overlap | Assessment | Recommendation |
|---------|-----------|----------------|
| **Airflow vs Kubeflow Pipelines** | Both are workflow orchestrators | Use Airflow for data ETL, Kubeflow for ML training. Document boundary. |
| **NGINX Ingress vs Istio Gateway** | Both are ingress controllers | Migrate to Istio Gateway. Remove NGINX after migration. |
| **Prometheus+Grafana vs Evidently AI** | Both monitor metrics | Prometheus for system metrics, Evidently for ML-specific drift. Complementary. ✅ |
| **ELK vs Langfuse** | Both handle logs/traces | ELK for system logs, Langfuse for LLM traces only. Complementary. ✅ |
| **Jaeger vs Istio tracing** | Both do distributed tracing | Use Jaeger. Istio can forward traces to Jaeger via Zipkin protocol. ✅ |
| **Flink vs Spark Streaming** | Both process streams | Flink for real-time validation (low latency), Spark Streaming for micro-batch aggregation. Correct split. ✅ |
| **Redis (Airflow) vs Redis (cache)** | Two Redis instances | Use ONE Redis with different databases: db0 for Airflow, db1 for feature cache. |
| **PostgreSQL (app) vs PostgreSQL (DW) vs PostgreSQL (Airflow) vs PostgreSQL (Keycloak)** | 4 PostgreSQL instances | Consider using ONE PostgreSQL with multiple databases, or use CloudSQL for managed service. Separate instances are OK for isolation. |

---

## 10. Missing Components (Recommendations)

| # | Missing Component | Priority | Recommendation |
|---|-------------------|----------|----------------|
| 1 | **PodDisruptionBudget** for all stateful services | HIGH | Kafka, PostgreSQL, Elasticsearch need PDBs to prevent data loss during node drains |
| 2 | **NetworkPolicy** YAML files | HIGH | Currently no network isolation between namespaces. Any pod can talk to any pod. |
| 3 | **ResourceQuota** per namespace | MEDIUM | Prevent any single namespace from consuming all cluster resources |
| 4 | **HorizontalPodAutoscaler** for FastAPI, Spark Workers | MEDIUM | Currently fixed replicas:1 |
| 5 | **Persistent Volume Claims** for MinIO, PostgreSQL, Elasticsearch, Kafka | HIGH | Data must survive pod restarts. Current plan doesn't show PVC specs. |
| 6 | **Secrets management** | HIGH | Database passwords, API keys, S3 credentials need K8s Secrets or external vault. Currently no secrets strategy. |
| 7 | **Backup & restore procedures** | MEDIUM | No backup for PostgreSQL DW, MinIO data, Kafka topics |
| 8 | **Rollback procedures** | MEDIUM | What happens if a Helm upgrade fails? Document rollback commands. |
| 9 | **Cost estimation document** | LOW | For academic presentation, showing you've considered costs demonstrates maturity |
| 10 | **Disaster recovery plan** | LOW | Even a simple "if X fails, do Y" document adds value |

---

## 11. Overall Verdict

### Scorecard:

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Architecture Design** | 9/10 | Comprehensive, modern, follows industry patterns |
| **Tool Selection** | 8/10 | Mostly excellent choices. RayServe may be overkill. RAGFlow dependencies heavy. |
| **Data Flow Design** | 9/10 | Three distinct flows (Batch/Stream/CDC) are well-designed and complete |
| **Security Design** | 8/10 | SSO + mTLS + RBAC is solid. Missing: NetworkPolicies, Secrets management |
| **Scalability Design** | 7/10 | KEDA + canary is good. But GKE cluster sizing is completely inadequate. |
| **Feasibility** | 6/10 | Current hardware (1x e2-medium) cannot run >10% of this. Need 6+ larger nodes. |
| **Coursework Coverage** | 9/10 | All 4 sections covered. Section 01 (Data Generator) needs implementation. |
| **Documentation** | 9/10 | README_EXTENDED + NEW_PLANS + diagrams are excellent. |
| **Implementation Readiness** | 5/10 | Design is complete, but zero Helm charts/configs exist for new components. |

### **Overall: 7.8/10 — Strong design, needs infrastructure planning and implementation.**

---

## 12. Action Items (Prioritized)

### Must-Do Before Implementation:

1. [ ] **Resize GKE cluster** — Minimum 2x `e2-standard-8` nodes (or 3x `e2-standard-4`)
2. [ ] **Create PersistentVolumeClaims** for MinIO, PostgreSQL, Elasticsearch, Kafka
3. [ ] **Add health probes** (liveness + readiness) to existing FastAPI deployment
4. [ ] **Fix Terraform provider** — Upgrade to google provider v5+
5. [ ] **Fix firewall rule** — Restrict Jenkins access to specific IPs
6. [ ] **Add Kubernetes Secrets** for all database passwords, API keys
7. [ ] **Add Kafka claim-check pattern** — Don't send raw images through Kafka; send MinIO paths

### Should-Do During Implementation:

8. [ ] **Add PodDisruptionBudgets** for Kafka, PostgreSQL, Elasticsearch
9. [ ] **Add NetworkPolicies** per namespace
10. [ ] **Add ResourceQuotas** per namespace
11. [ ] **Use KubernetesExecutor** for Airflow instead of CeleryExecutor
12. [ ] **Add `time_id` FK** to `fact_detections` schema
13. [ ] **Plan NGINX → Istio migration** as a phased approach
14. [ ] **Document which tools use native OIDC vs OAuth2 Proxy**
15. [ ] **Consider replacing RayServe** with Triton ensemble pipeline
16. [ ] **Share Redis instance** across Airflow and feature cache (separate databases)
17. [ ] **Implement Data Generator** (`data_generator/generator.py`) — coursework Section 01

### Nice-to-Have:

18. [ ] **Add Grafana dashboard JSON** for drift detection visualization
19. [ ] **Add cost estimation** for GCP resources
20. [ ] **Consider CloudSQL** for managed PostgreSQL (reduces operational burden)
21. [ ] **Add CI/CD stages** for data pipeline testing (Great Expectations in Jenkins)
22. [ ] **Consider RAGFlow alternatives** (LangChain + FastAPI) if resource-constrained

---

## 13. Conclusion

Kiến trúc này rất **tham vọng và toàn diện** — nó cover gần như tất cả các khía cạnh của một hệ thống MLOps hiện đại. Thiết kế data flow (Batch/Stream/CDC), ML pipeline (Kubeflow→MLflow→KServe+Triton), và security (Keycloak+Istio mTLS) đều follow best practices.

**Điểm mạnh nhất**: Documentation xuất sắc, tool selection phù hợp, data flow design rõ ràng.

**Điểm cần cải thiện nhất**: Infrastructure sizing (cluster quá nhỏ), missing operational configs (PVC, PDB, NetworkPolicy, Secrets), và chưa có implementation code cho các component mới.

**Khuyến nghị**: Bắt đầu triển khai theo phase, mỗi phase validate trước khi sang phase tiếp. Không deploy tất cả 50+ pods cùng lúc.

---

*Architecture review completed: 2026-04-12*
*Tools analyzed: 35+ tools across 16 namespaces*
*Code reviewed: Terraform, Helm charts, FastAPI, Jenkinsfile, Dockerfile*
