#!/usr/bin/env python3
"""Hand-laid swimlane overview, polished hall-of-fame style: full-card nodes
with shadow, numbered circle badges, zone header bands, rounded elbows.
Emits 01-overview.{svg,png,drawio} (drawio keeps identical routing via baked
waypoints; main numbered flow edges carry flowAnimation).

Layout contract:
- zone order is fixed (user decision): Platform / Data / Training / Serving /
  Drift / RAG / Observability
- zones span x=120..2080; long cross-zone arrows never cross zone interiors:
  they run on margin rails (left rail = drift->retrain loop, right rails =
  deploy / features+metadata / telemetry) and only travel horizontally inside
  the gutters between zones.
- full cards are ~116x92: row pitch 116, zone heights sized accordingly."""
import os

from diagram_render_lib import Diagram

OUTDIR = os.path.dirname(os.path.abspath(__file__))
W, H = 2320, 2300

ZONES = [
 (120,  100, 1960, 140, "Platform  ·  IaC + CI/CD (GitOps) + SSO + Mesh + Policy",         "#eef2f7", "#9aa4b2"),
 (120,  290, 1960, 498, "Data Pipeline (L2)  ·  Iceberg Lakehouse  (batch + stream + CDC)", "#e9f3fe", "#7badd6"),
 (120,  838, 1960, 266, "Training Pipeline (L3)",                                           "#eef7ee", "#86bf86"),
 (120, 1154, 1960, 266, "Serving Pipeline (L3)",                                            "#fff3e6", "#e0a86a"),
 (120, 1470, 1960, 174, "Drift -> Retrain -> Canary Loop  ★  (L3 centerpiece)",             "#fdecec", "#d98a8a"),
 (120, 1694, 1960, 266, "RAG / LLM (L3 · AI Track 4B)",                                     "#f3eefb", "#b193d6"),
 (120, 2010, 1960, 152, "Observability",                                                    "#eafaf0", "#86c9a8"),
]

d = Diagram(W, H, "Face-Detect MLOps — System Overview (best-of-breed, numbered data flow)",
            ZONES, subtitle="L1 done · L2/L3/RAG design — best-of-breed 2026, single GKE cluster",
            cards=True, badges=True, zone_header=True, corner_r=10)

# ---- margin corridor rails (outside the zone boxes) ----
d.rail("retrain",   60)    # left:  drift -> retrain loop (centerpiece)
d.rail("deploy",   2130)   # right: CD / model deploy
d.rail("features", 2200)   # right: online features + catalog metadata
d.rail("telemetry", 2270)  # right: logs / traces / metrics long-haul

# ---------------- Platform (y=185) ----------------
d.card("dev",       200, 185, "#dfe7f0", "Developer")
d.icon("github",    348, 185, "github", "GitHub")
d.icon("gha",       496, 185, "githubactions", "GitHub Actions\nbuild+test")
d.icon("fdimage",   644, 185, "fdimage", "face-detect\nimage")
d.icon("registry",  792, 185, "docker", "Image registry")
d.icon("argocd",    940, 185, "argocd", "ArgoCD\nCD (GitOps)")
d.icon("terraform",1080, 185, "terraform", "Terraform\nGKE+GPU")
d.icon("ansible",  1212, 185, "ansible", "Ansible")
d.icon("keycloak", 1350, 185, "keycloak", "Keycloak SSO")
d.icon("istio",    1488, 185, "istio", "Istio ambient")
d.icon("vault",    1620, 185, "vault", "Vault + ESO")
d.icon("kyverno",  1748, 185, "kyverno", "Kyverno")
d.icon("certmgr",  1888, 185, "certmanager", "cert-manager")

