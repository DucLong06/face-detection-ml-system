# T4 — Drift → Retrain → Canary Loop ★ (L3 centerpiece)

**Priority:** P0 (differentiator) · **Status:** pending · **Depends:** T1,T2,T3 · **Sơ đồ:** `diagrams/icons/05-drift-loop.png`

## Overview
Đóng vòng lặp MLOps thật — phần tách "MLOps" khỏi "k8s + model": data drift → detect → auto-retrain → canary → promote/rollback.

## Namespaces + Tools

| Namespace | Tool | Vai trò |
|---|---|---|
| `ml-monitoring` | **Evidently** | data/prediction drift (KS-test/PSI), export Prometheus |
| `ml-monitoring` | **Alibi Detect** | outlier + adversarial + advanced drift |
| `monitoring` | **Prometheus + Thanos** | metrics + alert rule + long-term store |
| `monitoring` | **Alertmanager** | route alert → webhook |
| `data-orchestration` | **Argo Events** | webhook → trigger pipeline (event bus) |
| `ml-platform` | **Kubeflow** retrain pipeline + **MLflow** | retrain + eval + register Staging |
| `model-serving` | **Flagger** | canary model mới → promote/rollback |

## Design (loop)
```
KServe/Triton predictions
  → Evidently (drift) + Alibi Detect (outlier) → drift_score → Prometheus
  → Prometheus alert rule (score>0.5) → Alertmanager → webhook
  → Argo Events → trigger Kubeflow retrain pipeline
       fetch Gold (Iceberg, lakeFS pinned) + retrain (Ray) + eval vs baseline (GE)
       → if F1>baseline: MLflow Staging → KServe canary 5%
  → Flagger 5→100% (auto-rollback nếu degrade) → promote → loop restart
```
- **Drift scenarios:** image-quality shift, face-count dist, confidence decay, schema change.
- **Reproducible retrain:** lakeFS pin data version + Iceberg snapshot.
- **Human-in-loop option:** Kubeflow approval step trước Production (open question #3).

## Build Steps
1. Evidently CronJob + reference profile (MinIO) + Prometheus exporter.
2. Alibi Detect detector (outlier/adversarial).
3. Prometheus alert rule + Alertmanager webhook receiver.
4. Argo Events Sensor → trigger Kubeflow pipeline API.
5. Retrain pipeline (T2) + eval gate + MLflow Staging.
6. KServe canary patch + Flagger analysis; Grafana drift dashboard.

## Success Criteria
- [ ] Drop chunk drift → alert < 5 min → retrain auto-trigger
- [ ] Model mới qua canary, auto-rollback khi degrade
- [ ] Retrain reproducible (lakeFS + Iceberg snapshot)
- [ ] Demo video 5-min full loop

## Risks
- Webhook→Argo Events→Kubeflow fragile → test manual trigger trước.
- Ground-truth cho drift (open question #2) → giả định manual label.

## Reference repos
- https://github.com/safoinme/MLStack-Kubernetes-Argo-Docker-Git-DVC-MLFlow-KServe
- https://codingwithtaz.blog/2025/07/27/build-event-driven-ml-pipelines-with-argo-workflows/
