#!/usr/bin/env python3
"""Per-zone drill-down diagrams -> .png/.svg/.drawio via the shared corridor
renderer (diagram_render_lib). Decisions baked in: lakeFS Iceberg REST Catalog
(no Nessie), shared GPU pool (MIG + Kueue), human approval gate.
Numbered edge labels "(N) ..." mark the main flow (thick + flowAnimation in drawio)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from diagram_render_lib import Diagram

OUT = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT, exist_ok=True)


S = 1.3   # card-style re-space: uniform scale opens room for 116x92 cards
          # while keeping each zone's relative layout (fonts stay fixed size)


def _autofit_zones(zs, whs):
    """tighten each zone box around the cards whose center lies inside it
    (top inset clears the 30px header band); then re-expand parents so nested
    zone boxes stay fully contained. Fixes band/bottom collisions generically."""
    PAD_T, PAD_B, PAD_X = 46, 20, 18
    fitted = []
    for (x, y, w, h, t, f, st) in zs:
        inside = [(nx, ny, nw, nh) for nx, ny, nw, nh in whs if x < nx < x + w and y < ny < y + h]
        if not inside:
            fitted.append([x, y, w, h, t, f, st]); continue
        l = min(nx - nw / 2 for nx, ny, nw, nh in inside) - PAD_X
        r = max(nx + nw / 2 for nx, ny, nw, nh in inside) + PAD_X
        tp = min(ny - nh / 2 for nx, ny, nw, nh in inside) - PAD_T
        bt = max(ny + nh / 2 for nx, ny, nw, nh in inside) + PAD_B
        fitted.append([l, tp, r - l, bt - tp, t, f, st])
    for i, (ox, oy, ow, oh, *_r) in enumerate(zs):       # parent ⊇ child boxes
        for j, fj in enumerate(fitted):
            if i == j:
                continue
            cx, cy = fj[0] + fj[2] / 2, fj[1] + fj[3] / 2
            if ox < cx < ox + ow and oy < cy < oy + oh and (zs[j][2] < ow and zs[j][3] < oh):
                fi = fitted[i]
                l = min(fi[0], fj[0] - 12); tp = min(fi[1], fj[1] - 46)
                r = max(fi[0] + fi[2], fj[0] + fj[2] + 12); bt = max(fi[1] + fi[3], fj[1] + fj[3] + 12)
                fitted[i] = [l, tp, r - l, bt - tp, fi[4], fi[5], fi[6]]
    return [tuple(z) for z in fitted]


def build(outname, title, W, H, Z, N, E):
    zs = [(x * S, y * S, w * S, h * S, t, f, st) for x, y, w, h, t, f, st in Z]
    whs = []
    for nid, (x, y, k, ic, lbl) in N.items():
        if k == 'i':
            w = max(116, max(len(ln) for ln in lbl.split("\n")) * 6.2 + 18)
            whs.append((x * S, y * S, w, 92))
        else:
            whs.append((x * S, y * S, 128, 54))
    zs = _autofit_zones(zs, whs)
    d = Diagram(int(W * S), int(H * S), title, zs, aw=128,
                cards=True, badges=True, zone_header=True, corner_r=10)
    for nid, (x, y, k, ic, lbl) in N.items():
        (d.icon if k == 'i' else d.card)(nid, x * S, y * S, ic, lbl)
    for row in E:
        s, t, lbl, col, dash = row[:5]
        opts = dict(row[5]) if len(row) > 5 else {}
        if 'rail_y' in opts:
            opts['rail_y'] *= S
        d.edge(s, t, lbl, col, dashed=bool(dash), main=lbl.startswith("("), **opts)
    d.write(f"{OUT}/{outname}", png_width=2200, drawio_name=outname)
    print("built", outname)


def ni(N, id, x, y, ic, l): N[id] = (x, y, 'i', ic, l)
def na(N, id, x, y, f, l): N[id] = (x, y, 'a', f, l)


# ============================ ZONE 1: DATA ============================
N = {}
na(N, "wider", 110, 230, "#cfe0f3", "WIDER FACE\n(batch)")
na(N, "camera", 110, 640, "#cfe0f3", "Camera / API\n(stream)")
na(N, "appdb", 110, 780, "#cfe0f3", "App DB\n(CDC)")
ni(N, "bronze", 440, 230, "minio", "MinIO Bronze\n(S3)")
ni(N, "silver", 820, 230, "minio", "MinIO Silver\n(S3)")
ni(N, "gold", 1180, 230, "iceberg", "Iceberg Gold")
ni(N, "lakefs", 1450, 230, "lakefs", "lakeFS REST\ncatalog + version")
ni(N, "trino", 1690, 230, "trino", "Trino")
ni(N, "pg", 1930, 230, "postgresql", "PostgreSQL DW")
ni(N, "redisf", 1930, 360, "redis", "Feast online")
ni(N, "spark1", 620, 430, "spark", "Spark\ntransform")
ni(N, "ge1", 530, 360, "greatexpectations", "GE #1")     # offset so vertical drops into Spark stay clear
ni(N, "spark2", 1000, 430, "spark", "Spark\ntransform")
ni(N, "ge2", 910, 360, "greatexpectations", "GE #2")
ni(N, "kafka", 450, 640, "kafka", "Kafka topics\nraw/validated/cdc")
ni(N, "schema", 650, 600, "schemaregistry", "Schema Registry")
ni(N, "debezium", 450, 790, "debezium", "Debezium")
ni(N, "connect", 650, 790, "kafkaconnect", "Kafka Connect")
ni(N, "flink", 950, 650, "flink", "Flink validate")
ni(N, "airflow", 1180, 650, "airflow", "Airflow")
ni(N, "argoev", 1340, 650, "argo", "Argo Events")
ni(N, "openmeta", 1600, 650, "openmetadata", "OpenMetadata\ncatalog+lineage+RBAC")
Z = [(300, 150, 1820, 250, "ns: data-storage  ·  lakehouse (storage layers)", "#fff5e6", "#e0a86a"),
     (300, 330, 860, 170, "ns: data-processing  (Spark transforms)", "#eef0fb", "#7d8fd6"),
     (300, 560, 560, 300, "ns: data-ingestion", "#e9f3fe", "#7badd6"),
     (880, 580, 220, 160, "ns: data-streaming", "#eef7ee", "#86bf86"),
     (1140, 580, 300, 160, "ns: data-orchestration", "#f3eefb", "#b193d6"),
     (1480, 580, 360, 160, "ns: data-catalog", "#fde9f0", "#d98ab0")]
E = [("wider", "bronze", "(1a) batch", "#1864ab", 0), ("camera", "kafka", "(1b) stream", "#1864ab", 0),
     ("appdb", "debezium", "(1c) cdc", "#1864ab", 0), ("debezium", "connect", "", "#c92a2a", 0), ("connect", "kafka", "", "#c92a2a", 0),
     ("schema", "kafka", "", "#9aa4b2", 1), ("kafka", "flink", "(2) validate", "#1864ab", 0),
     ("flink", "bronze", "(3) land", "#1864ab", 0), ("flink", "redisf", "sidecar: online feat", "#e8590c", 1),
     ("bronze", "spark1", "(4) read", "#1864ab", 0), ("spark1", "silver", "write", "#1864ab", 0), ("ge1", "silver", "GE#1", "#2b8a3e", 1),
     ("silver", "spark2", "(5) read", "#1864ab", 0), ("spark2", "gold", "write", "#1864ab", 0), ("ge2", "gold", "GE#2", "#2b8a3e", 1),
     ("gold", "lakefs", "(6) version", "#1864ab", 0), ("gold", "trino", "", "#1864ab", 0), ("trino", "pg", "DW", "#1864ab", 0),
     ("gold", "openmeta", "lineage", "#2b8a3e", 1), ("airflow", "spark1", "schedule", "#9aa4b2", 1), ("airflow", "spark2", "", "#9aa4b2", 1),
     ("ge2", "argoev", "fail→alert", "#c92a2a", 1)]
build("zone-1-data", "Drill-down — Data Pipeline (L2 lakehouse: batch+stream+CDC)", 2240, 920, Z, N, E)

# ============================ ZONE 2: TRAINING ============================
N = {}
ni(N, "trino", 110, 300, "trino", "Gold via Trino\n(Iceberg)")
ni(N, "feast", 330, 300, "feast", "Feast offline")
ni(N, "redisf", 330, 440, "redis", "Feast online")
ni(N, "notebooks", 560, 200, "kubeflow", "Notebooks")
ni(N, "kfp", 560, 330, "kubeflow", "Kubeflow Pipeline\nload→prep→train→eval→register→export")
ni(N, "katib", 880, 260, "katib", "Katib HPO\n(trials fan-out)")
ni(N, "ray", 880, 400, "ray", "Ray / KubeRay\ntrain (GPU / CPU-slow)")
ni(N, "gpu", 880, 540, "gpu", "GPU pool (optional)\nCPU fallback (slow)")
ni(N, "mlflow", 1150, 330, "mlflow", "MLflow\ntracking + registry")
ni(N, "onnx", 1400, 300, "kserve", "ONNX export (CPU)")
ni(N, "trt", 1400, 430, "nvidia", "TensorRT INT8\n(GPU only)")
ni(N, "store", 1620, 330, "minio", "Model store\n(MinIO/Iceberg)")
Z = [(80, 150, 420, 360, "ns: data-storage / feast (inputs)", "#fff5e6", "#e0a86a"),
     (520, 150, 780, 440, "ns: ml-platform", "#eef0fb", "#7d8fd6"),
     (1320, 250, 460, 230, "export + model store", "#eef7ee", "#86bf86")]
E = [("trino", "feast", "(1) materialize", "#2b8a3e", 0), ("feast", "redisf", "online", "#2b8a3e", 1),
     ("feast", "kfp", "(2) load features", "#2b8a3e", 0), ("notebooks", "kfp", "(3) author", "#9aa4b2", 1),
     ("kfp", "katib", "(4) HPO", "#2b8a3e", 0), ("kfp", "ray", "(5) train", "#2b8a3e", 0), ("ray", "gpu", "uses", "#9aa4b2", 1),
     ("katib", "ray", "best trial", "#2b8a3e", 1), ("kfp", "mlflow", "(6) register", "#2b8a3e", 0),
     ("mlflow", "onnx", "(7) export", "#2b8a3e", 0), ("onnx", "trt", "opt (GPU)", "#2b8a3e", 1),
     ("onnx", "store", "(8) store", "#2b8a3e", 0), ("trt", "store", "", "#2b8a3e", 1)]
build("zone-2-training", "Drill-down — Training Pipeline (L3: Kubeflow·Katib·Ray·MLflow·Feast)", 1840, 660, Z, N, E)

# ============================ ZONE 3: SERVING ============================
N = {}
na(N, "user", 110, 330, "#f2dcc2", "End User")
ni(N, "istio", 300, 330, "istio", "Istio gateway\nmTLS · route")
ni(N, "kserve", 520, 330, "kserve", "KServe\nInferenceService")
ni(N, "knative", 520, 470, "knative", "Knative\nscale-to-zero")
ni(N, "v1", 760, 250, "nvidia", "Model v1 (Triton)\nprimary 90%")
ni(N, "v2", 760, 410, "nvidia", "Model v2 (Triton)\ncanary 10%")
ni(N, "gpu", 760, 560, "gpu", "GPU pool (optional)\nCPU = ONNX")
ni(N, "flagger", 1020, 250, "flagger", "Flagger canary\n5→25→50→100%")
ni(N, "iter8", 1020, 410, "iter8", "Iter8 A/B + SLO")
ni(N, "keda", 1240, 330, "keda", "KEDA autoscale")
ni(N, "mlflow", 520, 180, "mlflow", "MLflow registry")
ni(N, "redisf", 300, 490, "redis", "Feast online")
ni(N, "prom", 1240, 490, "prometheus", "Prometheus")
Z = [(80, 250, 160, 170, "ingress", "#fff3e6", "#e0a86a"),
     (260, 120, 1120, 520, "ns: model-serving", "#fff5e6", "#e0a86a")]
E = [("user", "istio", "(1) request", "#b8741a", 0), ("istio", "kserve", "(2) route", "#b8741a", 0),
     ("mlflow", "kserve", "(4) load model", "#b8741a", 1), ("redisf", "kserve", "(5) features", "#b8741a", 1),
     ("kserve", "v1", "(3) runtime", "#b8741a", 0), ("kserve", "v2", "", "#b8741a", 0), ("knative", "kserve", "scale-0", "#9aa4b2", 1),
     ("v1", "gpu", "MIG", "#9aa4b2", 1), ("v2", "gpu", "MIG", "#9aa4b2", 1),
     ("flagger", "v1", "split", "#c92a2a", 1), ("flagger", "v2", "split", "#c92a2a", 1), ("iter8", "flagger", "experiment", "#c92a2a", 1),
     ("kserve", "prom", "(7) metrics", "#059669", 1, {"rail_y": 665}), ("prom", "keda", "rate/lag", "#9aa4b2", 1), ("keda", "kserve", "(8) scale", "#9aa4b2", 1, {"rail_y": 130})]
build("zone-3-serving", "Drill-down — Serving (L3: KServe+Knative+Triton/MIG+Flagger+Iter8+KEDA)", 1500, 700, Z, N, E)

# ============================ ZONE 4: DRIFT LOOP ============================
N = {}
ni(N, "kserve", 160, 330, "kserve", "KServe + Triton\n(production)")
ni(N, "evidently", 400, 250, "evidently", "Evidently\ndata/pred drift")
ni(N, "alibi", 400, 410, "alibidetect", "Alibi Detect\noutlier/adversarial")
ni(N, "prom", 640, 330, "prometheus", "Prometheus\n+ Thanos")
na(N, "decide", 870, 330, "#ffe0b3", "drift_score\n> 0.5 ?")
ni(N, "alertmgr", 1100, 330, "alertmanager", "Alertmanager")
ni(N, "argoev", 1330, 330, "argo", "Argo Events")
ni(N, "kfp", 1560, 330, "kubeflow", "Kubeflow retrain\nfetch Gold→train(Ray)→eval(GE)")
ni(N, "datapin", 1560, 470, "lakefs", "lakeFS + Iceberg\nsnapshot (reproducible)")
ni(N, "mlflow", 1560, 200, "mlflow", "MLflow Staging\n(F1>baseline)")
na(N, "approval", 1300, 95, "#cdeccd", "Human approval\n(gate to Prod)")   # above the auto-fitted zone band
ni(N, "flagger", 760, 520, "flagger", "Flagger canary 5%")
Z = [(120, 160, 560, 360, "ns: ml-monitoring + monitoring", "#fdecec", "#d98a8a"),
     (1020, 160, 720, 400, "ns: data-orchestration + ml-platform", "#eef0fb", "#7d8fd6")]
E = [("kserve", "evidently", "(1) predictions", "#c92a2a", 0), ("kserve", "alibi", "inputs", "#c92a2a", 1),
     ("evidently", "prom", "(2) drift_score", "#c92a2a", 0), ("alibi", "prom", "", "#c92a2a", 1),
     ("prom", "decide", "(3)", "#c92a2a", 0), ("decide", "alertmgr", "(4) >0.5 alert", "#c92a2a", 0),
     ("alertmgr", "argoev", "(5) webhook", "#c92a2a", 0), ("argoev", "kfp", "(6) retrain", "#c92a2a", 0),
     ("datapin", "kfp", "pin data", "#9aa4b2", 1), ("kfp", "mlflow", "(7) Staging", "#2b8a3e", 0),
     ("mlflow", "approval", "(8) request", "#0e7c66", 0), ("approval", "flagger", "(9) approved→canary", "#0e7c66", 0),
     ("flagger", "kserve", "(10) promote / rollback", "#c92a2a", 1)]
build("zone-4-drift-loop", "Drill-down — Drift→Retrain→Canary Loop ★ (closed loop, human-gated)", 1800, 640, Z, N, E)

# ============================ ZONE 5: RAG ============================
N = {}
na(N, "docs", 155, 200, "#e6dcf3", "Docs: reports /\nrunbooks / metadata")
ni(N, "embed_i", 330, 200, "embedding", "Embed (BGE)")
ni(N, "qdrant", 560, 200, "qdrant", "Qdrant\nvector DB")
ni(N, "typesense", 560, 330, "typesense", "Typesense\nkeyword")
na(N, "q", 155, 470, "#e6dcf3", "User question")
ni(N, "ragflow", 330, 470, "ragflow", "RAGFlow\norchestrator")
ni(N, "merge", 780, 470, "embedding", "merge + rerank")
ni(N, "guard", 1010, 470, "guardrails", "NeMo Guardrails\nin + out")
ni(N, "vllm", 1250, 470, "vllm", "vLLM (GPU)\nor Ollama (CPU)")
ni(N, "langfuse", 1250, 330, "langfuse", "Langfuse\ntrace/cost/eval")
Z = [(80, 120, 720, 300, "Phase A — offline indexing", "#f0eaf8", "#b193d6"),
     (80, 400, 1420, 180, "Phase B — online query", "#f3eefb", "#b193d6")]
E = [("docs", "embed_i", "chunk", "#7c3aed", 0), ("embed_i", "qdrant", "index", "#7c3aed", 0), ("embed_i", "typesense", "index", "#7c3aed", 1),
     ("q", "ragflow", "(1) ask", "#7c3aed", 0), ("ragflow", "qdrant", "(3) vector", "#7c3aed", 0), ("ragflow", "typesense", "(4) keyword", "#7c3aed", 0),
     ("qdrant", "merge", "(5) context", "#7c3aed", 0), ("typesense", "merge", "", "#7c3aed", 0),
     ("merge", "guard", "(6) guard-in", "#7c3aed", 0), ("guard", "vllm", "(7) generate", "#7c3aed", 0),
     ("vllm", "guard", "(8) guard-out", "#7c3aed", 1), ("guard", "q", "(9) response", "#7c3aed", 0, {"via": "below"}),
     ("vllm", "langfuse", "(10) trace", "#059669", 1)]
build("zone-5-rag", "Drill-down — RAG/LLM (indexing + query, Guardrails wrap, vLLM)", 1560, 640, Z, N, E)

# ============================ ZONE 6: PLATFORM / IaC + APP DEPLOY (app-centric) ============================
N = {}
na(N, "dev", 110, 255, "#dfe7f0", "Developer")
na(N, "appsrc", 310, 255, "#dbe7f7", "face-detect app\nFastAPI + YOLOv11 code")
ni(N, "github", 510, 255, "github", "GitHub")
ni(N, "gha", 670, 255, "githubactions", "GitHub Actions\nbuild + test")
ni(N, "fdimage", 830, 255, "fdimage", "face-detect\nimage")
ni(N, "registry", 990, 255, "docker", "Image registry")
ni(N, "argocd", 1130, 255, "argocd", "ArgoCD\nCD (GitOps)")
ni(N, "istio", 1310, 330, "istio", "Istio gateway\nmTLS")  # below the CD->KServe row so the deploy edge stays clear
ni(N, "kserve", 1500, 255, "kserve", "KServe\n(L1: FastAPI)")
ni(N, "triton", 1670, 255, "nvidia", "Triton\nGPU:TensorRT / CPU:ONNX")
ni(N, "yolo", 1580, 380, "yolo", "YOLOv11 model")
na(N, "enduser", 1450, 370, "#f2dcc2", "End User")
ni(N, "terraform", 1430, 560, "terraform", "Terraform\nGKE + GPU pool")
ni(N, "ansible", 1600, 560, "ansible", "Ansible\nVM config")
na(N, "user", 150, 600, "#dfe7f0", "Ops user")
ni(N, "keycloak", 320, 600, "keycloak", "Keycloak OIDC")
ni(N, "oauth", 490, 600, "oauth2proxy", "OAuth2 Proxy")
na(N, "uis", 680, 600, "#e7eefc", "Ops UIs\n1-cookie SSO")
ni(N, "kyverno", 320, 730, "kyverno", "Kyverno")
ni(N, "vault", 490, 730, "vault", "Vault + ESO")
ni(N, "certmgr", 650, 730, "certmanager", "cert-manager")
na(N, "gov", 860, 730, "#fff0d6", "Governance baseline\n(applied to ALL ns)")
Z = [(70, 175, 1010, 165, "CI/CD — GitHub Actions (build the app image)", "#eef2f7", "#9aa4b2"),
     (1230, 170, 720, 310, "Google Kubernetes Engine + GPU pool (MIG)", "#e9f3fe", "#7badd6"),
     (1250, 210, 690, 205, "ns: model-serving  ·  the running app", "#fff5e6", "#e0a86a"),
     (1250, 505, 420, 110, "IaC (provision)", "#eef7ee", "#86bf86"),
     (70, 540, 1010, 250, "auth (SSO) + policy + secrets", "#f3eefb", "#b193d6")]
E = [("dev", "appsrc", "writes", "#5b6472", 0), ("appsrc", "github", "push code", "#5b6472", 0),
     ("github", "gha", "trigger", "#5b6472", 0), ("gha", "fdimage", "build+test", "#5b6472", 0),
     ("fdimage", "registry", "push image", "#5b6472", 0), ("registry", "argocd", "manifest", "#5b6472", 0),
     ("argocd", "kserve", "deploy app", "#5b6472", 0),
     ("enduser", "istio", "", "#b8741a", 0), ("istio", "kserve", "route", "#b8741a", 0),
     ("kserve", "triton", "runtime", "#b8741a", 0), ("triton", "yolo", "inference", "#1864ab", 0),
     ("terraform", "ansible", "then", "#9aa4b2", 1), ("terraform", "istio", "provision GKE+GPU", "#9aa4b2", 1),
     ("user", "keycloak", "login", "#7c3aed", 0), ("keycloak", "oauth", "", "#7c3aed", 0), ("oauth", "uis", "SSO 1-cookie", "#7c3aed", 0),
     ("kyverno", "gov", "policy", "#9aa4b2", 1), ("vault", "gov", "secrets", "#9aa4b2", 1), ("certmgr", "gov", "TLS", "#9aa4b2", 1)]
build("zone-6-platform", "Drill-down — Platform/IaC + App Deploy (face-detection: code -> image -> GKE)", 1990, 840, Z, N, E)

# ============================ ZONE 7: OBSERVABILITY ============================
N = {}
na(N, "svcs", 110, 360, "#dfeeea", "All services\n(OTLP)")
ni(N, "otel", 330, 360, "opentelemetry", "OTel Collector")
ni(N, "prom", 600, 230, "prometheus", "Prometheus")
ni(N, "thanos", 820, 230, "thanos", "Thanos (long-term)")
ni(N, "grafana", 1040, 230, "grafana", "Grafana")
ni(N, "alertmgr", 820, 330, "alertmanager", "Alertmanager")
na(N, "drift", 1040, 330, "#fdd9d9", "→ Drift loop")
ni(N, "filebeat", 600, 460, "filebeat", "Filebeat")
ni(N, "logstash", 790, 460, "logstash", "Logstash")
ni(N, "elastic", 980, 460, "elasticsearch", "Elasticsearch")
ni(N, "kibana", 1170, 460, "kibana", "Kibana")
ni(N, "jaeger", 660, 615, "jaeger", "Jaeger")
Z = [(540, 170, 720, 170, "ns: monitoring (metrics + alert)", "#eafaf0", "#86c9a8"),
     (540, 400, 820, 130, "ns: logging (ELK)", "#fff5e6", "#e0a86a"),
     (540, 550, 300, 110, "ns: tracing", "#e9f3fe", "#7badd6")]
E = [("svcs", "otel", "(1) OTLP", "#059669", 0), ("otel", "prom", "metrics", "#059669", 0),
     ("prom", "thanos", "(2) store", "#059669", 0), ("thanos", "grafana", "viz", "#059669", 0),
     ("prom", "alertmgr", "alert", "#c92a2a", 0), ("alertmgr", "drift", "(5)", "#c92a2a", 1),
     ("otel", "filebeat", "logs", "#b8741a", 0), ("filebeat", "logstash", "(3)", "#b8741a", 0), ("logstash", "elastic", "", "#b8741a", 0), ("elastic", "kibana", "", "#b8741a", 0),
     ("otel", "jaeger", "(4) traces", "#7c3aed", 0)]
build("zone-7-observability", "Drill-down — Observability (OTel → metrics / logs / traces)", 1380, 700, Z, N, E)
print("ALL DRILLDOWNS DONE")
