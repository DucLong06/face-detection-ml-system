# observability/ (values-only)

Stack giám sát — **chỉ giữ values + version pin**, KHÔNG vendor template (ArgoCD kéo upstream).
Thay cho cách cũ `helmfile` + chart vendored local.

## Components & version pin
| Component | Upstream repo | Version | Namespace |
|---|---|---|---|
| kube-prometheus-stack | prometheus-community | 67.4.0 | monitoring |
| jaeger | jaegertracing | 3.3.2 | tracing |
| elasticsearch / kibana / filebeat / logstash | helm.elastic.co | 8.5.1 | logging |

## Thứ tự deploy (sync-wave)
`elasticsearch` → (`logstash`, `kibana`, `filebeat`) → `jaeger`

## Cách update (đơn giản hoá)
Đổi 1 dòng version trong README + ArgoCD Application → ArgoCD tự kéo chart mới. Không đụng template.

> Triển khai thật ở **phase 11 (D15)**. Đây là cấu trúc values-only sẵn sàng cho GitOps.
