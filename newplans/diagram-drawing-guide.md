# Hướng dẫn vẽ sơ đồ kiến trúc — Face-Detect MLOps (best-of-breed)

> Mục đích: spec để **bạn tự vẽ** trong draw.io. Mỗi zone có: danh sách component (tool thật) · các step đánh số · từng mũi tên `from → to (nhãn)` · bố cục · pattern chống rối · góp ý. Đọc **§0 nguyên tắc** trước.
> File skeleton có sẵn: `diagrams/icons/01-overview.drawio` (mở draw.io, mỗi zone tách thành 1 Page riêng để drill-down).

---

## §0. Nguyên tắc style (áp cho mọi hình)

**Bố cục**
- **Landscape, flow trái→phải.** Mỗi pipeline = 1 **swimlane** (container nền pastel, tiêu đề bold góc trên-trái).
- **Namespace = container dashed** lồng bên trong lane (ghi `ns: xxx`).
- Icon đồng cỡ ~50px, **logo thật**, nhãn ngắn ngay dưới icon.

**Ngữ nghĩa shape (quan trọng — đây là chỗ hay vẽ sai)**
- **Storage / tầng dữ liệu** (Bronze/Silver/Gold, DW, store) = shape **cylinder / bucket** (hoặc icon MinIO/Iceberg/Postgres). KHÔNG dùng icon engine cho tầng dữ liệu.
- **Processing engine** (Spark/Flink) = rounded-rect có logo, **đặt TRÊN mũi tên transform** giữa 2 tầng storage.
- **Queue/topic** (Kafka topic) = shape **pill/hexagon**, đặt tên topic thật (`raw-images`, `validated`, `cdc.*`).
- **Artifact** (Sources, Question, Model Registry) = rounded-rect có tên, không cần logo.

**Mũi tên & nhãn**
- **Numbered steps `(1)(2)(3)`** trên mũi tên luồng chính → người xem đọc được thứ tự.
- Màu theo ngữ nghĩa: data=xanh dương `#1864ab` · control/trigger=cam `#b8741a` · drift loop=đỏ `#c92a2a` · telemetry=xanh lá `#059669` · RAG=tím `#7c3aed` · phụ/dotted=xám.
- `edgeStyle=orthogonalEdgeStyle;rounded=1` (vuông góc, bo góc). Nhãn ≤3 từ + có nền trắng mờ.

**3 pattern chống rối (must)**
1. **Gate-on-transform**: data-quality check (GE) đặt **ngay trên mũi tên** Bronze→Silver, Silver→Gold → "validate trước khi promote".
2. **Sidecar low-latency**: luồng feature online (Flink→Redis) vẽ **vòng ngoài**, KHÔNG đi qua medallion (vì cần low-latency, không chờ batch).
3. **Distribution bus**: từ 1 hub (vd Gold) kẻ **1 đường trục** rồi rẽ nhánh xuống nhiều đích — thay vì N mũi tên riêng tỏa ra (chống rối mạnh nhất).

**Anti-overlap**
- Giãn node ≥130px; mũi tên cùng tầng đi ngang, khác tầng đi dọc trong "gutter" (rãnh giữa các hàng).
- Nhãn vụn (read/write/schema…) → bỏ, chỉ giữ numbered + nhãn quan trọng.
- Node đừng nằm trên đường thẳng của mũi tên khác (vd Schema Registry không đặt trên đường batch).

---

## §1. ZONE DATA PIPELINE (drill-down) — zone phức tạp nhất

**Namespaces:** `data-ingestion` `data-streaming` `data-processing` `data-storage` `data-quality` `data-orchestration` `data-catalog`

