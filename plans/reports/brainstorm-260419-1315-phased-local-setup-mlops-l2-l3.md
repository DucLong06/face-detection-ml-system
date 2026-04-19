# Brainstorm Report — Phased Local Setup cho MLOps L2+L3

**Date:** 2026-04-19 13:15 ICT
**Author:** Solution Brainstormer (Claude)
**Scope:** Review commit PR #5 (MLOps L2+L3 plan) + diagram redraw strategy + local feasibility on user machine + phased namespace rollout
**Related report:** `brainstorm-260416-0000-mlops-level2-level3-reality-check.md`

---

## 1. Problem Statement

User vừa merge PR #5 (`planning/mlops-level2-level3`) thêm kế hoạch nâng cấp hệ thống face-detection từ MLOps L1 (đang chạy GKE) lên L2 (Data Engineering) + L3 (Advanced ML Platform + RAG/LLM). Cần:

1. Review thiết kế đã ổn chưa, có buildable không.
2. Hình vẽ trong `images/*.png` đang dense + khó đọc — cần phương án vẽ lại.
3. Cấu hình máy local (i5-10400, 38GB RAM, no GPU, 13GB free disk) có đủ không.
4. Mục tiêu: **setup đủ ở local** theo từng **namespace/phase riêng lẻ** trước (không cần chạy mượt full).

---

## 2. Design Assessment — PR #5

### 2.1 Verdict tổng thể: 7.8/10 (theo ADR đã có), OK để build

