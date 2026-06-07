---
name: mlops-l2-l3-rag-complete-build
date: 2026-06-04 22:13
updated: 2026-06-05 09:10
status: pending
type: master-roadmap (best-of-breed MLOps L2→L3 + RAG)
env: single Kubernetes cluster (ample hardware), namespace-isolated
scope: Full L3 + RAG, best-of-breed (no resource compromise)
---

# Master Plan — Best-of-Breed MLOps L2/L3 + RAG (single cluster, namespace-isolated)

## Goal
Hoàn thiện face-detect-gke từ **L1 (done)** → data pipeline (L2) → ML platform + serving + drift-loop (L3) → RAG (4B), bằng **stack tốt nhất 2026**, trên **1 cluster K8s phần cứng thoải mái**, chia **namespace chuẩn**. Output đợt này = **plan + sơ đồ để review** (chưa deploy).

> **Decisions (user-confirmed):** env = single best-of-breed cluster (bỏ hybrid kind/GKE) · scope = Full L3+RAG · output = plan+diagrams · vector DB = **Qdrant** · logs = **ELK** · tracing = **Jaeger** · data versioning = **lakeFS**.

## Context Reports
- Stack validation 2026: [researcher-260604-2213-mlops-l2-l3-stack-validation-report.md](researcher-260604-2213-mlops-l2-l3-stack-validation-report.md)
- Reality-check + design-cut brainstorms: brainstorm/reality-check reports (xem git history)
- Canonical full design (50-tool gốc): `git show origin/planning/mlops-level2-level3:NEW_PLANS.md`

## Architecture review doc + diagrams
- **Review doc:** [`./README.md`](./README.md)
- **Hướng dẫn tự vẽ sơ đồ (per-zone spec + steps + style):** [`diagram-drawing-guide.md`](./diagram-drawing-guide.md)
- **Drill-down per-zone (editable .drawio + png):** `diagrams/icons/drilldown/zone-1..7-*.drawio`
- **Quyết định kiến trúc đã chốt (research):** Iceberg catalog = **lakeFS REST Catalog** (bỏ Nessie) · GPU = **shared pool MIG + Kueue** · Drift loop = **human-approval gate trước Prod**.
- **Overview (hand-laid swimlane, hall-of-fame style):** `diagrams/icons/01-overview.drawio` (**editable** trong draw.io, logo nhúng base64) + `01-overview.png` (preview). Numbered steps (1)→(10) + named artifacts. Builder: `overview_builder.py`.
- **Sơ đồ detail (auto-layout, logo thật, no overlap):** `02-data-pipeline` `03-ml-platform` `04-serving` `05-drift-loop` `06-rag` `07-platform-observability` + `08-namespace-topology`. Generator: `diag2_*.py` + `prep_icons*.py` (`diagrams` lib + Graphviz).

## Tracks (theo namespace tier)

| # | Track | Namespaces | Tools best-of-breed | File |
|---|---|---|---|---|
| T0 | Platform foundation | `istio-system` `auth` `argocd` `kyverno` `vault` `external-secrets` `cert-manager` | Istio ambient, Keycloak+OAuth2 Proxy, ArgoCD, Kyverno, Vault+ESO, cert-manager | [phase-t0-platform-foundation.md](./phase-t0-platform-foundation.md) |
| T1 | Data pipeline (L2) | `data-ingestion` `data-streaming` `data-processing` `data-storage` `data-quality` `data-orchestration` `data-catalog` | Kafka(Strimzi)+Schema Registry+Debezium, Flink, Spark, MinIO+**Iceberg**+**lakeFS**, **Trino**, PostgreSQL, Redis, Great Expectations, Airflow+Argo Events, **OpenMetadata** | [phase-t1-data-pipeline.md](./phase-t1-data-pipeline.md) |
| T2 | ML platform (L3) | `ml-platform` | **Kubeflow** (Pipelines/Notebooks/Katib/Profiles), MLflow, **Feast**, **Ray/KubeRay**, ONNX/TensorRT | [phase-t2-ml-platform.md](./phase-t2-ml-platform.md) |
| T3 | Serving (L3) | `model-serving` | KServe + **Knative** + Triton/TensorRT (GPU), KEDA, Flagger, **Iter8** | [phase-t3-serving.md](./phase-t3-serving.md) |
| T4 | **Drift→Retrain loop ★** | `ml-monitoring` + `monitoring` + `data-orchestration` + `ml-platform` | Evidently + **Alibi Detect** → Prometheus/Thanos → Alertmanager → Argo Events → Kubeflow retrain → MLflow → Flagger canary | [phase-t4-drift-retrain-loop.md](./phase-t4-drift-retrain-loop.md) |
| T5 | RAG/LLM (4B) | `rag` | **vLLM** (GPU), RAGFlow, **Qdrant**, Typesense, **NeMo Guardrails**, Langfuse | [phase-t5-rag-llm.md](./phase-t5-rag-llm.md) |
| T6 | Observability + Security + SSO + Governance | `monitoring` `logging` `tracing` `auth` `data-catalog` | Prometheus+**Thanos**+Grafana, **ELK** (ES+Kibana+Logstash+Filebeat), **Jaeger**+OTel Collector, Keycloak 6-role RBAC, OpenMetadata RBAC | [phase-t6-observability-security.md](./phase-t6-observability-security.md) |

