---
phase: 7
title: "T1 Data pipeline (L2)"
status: pending
priority: P1
effort: "3-4d"
dependencies: [6]
---

# Phase 7: T1 Data Pipeline (L2 Lakehouse)

## Overview
Dựng lakehouse theo sơ đồ zone Data: 3 nguồn (batch/stream/CDC) → Kafka/Flink → MinIO Bronze→Silver→Iceberg Gold (Spark + GE gates) → Trino/PG; lakeFS version; Airflow orchestrate; OpenMetadata catalog. Spec chi tiết per-tool: `docs/architecture/phase-t1-data-pipeline.md` (nguồn từ newplans) — phase này là thứ tự dựng + wiring + values.

## Thứ tự dựng (3 đợt nhỏ, mỗi đợt e2e demo được)
**7a — Object store + batch path 🟢**: MinIO → lakeFS → Spark-operator → GE → Trino. Demo: WIDER FACE subset → Bronze → Spark transform → Silver → GE pass → Gold (Iceberg qua lakeFS REST catalog) → Trino query.
**7b — Stream + CDC path 🟢**: Strimzi Kafka (+Schema Registry) → Flink (validate) → Bronze; PostgreSQL app DB + Debezium → Kafka. Demo: producer giả camera + 1 bảng PG đổi → topic → Flink → MinIO.
**7c — Orchestrate + catalog 🟢/🟡**: Airflow (DAG chạy 7a pipeline định kỳ) → Redis (Feast online store chuẩn bị cho T2) → OpenMetadata (🟡 nặng — bật sau cùng, ingest lineage từ Trino/Airflow).

## Values & Apps
Mỗi tool: `gitops/platform/data/<tool>/values-cpu.yaml` + Application sync-wave 2-4. Jobs/DAGs vào `pipelines/{spark-jobs,flink-jobs,airflow-dags}/` — Airflow git-sync DAGs từ chính monorepo.

## RAM budget (máy 40GB — validated)
Kafka 1 broker dev; Flink session 1 TM; Spark on-demand; OpenMetadata bật được (~4GB) nhưng vẫn dựng sau cùng 7c. <!-- Updated: Validation Session 1 --> Ghi expected RAM từng values-cpu vào README data.

## Implementation Steps
1. 7a tools (5 Application) + spark job đầu (`pipelines/spark-jobs/bronze-to-silver/`) + GE suite + demo script.
2. 7b: Strimzi CRD-based; Flink job validate (`pipelines/flink-jobs/validate/`); Debezium connector config.
3. 7c: Airflow values (git-sync) + DAG medallion; Redis; OpenMetadata (hoặc defer có ghi chú).
4. Smoke e2e cả 3 path; README `gitops/platform/data/` + `pipelines/` (kiến trúc + cách thêm job mới).

## Success Criteria
- [ ] 3 demo path chạy: batch→Gold→Trino query trả kết quả; stream+CDC vào Bronze; DAG schedule chạy
- [ ] GE gate fail chặn được write (test negative)
- [ ] lakeFS commit/branch hoạt động trên Gold
- [ ] README data + pipelines viết xong, ghi RAM từng tool

## Risk Assessment
- RAM tổng vượt máy → thứ tự 7a/7b/7c cho phép dừng giữa chừng vẫn có giá trị; scale-to-zero những gì không demo.
- Iceberg + lakeFS REST catalog config kẹt → đã có research report 260604 làm chuẩn; fallback Iceberg REST catalog độc lập.

## Red-Team Adjudicated Updates (260611)
- F2: Trino values-cpu: `server.workers=0` (coordinator-only) + heap 2G + query.max-memory-per-node=512MB — default chart = 16-24GB.
- F8: JVM sizing: Kafka Xmx512m, Connect 768m, Flink TM 1g/1 slot.
- F4: OpenMetadata: host `vm.max_map_count=262144`, ES heap ≤1g, TẮT Airflow-ingestion bundled (dùng Airflow T1).
- O7: tách wave operator vs CR (Strimzi op wave N → Kafka/Connect/Topic CR wave N+1; tương tự spark/flink operator).
- O8: PG values: `wal_level=logical` + max_replication_slots từ lần cài đầu (Debezium).
- S10: đúng 1 KafkaConnect cluster; Debezium = KafkaConnector CR; CẤM Debezium Server standalone.
- S11: bảng phân vai catalog vào README data: lakeFS REST = Iceberg catalog (write-path) · OpenMetadata = discovery/lineage (read-only, cấm reference trong job/Trino config).
- S9: GE 1 config root `pipelines/quality/`, suites: data-gate.* vs model-eval.*.
- B6: Airflow = ETL định kỳ DUY NHẤT (rule trigger toàn cục).