# ---------------- Data (rows 380 / 496 / 612 / 728) ----------------
d.icon("ge1",  645, 380, "greatexpectations", "GE #1")     # offset so drops into Spark stay clear
d.icon("ge2", 1025, 380, "greatexpectations", "GE #2")
d.card("wider",  220, 496, "#cfe0f3", "WIDER FACE\n(batch)")
d.icon("minio_b",  580, 496, "minio", "MinIO\nBronze (S3)")
d.icon("spark1",   760, 496, "spark", "Spark\ntransform")
d.icon("minio_s",  940, 496, "minio", "MinIO\nSilver (S3)")
d.icon("spark2",  1120, 496, "spark", "Spark\ntransform")
d.icon("gold",    1300, 496, "iceberg", "Iceberg\nGold")
d.icon("openmeta", 1650, 496, "openmetadata", "OpenMetadata\ncatalog+RBAC")
d.card("camera", 220, 612, "#cfe0f3", "Camera / API\n(stream)")
d.icon("kafka",    430, 612, "kafka", "Kafka topics")
d.icon("flink",    620, 612, "flink", "Flink validate")
d.icon("redis",    850, 612, "redis", "Feast online")
d.card("appdb",  220, 728, "#cfe0f3", "App DB\n(CDC)")
d.icon("debezium", 430, 728, "debezium", "Debezium")
d.icon("schemareg", 620, 728, "schemaregistry", "Schema Registry")
d.icon("airflow",  760, 728, "airflow", "Airflow")
d.icon("lakefs",  1120, 728, "lakefs", "lakeFS\n(versioning)")
d.icon("trino",   1300, 728, "trino", "Trino")
d.icon("pg",      1490, 728, "postgresql", "PostgreSQL DW")

# ---------------- Training (rows 928 / 1044) ----------------
d.icon("notebooks", 580, 928, "kubeflow", "Notebooks")
d.icon("katib",    1150, 928, "katib", "Katib HPO")
d.icon("feast",     770, 1044, "feast", "Feast offline")
d.icon("kubeflow",  960, 1044, "kubeflow", "Kubeflow\nPipelines")
d.icon("ray",      1150, 1044, "ray", "Ray train\nGPU / CPU")
d.icon("mlflow",   1340, 1044, "mlflow", "MLflow\nregistry")
d.icon("onnx",     1540, 1044, "nvidia", "ONNX(CPU)/\nTensorRT(GPU)")

# ---------------- Serving (rows 1244 / 1360) ----------------
d.card("enduser", 220, 1244, "#f2dcc2", "End User")
d.icon("kserve",  440, 1244, "kserve", "KServe")
d.icon("triton",  620, 1244, "nvidia", "Triton\n(GPU/CPU)")
d.icon("keda",    810, 1244, "keda", "KEDA")
d.icon("flagger", 810, 1360, "flagger", "Flagger canary")

# ---------------- Drift (row 1560) ----------------
d.icon("evidently", 440, 1560, "evidently", "Evidently")
d.icon("alibi",     630, 1560, "alibidetect", "Alibi Detect")
d.icon("prom",      830, 1560, "prometheus", "Prometheus")
d.icon("alertmgr", 1020, 1560, "alertmanager", "Alertmanager")
d.icon("argoev",   1210, 1560, "argo", "Argo Events")

# ---------------- RAG (rows 1784 / 1842 / 1900) ----------------
d.card("question", 220, 1842, "#e6dcf3", "User question")
d.icon("ragflow",   430, 1842, "ragflow", "RAGFlow")
d.icon("qdrant",    610, 1784, "qdrant", "Qdrant")
d.icon("typesense", 610, 1900, "typesense", "Typesense")
d.icon("guardrails", 800, 1842, "guardrails", "Guardrails")
d.icon("vllm",      980, 1842, "vllm", "vLLM / Ollama")
d.icon("langfuse", 1160, 1842, "langfuse", "Langfuse")

# ---------------- Observability (row 2100, spread to fill the zone width) ----------------
d.icon("thanos",  440, 2100, "thanos", "Thanos")
d.icon("grafana", 700, 2100, "grafana", "Grafana")
d.icon("elk",    1020, 2100, "elasticsearch", "ELK")
d.icon("kibana", 1280, 2100, "kibana", "Kibana")
d.icon("jaeger", 1600, 2100, "jaeger", "Jaeger + OTel")

# ---- edges ----
GRAY, BLUE, GREEN, ORANGE, RED, PURPLE, TEAL = "#5b6472", "#1864ab", "#2b8a3e", "#b8741a", "#c92a2a", "#7c3aed", "#059669"
SUPPORT = "#9aa4b2"

# platform CI/CD chain
d.edge("dev", "github", "code", GRAY)
d.edge("github", "gha", "push", GRAY)
d.edge("gha", "fdimage", "build", GRAY)
d.edge("fdimage", "registry", "push image", GRAY)
d.edge("registry", "argocd", "", GRAY)
d.edge("argocd", "kserve", "deploy app", GRAY, dashed=True, corridor="deploy")
d.edge("terraform", "ansible", "", SUPPORT, dashed=True)
d.edge("ansible", "istio", "provision GKE+GPU", SUPPORT, dashed=True, via="below")