### Components
| Nhóm | Tool (icon) | Shape | Vai trò |
|---|---|---|---|
| Sources | WIDER FACE / Camera·API / App DB | artifact ×3 | batch / stream / cdc |
| Ingestion | Kafka KRaft (Strimzi) | engine | event bus; topics: `raw-images` `validated` `cdc.*` |
| | Schema Registry (Apicurio) | engine | validate schema Avro |
| | Debezium + Kafka Connect | engine | CDC từ WAL |
| Streaming | Flink | engine (transform) | validate real-time |
| Storage | MinIO Bronze (S3) / MinIO Silver (S3) / Iceberg Gold | **cylinder/bucket** ×3 | 3 tầng medallion |
| | lakeFS | storage | git-for-data (branch/commit) |
| | Iceberg REST catalog (Nessie) | engine | table catalog |
| Processing | Spark | engine ×2 | transform Bronze→Silver, Silver→Gold |
| Quality | Great Expectations | gate ×2 | GE#1, GE#2 (trên mũi tên transform) |
| Serving store | PostgreSQL DW / Redis (Feast online) / Trino | storage/engine | warehouse / online cache / query |
| Orchestration | Airflow / Argo Events | engine | batch DAG / event trigger |
| Catalog | OpenMetadata | engine | catalog + lineage + RBAC |

### Các step (đánh số trên mũi tên)
- **(1a) batch:** `WIDER FACE → MinIO Bronze` (đường vòng trái, thẳng xuống Bronze)
- **(1b) stream:** `Camera/API → Kafka (raw-images)`
- **(1c) cdc:** `App DB → Debezium → Kafka (cdc.*)`
- **(2) validate stream:** `Kafka → Flink`
- **(3) land:** `Flink → MinIO Bronze` (stream + batch hợp nhất ở Bronze — kiểu Kappa)
- **sidecar:** `Flink → Redis (Feast online)` — *vẽ vòng ngoài, coral, không qua medallion*
- **(4) transform:** `MinIO Bronze → [Spark · GE#1] → MinIO Silver`
- **(5) transform:** `MinIO Silver → [Spark · GE#2] → Iceberg Gold`
- **(6) distribute (bus):** `Gold → {OpenMetadata (lineage), lakeFS (version), Trino}` — *1 trục rồi rẽ 3 nhánh*
- **(7) serve:** `Trino → PostgreSQL DW` và `Trino → Feast offline`
- phụ: `Schema Registry ↔ Kafka` (dotted); `Airflow → Spark` (dotted, schedule); `GE fail → Argo Events` (đỏ, alert)
- ra ngoài zone: `Gold/Trino → Training zone (5 load)`; `OpenMetadata → RAG zone (index)`

### Bố cục (trái→phải)
`[3 sources xếp dọc] → [cột ingestion: Kafka+Schema+Debezium] → [Flink] → [hàng medallion: Bronze→Spark→Silver→Spark→Gold, GE phía trên] → [Gold hub → bus xuống: OpenMeta/lakeFS/Trino] → [DW + Feast]`. Stream sidecar (Flink→Redis) ở hàng riêng phía dưới.

### Góp ý
- Đừng vẽ "Spark Bronze/Silver/Gold" (3 Spark). Tầng = storage, Spark = transform ở giữa.
- GE đặt trên mũi tên, không thành node rời lủng lẳng.
- Bus từ Gold quan trọng — tránh 5 mũi tên tỏa ra từ Gold.

---

## §2. ZONE TRAINING PIPELINE (drill-down)

**Namespace:** `ml-platform`

### Components
| Tool | Vai trò |
|---|---|
| Kubeflow (Notebooks · Pipelines · Profiles) | explore + orchestrate training DAG + multi-user theo SSO |
| Katib | HPO (spawn nhiều trial) |
| Ray / KubeRay | distributed training YOLOv11 (GPU) |
| MLflow | tracking + model registry (stage None→Staging→Prod→Archived) |
| Feast | offline (đọc Gold/Iceberg) + online (Redis) |
| ONNX export / TensorRT INT8 | tối ưu inference (GPU) |
| Model store (MinIO/Iceberg) | lưu artifact model |

### Các step
- **(1) materialize:** `Iceberg Gold (qua Trino) → Feast offline`
- **(2) load:** `Feast offline → Kubeflow Pipeline`
- **(3) author:** `Notebooks → Kubeflow Pipeline` (DS viết pipeline)
- **(4) HPO:** `Pipeline → Katib` (Katib fan-out N trial)
- **(5) train:** `Katib/Pipeline → Ray` (train phân tán trên GPU)
- **(6) register:** `Pipeline → MLflow` (log metric/param + register model)
- **(7) export:** `MLflow → ONNX → TensorRT INT8`
- **(8) store:** `ONNX/TensorRT → Model store (MinIO/Iceberg)`
- ra ngoài: `MLflow → Serving zone (deploy)`

