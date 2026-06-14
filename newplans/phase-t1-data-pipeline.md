# T1 — Data Pipeline (L2, best-of-breed lakehouse)

**Priority:** P0 · **Status:** pending · **Blocks:** T2,T4 · **Sơ đồ:** `diagrams/icons/02-data-pipeline.png`

## Overview
Lakehouse medallion **Bronze→Silver→Gold** trên **Apache Iceberg** + MinIO, versioned bằng **lakeFS**, query bằng **Trino**, lineage/governance bằng **OpenMetadata**. 3 luồng: Batch (WIDER FACE), Stream (Flink), CDC (Debezium).

## Namespaces + Tools

| Namespace | Tool | Vai trò |
|---|---|---|
| `data-ingestion` | **Kafka KRaft (Strimzi operator)** + **Schema Registry** + **Debezium** + **Kafka Connect** | event streaming, schema governance (Avro), CDC từ WAL |
| `data-streaming` | **Apache Flink** (Flink K8s Operator) | real-time validate, exactly-once |
| `data-processing` | **Apache Spark** (Spark Operator) | batch ETL Bronze/Silver/Gold |
| `data-storage` | **MinIO** + **Apache Iceberg** + **lakeFS** + **Trino** + **PostgreSQL** + **Redis** | data lake (S3), table format ACID/time-travel, git-for-data, SQL engine, serving metadata, online cache |
| `data-quality` | **Great Expectations** | 2 quality gates (Bronze→Silver, Silver→Gold) |
| `data-orchestration` | **Airflow** (KubernetesExecutor) + **Argo Events** | ETL DAG + event-driven trigger |
| `data-catalog` | **OpenMetadata** | catalog + column-lineage + **RBAC theo SSO** |

## Design
- **Claim-check:** ảnh→MinIO, metadata event (~500B)→Kafka.
- **Iceberg lakehouse:** Bronze/Silver/Gold là Iceberg tables trên MinIO → ACID, schema-evolution, time-travel. Catalog: REST catalog/Nessie (open question #5).
- **lakeFS:** branch/commit data như git → reproducible training set, rollback.
- **Trino:** federated SQL trên Iceberg → ML đọc Gold; Data Analyst query.
- **Stream:** Kafka→Flink validate→Redis (online feature).
- **CDC:** Debezium→Kafka Connect→Kafka→Spark merge→Iceberg.
- **Governance:** Iceberg + Airflow → ingest lineage vào OpenMetadata tự động; policy theo role.

## Build Steps
1. Strimzi Kafka + Schema Registry + Debezium/Connect.
2. MinIO + Iceberg REST catalog + lakeFS.
3. Spark Operator: Bronze/Silver/Gold jobs ghi Iceberg; GE 2 gates.
4. Flink Operator: stream validate job.
5. Trino + PostgreSQL + Redis.
6. Airflow DAG + Argo Events; OpenMetadata ingestion (Spark/Airflow/Iceberg connectors).

## Success Criteria
- [ ] Iceberg Gold tables query được qua Trino, time-travel hoạt động
- [ ] lakeFS commit/branch data thành công
- [ ] GE 2 gates pass; fail → Argo Events alert
- [ ] OpenMetadata hiển thị lineage source→Gold + áp policy theo role

## Risks
- Iceberg catalog choice (REST/Nessie/Hive) ảnh hưởng compatibility → chốt sớm.
- OpenMetadata cần ES + MySQL (nặng) → namespace riêng, quota đủ.
