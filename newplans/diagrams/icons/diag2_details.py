import os
from diagrams import Diagram, Cluster, Edge
from diagrams.custom import Custom
from diagrams.onprem.queue import Kafka
from diagrams.onprem.analytics import Spark, Flink, Trino
from diagrams.onprem.workflow import Airflow, KubeFlow
from diagrams.onprem.gitops import ArgoCD, Flagger
from diagrams.onprem.mlops import Mlflow
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.monitoring import Prometheus, Grafana, Thanos
from diagrams.onprem.tracing import Jaeger
from diagrams.onprem.network import Istio
from diagrams.onprem.client import Users, Client
from diagrams.onprem.certificates import CertManager
from diagrams.onprem.vcs import Github
from diagrams.programming.framework import Fastapi
from diagrams.elastic.elasticsearch import Elasticsearch, Kibana, Logstash
from diagrams.elastic.beats import Filebeat

IC = "/tmp/icons/png"
OUT = "/mnt/data/mlops/Long-project/face-detect-gke/plans/260604-2213-mlops-l2-l3-rag-complete-build/diagrams/icons"
def C(label, name): return Custom(label, f"{IC}/{name}.png")
GA = {"fontsize": "20", "bgcolor": "white", "pad": "0.5", "nodesep": "0.4", "ranksep": "1.0", "fontname": "Sans", "splines": "ortho"}
def cl(bg): return {"fontsize": "14", "style": "rounded,filled", "fontname": "Sans-Bold", "margin": "12", "bgcolor": bg}

# ============ 02 DATA PIPELINE (detailed) ============
with Diagram("T1 — Data Pipeline (L2): Kafka · Flink · Spark · Iceberg Lakehouse · Trino · OpenMetadata",
             filename=f"{OUT}/02-data-pipeline", outformat="png", show=False, direction="LR", graph_attr=GA):
    src = Client("WIDER FACE /\ncamera / API /\napp DB")
    with Cluster("ns: data-ingestion", graph_attr=cl("#e9f3fe")):
        kfk = Kafka("Kafka KRaft\n(Strimzi)")
        sr = C("Schema Registry", "schemaregistry")
        dz = C("Debezium CDC", "debezium")
        kc = C("Kafka Connect", "kafkaconnect")
        dz >> kc >> kfk
        kfk - Edge(style="dotted") - sr
    with Cluster("ns: data-streaming", graph_attr=cl("#eef0fb")):
        fl = Flink("Flink\nreal-time validate")
    with Cluster("ns: data-processing", graph_attr=cl("#eef0fb")):
        with Cluster("Spark medallion", graph_attr=cl("#dde7fb")):
            b = Spark("Bronze")
            s = Spark("Silver")
            g = Spark("Gold")
            b >> Edge(label="GE#1") >> s >> Edge(label="GE#2") >> g
    with Cluster("ns: data-quality", graph_attr=cl("#eafaf0")):
        ge = C("Great Expectations\n(2 gates)", "greatexpectations")
    with Cluster("ns: data-storage (lakehouse + warehouse)", graph_attr=cl("#fff5e6")):
        mn = C("MinIO\n(S3)", "minio")
        ice = C("Iceberg tables\nBronze/Silver/Gold", "iceberg")
        lf = C("lakeFS\ndata versioning", "lakefs")
        pg = PostgreSQL("PostgreSQL\nserving metadata")
        rd = Redis("Redis\nonline cache")
        tr = Trino("Trino\nquery engine")
        mn - Edge(style="dotted") - ice
        lf - Edge(style="dotted", label="branch/commit") - ice
        tr >> Edge(label="SQL") >> ice
    with Cluster("ns: data-orchestration", graph_attr=cl("#f3eefb")):
        af = Airflow("Airflow\nETL DAGs")
        ae = C("Argo Events", "argo")
    with Cluster("ns: data-catalog", graph_attr=cl("#fde9f0")):
        om = C("OpenMetadata\ncatalog + lineage + RBAC", "openmetadata")
    # flows
    src >> Edge(label="img→MinIO (claim-check)") >> mn
    src >> Edge(label="metadata events") >> kfk
    kfk >> Edge(label="stream") >> fl >> Edge(label="valid") >> rd
    kfk >> Edge(label="raw") >> b
    mn >> Edge(label="bronze read") >> b
    g >> Edge(label="validate") >> ge
    ge >> Edge(label="gold") >> ice
    g >> Edge(label="serving rows") >> pg
    af >> Edge(style="dashed", label="schedule") >> b
    ge >> Edge(color="firebrick", style="dashed", label="fail→alert") >> ae
    ice >> Edge(color="seagreen", style="dashed", label="lineage ingest") >> om
    af >> Edge(color="seagreen", style="dashed") >> om
    ice >> Edge(color="seagreen", style="dashed", label="Gold → ML (T2)") >> tr