**Critical path:** T0 → T1 → T2 → T3 → **T4** → T6. T5 (RAG) song song/cuối (khác domain).

## Namespace taxonomy (chia chuẩn — chi tiết `08-namespace-topology`)
~20 namespace, mỗi cái = 1 domain, không trộn vai trò: platform (6) · data (7) · ml (3) · rag (1) · observability (3).

## Governance baseline (áp MỌI namespace, ép bằng Kyverno)
ResourceQuota+LimitRange · NetworkPolicy default-deny · Istio PeerAuthentication mTLS STRICT · AuthorizationPolicy allow-list · scoped RBAC+ServiceAccount · PodDisruptionBudget (stateful) · labels `team/tier/cost-center/data-classification` · PriorityClass.

## SSO + RBAC (Keycloak → mọi tool)
1 IdP Keycloak, 6 realm roles: `user` `data-analyst` `data-scientist` `data-engineer` `ml-engineer` `admin` → map sang Kubeflow Profiles + OpenMetadata policies + Grafana/MLflow/Airflow/Kibana qua OIDC. SSO 1 cookie `*.face-detect.dev`.

## Best-of-breed upgrades so với bản trước
| Vai trò | Cũ (hybrid/nhẹ) | Mới (best) |
|---|---|---|
| Orchestrator ML | Argo (kind) | **Kubeflow full** |
| Mesh | Linkerd | **Istio ambient** |
| Logs | Loki | **ELK** |
| Table format | Parquet thô | **Apache Iceberg** |
| Query | — | **Trino** |
| Data versioning | DVC | **lakeFS** |
| Feature store | — | **Feast** |
| Distributed train | — | **Ray/KubeRay** |
| LLM serving | Ollama CPU | **vLLM GPU** |
| Vector DB | Weaviate | **Qdrant** |
| Catalog/governance | (cut) | **OpenMetadata** |
| GitOps/policy/secrets | — | **ArgoCD + Kyverno + Vault** |
| Metrics LT | — | **Thanos** |

## Reuse assets
- L1 hardening (probes/HPA/RBAC/NetworkPolicy/PDB/quota) → nền T0.
- Kafka Helm chart (`AddDataFlow` branch) → khởi điểm `data-ingestion` (nâng lên Strimzi operator).

## Success Criteria (đợt plan này)
- [x] Master plan + 7 phase, mỗi tool có vai trò + namespace
- [x] Namespace taxonomy + governance baseline
- [x] Bộ 8 sơ đồ icon (overview ngang + 6 detail + namespace topology)
- [ ] User review kiến trúc + chức năng tool (đang chờ)

## Out of Scope (đợt này)
- Deploy thật / Helm / manifest mới (chỉ plan + sơ đồ)
- Tuning chi tiết resource per-tool (làm khi build)

## Open Questions
1. GPU node pool: bao nhiêu GPU cho train (Ray/Kubeflow) + serve (Triton) + vLLM (RAG)? 3 nơi dùng GPU.
2. Ground-truth cho drift loop: manual label / active learning?
3. MLflow Staging→Production: auto theo threshold hay human-approval (Kubeflow approval step)?
4. RAG: deploy thật hay giữ ở mức design (khác domain)? Tách repo riêng?
5. Iceberg catalog: REST catalog / Nessie / Hive Metastore — chọn cái nào?
