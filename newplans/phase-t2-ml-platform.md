# T2 — ML Platform (L3, full Kubeflow)

**Priority:** P1 · **Status:** pending · **Depends:** T1 · **Blocks:** T3,T4 · **Sơ đồ:** `diagrams/icons/03-ml-platform.png`

## Overview
Nền tảng ML đầy đủ: explore (Notebooks) → training DAG (Pipelines) → HPO (Katib) → distributed (Ray) → tracking/registry (MLflow) → feature store (Feast) → export (ONNX/TensorRT). Multi-user qua Kubeflow Profiles + SSO.

## Namespace `ml-platform` + Tools

| Tool | Vai trò |
|---|---|
| **Kubeflow Pipelines** | training DAG tái lập (load→preprocess→train→eval→register→export) |
| **Kubeflow Notebooks** | DS explore data, multi-user Profiles (map role SSO) |
| **Katib** | hyperparameter tuning (HPO) |
| **Ray / KubeRay** | distributed training/tuning ở scale |
| **MLflow** | experiment tracking + model registry (stage None→Staging→Prod→Archived) |
| **Feast** | feature store: offline (Iceberg via Trino) + online (Redis) |
| **ONNX / TensorRT** | export tối ưu inference (TensorRT INT8 trên GPU) |

## Design
- **Boundary orchestrator:** Kubeflow = ML training; Airflow = data ETL (T1). Không chồng.
- **Feast:** offline store đọc Gold (Iceberg) → materialize sang Redis online → train + serve dùng chung định nghĩa feature (consistency train/serve).
- **Ray:** scale training YOLOv11 + Katib trials song song trên GPU node pool.
- **Registry:** MLflow link model ↔ dataset (lakeFS version) ↔ Iceberg snapshot → full reproducibility.
- **Profiles:** mỗi role SSO → 1 Kubeflow Profile (namespace ảo) → isolation multi-user.

## Build Steps
1. Kubeflow (Pipelines + Notebooks + Katib + Profiles + Central Dashboard) qua ArgoCD.
2. MLflow + PostgreSQL backend + MinIO/Iceberg artifact.
3. Feast: định nghĩa feature, offline (Trino/Iceberg) + online (Redis).
4. KubeRay operator + RayCluster (GPU).
5. Training pipeline component: load Feast→train (Ray)→eval mAP→register MLflow→export ONNX→TensorRT.

## Success Criteria
- [ ] Training DAG chạy end-to-end, log MLflow, model versioned + staged
- [ ] Katib (qua Ray) tìm HP tốt hơn ≥1–2% accuracy
- [ ] Feast serve online feature < 10ms; train/serve consistency
- [ ] ONNX serve được; mAP không giảm >1% vs PyTorch
- [ ] Kubeflow Profile theo role SSO hoạt động

## Risks
- Kubeflow + Ray + Feast nhiều component → quota namespace `ml-platform` rộng.
- GPU scheduling (Ray train vs Triton serve vs vLLM) → cần kế hoạch GPU node pool (open question #1).
