# Red-Team Architecture Findings — Bảng Adjudication

**Date:** 2026-06-11 · **Phase 1 của plan `260611-0000`** · 3 reviewer (Tài nguyên F / Thứ tự O / Chồng chéo+GitOps S) · 36 findings, dedupe còn **8 quyết định + 1 gói fix kỹ thuật**.
**Ràng buộc tôn trọng:** không finding nào đề xuất đảo quyết định đã khóa (Full Kubeflow, monorepo, GHCR, kind, stack...).

## Verdict tổng
Kế hoạch **khả thi** trên máy 40GB **với điều kiện**: kỷ luật park/unpark stack theo phase (trần resident ~24GB — vỡ lần đầu ở Phase 8), sửa 4 CRIT trước khi bắt tay (sealed-key backup, Trino heap, CI race, Kyverno failurePolicy), và chốt 3 quyết định kiến trúc serving (Kubeflow bundle / Flagger provider / Iter8).

## Bảng RAM tích lũy (lens F — ước tính default charts, usable ≈32GB)
P5: 4.5 → P6: 5.7 → +11a: 8.2 → +7a: 12.7 → +7b: 17.2 → +7c: 23.7 → **+P8 Kubeflow: 34.2 ← VỠ TRẦN** → +P9: 37.2 → +P11b: 42.7 → +P12: ~50 (nếu không park gì).

## GÓI A — Fix kỹ thuật thuần, không trade-off (đề xuất: áp tất cả)
| ID | Fix |
|---|---|
| F2 | Trino values-cpu: workers=0 coordinator-only, heap 2G (default = bom 16-24GB) |
| F4 | OpenMetadata: host `vm.max_map_count=262144`, ES heap 512m-1g, tắt Airflow ingestion bundled (dùng Airflow T1) |
| F6 | KServe demo: `kind load docker-image` trước, progress-deadline 600s, đo cold-start trừ first-pull |
| F8 | JVM sizing 7b: Kafka Xmx512m, Connect 768m, Flink TM 1g; park 7b sau demo |
| F9 | Katib/criteria CPU-thực-tế: dataset ≤200 ảnh, epochs=1, metric = chứng minh plumbing; tiêu chí accuracy/latency đánh dấu "GPU-phase only" |
| F11a | 3 PriorityClass + requests=limits cho stateful JVM + taint control-plane NoSchedule + ResourceQuota theo bảng RAM |
| F11b+S8+O11 | Kyverno: `failurePolicy: Ignore` trên kind; enforce theo SCOPE (chỉ ns tự viết chart) sau khi P10 xanh, không theo thời gian; PolicyException tracked trong git |
| F12 | Host sysctls inotify (512/1048576); cân nhắc 1 worker node thay 2; crictl prune định kỳ |
| O5 | Thêm `prometheus-pushgateway` vào 11a (P10 cần chỗ push drift_score) |
| O6 | kube-prometheus-stack → wave 1; ServiceMonitor/PrometheusRule tách app "monitors" wave 4 (tránh CRD race khi bootstrap máy trắng) |
| O7 | Tách wave operator vs CR (Strimzi/Spark/Flink: operator wave N, CR wave N+1) |
| O8 | PG values 7b: `wal_level=logical` + max_replication_slots ngay từ đầu (Debezium cần) |
| O9 | KEDA demo trên workload non-Knative (transformer/consumer); phase 9 dependencies thêm 11a |
| O12 | Application specs P8/P9: `ServerSideApply=true` (CRD lớn vượt 262KB annotation) |
| S2 | CI bump-tag: `concurrency` group + `git pull --rebase` + retry 3x; test 2-push-nhanh |
| S4 | root-app tự quản chính nó (copy vào gitops/apps/) — hết drift khi sửa root |
| S5 | namespaces app: Prune=false; rule "thử nghiệm tay vào scratch ns, selfHeal sẽ nuốt mọi thứ khác" vào gitops/README |
| S9 | GE 1 config root, suites tách namespace: data-gate.* vs model-eval.* |
| S10 | CDC: đúng 1 KafkaConnect cluster, Debezium = KafkaConnector CR trong nó; cấm Debezium Server standalone |
| S11 | Bảng phân vai catalog: lakeFS REST = Iceberg catalog (write-path) vs OpenMetadata = discovery/lineage (read-only) |
| S12 | GHCR: checklist "flip public" mỗi image mới, hoặc private + sealed imagePullSecret sau P6 |
| F10 | RAGFlow: chạy P12 khi T1/T2 đã park; pre-write câu hỏi fallback LlamaIndex (>1 ngày kẹt) |

