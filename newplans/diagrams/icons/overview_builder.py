#!/usr/bin/env python3
"""Hand-laid overview, Gemini-reference column layout: top platform band,
4 vertical pipeline columns (Processing / ETL & Storage / Training / Drift),
serving box below the right columns, RAG + Observability bands at the bottom.
Emits 01-overview.{svg,png,drawio} (drawio keeps identical routing via baked
waypoints; main numbered flow edges carry flowAnimation).

Layout contract:
- node set and the numbered data flow (1)->(10) are frozen (user decision);
  only geometry/styling may change between revisions.
- the 4 columns share one y-range (340..1200) so the router's horizontal
  gutters stay clean: 310 (below platform), 1245 (below columns), 1690
  (below serving), 2055 (below RAG).
- cards are 150x112 with role captions; column rows sit on a 160px pitch so
  48px inter-row lanes stay free for cross-column runs."""
import os

from diagram_render_lib import Diagram

OUTDIR = os.path.dirname(os.path.abspath(__file__))
W, H = 2500, 2400

ZONES = [
 (120,  100, 2260, 180, "Central & Support Plane  ·  IaC + CI/CD (GitOps) + SSO + Mesh + Policy", "#eef2f7", "#9aa4b2"),
 (400,  340,  390, 860, "Processing (L2)",                                   "#e9f3fe", "#7badd6"),
 (830,  340,  390, 860, "ETL & Storage (L2)",                                "#e9f3fe", "#7badd6"),
 (1260, 340,  390, 860, "Training Pipeline (L3)",                            "#eef7ee", "#86bf86"),
 (1690, 340,  220, 860, "Drift Loop ★",                                      "#fdecec", "#d98a8a"),
 (1260, 1290, 650, 370, "Serving Pipeline (L3)",                             "#fff3e6", "#e0a86a"),
 (120, 1720, 2260, 300, "RAG / LLM (L3 · AI Track 4B)",                      "#f3eefb", "#b193d6"),
 (120, 2090, 2260, 180, "Observability",                                     "#eafaf0", "#86c9a8"),
]

d = Diagram(W, H, "Face-Detect MLOps — System Overview (best-of-breed, numbered data flow)",
            ZONES, subtitle="L1 done · L2/L3/RAG design — best-of-breed 2026, single GKE cluster",
            cards=True, badges=True, zone_header=True, corner_r=10,
            card_h=112, card_icon=56, card_min_w=150, role_caption=True)

# ---- margin corridor rails ----
d.rail("deploy",    1990)  # ArgoCD -> KServe vertical run (right of serving box)
d.rail("telemetry", 2420)  # logs / traces / metrics long-haul to bottom band

# ---------------- Central & Support Plane (y=205) ----------------
d.card("dev",       230, 205, "#dfe7f0", "Developer")
d.icon("github",    400, 205, "github", "GitHub")
d.icon("gha",       570, 205, "githubactions", "GitHub Actions\n(build + test)")
d.icon("fdimage",   740, 205, "fdimage", "face-detect\n(image)")
d.icon("registry",  910, 205, "docker", "Image registry")
d.icon("argocd",   1080, 205, "argocd", "ArgoCD\n(CD · GitOps)")
d.icon("terraform",1250, 205, "terraform", "Terraform\n(GKE + GPU)")
d.icon("ansible",  1420, 205, "ansible", "Ansible")
d.icon("keycloak", 1590, 205, "keycloak", "Keycloak\n(SSO)")
d.icon("istio",    1760, 205, "istio", "Istio\n(ambient mesh)")
d.icon("vault",    1930, 205, "vault", "Vault + ESO\n(secrets)")
d.icon("kyverno",  2100, 205, "kyverno", "Kyverno\n(policy)")
d.icon("certmgr",  2270, 205, "certmanager", "cert-manager\n(TLS)")

# ---------------- Sources (left rail, outside zones) ----------------
d.card("camera", 230,  456, "#cfe0f3", "Camera / API\n(stream)")
d.card("appdb",  230,  616, "#cfe0f3", "App DB\n(CDC)")
d.card("wider",  230, 1096, "#cfe0f3", "WIDER FACE\n(batch)")

# ---------------- Processing column (rows 456..1096, pitch 160) ----------------
d.icon("kafka",     505,  456, "kafka", "Kafka\n(topics)")
d.icon("schemareg", 685,  456, "schemaregistry", "Schema Registry\n(serialization)")
d.icon("debezium",  505,  616, "debezium", "Debezium\n(CDC)")
d.icon("flink",     685,  616, "flink", "Flink\n(validate)")
d.icon("airflow",   505,  776, "airflow", "Airflow\n(orchestration)")
d.icon("ge1",       685,  776, "greatexpectations", "GE #1\n(data quality)")
d.icon("redis",     505,  936, "redis", "Feast online\n(Redis)")
d.icon("minio_b",   595, 1096, "minio", "MinIO Bronze\n(S3 raw)", hl="#fbe3c8")

# ---------------- ETL & Storage column ----------------
d.icon("spark1",    935,  456, "spark", "Spark\n(transform)")
d.icon("minio_s",   935,  616, "minio", "MinIO Silver\n(S3 refined)", hl="#eceff3")
d.icon("openmeta", 1115,  616, "openmetadata", "OpenMetadata\n(catalog + RBAC)")
d.icon("spark2",    935,  776, "spark", "Spark\n(transform)")
d.icon("ge2",      1115,  776, "greatexpectations", "GE #2\n(data quality)")
d.icon("gold",      935,  936, "iceberg", "Iceberg Gold\n(lakehouse)", hl="#fdf2cc")
d.icon("lakefs",   1115,  936, "lakefs", "lakeFS\n(versioning)")
d.icon("trino",     935, 1096, "trino", "Trino\n(SQL engine)")
d.icon("pg",       1115, 1096, "postgresql", "PostgreSQL\n(DW)")

