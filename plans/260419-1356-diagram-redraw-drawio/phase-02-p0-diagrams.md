---
phase: 02
title: P0 diagrams (4 core, gen-XML approach)
status: pending
priority: P0
effort: ~2–3h (Claude gen + user review)
blockedBy: [01]
blocks: [05]
---

**Workflow (updated)**:
1. Claude generate `.drawio` XML cho 4 diagrams theo spec section Architecture dưới.
2. User import vào Draw.io → review layout.
3. User tinh chỉnh: nudge positions nếu overlap, swap text-box placeholder sang SVG logo nếu muốn polish.
4. User export PNG 1920px scale 2x.
5. Commit `.drawio` + `.png`.

**Claude responsibility**: XML skeleton 70–80% complete với zones colored, arrows labeled, K8s built-in stencils where available.
**User responsibility**: visual review, positioning tweaks, PNG export.

# Phase 02 — P0 Diagrams (4 core)

## Context Links
- Plan: [../plan.md](./plan.md)
- Phase 01: [./phase-01-setup-template-and-style-guide.md](./phase-01-setup-template-and-style-guide.md)
- Source PNGs: `images/02_batch_data_flow.png`, `06_model_serving.png`, `05_ml_training_pipeline.png`, `01_full_system_overview.png`
- Spec reference: `NEW_PLANS.md` sections 1 (current), 2 (MLOps L2), 3 (MLOps L3), 10 (diagrams ref)

## Overview
- **Priority**: P0 (core coursework diagrams, must-have)
- **Status**: pending
- **Description**: Vẽ 4 diagrams cốt lõi — batch flow, model serving, ML training, full system overview. Thứ tự: từ đơn giản đến phức tạp để practice Draw.io workflow.

## Key Insights
- Thứ tự quan trọng: **02 batch → 06 serving → 05 training → 01 overview**. 01 để cuối vì phức tạp nhất, cần quen tool trước.
- Mỗi diagram = copy `_template.drawio` → rename → edit → export PNG.
- Side-by-side với `architecture.png` khi edit để giữ style consistent.

## Requirements

### Functional per diagram
- Visual flow rõ ràng source → sink, left-to-right primary.
- All data stores/tools/actors có icon + name label.
- Arrows labeled với verb ("Validate", "Query", "Route", "Publish"...).
- Zone containers group by namespace/logical concern.

### Non-Functional
- Style match `architecture.png` L1 (palette, fonts, arrow style).
- PNG export 1920px wide min, scale 2x, white background.
- `.drawio` uncompressed, git-diffable.

## Architecture per Diagram

### 02-batch-data-flow (~1.5h)
**Flow**: `WIDER FACE dataset` → `MinIO Bronze` → `Spark (Bronze→Silver)` → `Great Expectations validation` → `Spark (Silver→Gold)` → `PostgreSQL DW + MinIO Gold + DVC`

**Zones**: `storage-ns` (MinIO + PG), `processing-ns` (Spark), `validation-ns` (GE), `metadata-ns` (DataHub sidebar).
**Canvas**: 1920×1080.
**Arrows labeled**: "Load raw images", "Clean + crop", "Validate expectations", "Aggregate features", "Write gold tables", "Version dataset".

### 06-model-serving (~1.5h)
**Flow**: `End User / Camera` → `NGINX Ingress` (or Istio) → `FastAPI` / `KServe InferenceService` → `Triton Server (ensemble: preproc → YOLOv11 → postproc)` → response
**Sidecars**: Prometheus (metrics), Jaeger (traces), ELK (logs) — arrows dashed thinner.
**Zones**: `serving-ns`, `monitoring-ns`, `tracing-ns`, `logging-ns`.
**Canvas**: 1920×1080.
**Arrows labeled**: "HTTP POST /detect", "Route", "Inference", "Preprocess", "YOLO forward", "NMS postprocess", "Metrics", "Traces", "Logs".

### 05-ml-training-pipeline (~1.5h)
**Flow**: `Kubeflow Notebook (EDA)` → `Kubeflow Pipeline DAG` (data-load → train → eval → register) → `MLflow Registry` → `Model staging: None→Staging→Production` → `KServe deploy canary`
**Side branch**: `Katib HPO` parallel trials → best hyperparams → main pipeline.
**Zones**: `ml-pipeline-ns` (Kubeflow+MLflow+Katib), `storage-ns` (MinIO gold input + MinIO models output), `serving-ns` (KServe destination).
**Canvas**: 1920×1080 (hoặc TD layout 1080×1920 nếu nhiều stages).
**Arrows labeled**: "Load gold features", "Train YOLOv11", "Evaluate mAP", "Register candidate", "Approve staging", "Canary 10%", "Promote prod".