**Sub-DAG trong Kubeflow** (vẽ 6 bước nhỏ dọc trong box Pipeline): `load → preprocess → train → evaluate → register → export`.

### Góp ý
- Tách rõ **orchestration (Kubeflow)** vs **tracking/registry (MLflow)** — 2 thứ khác nhau.
- Katib vẽ fan-out trial (1→N) để thấy HPO. Ray là compute backend bên dưới.
- Feast nối cả 2 zone: offline (training) + online (serving) → vẽ 1 Feast với 2 cửa.

---

## §3. ZONE SERVING PIPELINE (drill-down)

**Namespace:** `model-serving`

### Components
| Tool | Vai trò |
|---|---|
| Istio gateway | ingress, mTLS, auth, route |
| KServe (InferenceService) | orchestration serving |
| Knative | scale-to-zero, concurrency |
| Triton + TensorRT | engine inference GPU, dynamic batching |
| KEDA | autoscale theo event (rate/Kafka lag) |
| Flagger | canary 5→25→50→100%, auto-rollback |
| Iter8 | A/B + SLO experiment |
| Feast online (Redis) | online feature lúc infer |

### Các step
- **(1) request:** `End User → Istio gateway`
- **(2) route:** `Istio → KServe`
- **(3) runtime:** `KServe → Triton` (GPU batching)
- **(4) load model:** `MLflow registry → KServe` (lúc startup, dotted)
- **(5) features:** `Feast online (Redis) → KServe` (mỗi request)
- **(6) response:** `Triton → End User`
- **(7) autoscale:** `KServe → Prometheus → KEDA → KServe` (scale)
- **(8) canary:** `Flagger điều phối split traffic primary(v1)/canary(v2)`; `Iter8 chạy A/B`
- ra ngoài: `KServe → Drift zone (predictions)`

**Chi tiết canary:** vẽ 2 box model dưới Flagger — `Model v1 (primary, 90%)` + `Model v2 (canary, 10%)` với nhãn %.

### Góp ý
- Knative = scale-to-zero; KEDA = event-scale → vẽ cả 2, đừng nhầm 1.
- GPU node pool dùng chung với Training + RAG → ghi chú "shared GPU pool".

---

## §4. ZONE DRIFT → RETRAIN → CANARY LOOP ★ (centerpiece — vẽ dạng VÒNG)

**Namespaces:** `ml-monitoring` `monitoring` `data-orchestration` `ml-platform` `model-serving`

### Components
| Tool | Vai trò |
|---|---|
| Evidently | data/prediction drift (KS-test/PSI) |
| Alibi Detect | outlier / adversarial |
| Prometheus + Thanos | metrics + long-term |
| Alertmanager | route alert |
| Argo Events | webhook → trigger pipeline |
| Kubeflow (retrain) | retrain DAG |
| MLflow (Staging) | model mới |
| Flagger | canary promote/rollback |

### Các step (vòng khép kín — bố cục tròn/loop)
- **(1) observe:** `KServe/Triton → Evidently` (predictions) + `→ Alibi Detect` (inputs)
- **(2) score:** `Evidently → Prometheus` (drift_score) ; `Alibi → Prometheus` (outlier)
- **(3) alert:** `Prometheus → Alertmanager` (rule: drift_score>0.5 trong 5m) — *vẽ decision diamond "drift > threshold?"*
- **(4) trigger:** `Alertmanager → Argo Events` (webhook)
- **(5) retrain:** `Argo Events → Kubeflow retrain pipeline`
- **(6) reproducible fetch:** retrain đọc `Iceberg Gold snapshot + lakeFS pinned version` (ghi chú reproducibility)
- **(7) eval:** train (Ray) → eval vs baseline (GE) → nếu `F1>baseline`
- **(8) stage:** `Kubeflow → MLflow Staging`
- **(9) canary:** `MLflow → Flagger → KServe canary 5%`
- **(10) decide:** `Flagger → promote 100%` HOẶC `rollback` → quay lại (1) **loop**

