# Implementation Steps — CPU-first, self-install (Helm + GitHub Actions)

> Hướng dẫn **làm theo từng bước** để tự dựng hệ thống. Bắt đầu **CPU-only** (máy bạn chưa có GPU); mỗi tool đánh dấu **[CPU]** / **[GPU opt]**. Mỗi chart có **1 base + 2 values**: `values-cpu.yaml` (mặc định) / `values-gpu.yaml` (bật khi có GPU). Kiến trúc/sơ đồ không đổi giữa 2 profile.
>
> Quy ước: 🟢 = chạy CPU thoải mái · 🟡 = CPU được nhưng chậm (train/LLM) · 🔵 = chỉ khác backend khi có GPU. Mọi deploy đi qua **ArgoCD (GitOps)** — không `kubectl apply` tay.

---

## Phase 0 — Chuẩn bị (local) 🟢
- Cài CLI: `kubectl`, `helm`, `git`, `docker`, `kind` (hoặc `k3d`). *(học: helm.sh/docs, kind.sigs.k8s.io)*
- Tạo cluster CPU local:
  ```bash
  kind create cluster --name facedetect --config kind-config.yaml   # 1 control + 2 worker
  ```
- Tạo Git repo (mono) cấu trúc GitOps:
  ```
  infra/        # helm values + argocd apps (app-of-apps)
  charts/       # helm chart của app + các service tự viết
  app/          # face-detect FastAPI + YOLOv11 (đã có ở api/)
  .github/workflows/   # GitHub Actions CI
  ```
- **Học trước:** Helm (chart/values/release), GitHub Actions (job/step/secrets), ArgoCD (Application CRD, app-of-apps).

---

## Phase 1 — Nền tảng cluster + GitOps (T0) 🟢
| Bước | Tool | Lệnh skeleton | CPU/GPU |
|---|---|---|---|
| 1.1 | **ArgoCD** | `helm repo add argo https://argoproj.github.io/argo-helm` → `helm install argocd argo/argo-cd -n argocd --create-namespace` | 🟢 |
| 1.2 | **Istio ambient** (có thể hoãn) | `helm install istiod istio/istiod` + ambient profile | 🟢 |
| 1.3 | **cert-manager** | `helm install cert-manager jetstack/cert-manager --set crds.enabled=true` | 🟢 |
| 1.4 | **Kyverno** (policy) | `helm install kyverno kyverno/kyverno -n kyverno --create-namespace` | 🟢 |
| 1.5 | **Vault + ESO** (hoãn được) | `helm install vault hashicorp/vault` + external-secrets | 🟢 |
| 1.6 | **Keycloak SSO** (hoãn được) | `helm install keycloak bitnami/keycloak` | 🟢 |

- Tạo **ArgoCD app-of-apps**: 1 `Application` trỏ `infra/` → ArgoCD tự sync mọi thứ.
- **Governance baseline**: viết Kyverno ClusterPolicy ép quota/netpol/labels mỗi namespace.
- **Success:** `kubectl get applications -n argocd` xanh; `kubectl get ns` đủ namespace.

---

## Phase 2 — Đưa APP L1 lên cluster (CI/CD) 🟢
| Bước | Việc | CPU/GPU |
|---|---|---|
| 2.1 | **GitHub Actions CI**: build+test image face-detect, push GHCR/Docker Hub | 🟢 |
| 2.2 | **Helm chart app** (`charts/face-detection/`) — `values-cpu.yaml`: FastAPI/ONNX-CPU, resources CPU | 🟢 |
| 2.3 | **ArgoCD** deploy chart vào `model-serving` | 🟢 |
| 2.4 | Verify: `curl` endpoint detect → trả bbox | 🟢 |

`.github/workflows/ci.yaml` skeleton:
```yaml
on: { push: { branches: [main], paths: ['app/**','charts/**'] } }
jobs:
  build:
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t ghcr.io/<you>/face-detect:${{ github.sha }} app/
      - run: pytest app/          # test trước khi push
      - run: docker push ghcr.io/<you>/face-detect:${{ github.sha }}
      - run: |  # update image tag trong values → ArgoCD tự deploy (GitOps)
          yq -i '.image.tag="${{ github.sha }}"' charts/face-detection/values-cpu.yaml
          git commit -am "ci: bump image" && git push
```
- **Học:** GitHub Actions (GHCR login, secrets), yq, ArgoCD image updater (tuỳ chọn).

---

## Phase 3 — Data pipeline lõi (T1) 🟢
| Bước | Tool | Helm repo | CPU/GPU |
|---|---|---|---|
| 3.1 | **MinIO** | `bitnami/minio` | 🟢 |
| 3.2 | **lakeFS + Iceberg REST catalog** | `lakefs/lakefs` | 🟢 |
| 3.3 | **Spark Operator** + job medallion (Bronze→Silver→Gold ghi Iceberg) | `spark-operator` | 🟢 |
| 3.4 | **Great Expectations** (CronJob 2 gate) | image GE | 🟢 |
| 3.5 | **PostgreSQL, Redis** | `bitnami/postgresql`, `bitnami/redis` | 🟢 |

- Bỏ tạm Kafka/Flink/Debezium/Trino/OpenMetadata → thêm ở Phase 8.
- **Success:** Iceberg Gold query được; GE pass; data versioned trong lakeFS.

---