# ---------------- Training column ----------------
d.icon("feast",    1365,  456, "feast", "Feast\n(offline store)")
d.icon("notebooks",1545,  456, "kubeflow", "Notebooks\n(Jupyter)")
d.icon("kubeflow", 1365,  616, "kubeflow", "Kubeflow\n(pipelines)")
d.icon("katib",    1545,  616, "katib", "Katib\n(HPO)")
d.icon("ray",      1365,  776, "ray", "Ray train\n(GPU / CPU)")
d.icon("mlflow",   1365,  936, "mlflow", "MLflow\n(registry)")
d.icon("onnx",     1365, 1096, "nvidia", "ONNX(CPU)/\nTensorRT(GPU)")

# ---------------- Drift column (loop flows bottom -> top -> training) ----------------
d.icon("argoev",   1800,  456, "argo", "Argo Events\n(event trigger)")
d.icon("alertmgr", 1800,  616, "alertmanager", "Alertmanager\n(alerting)")
d.icon("prom",     1800,  776, "prometheus", "Prometheus\n(metrics)")
d.icon("alibi",    1800,  936, "alibidetect", "Alibi Detect\n(outliers)")
d.icon("evidently",1800, 1096, "evidently", "Evidently\n(drift monitor)")

# ---------------- Serving box (rows 1406 / 1566) ----------------
d.icon("kserve",   1365, 1406, "kserve", "KServe\n(inference)")
d.icon("triton",   1545, 1406, "nvidia", "Triton\n(GPU/CPU)")
d.icon("keda",     1725, 1406, "keda", "KEDA\n(autoscale)")
# row 2 sits right of kserve so the column under it stays free for the
# telemetry corridor exits (kserve -> elk / jaeger)
d.card("enduser",  1545, 1566, "#f2dcc2", "End User")
d.icon("flagger",  1725, 1566, "flagger", "Flagger\n(canary)")

# ---------------- RAG band (rows 1820 / 1948) ----------------
d.card("question",  230, 1820, "#e6dcf3", "User question")
d.icon("ragflow",   430, 1820, "ragflow", "RAGFlow\n(RAG engine)")
d.icon("qdrant",    640, 1820, "qdrant", "Qdrant\n(vectors)")
d.icon("typesense", 640, 1948, "typesense", "Typesense\n(keyword)")
d.icon("guardrails",850, 1820, "guardrails", "Guardrails\n(safety)")
d.icon("vllm",     1060, 1820, "vllm", "vLLM / Ollama\n(LLM serving)")
d.icon("langfuse", 1270, 1820, "langfuse", "Langfuse\n(tracing)")

# ---------------- Observability band (row 2195) ----------------
d.icon("thanos",  440, 2195, "thanos", "Thanos\n(metrics LTS)")
d.icon("grafana", 700, 2195, "grafana", "Grafana\n(dashboards)")
d.icon("elk",    1020, 2195, "elasticsearch", "ELK\n(logs)")
d.icon("kibana", 1280, 2195, "kibana", "Kibana\n(log UI)")
d.icon("jaeger", 1600, 2195, "jaeger", "Jaeger + OTel\n(traces)")

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
d.edge("minio_b", "spark1", "(3) read", BLUE, main=True, rail_y=696)
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
d.edge("notebooks", "kubeflow", "", SUPPORT, dashed=True)
d.edge("kubeflow", "katib", "", GREEN)
d.edge("kubeflow", "ray", "", GREEN)
d.edge("kubeflow", "mlflow", "(6) register", GREEN, main=True)
d.edge("mlflow", "onnx", "", GREEN, main=True)

# serving
d.edge("enduser", "kserve", "(7) request", ORANGE, main=True)
d.edge("mlflow", "kserve", "deploy model", ORANGE, dashed=True)
d.edge("kserve", "triton", "", ORANGE, main=True)
d.edge("redis", "kserve", "online features", ORANGE, dashed=True)
d.edge("keda", "kserve", "scale", SUPPORT, dashed=True, rail_y=1486)
d.edge("flagger", "kserve", "(10) promote", RED, main=True, rail_y=1486)

# drift -> retrain loop (column flows bottom-up, then a short hop to training)
d.edge("kserve", "evidently", "(8) predictions", RED, main=True)
d.edge("kserve", "alibi", "", RED, dashed=True)
d.edge("evidently", "prom", "drift_score", RED, main=True)
d.edge("prom", "alertmgr", "alert", RED, main=True)
d.edge("alertmgr", "argoev", "webhook", RED, main=True)
d.edge("argoev", "kubeflow", "(9) retrain", RED, main=True, width=3.2, rail_y=536)

# rag
d.edge("question", "ragflow", "ask", PURPLE, main=True)
d.edge("ragflow", "qdrant", "vector", PURPLE, main=True)
d.edge("ragflow", "typesense", "keyword", PURPLE, rail_y=1884)
d.edge("qdrant", "guardrails", "", PURPLE, main=True)
d.edge("guardrails", "vllm", "generate", PURPLE, main=True)
d.edge("vllm", "langfuse", "", PURPLE, dashed=True)
d.edge("openmeta", "qdrant", "catalog index", SUPPORT, dashed=True)

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
], 120, 2290)

d.write(f"{OUTDIR}/01-overview", png_width=2500, drawio_name="Overview")
print("01-overview written")