### 01-full-system-overview (~2.5h) — hardest, for last
**Content**: ALL 16 namespaces + 5 actor roles + key data flows.
**Zones** (grouped by horizontal layer):
1. **Top row actors**: End User, Data Scientist, Data Engineer, Data Analyst, ML Engineer, DevOps Admin
2. **Gateway layer**: Istio Gateway, Keycloak, OAuth2 Proxy, cert-manager, NGINX Ingress
3. **Serving layer**: `model-serving-ns` (FastAPI+YOLO), `serving-ns` (KServe+Triton+RayServe), `ml-pipeline-ns` (Kubeflow+MLflow+Katib)
4. **Data layer**: `ingestion-ns` (Kafka+Schema Reg+Debezium), `streaming-ns` (Flink), `processing-ns` (Spark+GE+Generator), `storage-ns` (MinIO+PG+Redis+DVC)
5. **Platform layer**: `rag-ns` (Ollama+RAGFlow+Weaviate+Langfuse), `orchestration-ns` (Airflow), `metadata-ns` (DataHub), `monitoring-ns` (Prom+Graf+Evidently+k6+Locust), `logging-ns` (ELK+Filebeat), `tracing-ns` (Jaeger)
6. **Bottom row external**: Jenkins, GitHub, Docker Hub, Terraform, Ansible, Helm, ArgoCD, deployKF

**Canvas**: 2560×1440 (scale up template).
**Key flows drawn**: main request path (solid bold), CI/CD path (dashed), training path (dotted), observability (thin gray).

## Related Code Files

**Create**:
- `docs/diagrams/02-batch-data-flow.drawio` + `.png`
- `docs/diagrams/06-model-serving.drawio` + `.png`
- `docs/diagrams/05-ml-training-pipeline.drawio` + `.png`
- `docs/diagrams/01-full-system-overview.drawio` + `.png`

**Read only**:
- `docs/diagrams/_template.drawio` (copy base)
- `images/{01,02,05,06}_*.png` (visual reference cho content, không match style)
- `images/architecture.png` (style reference)
- `NEW_PLANS.md` sections 2–3 (technical accuracy check)

## Implementation Steps (per diagram)

1. `cp docs/diagrams/_template.drawio docs/diagrams/XX-slug.drawio`.
2. Mở trong Draw.io/VSCode extension.
3. Update title block: "Face Detection MLOps — {Diagram Name}".
4. Sketch layout 5 phút trên giấy (zones + flow direction).
5. Drag-drop icons từ shape library. Paste SVG cho tool thiếu.
6. Vẽ zone containers (rounded rectangles) với color palette.
7. Connect arrows, label verb-based.
8. Spot-check side-by-side với `architecture.png` L1 → chỉnh color/font/arrow nếu lệch.
9. `File → Save` (ensure Compressed: OFF).
10. `File → Export As → PNG` → options: Zoom 200%, Border 10px, Transparent background OFF (white bg), Save as `XX-slug.png`.
11. `git add docs/diagrams/XX-slug.{drawio,png}`.

## Todo List

- [ ] 02-batch-data-flow: draw + export + commit
- [ ] 06-model-serving: draw + export + commit
- [ ] 05-ml-training-pipeline: draw + export + commit
- [ ] 01-full-system-overview: expand canvas to 2560×1440, draw + export + commit
- [ ] Spot-check all 4 side-by-side consistency review
- [ ] Git commit batch: `docs(diagrams): add P0 architecture diagrams (batch, serving, training, overview)`

## Success Criteria
- [ ] 4 cặp `.drawio` + `.png` trong `docs/diagrams/`
- [ ] Tất cả mở lại được trong Draw.io không lỗi
- [ ] PNG 1920px+ wide, file ≤500KB each (compression reasonable)
- [ ] XML uncompressed (`head -5 *.drawio` readable)
- [ ] Visual side-by-side với `architecture.png`: palette match, font match, arrow style match

## Risk Assessment

| Risk | Mitigation |
|---|---|
| Diagram 01 quá phức tạp 1 ảnh không đọc được | Dùng canvas lớn 2560×1440, font-size hơn cho labels, spacing rộng |
| Effort blow out (quá 7h) | Timebox mỗi diagram 1.5–2h. Nếu quá → simplify: giảm số tool visible, label ngắn hơn |
| Draw.io crash khi paste nhiều SVG logos | Save thường xuyên (Ctrl+S), split work thành sessions |
| Style drift giữa 4 diagrams (vẽ qua nhiều session) | Luôn mở `02-batch-data-flow` (đã hoàn thành) side-by-side khi vẽ diagram kế |

## Security Considerations
Brand logos (Jenkins, Grafana, Ollama, ...) — academic fair-use. Nếu có concern, fallback generic pod + text label.

## Next Steps
→ Phase 03 (P1 diagrams: stream, cdc, drift).