## Phase 4 — ML platform + training (T2) 🟡 (train CPU chậm)
| Bước | Tool | CPU/GPU |
|---|---|---|
| 4.1 | **MLflow** (`bitnami/mlflow`) — tracking + registry | 🟢 |
| 4.2 | **Argo Workflows** (nhẹ, CPU) hoặc Kubeflow (nặng hơn) | 🟢 |
| 4.3 | Training pipeline: load Gold → train YOLOv11 → eval → register MLflow → **export ONNX** | 🟡 train CPU (ít epoch/dataset nhỏ) |
| 4.4 | **Feast** (offline Iceberg + online Redis) — tuỳ chọn | 🟢 |

- **`values-gpu.yaml`:** đổi training job sang **Ray + GPU**, export thêm **TensorRT INT8**.
- **Success:** model versioned trong MLflow + có file ONNX.

---

## Phase 5 — Serving nâng cấp (T3) 🔵 CPU=ONNX / GPU=TensorRT
| Bước | Tool | CPU/GPU |
|---|---|---|
| 5.1 | **KServe** (+ Knative) | 🟢 control-plane |
| 5.2 | **InferenceService** — `values-cpu`: **Triton ONNX-CPU** (hoặc giữ FastAPI) | 🔵 |
| 5.3 | **KEDA** (autoscale) + **Flagger** (canary) | 🟢 |

- **`values-gpu.yaml`:** Triton **TensorRT** + `nvidia.com/gpu: 1` + MIG.
- **Success:** InferenceService Ready, infer ra bbox; canary shift chạy.

---

## Phase 6 — Vòng lặp Drift→Retrain→Canary (T4) ★ 🟢
| Bước | Tool | CPU/GPU |
|---|---|---|
| 6.1 | **Prometheus + Grafana** (`kube-prometheus-stack`) | 🟢 |
| 6.2 | **Evidently** CronJob → export `drift_score` → Prometheus | 🟢 |
| 6.3 | **Alertmanager** → webhook → **Argo Events** → trigger retrain pipeline (Phase 4) | 🟢 |
| 6.4 | retrain → MLflow Staging → KServe **canary 5%** → **human approve** → promote/rollback | 🟡 (retrain CPU chậm) |

- **Success:** drop chunk data drift → alert < 5min → retrain auto → canary → bạn approve → promote. **Đây là phần ăn điểm.**

---

## Phase 7 — Observability + Security + SSO (T6) 🟢
- **ELK** (`elastic/eck`) hoặc Loki (nhẹ hơn) · **Jaeger + OTel Collector** · **Grafana dashboards** (drift).
- **Keycloak** 6 role → SSO mọi UI (OAuth2 Proxy). **Kyverno** siết governance. **Vault** secrets.
- **Success:** 1 cookie SSO mọi UI; metrics/logs/traces tập trung.

---

## Phase 8 — Mở rộng data (streaming + CDC + governance) 🟢
- **Kafka (Strimzi)** + Schema Registry + **Debezium** (CDC) + Kafka Connect · **Flink** (stream validate) · **Trino** (SQL) · **OpenMetadata** (catalog + lineage + RBAC).

---

## Phase 9 — RAG / LLM (T5) 🔵 CPU=Ollama / GPU=vLLM
| Bước | Tool | CPU/GPU |
|---|---|---|
| 9.1 | **LLM serving** — `values-cpu`: **Ollama** (TinyLlama/Qwen2.5-0.5B GGUF) | 🔵 CPU |
| 9.2 | **Qdrant** (vector) + **Typesense** (keyword) | 🟢 |
| 9.3 | **RAGFlow** orchestrator + embedding BGE/MiniLM (CPU) | 🟢 |
| 9.4 | **NeMo Guardrails** + **Langfuse** | 🟢 |

- **`values-gpu.yaml`:** đổi Ollama → **vLLM** (GPU, throughput cao).
- **Success:** hỏi-đáp metadata, guardrails chặn, Langfuse log trace.

---

## CPU → GPU: chuyển đổi sau này (không vẽ/dựng lại)
Chỉ đổi values ở 4 chart:
```bash
helm upgrade face-detection charts/face-detection -f values-gpu.yaml   # Triton TensorRT
helm upgrade training       charts/training       -f values-gpu.yaml   # Ray GPU
helm upgrade llm            charts/llm            -f values-gpu.yaml   # vLLM
# + thêm GPU node pool (Terraform) + nvidia device plugin + MIG/Kueue
```

## Thứ tự khuyên (lát cắt dọc trước)
**P0→P1→P2 (app L1 chạy GitOps) → P3 lõi → P4 → P5 → P6 (đóng vòng lặp ★)** rồi mới P7→P8→P9.
Đừng dựng cả 20 namespace cùng lúc — xong vòng lặp P6 là đã có "MLOps thật".

## Học gì (self-study pointers)
- Helm: chart structure, values override, `helm upgrade --install`
- GitHub Actions: build/push GHCR, secrets, path filter, matrix
- ArgoCD: Application, app-of-apps, auto-sync, image updater
- KServe/Triton: InferenceService CRD, ONNX vs TensorRT runtime
- Evidently + Prometheus alert + Argo Events: webhook → workflow trigger

## Unresolved (quyết khi làm)
1. Registry: GHCR hay Docker Hub?
2. Cluster thật khi cần GPU: GKE GPU node pool hay máy có GPU on-prem?
3. Orchestrator ML: Argo Workflows (nhẹ, CPU-first) hay Kubeflow full (khi có GPU/nhiều RAM)?
