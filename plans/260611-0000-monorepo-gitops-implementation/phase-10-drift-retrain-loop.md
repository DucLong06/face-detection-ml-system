---
phase: 10
title: "T4 Drift→Retrain loop ★"
status: pending
priority: P1
effort: "2-3d"
dependencies: [9]
---

# Phase 10: T4 Drift→Retrain→Canary Loop ★ CENTERPIECE

## Overview
Khép vòng tự động: KServe predictions → Evidently/Alibi drift → Prometheus → Alertmanager → Argo Events → KFP retrain (data pin lakeFS) → MLflow Staging → human approval → Flagger canary. Spec: `docs/architecture/phase-t4-drift-retrain-loop.md`. Đây là deliverable đắt giá nhất — mọi phase trước phục vụ nó.

## Tools (gitops/platform/drift/) — sync-wave 7
| Tool | Vai trò |
|---|---|
| Evidently (service/cron) | data+prediction drift → metric `drift_score` |
| Alibi Detect | outlier/adversarial (dashed support — có thể defer 1 nhịp) |
| Argo Events | webhook từ Alertmanager → trigger KFP run |
| (có sẵn) Prometheus/Alertmanager | rule `drift_score > 0.5` (phase 11 minimal đã cài) |

## Wiring chi tiết (khớp sơ đồ zone Drift)
1. KServe inference logger → log requests/predictions vào MinIO (hoặc Kafka topic predictions).
2. Evidently job (Airflow DAG hoặc CronJob) đọc window predictions vs reference (Gold snapshot) → push `drift_score` → Pushgateway/Prom.
3. PrometheusRule: alert `DriftHigh` → Alertmanager route → webhook receiver (Argo Events EventSource).
4. Argo Events Sensor → tạo KFP run (pipeline T2) với param lakeFS ref pin.
5. Pipeline xong → model MLflow Staging; **human approval** = manual promote (MLflow UI/CLI) → bump model version trong gitops → Flagger canary (phase 9).

## Implementation Steps
1. Inference logging bật trên InferenceService; verify data đến MinIO/Kafka.
2. Evidently job + Pushgateway; demo drift giả (shift input distribution bằng script).
3. PrometheusRule + Alertmanager webhook + Argo Events EventSource/Sensor → KFP run tự khởi động.
4. Chạy trọn vòng: inject drift → alert → retrain run → Staging model → approve tay → canary lên.
5. Đo thời gian vòng + ghi runbook `docs/runbooks/drift-loop.md`; README drift domain.

## Success Criteria
- [ ] Vòng full tự động tới Staging, dừng đúng ở human gate, promote tay → canary
- [ ] Demo drift giả lặp lại được bằng script (`pipelines/rag-indexing` không liên quan — script ở `pipelines/drift-demo/`)
- [ ] Runbook + README drift viết xong

## Risk Assessment
- Chuỗi 6 hệ thống nối nhau — debug khó → dựng từng khớp một có verify riêng (steps 1-3 độc lập).
- Vòng tự kích hoạt liên tục (alert flapping) → alert `for: 10m` + Sensor dedupe/throttle.

## Red-Team Adjudicated Updates (260611)
- O5: Pushgateway nằm trong 11a (đã thêm) — P10.2 push drift_score vào đó.
- B6: Evidently = **CronJob thuần** (bỏ phương án Airflow DAG — drift loop không phụ thuộc Airflow); Argo Events = trigger retrain DUY NHẤT; KFP run prefix `drift-`/`manual-`.
- B3: bước cuối loop dùng KServe canaryTrafficPercent (không Flagger trên ISVC).