# data: sources -> ingestion -> medallion
d.edge("wider", "minio_b", "(1b) batch", BLUE, main=True)
d.edge("camera", "kafka", "(1s) stream", BLUE, main=True)
d.edge("appdb", "debezium", "(1c) CDC", BLUE, main=True)
d.edge("debezium", "kafka", "", BLUE, main=True)
d.edge("schemareg", "kafka", "", SUPPORT, dashed=True)
d.edge("kafka", "flink", "(2) validate", BLUE, main=True)
d.edge("flink", "redis", "", BLUE, dashed=True)
d.edge("flink", "minio_b", "", BLUE, dashed=True)
d.edge("minio_b", "spark1", "(3) read", BLUE, main=True)
d.edge("spark1", "minio_s", "", BLUE, main=True)
d.edge("minio_s", "spark2", "", BLUE, main=True)
d.edge("spark2", "gold", "(4) write Gold", BLUE, main=True)
d.edge("ge1", "minio_s", "", GREEN, dashed=True)
d.edge("ge2", "gold", "", GREEN, dashed=True)
d.edge("gold", "lakefs", "", SUPPORT, dashed=True)
d.edge("trino", "gold", "", BLUE)
d.edge("gold", "pg", "", BLUE)
d.edge("airflow", "spark1", "", SUPPORT, dashed=True)
d.edge("gold", "openmeta", "", GREEN, dashed=True)

# training
d.edge("trino", "feast", "(5) load", GREEN, main=True)
d.edge("feast", "kubeflow", "", GREEN, main=True)
d.edge("notebooks", "kubeflow", "", SUPPORT, dashed=True, via="above")
d.edge("kubeflow", "katib", "", GREEN)
d.edge("kubeflow", "ray", "", GREEN)
d.edge("kubeflow", "mlflow", "(6) register", GREEN, main=True, via="below")
d.edge("mlflow", "onnx", "", GREEN, main=True)

# serving
d.edge("enduser", "kserve", "(7) request", ORANGE, main=True)
d.edge("mlflow", "kserve", "deploy model", ORANGE, dashed=True)
d.edge("kserve", "triton", "", ORANGE, main=True)
d.edge("redis", "kserve", "online features", ORANGE, dashed=True, corridor="features")
d.edge("keda", "kserve", "scale", SUPPORT, dashed=True, via="above")
d.edge("flagger", "kserve", "(10) promote", RED, main=True, via="below")

# drift -> retrain loop
d.edge("kserve", "evidently", "(8) predictions", RED, main=True)
d.edge("kserve", "alibi", "", RED, dashed=True)
d.edge("evidently", "prom", "drift_score", RED, main=True, via="below")
d.edge("prom", "alertmgr", "alert", RED, main=True)
d.edge("alertmgr", "argoev", "webhook", RED, main=True)
d.edge("argoev", "kubeflow", "(9) retrain", RED, main=True, width=3.2, corridor="retrain")

# rag
d.edge("question", "ragflow", "ask", PURPLE, main=True)
d.edge("ragflow", "qdrant", "vector", PURPLE, main=True)
d.edge("ragflow", "typesense", "keyword", PURPLE)
d.edge("qdrant", "guardrails", "", PURPLE, main=True)
d.edge("guardrails", "vllm", "generate", PURPLE, main=True)
d.edge("vllm", "langfuse", "", PURPLE, dashed=True)
d.edge("openmeta", "qdrant", "catalog index", SUPPORT, dashed=True, corridor="features")

# observability
d.edge("prom", "thanos", "store", TEAL, corridor="telemetry")
d.edge("thanos", "grafana", "", TEAL)
d.edge("elk", "kibana", "", TEAL)
d.edge("kserve", "elk", "logs", TEAL, dashed=True, corridor="telemetry")
d.edge("kserve", "jaeger", "traces", TEAL, dashed=True, corridor="telemetry")

d.legend([
    ("#1f2937", False, "solid thick = main numbered flow (1)→(10)"),
    ("#9aa4b2", True,  "dashed = support / control plane"),
    ("#c92a2a", False, "red = drift → retrain → canary loop ★"),
], 120, 2190)

d.write(f"{OUTDIR}/01-overview", png_width=2400, drawio_name="Overview")
print("01-overview written")
