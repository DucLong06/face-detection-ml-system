---
phase: 8
title: "T2 ML platform"
status: pending
priority: P1
effort: "2-3d"
dependencies: [7]
---

# Phase 8: T2 ML Platform

## Overview
Train path: Trino/Gold → Feast → KFP pipeline (load→prep→train→eval→register→export) → Katib HPO → Ray train (CPU-slow) → MLflow registry → ONNX export. Spec: `docs/architecture/phase-t2-ml-platform.md`.

## Quyết định (validated 260611 — USER CHỐT, không tranh cãi lại)
**FULL Kubeflow** (manifests platform-agnostic) trên kind 40GB. **Điều kiện fallback đã thoả thuận:** kẹt >2 ngày công → chuyển KFP-standalone + Katib riêng, cùng cấu trúc thư mục values. Red-team phase 1 chỉ soát execution risk (thứ tự cài, version pin, RAM), KHÔNG reverse quyết định này. <!-- Updated: Validation Session 1 -->

## Tools (gitops/platform/ml/) — sync-wave 5
| Tool | Ghi chú CPU |
|---|---|
| Kubeflow full (manifests) | KFP+Notebooks+Katib+Profiles; pin version manifests; 🟡 RAM ~8-10GB |
| Katib | trials=2-3 demo HPO |
| KubeRay | RayJob train; values-gpu stub sẵn |
| MLflow | backend PG (T1) + artifact MinIO (T1) |
| Feast | offline=Trino/parquet, online=Redis (T1) |

## Implementation Steps
1. MLflow + Feast trước (storage có sẵn từ T1) — demo: materialize features từ Gold, log 1 run.
2. Kubeflow manifests install (pin release) + pipeline `pipelines/kubeflow/face-train-pipeline.py`: fetch Gold (lakeFS pin) → train YOLO (CPU, epochs nhỏ) → eval (GE trên output) → register MLflow → export ONNX → MinIO model store.
3. Katib experiment file + KubeRay RayJob biến thể train.
4. E2E: chạy pipeline → model xuất hiện MLflow registry + ONNX trong MinIO.
5. README ml domain (kiến trúc + cách chạy pipeline + chỗ cắm GPU sau).

## Success Criteria
- [ ] KFP run hoàn chỉnh 6 bước, model trong MLflow + ONNX trong MinIO
- [ ] Feast: 1 feature view materialize offline→online
- [ ] Katib experiment hoàn thành ≥2 trials
- [ ] README ml viết xong

## Risk Assessment
- Train CPU quá lâu → dataset subset + epochs=1-2, mục tiêu là PIPELINE chạy, không phải model tốt.
- Full KF trên kind kẹt cert/webhook/Istio-dependency → fallback condition ở trên; log mốc thời gian debug để biết khi nào chạm 2 ngày.

## Red-Team Adjudicated Updates (260611)
- B2: kustomize KF = bundle TRỪ KServe/Knative; Istio của KF = Istio cluster (istio-system owned-by-KF); giữ MySQL/MinIO bundled của KFP (không rewire sang T1 — F3).
- F3/O12: chia ≥4 ArgoCD app theo sync-wave (istio → cert/dex → KFP → Katib/Notebooks) + `ServerSideApply=true`; log giờ debug từ giờ 0 cho fallback-clock 2 ngày.
- F9: Katib trials: dataset ≤200 ảnh, epochs=1, metric = plumbing-proof; tiêu chí accuracy/latency = "GPU-phase only".
- F1/B1: trên lab k3s ≥56GB không cần park 7b/OM trước khi cài KF; mỗi component KF phải vừa 1 node 8GB (kiểm requests).
- B6: CẤM KFP recurring runs (Airflow/ArgoEvents own scheduling).
