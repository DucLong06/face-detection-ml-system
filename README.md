<!-- omit in toc -->
# Face Detection ML System 
<!-- omit in toc -->
## Table of Contents
- [Overview](#overview)
  - [System Architecture](#system-architecture)
- [Features](#features)
  - [Core Components](#core-components)
  - [Observability Stack](#observability-stack)
  - [DevOps Automation](#devops-automation)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
  - [Cloud Platform](#cloud-platform)
  - [Required Tools](#required-tools)
  - [Optional Tools](#optional-tools)
- [Infrastructure Setup](#infrastructure-setup)
  - [1. Google Cloud Configuration](#1-google-cloud-configuration)
  - [2. Cluster Deployment](#2-cluster-deployment)
    - [Enable Kubernetes Engine API](#enable-kubernetes-engine-api)
    - [Generate SSH keys](#generate-ssh-keys)
    - [Deploy GKE cluster](#deploy-gke-cluster)
    - [Configure cluster access](#configure-cluster-access)
  - [3. Jenkins Setup](#3-jenkins-setup)
- [Application Deployment](#application-deployment)
- [Observability Stack](#observability-stack-1)
  - [Monitoring Setup](#monitoring-setup)
  - [Dashboard Access](#dashboard-access)
- [CI/CD Pipeline](#cicd-pipeline)
  - [Jenkins Installation](#jenkins-installation)
  - [Pipeline Configuration](#pipeline-configuration)
  - [Deployment Process](#deployment-process)
  - [Testing](#testing)

## Overview
This project demonstrates a production-grade MLOps pipeline that deploys a YOLOv11-based face detection service on Google Kubernetes Engine (GKE). By leveraging modern cloud-native technologies, it offers a complete solution for automated deployment, comprehensive monitoring, and efficient scaling of machine learning models in production. The pipeline incorporates industry best practices for CI/CD, observability, and infrastructure as code.

### Why this stack (v0.2 scope)
- **Inference**: FastAPI + YOLOv11 (Ultralytics) — lightweight, GPU-optional, OpenTelemetry-instrumented
- **Orchestration**: Kubeflow Pipelines + Katib + MLflow — covers train DAG, HPO, model registry in one ecosystem (no Airflow overlap)
- **Data**: Kafka KRaft + Spark + MinIO + Great Expectations — event-driven ingest, batch processing, S3-compatible artifact storage, declarative data quality
- **Observability**: Prometheus + Grafana + ELK + Jaeger + Evidently — three pillars (metrics/logs/traces) + ML drift detection
- **Security**: Istio mTLS + Dex OIDC + OAuth2 Proxy + NetworkPolicy — defense in depth without Keycloak heavyweight
- **DevOps**: Jenkins + Terraform + Helm — battle-tested, no abstraction tax (skip ArgoCD/deployKF for single-cluster scope)

### What I cut & why (post-YAGNI audit)
Per [docs/archive/cut-components-v0.1.md](docs/archive/cut-components-v0.1.md), removed ~18 components from v0.1 plan:
- **Entire RAG stack** (RAGFlow, Ollama, Weaviate, Typesense, Langfuse) — irrelevant to face DETECTION (computer vision ≠ LLM use case)
- **Triton + RayServe + RayTune** — serving framework redundancy (KServe sufficient)
- **Flink** — Spark Structured Streaming covers throughput target
- **Airflow + ArgoCD + deployKF** — orchestration overlap (Kubeflow + Jenkins + helm suffice)
- **DVC + DataHub + Locust + NGINX Ingress + Keycloak** — redundant or overkill

Result: 40 components / 16 ns → **22 components / 9 ns**. Estimated cost: $1118/mo → $311/mo. Interview narrative: depth over breadth.

### What's next
- L1 production hardening: liveness/readiness probes, HPA, scoped RBAC, NetworkPolicy, PDB (Phase 03)
- L2 actual deployment (currently docs-only) — Kafka + Spark + MinIO in `data-platform-ns`
- L3 Istio mTLS STRICT + KServe canary demo

### System Architecture
The system architecture diagram below illustrates the main components and their interactions:

![System Architecture Diagram](images/architecture.png)

## Features

### Core Components
- **ML Service**: Production-ready face detection service powered by YOLOv11
- **Cloud Infrastructure**: Fully automated GCP infrastructure using Terraform and Ansible
- **Kubernetes Orchestration**: Scalable deployment on Google Kubernetes Engine (GKE)

### Observability Stack
- **Metrics Monitoring**: Real-time performance tracking with Prometheus and Grafana
- **Log Management**: Centralized logging with Elasticsearch, Logstash, and Kibana (ELK Stack)
- **Distributed Tracing**: Request tracing and performance analysis with Jaeger

### DevOps Automation
- **CI/CD Pipeline**: Automated testing and deployment using Jenkins
- **Infrastructure as Code**: Version-controlled infrastructure with Terraform
- **Configuration Management**: Automated provisioning with Ansible

## Repository Structure
```
.
├── api/                                # Face detection API service
├── charts/                             # Helm charts for deployment
│   ├── face-detection/                 # Application chart
│   └── nginx-ingress/                  # Ingress controller
├── custom_images/                      # Custom container images
│   └── jenkins/                        # Jenkins configuration
├── infrastructure/                     # Infrastructure as Code
│   ├── ansible/                        # Ansible playbooks
│   ├── credentials/                    # GCP credentials
│   ├── ssh_keys/                       # SSH keys for instances
│   └── terraform/                      # Terraform configurations
├── models/                             # ML model files
├── monitoring/                         # Observability components
│   ├── K8s/                            # Kubernetes monitoring
│   │   ├── elk-filebeat/               # ELK Stack configuration
│   │   ├── helmfile.yaml               # Helm releases
│   │   ├── jaeger/                     # Distributed tracing
│   │   └── kube-prometheus-stack/      # Prometheus & Grafana
│   └── Local/                          # Local monitoring setup
├── notebooks/                          # Training notebooks
└── scripts/                            # Utility scripts
```

## Prerequisites

### Cloud Platform
- Google Cloud Platform account with billing enabled
- Sufficient permissions to create GKE clusters and service accounts

### Required Tools
| Tool             | Minimum Version | Purpose                       |
| ---------------- | --------------- | ----------------------------- |
| Google Cloud SDK | ≥ 440.0.0       | GCP resource management       |
| Terraform        | ≥ 1.5.0         | Infrastructure provisioning   |
| kubectl          | ≥ 1.26.0        | Kubernetes cluster management |
| Helm             | ≥ 3.12.0        | Package management            |
| Helmfile         | ≥ 0.151.0       | Helm chart orchestration      |
| Docker           | ≥ 24.0.0        | Container management          |

### Optional Tools
- kubens - Kubernetes namespace switching utility
- kubectx - Kubernetes context switching utility

## Infrastructure Setup

### 1. Google Cloud Configuration
1. Install and configure Google Cloud SDK:
```bash
# Follow installation guide at: cloud.google.com/sdk/docs/install
gcloud init
gcloud auth application-default login
```
2. Create service account:
- Configure editor role
- Store credentials in `infrastructure/credentials/`
- Update configuration in [`terraform/terraform.tfvars`](https://github.com/DucLong06/face-detect-gke-observability/blob/bb9611ee20d2f6536710a32eac5848f7dd1cf2de/infrastructure/terraform/terraform.tfvars#L2-L5)

![Service Account Creation](images/service-account-creation.gif)

### 2. Cluster Deployment
#### Enable Kubernetes Engine API

Before creating a GKE cluster, you need to enable the Kubernetes Engine API for your Google Cloud Project:

1. Navigate to Google Cloud Console Marketplace:
   ```
   https://console.cloud.google.com/marketplace/product/google/container.googleapis.com
   ```
   
2. Ensure you have selected the correct project in the Google Cloud Console header

3. On the Kubernetes Engine API page, click the "Enable" button

4. Once enabled, you'll see a "Manage" button and status indicating the API is active
  ![Enable k8s gke](images/enable-k8s-api.png)

**Note**: Enabling this API is a prerequisite for all GKE operations and only needs to be done once per project. If you encounter any "API not enabled" errors during cluster creation, ensure this step has been completed successfully.

#### Generate SSH keys
```bash
cd infrastructure
make generate-key # Generate SSH keys
```

#### Deploy GKE cluster
```bash
make init
make plan
make apply  # Takes approximately 10-15 minutes
```

#### Configure cluster access
```bash
gcloud container clusters get-credentials [CLUSTER_NAME] --region [REGION]
kubectx [CLUSTER_NAME]
```

![Cluster Connection](images/cluster-connection.gif)

### 3. Jenkins Setup
Deploy Jenkins on Google Compute Engine using Ansible:
```bash
cd infrastructure
make deploy
```

![Ansible Jenkins](images/ansible-jenkins.png)

## Application Deployment

1. Create required namespaces:
```bash
kubectl create namespace model-serving
kubectl create namespace nginx-ingress
```

2. Deploy components:
```bash
# Install Nginx ingress controller
helm upgrade --install nginx-ingress charts/nginx-ingress --namespace nginx-ingress 

# Deploy face detection service
helm upgrade --install face-detection charts/face-detection --namespace model-serving
```

## Observability Stack

### Monitoring Setup
1. Setup with Helmfile:
```bash
# Using Helmfile (recommended)
cd monitoring/K8s
helmfile sync
```

2. Setup with Docker:
```bash
# Alternative: Using Docker Compose
cd monitoring/Local
docker compose up -d
cd elk && docker compose up -d
```

### Dashboard Access
1. Grafana (`http://[NODE_IP]:30000`):
```bash
# Retrieve admin password
kubectl get secret kube-prometheus-stack-grafana -o jsonpath="{.data.admin-password}" | base64 --decode
```

![Grafana Dashboard](images/grafana-dashboard.png)

2. Kibana (`http://[NODE_IP]:5601`):
```bash
# Retrieve elastic user password
kubectl get secret elasticsearch-master-credentials -o jsonpath="{.data.password}" | base64 --decode
```

![Kibana Interface](images/kibana-interface.png)

3. Jaeger UI is accessible at `http://[NODE_IP]:16686`

![Jaeger Tracing](images/jaeger-tracing.png)

## CI/CD Pipeline

### Jenkins Installation
1. Connect to Google Compute Engine:
```bash
cd infrastructure 
ssh -i ssh_keys/jenkins_key [USERNAME]@[GCE_EXTERNAL_IP]
```

2. Access Jenkins UI:
- Navigate to `http://[GCE_EXTERNAL_IP]:8081`
- Retrieve initial admin password:
```bash
sudo docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

![Jenkins Setup through Docker](images/jenkins-docker-setup.gif)

### Pipeline Configuration
1. Install required plugins:
- Kubernetes
- Docker and Docker Pipeline
- Google Cloud SDK

![Install Plugins Jenkins](images/install-plugins-jenkins.gif)

Note: If Jenkins fails to restart after plugin installation, SSH into the GCE instance and restart the container:
```bash
sudo docker start jenkins
```

2. Configure credentials:
- GitHub authentication
![GitHub Credentials](images/jenkins-credential-github.gif)
- DockerHub access token
![Docker Credentials](images/jenkins-credental-dockerhub.gif)
- GKE service account
```bash
# Create service account
kubectl create serviceaccount model-serving-sa -n model-serving

# Get token (default expiration: 1 hour)
kubectl create token model-serving-sa -n model-serving
```
![GKE Credentials](images/jenkins-credential-gke.gif)
**Note:** 
- Default token has 1 hour expiration time
- To create token with longer duration, use the `--duration` flag

Example:
```bash
# Create token valid for 1 year 
kubectl create token model-serving-sa -n model-serving --duration=8760h
```
4. Set up GKE permissions:

> **⚠️ DEPRECATED (Phase 03 L1 hardening)**: The commands below grant `cluster-admin` to `model-serving-sa` and the namespace's default SA. The chart now ships scoped `Role`/`RoleBinding` (`charts/face-detection/templates/rbac.yaml`). Use the scoped RBAC instead and audit-delete legacy bindings — see [docs/deployment-guide.md §Production Hardening](docs/deployment-guide.md#production-hardening-phase-03--l1-fundamentals).

```bash
# LEGACY (DO NOT USE for new installs):
kubectl create clusterrolebinding model-serving-admin-binding \
  --clusterrole=cluster-admin \
  --serviceaccount=model-serving:model-serving-sa

kubectl create clusterrolebinding cluster-admin-default-binding \
  --clusterrole=cluster-admin \
  --user=system:serviceaccount:model-serving:default
```

![Jenkins GKE Configuration](images/jenkins-gke-config.gif)

4. Configure pipeline:
- Create pipeline job
- Link Git repository
- Set up Jenkinsfile

![Pipeline Configuration](images/jenkins-pipeline-config.gif)

### Deployment Process
The CI/CD pipeline includes the following stages:
1. Code validation and linting
2. Automated testing
3. Docker image building
4. Container registry push
5. GKE deployment

![Pipeline Execution](images/jenkins-pipeline-done.png)

### Testing
1. Verify service status:
```bash
kubectl get services -n model-serving
```

2. Test endpoints:
```bash
# Health check endpoint
curl http://[SERVICE_IP]:8000/health

# Face detection endpoint
curl -X POST http://[SERVICE_IP]:8000/detect/faces/image \
  -F "image=@/path/to/image.jpg"
```

![API Testing](images/api-testing.gif)