# ============ 03 ML PLATFORM (detailed) ============
with Diagram("T2 — ML Platform (L3): Kubeflow · Katib · MLflow · Feast · Ray (KubeRay)",
             filename=f"{OUT}/03-ml-platform", outformat="png", show=False, direction="LR", graph_attr=GA):
    data = Trino("Gold (Iceberg)\nvia Trino")
    with Cluster("ns: ml-platform", graph_attr=cl("#eef0fb")):
        with Cluster("Kubeflow", graph_attr=cl("#dde7fb")):
            nb = KubeFlow("Notebooks")
            kfp = KubeFlow("Pipelines\n(train DAG)")
            kt = C("Katib\nHPO", "katib")
        ray = C("Ray / KubeRay\ndistributed train", "ray")
        ml = Mlflow("MLflow\ntracking + registry")
        with Cluster("Feast feature store", graph_attr=cl("#e7f7ee")):
            feo = C("Feast offline\n(Iceberg)", "feast")
            fon = Redis("Feast online\n(Redis)")
    with Cluster("model export", graph_attr=cl("#fff5e6")):
        onnx = C("ONNX export", "kserve")
        trt = C("TensorRT INT8\n(GPU)", "nvidia")
    data >> Edge(label="load") >> feo
    feo >> Edge(label="materialize") >> fon
    data >> Edge(label="explore") >> nb >> Edge(label="author") >> kfp
    kfp >> Edge(label="tune") >> kt
    kfp >> Edge(label="scale train") >> ray
    feo >> Edge(label="features") >> kfp
    kfp >> Edge(label="log metrics/model") >> ml
    ml >> Edge(label="export") >> onnx >> Edge(style="dashed", label="opt") >> trt
    ml >> Edge(color="seagreen", style="dashed", label="model → Serving (T3)") >> onnx

# ============ 04 SERVING (detailed) ============
with Diagram("T3 — Serving (L3): KServe + Knative + Triton/TensorRT + KEDA + Flagger + Iter8",
             filename=f"{OUT}/04-serving", outformat="png", show=False, direction="LR", graph_attr=GA):
    user = Users("End User")
    ist = Istio("Istio ambient\ngateway · mTLS")
    with Cluster("ns: model-serving", graph_attr=cl("#fff5e6")):
        with Cluster("KServe InferenceService", graph_attr=cl("#ffe9cc")):
            kn = C("Knative\nscale-to-zero", "knative")
            ks = C("KServe", "kserve")
            tr = C("Triton + TensorRT\n(GPU, dynamic batch)", "nvidia")
            ks >> Edge(label="runtime") >> tr
            kn - Edge(style="dotted") - ks
        kd = C("KEDA\nevent autoscale", "keda")
        fg = Flagger("Flagger\ncanary 5→100%")
        it = C("Iter8\nA/B + SLO", "iter8")
    reg = Mlflow("MLflow registry")
    fs = Redis("Feast online")
    pr = Prometheus("Prometheus")
    user >> Edge(label="request") >> ist >> Edge(label="route") >> ks
    reg >> Edge(style="dashed", label="model pull (S3/Iceberg)") >> ks
    fs >> Edge(label="online features") >> ks
    ks >> Edge(color="seagreen", style="dashed", label="metrics") >> pr
    pr >> Edge(style="dashed", label="rate/lag") >> kd >> Edge(style="dashed", label="scale") >> ks
    fg >> Edge(style="dashed", label="traffic split") >> ks
    it >> Edge(style="dashed", label="experiment") >> fg

# ============ 05 DRIFT LOOP (detailed) ============
with Diagram("T4 — Drift → Retrain → Canary Loop ★ (L3 centerpiece)",
             filename=f"{OUT}/05-drift-loop", outformat="png", show=False, direction="LR", graph_attr=GA):
    with Cluster("ns: model-serving", graph_attr=cl("#fff5e6")):
        ks = C("KServe + Triton", "kserve")
        fg = Flagger("Flagger canary")
    with Cluster("ns: ml-monitoring", graph_attr=cl("#fdecec")):
        ev = C("Evidently\ndata/pred drift", "evidently")
        ad = C("Alibi Detect\noutlier/adversarial", "alibidetect")
    with Cluster("ns: monitoring", graph_attr=cl("#eafaf0")):
        pr = Prometheus("Prometheus")
        th = Thanos("Thanos\nlong-term")
        gf = Grafana("Grafana\ndrift dashboard")
        am = C("Alertmanager", "alertmanager")
        pr >> th
        pr >> gf
        pr >> Edge(label="rule score>0.5") >> am
    with Cluster("ns: data-orchestration", graph_attr=cl("#f3eefb")):
        ae = C("Argo Events\nwebhook→trigger", "argo")
    with Cluster("ns: ml-platform", graph_attr=cl("#eef0fb")):
        kfp = KubeFlow("Kubeflow\nretrain pipeline")
        ml = Mlflow("MLflow\nStaging")
    ks >> Edge(color="firebrick", label="predictions") >> ev
    ks >> Edge(color="firebrick", style="dashed", label="inputs") >> ad
    ev >> Edge(color="firebrick", label="drift_score") >> pr
    ad >> Edge(color="firebrick", style="dashed") >> pr
    am >> Edge(color="firebrick", label="webhook") >> ae
    ae >> Edge(color="firebrick", label="trigger") >> kfp
    kfp >> Edge(label="fetch Gold + retrain + eval") >> ml
    ml >> Edge(color="firebrick", style="dashed", label="canary 5%") >> fg
    fg >> Edge(color="firebrick", style="dashed", label="promote / rollback") >> ks

