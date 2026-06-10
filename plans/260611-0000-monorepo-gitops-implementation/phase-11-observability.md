---
phase: 11
title: "T6 Observability"
status: pending
priority: P2
effort: "2d"
dependencies: [6]
---

# Phase 11: T6 Observability (kéo sớm phần metrics)

## Overview
2 nhịp: **11a-minimal (kéo sớm, ngay sau phase 6 hoặc trước phase 9 bước 4)**: kube-prometheus-stack (Prom+Alertmanager+Grafana) — vì Flagger (P9) và drift loop (P10) cần metrics. **11b-full (sau P10)**: Thanos (long-term, MinIO bucket), ELK + Filebeat/Logstash, Jaeger + OTel Collector. Spec: `docs/architecture/phase-t6-observability-security.md`.

## Tools (gitops/platform/observability/) — sync-wave 3 (11a) / 8 (11b)
| Nhịp | Tool | Ghi chú CPU |
|---|---|---|
| 11a | kube-prometheus-stack | retention ngắn 2d local |
| 11b | Thanos sidecar+store | bucket MinIO (T1) |
| 11b | ELK (ES single-node + Kibana + Filebeat→Logstash) | ES 🟡 RAM ~2GB — bật khi máy chịu |
| 11b | Jaeger all-in-one + OTel Collector | app instrument OTLP (FastAPI middleware) |

## Implementation Steps
1. **11a**: kube-prometheus-stack values-cpu; ServiceMonitor cho face-detect + ArgoCD; 1 Grafana dashboard app (RPS/latency/error).
2. 11b Thanos: sidecar + objstore secret (sealed) → query frontend; verify query 7d sau retention prom.
3. 11b ELK: ES single node, Filebeat DaemonSet, parse app logs; Kibana index pattern.
4. 11b Tracing: OTel Collector gateway; FastAPI auto-instrument (`opentelemetry-instrument`); trace 1 request end-to-end thấy trên Jaeger.
5. Dashboards: drift loop panel (drift_score, retrain runs) — phục vụ demo P10. README observability domain.

## Success Criteria
- [ ] 11a: Grafana lên, dashboard app có data, Alertmanager route test OK (trước P9.4)
- [ ] 11b: Thanos query > retention; log app tìm được trên Kibana; trace thấy trên Jaeger
- [ ] README observability viết xong

## Risk Assessment
- ES RAM lớn → single-node + heap 1g; nếu vẫn chật: defer ELK sau cùng (loop P10 không phụ thuộc logs).
- Thanos phụ thuộc MinIO (T1) — 11b chỉ sau phase 7a.

## Red-Team Adjudicated Updates (260611)
- O5: thêm `prometheus-pushgateway` vào 11a (cùng wave).
- O6: kube-prometheus-stack → wave 1; mọi ServiceMonitor/PrometheusRule gom vào app "monitors" wave 4 (tránh CRD race khi bootstrap máy trắng).
- B5: Grafana dashboards = ConfigMap sidecar-provisioned trong git, CẤM UI-only.
- B8/B1: 2 ES (ELK + OpenMetadata) schedule lên node khác nhau bằng podAntiAffinity — không cần park OM.
