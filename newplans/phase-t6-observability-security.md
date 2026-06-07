# T6 — Observability + Security + SSO + Governance

**Priority:** P1 · **Status:** pending · **Cross-cutting** (feeds T4) · **Sơ đồ:** `diagrams/icons/07-platform-observability.png`

## Overview
Metrics/logs/traces toàn cluster + SSO RBAC xuyên suốt + data governance. Prometheus/Thanos là backbone cho T4 drift alerts.

## Namespaces + Tools

| Namespace | Tool | Vai trò |
|---|---|---|
| `monitoring` | **Prometheus + Thanos + Grafana + Alertmanager** | metrics HA + long-term + dashboard + alert |
| `logging` | **ELK** (Elasticsearch + Kibana + Logstash + Filebeat) | log tập trung, full-text search mạnh |
| `tracing` | **Jaeger + OpenTelemetry Collector** | distributed tracing, OTLP hợp nhất telemetry |
| `auth` | **Keycloak** (6 roles) | SSO RBAC nguồn gốc |
| `data-catalog` | **OpenMetadata** policies | data access theo role |

## Design
- **Telemetry hợp nhất:** OTel Collector nhận metrics/logs/traces (OTLP) → fan-out Prometheus/ELK/Jaeger.
- **Thanos:** Prometheus HA + long-term (object store) — best-of-breed metrics ở scale.
- **ELK:** full-text log search (mạnh hơn Loki) — đã chọn.
- **SSO RBAC 6 roles:** `user` `data-analyst` `data-scientist` `data-engineer` `ml-engineer` `admin` → map sang Kubeflow Profiles + OpenMetadata policies + Grafana/MLflow/Airflow/Kibana qua OIDC.
- **1 cookie** `*.face-detect.dev` cho mọi UI (OAuth2 Proxy + Istio).
- **Drift alerts:** Prometheus rule → Alertmanager → webhook (T4) + Slack.

## RBAC mapping (Keycloak role → quyền)
| Role | Quyền |
|---|---|
| data-analyst | đọc Gold + dashboards + catalog (no PII) |
| data-scientist | Notebooks + Feast + MLflow + catalog (read features/models) |
| data-engineer | Airflow + Flink/Spark UI + catalog edit + lineage |
| ml-engineer | KServe/Triton + Evidently + MLflow + serving metadata |
| admin | toàn quyền |
| user | chỉ inference API |

## Build Steps
1. kube-prometheus-stack + Thanos (object store).
2. ELK (ECK operator) + Filebeat DaemonSet.
3. OTel Collector + Jaeger.
4. Grafana dashboards: inference, data-pipeline, drift (T4).
5. Keycloak realm/roles/clients + OAuth2 Proxy mỗi UI; OpenMetadata policies.

## Success Criteria
- [ ] Metrics + logs + traces tập trung, query được; Thanos long-term
- [ ] Drift dashboard hiển thị model_drift_score
- [ ] SSO 1 lần login mọi UI; mỗi role thấy đúng phần được phép (Kubeflow Profile + OpenMetadata policy)

## Risks
- ELK + Thanos + Jaeger nặng → namespace quota rộng (OK vì cluster mạnh).
- SSO mapping nhiều tool → test từng tool OIDC.