# ============ 06 RAG (detailed) ============
with Diagram("T5 — RAG / LLM (L3 · 4B): vLLM · RAGFlow · Qdrant · Typesense · Guardrails · Langfuse",
             filename=f"{OUT}/06-rag", outformat="png", show=False, direction="LR", graph_attr=GA):
    q = Client("User question\n(chat UI)")
    with Cluster("ns: rag", graph_attr=cl("#f3eefb")):
        rf = C("RAGFlow\norchestrator", "ragflow")
        with Cluster("hybrid retrieval", graph_attr=cl("#ede7f6")):
            qd = C("Qdrant\nvector DB", "qdrant")
            ts = C("Typesense\nkeyword", "typesense")
        gr = C("NeMo Guardrails\nsafety", "guardrails")
        vllm = C("vLLM\n(GPU, paged-attn)", "vllm")
        lf = C("Langfuse\ntrace/cost/eval", "langfuse")
    src = C("OpenMetadata + DW\n(reports/docs/metadata)", "openmetadata")
    emb = C("embeddings\n(BGE/MiniLM)", "vllm")
    q >> Edge(label="query") >> rf
    rf >> Edge(label="embed") >> emb >> Edge(label="vector search") >> qd
    rf >> Edge(label="keyword search") >> ts
    qd >> Edge(label="context") >> rf
    ts >> Edge(label="context") >> rf
    rf >> Edge(label="guarded prompt") >> gr >> Edge(label="generate") >> vllm
    vllm >> Edge(label="answer") >> gr
    gr >> Edge(label="response") >> q
    vllm >> Edge(color="seagreen", style="dashed", label="trace") >> lf
    src >> Edge(style="dashed", label="index/embed") >> qd

# ============ 07 PLATFORM / SECURITY / OBSERVABILITY (detailed) ============
with Diagram("T0+T6 — Platform · Security · SSO · Observability",
             filename=f"{OUT}/07-platform-observability", outformat="png", show=False, direction="LR", graph_attr=GA):
    user = Users("Users\n(6 RBAC roles)")
    with Cluster("ns: platform (GitOps + policy + secrets)", graph_attr=cl("#eef2f7")):
        gh = Github("Git repo")
        ag = ArgoCD("ArgoCD")
        ky = C("Kyverno\npolicy-as-code", "kyverno")
        vault = C("Vault + ESO", "vault")
        cm = CertManager("cert-manager")
        gh >> ag
        ag >> Edge(style="dashed", label="enforce") >> ky
    with Cluster("ns: auth + istio-system", graph_attr=cl("#f3eefb")):
        kc = C("Keycloak\nrealm + roles", "keycloak")
        op = C("OAuth2 Proxy", "oauth2proxy")
        ist = Istio("Istio ambient\nmTLS STRICT")
        kc >> op >> ist
    with Cluster("ns: monitoring", graph_attr=cl("#eafaf0")):
        pr = Prometheus("Prometheus")
        th = Thanos("Thanos")
        gf = Grafana("Grafana")
        pr >> th
        pr >> gf
    with Cluster("ns: logging (ELK)", graph_attr=cl("#fff5e6")):
        fb = Filebeat("Filebeat")
        lo = Logstash("Logstash")
        es = Elasticsearch("Elasticsearch")
        kb = Kibana("Kibana")
        fb >> lo >> es >> kb
    with Cluster("ns: tracing", graph_attr=cl("#e9f3fe")):
        otc = C("OTel Collector", "opentelemetry")
        jg = Jaeger("Jaeger")
        otc >> jg
    apps = Client("All UIs + services\n(Grafana/MLflow/Airflow/\nKubeflow/OpenMetadata/Kibana)")
    user >> Edge(label="SSO login") >> kc
    ist >> Edge(label="1 cookie *.face-detect.dev") >> apps
    apps >> Edge(color="seagreen", style="dashed", label="metrics") >> pr
    apps >> Edge(style="dashed", label="logs") >> fb
    apps >> Edge(style="dashed", label="traces (OTLP)") >> otc
    ag >> Edge(style="dashed", label="deploy") >> apps
print("details done")