**Điểm mạnh** (industry-aligned, xác nhận qua research 2026):
- Medallion Bronze/Silver/Gold — standard.
- Kafka KRaft + Schema Registry + Debezium CDC — đúng pattern hiện đại.
- Airflow (batch ETL) + Kubeflow Pipelines (ML training) — boundary đúng theo best practice 2026 ([MLflow+Kubeflow+Airflow hybrid enterprise MLOps](https://uplatz.com/blog/integrating-mlflow-kubeflow-and-airflow-for-a-composable-enterprise-mlops-platform/)).
- KServe + Triton + canary/Iter8 — đúng L3 ([end-to-end K8s MLOps 2026](https://medium.com/@nsalexamy/building-a-production-ready-end-to-end-mlops-pipeline-on-kubernetes-full-walkthrough-aeb5b87cad60)).
- Claim-check pattern cho Kafka + MinIO — đã fix đúng.
- ADR section 12-20 đã fix nhiều gap (PVC, Secrets, NetworkPolicy, Istio migration, Airflow KubernetesExecutor).

**Điểm yếu cần nhớ khi build**:
- RayServe overkill → Triton ensemble thay thế.
- RAGFlow kéo theo ES+Redis+MySQL+MinIO phụ → cân nhắc **LangChain + FastAPI custom** hoặc **Haystack** đơn giản hơn.
- TinyLlama 1.1B chỉ cho demo (5 tok/s CPU).
- TensorRT cần GPU → dùng ONNX Runtime làm fallback trên CPU local.
- Keycloak nặng → có thể dùng **Dex** cho local, giữ Keycloak cho prod.
- Istio service mesh skip ở local (quá heavy cho 38GB) → dùng nginx-ingress có sẵn.

**Kết luận**: Thiết kế buildable, KHÔNG cần sửa kiến trúc gốc. Chỉ cần triển khai **từng phase**, không nhồi hết cùng lúc.

---

## 3. Diagram Redraw Strategy — Mermaid

### 3.1 Vấn đề với PNG hiện tại
- Dark-theme infographic-style, nhiều box chồng chéo, chữ nhỏ.
- Không diff được trong git (binary).
- Không rõ flow source→sink, layout ngang làm mất logic.
- File lớn (355KB–503KB/ảnh × 13 ảnh ~ 3MB repo bloat).

### 3.2 Phương án chọn: **Mermaid v11** (text-in-markdown)

**Lý do**:
- Git-trackable, review được trong PR.
- GitHub render native trong `.md`.
- Dễ sửa khi kiến trúc thay đổi.
- Skill `mermaidjs-v11` hỗ trợ v11 syntax (flowchart, C4, sequence, state, ER).
- `/preview --diagram` render local + Mermaid.

**Diagram cần vẽ lại (11 PNG → 11 Mermaid)**:

| # | PNG cũ | Kiểu Mermaid đề xuất |
|---|---|---|
| 01 | full_system_overview | **C4 Container diagram** (16 namespaces grouped by layer) |
| 02 | batch_data_flow | flowchart LR (Bronze→Silver→Gold) |
| 03 | stream_data_flow | flowchart LR (Camera→Kafka→Flink→Redis) |
| 04 | cdc_data_flow | flowchart LR (Postgres WAL→Debezium→Kafka→Spark) |
| 05 | ml_training_pipeline | flowchart TD (Kubeflow DAG) |
| 06 | model_serving | flowchart LR (Client→Istio→KServe→Triton) |
| 07 | rag_pipeline | flowchart LR (Query→Retriever→LLM→Response) |
| 08 | sso_security_flow | sequenceDiagram (OIDC 12-step) |
| 09 | drift_detection | flowchart TD (Evidently + Grafana alerts) |
| 10 | llm_security_architecture | flowchart LR (Guardrails layers) |
| 11 | enhanced_rag_pipeline | flowchart LR (Hybrid search Weaviate+Typesense) |

**Bonus**: 1 overview Excalidraw đẹp cho slide coursework (optional, sau).

### 3.3 Lưu trữ
- Lưu trong `docs/diagrams/*.md` (mỗi file 1 diagram + caption).
- Reference từ `NEW_PLANS.md`, `README_EXTENDED.md` thay cho `images/*.png`.
- Giữ lại PNG trong `images/` cho offline viewing, không xoá.

---

## 4. Local Machine Feasibility

### 4.1 Thực trạng

| Resource | Có | Full plan cần | Tier A (đề xuất) |
|---|---|---|---|
| vCPU | 12 | 36 | **8 cho cluster** |
| RAM | 38GB (29GB free) | 107GB | **24GB cho cluster** |
| GPU | None | T4 | None — CPU only |
| Disk free | **13GB / 95GB (86%)** ⚠️ | 640GB | **60GB** sau prune |

### 4.2 Blocker cần xử lý ngay

🔴 **Disk 86% full** — không thể pull thêm image (Kafka 500MB, Spark 800MB, Airflow 1.2GB, MinIO 200MB, Kubeflow 3GB+).

**Kế hoạch dọn (user đã chọn Prune Docker)**:
```bash
docker system df                    # check reclaimable ~50GB
docker system prune -a --volumes    # giải phóng 43–50GB
# Bonus nếu cần:
du -sh ~/.config ~/.cache ~/.vscode-server  # check manual
```
Sau prune, disk free sẽ lên ~55–60GB → đủ cho Tier A.

### 4.3 Kết luận khả thi

- **Tier A (Data Pipeline + Serving + Monitoring)**: khả thi, ~20–24GB RAM, 8 vCPU.
- **Tier B (thêm Kubeflow / DataHub / RAG)**: chỉ chạy được 1 tier B tại 1 thời điểm, tắt tier khác.
- **Tier C (Istio mesh, Keycloak full, Kubeflow full, RAGFlow)**: skip local → GKE.

---

## 5. Recommended Approach — Phased Namespace Rollout trên Kind

User đã chọn: **Kind + dev từng phase riêng lẻ**.

### 5.1 Caveat quan trọng về Kind

Theo research: **Kind không hỗ trợ NodePort/LoadBalancer native** — cần config `extraPortMappings` trong cluster config để expose ingress ([Kafka on Kind dev guide](https://medium.com/@martin.hodges/deploying-kafka-on-a-kind-kubernetes-cluster-for-development-and-testing-purposes-ed7adefe03cb)). Nếu cần truy cập Kafka từ laptop (producer CLI test), phải map cổng 9092. Với browser-only (Grafana/Airflow UI), dùng `kubectl port-forward` là đủ.

### 5.2 Phase Plan — 5 phase tuần tự

Mỗi phase = 1 namespace group, test độc lập, rồi tắt trước khi sang phase kế tiếp (tiết kiệm RAM).

#### **Phase 0 — Platform Base** (~4GB RAM)
Namespaces: `ingress-nginx`, `cert-manager` (optional), `monitoring-ns` (Prometheus + Grafana light).
- Kind cluster config: 1 control-plane + 2 workers, `extraPortMappings` 80/443/9092/8080/3000.
- `kind-config.yaml` + kubectl context setup.
- Grafana port-forward test.

#### **Phase 1 — Data Storage** (~6GB RAM)
Namespace: `storage-ns` (MinIO 1 pod + PostgreSQL 1 pod + Redis 1 pod).
- PVC hostPath local, PVC size nhỏ: MinIO 20Gi, Postgres 10Gi, Redis 1Gi.
- Seed test bucket `face-detection/raw` + test DB schema `dw_gold`.
- Smoke test: upload 1 ảnh qua `mc` CLI, query `psql`.

#### **Phase 2 — Ingestion & Processing** (~10GB RAM)
Namespaces: `ingestion-ns` (Kafka KRaft 1 broker + Schema Registry), `processing-ns` (Spark 1 master + 1 worker), `validation-ns` (Great Expectations).
- Kafka config: `message.max.bytes=1MB`, retention 24h (demo), RF=1, partitions=3.
- Spark submit batch job đọc MinIO Bronze → Silver.
- Great Expectations checkpoint `bronze_to_silver`.
- Smoke test: producer gửi metadata event → consumer đọc.

#### **Phase 3 — Orchestration** (~4GB RAM — thêm vào Phase 2 đang chạy)
Namespace: `orchestration-ns` (Airflow + KubernetesExecutor).
- Dùng `KubernetesExecutor` (không Celery) — tiết kiệm RAM, đúng ADR fix.
- 1 DAG test: trigger Spark batch job + Great Expectations validation.

#### **Phase 4 — Model Serving + Drift** (~6GB RAM — TẮT Phase 2/3 nếu OOM)
Namespaces: `model-serving-ns` (existing FastAPI+YOLO), `ml-pipeline-ns` (MLflow tracking + model registry — không cài full Kubeflow local), `monitoring-ns` (Evidently AI sidecar).
- MLflow chạy standalone với SQLite backend + MinIO artifacts.
- Drift detection CronJob đọc Gold PostgreSQL, gửi Prometheus metrics.

#### **Phase 5 (optional) — RAG Light** (~8GB RAM — TẮT các phase khác)
Namespace: `rag-ns` (Ollama `tinyllama:1.1b` + Weaviate embedded mode, không RAGFlow).
- LangChain + FastAPI custom thay RAGFlow → giảm 4 services phụ.
- Weaviate `text2vec-transformers` sidecar cho embeddings.
- Langfuse optional (self-hosted docker-compose, không cần K8s).

### 5.3 Bỏ hẳn ở local

- Istio service mesh → dùng nginx-ingress.
- Keycloak + OAuth2 Proxy → dev không cần SSO, GKE mới cần.
- Kubeflow Pipelines full → dùng MLflow CLI + Airflow thay training orchestration tạm.
- Katib HPO → chạy manual optuna/python script.
- DataHub → skip, demo lineage qua logs.
- TensorRT, RayServe, RAGFlow full → skip.

### 5.4 Kind cluster config gợi ý

```yaml
# kind-config.yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: face-mlops
nodes:
- role: control-plane
  extraPortMappings:
  - { containerPort: 80, hostPort: 80 }
  - { containerPort: 443, hostPort: 443 }
  - { containerPort: 9092, hostPort: 9092 }  # Kafka external
- role: worker
  labels: { pool: general }
- role: worker
  labels: { pool: stateful }
```
Start: `kind create cluster --config kind-config.yaml`
Resource allocation cho Docker Desktop/engine: giới hạn 24GB RAM, 8 vCPU.

---

## 6. Implementation Considerations & Risks

| Risk | Mitigation |
|---|---|
| Disk tràn khi pull images mới | Prune trước mỗi phase; set Docker log-driver `local` với rotation |
| Kafka không persist sau restart cluster | Dùng hostPath PVC hoặc accept mất data khi `kind delete` |
| OOM khi 2 phase chạy song song | Monitor `kubectl top nodes`; tắt phase cũ trước khi start phase mới |
| Ingress conflict khi nhiều UI cùng path | Dùng subpath `/grafana`, `/airflow`, `/mlflow` hoặc port-forward |
| Image pull rate limit Docker Hub | Login Docker Hub account; pre-pull images trước phase; dùng mirror local |
| PNG vs Mermaid migration scope creep | Chỉ vẽ lại 11 diagram chính, bỏ `architecture_design.html`/`architecture_detailed.html` |

---

## 7. Success Metrics

Local setup được coi là **đủ** khi:
- [ ] Phase 0: `kubectl get pods -A` — tất cả `Running`, Grafana truy cập được.
- [ ] Phase 1: Upload ảnh vào MinIO, query được Postgres.
- [ ] Phase 2: Kafka producer→consumer thông, Spark job chạy xong Bronze→Silver.
- [ ] Phase 3: 1 Airflow DAG chạy end-to-end trigger Spark + GE.
- [ ] Phase 4: MLflow UI log experiment, Evidently drift metric hiện trong Prometheus.
- [ ] (Optional) Phase 5: Ollama trả lời query qua FastAPI.
- [ ] 11 Mermaid diagrams trong `docs/diagrams/` replace references trong `NEW_PLANS.md`.
- [ ] `docker system df` < 40GB sau khi chạy tất cả phase.

---

## 8. Next Steps (đề xuất tạo `/plan`)

1. **Dọn disk** (1 lệnh): `docker system prune -a --volumes`.
2. **Chuẩn Kind config** + cluster up (Phase 0).
3. **Vẽ Mermaid diagrams** song song với implement (không blocking).
4. **Triển khai tuần tự Phase 1 → Phase 4** (Phase 5 tuỳ chọn).
5. **GKE upgrade plan** — tách riêng: node pool resize theo ADR section 12, deploy tier C (Istio, Keycloak, Kubeflow full, RAGFlow) chỉ trên cloud.

---

## 9. Open Questions (chưa giải quyết)

1. **MLflow backend**: SQLite đủ local, nhưng lên GKE dùng Postgres chung `storage-ns` hay instance riêng?
2. **Data Generator (coursework Section 01)**: implement Python CLI riêng hay tích hợp thành Airflow DAG?
3. **Coursework deadline**: có deadline cứng không? Ảnh hưởng tới có nên làm Phase 5 (RAG) hay không.
4. **GKE cost budget**: có budget chạy prod-like ($310–$933/tháng) không? Ảnh hưởng tới scope tier C.
5. **Diagram migration**: có giữ lại PNG cũ làm archive không, hay xoá hẳn để giảm repo size 3MB?

---

## Sources

- [MLOps in 2026 — The Definitive Guide](https://rahulkolekar.com/mlops-in-2026-the-definitive-guide-tools-cloud-platforms-architectures-and-a-practical-playbook/)
- [Integrating MLflow, Kubeflow, and Airflow for Composable Enterprise MLOps](https://uplatz.com/blog/integrating-mlflow-kubeflow-and-airflow-for-a-composable-enterprise-mlops-platform/)
- [Building Production-Ready End-to-End MLOps Pipeline on Kubernetes (Mar 2026)](https://medium.com/@nsalexamy/building-a-production-ready-end-to-end-mlops-pipeline-on-kubernetes-full-walkthrough-aeb5b87cad60)
- [Deploying Kafka on Kind for dev/test](https://medium.com/@martin.hodges/deploying-kafka-on-a-kind-kubernetes-cluster-for-development-and-testing-purposes-ed7adefe03cb)
- [Deploying Airflow on Kind with Helm](https://medium.com/@jarvinM/deploying-airflow-on-a-local-kubernetes-kind-cluster-with-helm-380d0fcf0639)
- [Kafka + MinIO on Kubernetes streaming](https://blog.min.io/stream-data-to-minio-using-kafka-kubernetes/)
- [Kubeflow vs MLflow vs ZenML comparison](https://www.zenml.io/blog/kubeflow-vs-mlflow)