### Góp ý
- Đây là **điểm ăn tiền** — vẽ thành **vòng kín** (mũi tên cuối quay về đầu), có decision diamond.
- Nhấn mạnh reproducibility: lakeFS pin data + Iceberg snapshot.
- Tùy chọn human-in-loop: thêm "approval" trước Production.

---

## §5. ZONE RAG / LLM (drill-down) — 2 phase: indexing + query

**Namespace:** `rag`

### Components
| Tool | Vai trò |
|---|---|
| RAGFlow | orchestrator (chunk/retrieve/generate) |
| Embedding (BGE/MiniLM) | vector hóa |
| Qdrant | vector DB |
| Typesense | keyword/hybrid |
| NeMo Guardrails | input + output safety |
| vLLM | LLM serving GPU |
| Langfuse | observability (trace/cost/eval) |

### Các step
**Phase A — Offline indexing (hàng trên):**
- `Docs (OpenMetadata + DW reports + runbooks) → chunk → Embedding → upsert Qdrant + Typesense`

**Phase B — Online query (hàng dưới):**
- **(1) ask:** `User question → RAGFlow`
- **(2) embed:** `RAGFlow → Embedding query`
- **(3) vector:** `→ Qdrant search`
- **(4) keyword:** `RAGFlow → Typesense search` (song song)
- **(5) merge:** `Qdrant + Typesense → rerank/context`
- **(6) guard-in:** `context → NeMo Guardrails` (jailbreak/PII)
- **(7) generate:** `→ vLLM` (GPU)
- **(8) guard-out:** `vLLM → NeMo Guardrails` (hallucination/safety)
- **(9) answer:** `→ User`
- **(10) trace:** mọi bước `→ Langfuse` (sidecar observability)

### Góp ý
- Guardrails **bọc 2 đầu** LLM (input + output) — vẽ vào/ra đều qua Guardrails.
- Hybrid retrieval = Qdrant (semantic) + Typesense (keyword) merge → thể hiện 2 nhánh gộp.
- Langfuse là sidecar trace tất cả, vẽ đường dotted xanh lá từ các bước.

---

## §6. ZONE PLATFORM (foundation — cross-cutting)

**Namespaces:** `istio-system` `auth` `argocd` `kyverno` `vault` `external-secrets` `cert-manager`

### Components & step
| Tool | Step |
|---|---|
| GitHub | (1) Dev push code |
| ArgoCD | (2) sync từ Git → **deploy toàn bộ namespace** (app-of-apps) — *distribution bus tỏa ra mọi zone* |
| Kyverno | (3) admission → ép governance baseline mọi pod/ns |
| Vault + ESO | (4) inject secret |
| cert-manager | (5) cấp TLS |
| Keycloak + OAuth2 Proxy + Istio | (6) SSO: `user → Keycloak → cookie *.face-detect.dev → mọi UI`; Istio mTLS + AuthorizationPolicy |

**Governance baseline** (vẽ 1 note "áp mọi ns"): ResourceQuota·LimitRange · NetworkPolicy deny-all · mTLS STRICT · AuthorizationPolicy · scoped RBAC+SA · PDB · labels · PriorityClass.

### Góp ý
- ArgoCD = deploy hub → bus tỏa xuống tất cả zone (dùng bus, đừng 7 mũi tên).
- Keycloak = SSO hub → bus tới mọi UI.

---

## §7. ZONE OBSERVABILITY (drill-down) — 3 pipeline song song

**Namespaces:** `monitoring` `logging` `tracing`

### Components & step
- **Hub:** `mọi service → OTel Collector` (OTLP: metrics/logs/traces) — *single entry*
- **(metrics):** `OTel → Prometheus → Thanos (long-term) → Grafana`
- **(logs):** `Filebeat → Logstash → Elasticsearch → Kibana` (ELK, đường thẳng)
- **(traces):** `OTel → Jaeger`
- **(alert):** `Prometheus → Alertmanager` → ra **Drift zone**

### Góp ý
- OTel Collector làm 1 cửa vào duy nhất rồi fan-out 3 pipeline → gọn.
- ELK vẽ pipeline tuyến tính 4 bước. Alertmanager là cầu nối sang drift loop.

