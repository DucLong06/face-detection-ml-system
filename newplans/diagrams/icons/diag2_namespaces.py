import os
from diagrams import Diagram, Cluster, Edge, Node
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
from diagrams.onprem.certificates import CertManager
from diagrams.elastic.elasticsearch import Elasticsearch, Kibana
IC = "/tmp/icons/png"
OUT = "/mnt/data/mlops/Long-project/face-detect-gke/plans/260604-2213-mlops-l2-l3-rag-complete-build/diagrams/icons"
def C(label, name): return Custom(label, f"{IC}/{name}.png")
GA = {"fontsize": "22", "bgcolor": "white", "pad": "0.6", "nodesep": "0.3", "ranksep": "0.7", "fontname": "Sans"}
def cl(bg): return {"fontsize": "15", "style": "rounded,filled", "fontname": "Sans-Bold", "margin": "12", "bgcolor": bg}

# Namespace topology: grouped by tier, no inter-edges (pure isolation map). Governance note as a cluster.
with Diagram("Namespace Topology + Governance Baseline (single best-of-breed cluster)",
             filename=f"{OUT}/08-namespace-topology", outformat="png", show=False, direction="TB", graph_attr=GA):

    with Cluster("PLATFORM tier", graph_attr=cl("#eef2f7")):
        with Cluster("istio-system", graph_attr=cl("#dfe7f0")): Istio("Istio ambient")
        with Cluster("auth", graph_attr=cl("#dfe7f0")): C("Keycloak + OAuth2", "keycloak")
        with Cluster("argocd", graph_attr=cl("#dfe7f0")): ArgoCD("ArgoCD")
        with Cluster("kyverno", graph_attr=cl("#dfe7f0")): C("Kyverno", "kyverno")
        with Cluster("vault / external-secrets", graph_attr=cl("#dfe7f0")): C("Vault + ESO", "vault")
        with Cluster("cert-manager", graph_attr=cl("#dfe7f0")): CertManager("cert-manager")

    with Cluster("DATA tier (L2)", graph_attr=cl("#e9f3fe")):
        with Cluster("data-ingestion", graph_attr=cl("#d6e8fb")): Kafka("Kafka+SR+Debezium")
        with Cluster("data-streaming", graph_attr=cl("#d6e8fb")): Flink("Flink")
        with Cluster("data-processing", graph_attr=cl("#d6e8fb")): Spark("Spark")
        with Cluster("data-storage", graph_attr=cl("#d6e8fb")):
            C("MinIO+Iceberg", "iceberg"); C("lakeFS", "lakefs"); Trino("Trino")
        with Cluster("data-quality", graph_attr=cl("#d6e8fb")): C("Great Exp.", "greatexpectations")
        with Cluster("data-orchestration", graph_attr=cl("#d6e8fb")): Airflow("Airflow+Argo Events")
        with Cluster("data-catalog", graph_attr=cl("#d6e8fb")): C("OpenMetadata", "openmetadata")

    with Cluster("ML tier (L3)", graph_attr=cl("#eef0fb")):
        with Cluster("ml-platform", graph_attr=cl("#dde7fb")):
            KubeFlow("Kubeflow"); Mlflow("MLflow"); C("Feast", "feast"); C("Ray", "ray")
        with Cluster("model-serving", graph_attr=cl("#dde7fb")):
            C("KServe", "kserve"); C("Triton", "nvidia"); Flagger("Flagger")
        with Cluster("ml-monitoring", graph_attr=cl("#dde7fb")):
            C("Evidently", "evidently"); C("Alibi Detect", "alibidetect")

    with Cluster("RAG tier (L3·4B)", graph_attr=cl("#f3eefb")):
        with Cluster("rag", graph_attr=cl("#ebddf7")):
            C("vLLM", "vllm"); C("RAGFlow", "ragflow"); C("Qdrant", "qdrant"); C("Langfuse", "langfuse")

    with Cluster("OBSERVABILITY tier", graph_attr=cl("#eafaf0")):
        with Cluster("monitoring", graph_attr=cl("#d8f3e3")): Prometheus("Prometheus+Thanos"); Grafana("Grafana")
        with Cluster("logging", graph_attr=cl("#d8f3e3")): Elasticsearch("ELK"); Kibana("Kibana")
        with Cluster("tracing", graph_attr=cl("#d8f3e3")): Jaeger("Jaeger+OTel")

    with Cluster("GOVERNANCE BASELINE — applied to EVERY namespace (enforced by Kyverno)", graph_attr=cl("#fff5e6")):
        Node("ResourceQuota +\nLimitRange", shape="note")
        Node("NetworkPolicy\ndefault-deny", shape="note")
        Node("PeerAuthentication\nmTLS STRICT", shape="note")
        Node("AuthorizationPolicy\n(allow-list)", shape="note")
        Node("scoped RBAC +\nServiceAccount", shape="note")
        Node("PodDisruptionBudget\n(stateful)", shape="note")
        Node("labels: team/tier/\ncost/data-class", shape="note")
print("namespace topology done")
