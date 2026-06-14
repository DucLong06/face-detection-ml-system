import os
from diagrams import Diagram, Cluster, Edge
from diagrams.custom import Custom
from diagrams.onprem.vcs import Github
from diagrams.onprem.ci import Jenkins
from diagrams.onprem.gitops import ArgoCD, Flagger
from diagrams.onprem.network import Istio
from diagrams.onprem.queue import Kafka
from diagrams.onprem.analytics import Spark, Flink, Trino
from diagrams.onprem.workflow import Airflow, KubeFlow
from diagrams.onprem.mlops import Mlflow
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.monitoring import Prometheus, Grafana, Thanos
from diagrams.onprem.tracing import Jaeger
from diagrams.onprem.client import Users
from diagrams.elastic.elasticsearch import Elasticsearch, Kibana

IC = "/tmp/icons/png"
def C(label, name): return Custom(label, f"{IC}/{name}.png")
OUT = "/mnt/data/mlops/Long-project/face-detect-gke/plans/260604-2213-mlops-l2-l3-rag-complete-build/diagrams/icons"
os.makedirs(OUT, exist_ok=True)

graph_attr = {"fontsize": "22", "bgcolor": "white", "pad": "0.6", "nodesep": "0.35",
              "ranksep": "1.5", "splines": "ortho", "fontname": "Sans", "rankdir": "LR"}
def cl(bg): return {"fontsize": "15", "style": "rounded,filled", "fontname": "Sans-Bold", "margin": "14", "bgcolor": bg}

with Diagram("Face-Detect MLOps — Best-of-Breed Target Architecture (single cluster, namespace-isolated)",
             filename=f"{OUT}/01-overview", outformat="png", show=False, direction="LR", graph_attr=graph_attr):
    dev = Users("Developer /\nEnd User")

    with Cluster("Platform (CI/CD · GitOps · Auth · Mesh)", graph_attr=cl("#eef2f7")):
        gh = Github("GitHub")
        ag = ArgoCD("ArgoCD")
        kc = C("Keycloak SSO", "keycloak")
        ist = Istio("Istio ambient\nmTLS gateway")

    with Cluster("Data Plane (L2)", graph_attr=cl("#e9f3fe")):
        kfk = Kafka("Kafka (Strimzi)")
        fl = Flink("Flink")
        sp = Spark("Spark")
        ice = C("Iceberg lakehouse", "iceberg")
        tr = Trino("Trino")
        af = Airflow("Airflow")
        om = C("OpenMetadata\ncatalog+RBAC", "openmetadata")

    with Cluster("ML Plane (L3)", graph_attr=cl("#eef0fb")):
        kf = KubeFlow("Kubeflow")
        ml = Mlflow("MLflow")
        fe = C("Feast", "feast")
        ray = C("Ray", "ray")

    with Cluster("Serving (L3)", graph_attr=cl("#fff5e6")):
        ks = C("KServe", "kserve")
        triton = C("Triton+TensorRT", "nvidia")
        fg = Flagger("Flagger canary")

    with Cluster("Drift Loop ★", graph_attr=cl("#fdecec")):
        ev = C("Evidently", "evidently")
        pr = Prometheus("Prometheus")

    with Cluster("RAG (L3 · 4B)", graph_attr=cl("#f3eefb")):
        vllm = C("vLLM", "vllm")
        rag = C("RAGFlow", "ragflow")
        qd = C("Qdrant", "qdrant")

    with Cluster("Observability", graph_attr=cl("#eafaf0")):
        gf = Grafana("Grafana+Thanos")
        es = Elasticsearch("ELK")
        jg = Jaeger("Jaeger")

    # main horizontal flow (general)
    dev >> Edge(label="code") >> gh >> Edge(label="GitOps") >> ag >> Edge(style="dashed", label="deploy all") >> ist
    ist >> Edge(label="(1) ingest") >> kfk
    kfk >> sp
    sp >> Edge(label="(2) Bronze→Gold (Iceberg)") >> ice
    ice >> Edge(style="dashed", label="(3) train data") >> kf
    kf >> Edge(label="(4) register") >> ml
    ml >> Edge(style="dashed", label="(5) deploy") >> ks
    ks >> triton
    ks >> Edge(color="firebrick", label="(6) predictions") >> ev
    ev >> Edge(color="firebrick", style="dashed", label="(7) drift→retrain") >> kf
    om >> Edge(style="dashed", label="metadata") >> rag
    ks >> Edge(color="seagreen", style="dashed", label="telemetry") >> gf
print("overview done")