## GÓI B — Quyết định cần user (trade-off thật)
| # | IDs | Vấn đề | Lựa chọn |
|---|---|---|---|
| B1 | F1 | Phase 8 vỡ trần RAM nếu giữ mọi thứ chạy | Chấp nhận kỷ luật **park/unpark** (trần ~24GB, tắt 7b+OM trước khi cài KF)? |
| B2 | F3+O1+O2 | Kubeflow manifests BẮT BUỘC kèm Istio (P6 "hoãn Istio" bị vô hiệu) + kèm cả KServe/Knative riêng | (a) KF bundle TRỪ KServe/Knative; P9 cài standalone dùng net-istio (reuse Istio của KF) — (b) dùng luôn KServe/Knative từ bundle KF |
| B3 | O3 | Flagger nginx provider KHÔNG canary được InferenceService | (a) KServe-native canaryTrafficPercent cho ISVC + Flagger demo trên L1 Deployment — (b) Flagger knative provider |
| B4 | S7 | Iter8 + Flagger giành nhau canary; Iter8 không bị khóa | Cắt Iter8 khỏi build (hình vẽ giữ dạng dashed optional)? |
| B5 | S1+O4+S3 | Máy-trắng hiện không trung thực từ P6+ (key sealed-secrets chết theo cluster, PAT tạo tay, PV state mất) | Chốt định nghĩa: bootstrap nhận đúng **2 input ngoài git** (GITHUB_PAT + sealed-key backup, restore-trước-cài-controller) + state data/model = **re-seed scripts** (make seed-data); Grafana dashboards = ConfigMap trong git |
| B6 | S6 | 3 scheduler giành quyền trigger | Rule: **Airflow = ETL định kỳ · Argo Events = trigger retrain DUY NHẤT · KFP recurring = cấm · Evidently = CronJob thuần** (drift loop sống không phụ thuộc Airflow); run-name prefix drift-/manual- |
| B7 | O10 | Langfuse v3 đòi ClickHouse+Redis+S3 (plan ghi "PG backend" — stale) | (a) pin Langfuse v2 (đủ demo, maintenance-only) — (b) v3 + ClickHouse (nặng thêm, đúng đời mới) |
| B8 | F1-liên-quan | Sau khi chốt B1: thứ tự 11b ELK — ES của ELK đụng ES của OpenMetadata (F5) | (a) park OM khi chạy 11b (mutually exclusive) — (b) OM dùng external ES chung |

## Quyết định user (điền sau interview)
| # | Quyết định user (260611) |
|---|---|
| Gói A | **ÁP TOÀN BỘ 23 fix** |
| B1 | **k3s multi-node trên lab 7+ server 8GB (≥56GB tổng)** — thay kind làm cluster chính (kind vẫn dùng được cho thử nhanh trên laptop). Constraint mới: mỗi pod ≤ ~6.5GB/node. Bảng park/unpark nới lỏng đáng kể; F1 hạ CRIT→minor |
| B2 | KF bundle TRỪ KServe/Knative; Istio do KF sở hữu (P6 ghi "Istio đến cùng KF"); P9 standalone net-istio |
| B3 | KServe-native canaryTrafficPercent cho ISVC; Flagger demo trên L1 Deployment |
| B4 | **GIỮ Iter8** — chỉ chế độ offline/shadow SLO assessment, CẤM traffic-shifting (Flagger độc quyền runtime traffic) |
| B5 | Contract máy-trắng 2-input (GITHUB_PAT + sealed-key backup, restore trước cài controller) + `make seed-data` + Grafana dashboards = ConfigMap |
| B6 | Rule trigger: Airflow=ETL · ArgoEvents=retrain duy nhất · KFP recurring=cấm · Evidently=CronJob; prefix drift-/manual- |
| B7 | Langfuse v3 + ClickHouse (Redis/MinIO reuse T1) |
| B8 | Tự giải quyết bởi B1: 2 ES schedule lên node khác nhau, không cần park OM khi chạy 11b |

**Diagrams impact:** KHÔNG cần sửa nội dung hình (Iter8 giữ, Debezium-in-Connect đã vẽ đúng, k3s/GKE không xuất hiện trong hình, Langfuse backend là chi tiết values) → Phase 2 hoàn tất.
