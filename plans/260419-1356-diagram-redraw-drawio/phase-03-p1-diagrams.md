---
phase: 03
title: P1 diagrams (3, gen-XML approach)
status: pending
priority: P1
effort: ~1.5h
blockedBy: [01]
blocks: [05]
---

**Workflow**: giống Phase 02 (Claude gen XML → user review+tweak → export PNG → commit).

# Phase 03 — P1 Diagrams (3 data flow + drift)

## Context Links
- Plan: [../plan.md](./plan.md)
- Phase 02: [./phase-02-p0-diagrams.md](./phase-02-p0-diagrams.md)
- Source PNGs: `images/03_stream_data_flow.png`, `04_cdc_data_flow.png`, `09_drift_detection.png`
- Spec reference: `NEW_PLANS.md` sections 2 (stream + CDC), 9 (drift), 3 (training retrain loop)

## Overview
- **Priority**: P1 (data engineering flows + ML quality)
- **Status**: pending
- **Description**: Vẽ 3 diagrams về stream processing, CDC từ Postgres, drift detection pipeline.

## Architecture per Diagram

### 03-stream-data-flow (~1h)
**Flow**: `Camera/API producer` → `MinIO upload` + `Kafka metadata event` → `Flink JobManager/TaskManager` → `Real-time validation` → `Redis (feature cache)` + `Kafka inference-results topic`
**Zones**: `ingestion-ns` (Kafka), `streaming-ns` (Flink), `storage-ns` (MinIO + Redis).
**Arrows labeled**: "Upload image", "Publish metadata", "Consume topic", "Validate", "Cache features", "Publish results".
**Canvas**: 1920×1080.

### 04-cdc-data-flow (~1h)
**Flow**: `PostgreSQL app DB` → WAL → `Debezium Connect` → `Kafka face-detection.cdc.postgres.* topics` → `Spark Streaming` / `Flink` → `Data Lake (MinIO Silver)` + `DW update`
**Zones**: external `app PG`, `ingestion-ns` (Debezium + Kafka), `processing-ns` (Spark), `storage-ns` (MinIO + DW).
**Arrows labeled**: "WAL log", "CDC events", "Publish CDC", "Consume", "Transform", "Append silver", "Update DW".
**Canvas**: 1920×1080.

### 09-drift-detection (~1–1.5h)
**Flow**: `PostgreSQL DW (Gold feature_image_stats)` → `Evidently AI drift calc` (daily Airflow CronJob) → `Prometheus metrics + alert` → `Grafana dashboard` + `Alertmanager` → `Slack/PagerDuty` → `Airflow retrain DAG trigger` (if drift > threshold)
**Zones**: `storage-ns` (PG DW), `monitoring-ns` (Evidently + Prom + Graf), `orchestration-ns` (Airflow), external (Slack).
**Sub-flow**: retrain DAG → Kubeflow Pipeline → MLflow new version → KServe canary deploy.
**Arrows labeled**: "Query gold features", "Compute drift score", "Export metrics", "Alert if threshold", "Notify", "Trigger retrain DAG".
**Canvas**: 1920×1200 (vertical stretch để fit sub-flow).

## Related Code Files

**Create**:
- `docs/diagrams/03-stream-data-flow.drawio` + `.png`
- `docs/diagrams/04-cdc-data-flow.drawio` + `.png`
- `docs/diagrams/09-drift-detection.drawio` + `.png`

**Read only**:
- `docs/diagrams/_template.drawio`
- `docs/diagrams/02-batch-data-flow.drawio` (style consistency reference from Phase 02)
- `images/{03,04,09}_*.png`
- `NEW_PLANS.md` sections 2, 9

## Implementation Steps
Giống Phase 02 workflow (copy template, sketch, draw, export, commit).

**Extra rule**: mở 1 diagram P0 đã done song song khi vẽ P1 để đảm bảo style consistent (palette, font, arrow style).

## Todo List

- [ ] 03-stream-data-flow: draw + export + commit
- [ ] 04-cdc-data-flow: draw + export + commit
- [ ] 09-drift-detection: draw + export + commit (vertical stretch canvas nếu cần)
- [ ] Side-by-side review với P0 diagrams
- [ ] Git commit batch: `docs(diagrams): add P1 data flow + drift diagrams`

## Success Criteria
- [ ] 3 cặp `.drawio` + `.png` trong `docs/diagrams/`
- [ ] Style consistent với P0 (spot-check 2 pair bất kỳ)
- [ ] Drift diagram thể hiện rõ retrain feedback loop

## Risk Assessment

| Risk | Mitigation |
|---|---|
| Drift diagram nhồi retrain sub-flow phức tạp | Tách retrain thành sub-diagram stub reference tới `05-ml-training-pipeline.drawio` |
| CDC topic naming inconsistent với Kafka section brainstorm | Verify `face-detection.cdc.postgres.*` pattern khớp `NEW_PLANS.md` §2.2.1 |

## Security Considerations
N/A.

## Next Steps
→ Phase 04 (P2: RAG + SSO + LLM security).