---

## §8. LẮP RÁP MASTER (cross-zone) — các mũi tên nối zone

| Từ | Đến | Nhãn |
|---|---|---|
| Data.Gold (Trino/Feast) | Training | (5) load |
| Training.MLflow | Serving | deploy |
| Serving.KServe | Drift | (8) predictions |
| Drift.ArgoEvents | Training.Kubeflow | (9) retrain |
| Drift.Flagger | Serving.KServe | (10) promote |
| Data.OpenMetadata | RAG.Qdrant | index |
| Platform.ArgoCD | mọi zone | deploy (bus) |
| mọi zone | Observability.OTel | telemetry |

Master = 7 swimlane xếp dọc, các mũi tên cross-zone đi trong gutter dọc ở các x khác nhau (tránh chồng). Bản đã có: `01-overview.drawio`.

---

## §9. Mẹo thực hành draw.io

- **Tách Page mỗi zone**: dùng `01-overview.drawio` làm Page "Master", thêm Page mới cho mỗi drill-down (§1–§7).
- **Swimlane**: chèn shape "Container"/"Horizontal Pool" → khóa (lock) → bỏ node vào trong.
- **Logo thật**: panel trái → Search Shapes gõ "kafka", "spark", "kubernetes"… hoặc kéo file PNG vào canvas (đã có logo ở `diagrams/icons/*` của bản render — copy ra dùng).
- **Edge orthogonal**: chọn mũi tên → Edit Style → `edgeStyle=orthogonalEdgeStyle;rounded=1;`. Numbered: double-click gõ `(1) ...`.
- **Distribution bus**: kẻ 1 line từ hub, thêm waypoint, rồi nhánh con từ điểm waypoint.
- **Icon đồng cỡ** ~50px; nhãn 11px dưới icon; storage dùng shape cylinder.
- **Export**: File → Export as → PNG (Zoom 200%) hoặc SVG. Nền trắng.
- **Màu lane** (pastel): platform `#eef2f7` · data `#e9f3fe` · training `#eef7ee` · serving `#fff3e6` · drift `#fdecec` · rag `#f3eefb` · observ `#eafaf0`.

---

## Quyết định đã chốt (research 2026) — đã bake vào drill-down `.drawio`
1. **Iceberg catalog → lakeFS Iceberg REST Catalog.** lakeFS giờ có REST catalog chuẩn → **gộp data-versioning + technical catalog** làm một, **bỏ Nessie** (tránh trùng git-branching). OpenMetadata vẫn lo discovery/lineage/RBAC (tầng governance, khác tầng technical catalog). [Dremio](https://www.dremio.com/blog/data-lakehouse-versioning-comparison-nessie-apache-iceberg-lakefs/) · [lakeFS](https://lakefs.io/blog/lakefs-iceberg-rest-catalog/)
2. **GPU → shared pool, policy-driven.** **MIG** (hardware isolation) cho serving Triton + vLLM + small-train; **full GPU** cho big training (Ray); scheduler **Kueue/Volcano** gang-scheduling + quota. Vẽ GPU pool = 1 node hạ tầng dùng chung. [ScaleOps](https://scaleops.com/blog/kubernetes-gpu-sharing/) · [debugg.ai](https://debugg.ai/resources/kubernetes-gpu-scheduling-2025-kueue-volcano-mig)
3. **Drift loop → có human-approval gate trước Production.** Auto: retrain→eval→Staging→canary; **bắt buộc human approve** trước promote 100%/Prod. [SUPERWISE](https://superwise.ai/blog/the-ultimate-guide-to-mlops-best-practices-and-scalable-tools-for-2025/)

## Drill-down đã vẽ sẵn (editable)
Thư mục `diagrams/icons/drilldown/` — 7 file `.drawio` + `.png` (1 zone/ file): `zone-1-data` `zone-2-training` `zone-3-serving` `zone-4-drift-loop` `zone-5-rag` `zone-6-platform` `zone-7-observability`. Mở trong draw.io để chỉnh. Generator: `drilldowns.py`. Các quyết định trên đã bake sẵn (lakeFS REST catalog, GPU pool MIG, human approval).
