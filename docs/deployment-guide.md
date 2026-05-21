# Deployment Guide

**Project**: Face Detection ML System (Level 1)  
**Last Updated**: 2026-04-15  
**Target Environment**: Google Cloud Platform (GKE)  
**Estimated Duration**: 45–60 minutes (first-time deployment)

## Overview

This guide provides step-by-step instructions for deploying the Face Detection ML System to Google Kubernetes Engine (GKE). It covers infrastructure provisioning, application deployment, and observability stack setup.

## Prerequisites

### Required Tools

| Tool | Version | Installation |
|------|---------|--------------|
| Google Cloud SDK | ≥ 440.0.0 | https://cloud.google.com/sdk/docs/install |
| Terraform | ≥ 1.5.0 | https://www.terraform.io/downloads |
| kubectl | ≥ 1.26.0 | `gcloud components install kubectl` |
| Helm | ≥ 3.12.0 | https://helm.sh/docs/intro/install/ |
| Docker | ≥ 24.0.0 | https://docs.docker.com/engine/install/ |
| git | ≥ 2.30.0 | https://git-scm.com/downloads |

### Cloud Account Requirements

- **Google Cloud Platform** account with billing enabled
- **Project ID** noted (e.g., `my-gcp-project`)
- **Editor role** or equivalent permissions
- **APIs enabled**: Compute Engine, Kubernetes Engine, Container Registry

### GCP API Setup

Enable required APIs:
```bash
gcloud services enable compute.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

---

## Step 1: Google Cloud Configuration

### 1.1 Initialize gcloud CLI

```bash
gcloud init
gcloud auth application-default login
```

**What it does**: Authenticates your local environment with GCP, creates default configuration.

### 1.2 Create GCP Service Account

For Terraform to manage resources, create a service account:

```bash
# Set your project ID
export PROJECT_ID="your-gcp-project-id"

# Create service account
gcloud iam service-accounts create terraform-user \
  --display-name="Terraform Service Account" \
  --project=$PROJECT_ID

# Grant Editor role (for development; use least-privilege in production)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:terraform-user@$PROJECT_ID.iam.gserviceaccount.com \
  --role=roles/editor

# Create and download key
gcloud iam service-accounts keys create terraform-key.json \
  --iam-account=terraform-user@$PROJECT_ID.iam.gserviceaccount.com
```

**Output**: `terraform-key.json` (save this securely, do NOT commit to git)

### 1.3 Store Credentials

```bash
# Move credentials to infrastructure directory
mkdir -p infrastructure/credentials
mv terraform-key.json infrastructure/credentials/

# Add credentials to .gitignore (if not already present)
echo "infrastructure/credentials/" >> .gitignore
```

---

## Step 2: Terraform Infrastructure Deployment

### 2.1 Configure Terraform Variables

Edit `infrastructure/terraform/terraform.tfvars`:

```hcl
project_id            = "your-gcp-project-id"
region                = "us-central1"
zone                  = "us-central1-a"
cluster_name          = "face-detection-cluster"
machine_type          = "e2-medium"

# Path to service account key
credentials_file      = "credentials/terraform-key.json"
```

### 2.2 Generate SSH Keys (for Jenkins)

```bash
cd infrastructure
make generate-key
```

**Output**: Creates `ssh_keys/jenkins_key` (private key) and `ssh_keys/jenkins_key.pub` (public key)

### 2.3 Initialize and Plan Terraform

```bash
cd infrastructure

# Initialize Terraform (downloads provider plugins)
make init

# Preview changes (should show GKE cluster, GCE VM, firewall rules)
make plan
```

**Expected output**: Plan showing creation of:
- 1× GKE cluster (e2-medium, preemptible)
- 1× GCE VM (n1-standard-1, for Jenkins)
- Firewall rules (SSH, HTTP, HTTPS)
- VPC network and subnets

### 2.4 Apply Terraform Configuration

```bash
# Deploy infrastructure (takes 10–15 minutes)
make apply

# Confirm by typing 'yes' when prompted
```

**What it does**:
- Creates GKE cluster in us-central1
- Provisions GCE VM for Jenkins
- Sets up VPC, subnets, firewall rules
- Outputs cluster endpoint and external IPs

**Output example**:
```
Outputs:
  cluster_endpoint = "https://35.201.202.30"
  cluster_region   = "us-central1"
  cluster_name     = "face-detection-cluster"
  gce_external_ip  = "34.567.890.123"
```

---

## Step 3: Kubernetes Cluster Configuration

### 3.1 Authenticate with GKE Cluster

```bash
# Configure kubectl to access the cluster
gcloud container clusters get-credentials face-detection-cluster \
  --region=us-central1

# Verify access
kubectl get nodes
```

**Expected output**:
```
NAME                                          STATUS   ROLES    AGE   VERSION
gke-face-detection-cluster-default-pool-...   Ready    <none>   5m    v1.28.5-gke.123456
```

### 3.2 Create Namespaces

```bash
# Create namespaces for application and monitoring
kubectl create namespace model-serving
kubectl create namespace nginx-ingress
kubectl create namespace monitoring
kubectl create namespace elastic-system
kubectl create namespace tracing
```

### 3.3 Create Service Account for Jenkins

```bash
# Create service account for Helm deployments
kubectl create serviceaccount model-serving-sa -n model-serving

# Create cluster role binding for service account
kubectl create clusterrolebinding model-serving-admin-binding \
  --clusterrole=cluster-admin \
  --serviceaccount=model-serving:model-serving-sa

# Get token (valid for 1 hour, extend if needed)
kubectl create token model-serving-sa \
  -n model-serving \
  --duration=8760h  # 1 year
```

**Save the token** — you'll need it for Jenkins configuration.

---

## Step 4: Jenkins Setup (Optional for CI/CD)

### 4.1 Provision Jenkins VM with Ansible

```bash
cd infrastructure

# Deploy Jenkins using Ansible (requires SSH key from Step 2.2)
make deploy
```

**What it does**:
- Installs Docker on GCE VM
- Starts Jenkins container
- Creates Jenkins admin user
- Configures GKE credentials

### 4.2 Access Jenkins UI

```bash
# Get Jenkins external IP from Terraform outputs
export JENKINS_IP="34.567.890.123"  # Replace with your IP

# Access Jenkins
open "http://$JENKINS_IP:8081"  # macOS
xdg-open "http://$JENKINS_IP:8081"  # Linux
start "http://$JENKINS_IP:8081"  # Windows
```

**Initial Jenkins Password**:
```bash
# SSH into Jenkins VM
ssh -i infrastructure/ssh_keys/jenkins_key ubuntu@$JENKINS_IP

# Get initial admin password
sudo docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword

# Exit SSH session
exit
```

### 4.3 Configure Jenkins

1. **Install Plugins**:
   - Kubernetes
   - Docker and Docker Pipeline
   - Google Cloud SDK

2. **Add Credentials** (Jenkins UI → Credentials):
   - **GitHub**: Username + Personal Access Token
   - **DockerHub**: Username + Access Token
   - **GKE**: Paste service account token from Step 3.3

3. **Create Pipeline Job**:
   - Item type: Pipeline
   - Pipeline script from SCM: Git
   - Repository URL: GitHub face-detect-gke URL
   - Script path: Jenkinsfile

---

## Step 5: Container Image Preparation

### 5.1 Build Docker Image (Local)

```bash
# Build image locally
docker build -t face-detection:latest -f Dockerfile .

# Test locally (requires YOLOv11 model in models/ directory)
docker run -p 8000:8000 face-detection:latest
curl http://localhost:8000/health
```

### 5.2 Push to Container Registry

```bash
# Authenticate with DockerHub (or your private registry)
docker login

# Tag and push
docker tag face-detection:latest longhd06/face-detection:latest
docker push longhd06/face-detection:latest

# Or, use Google Container Registry
docker tag face-detection:latest gcr.io/$PROJECT_ID/face-detection:latest
gcloud auth configure-docker
docker push gcr.io/$PROJECT_ID/face-detection:latest
```

**Note**: Later, Jenkins will automate this (Stage 2: Build)

---

## Step 6: Deploy NGINX Ingress Controller

### 6.1 Create NGINX Ingress Namespace

```bash
kubectl create namespace nginx-ingress
```

### 6.2 Install NGINX Ingress Controller

```bash
# Add Helm repository
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

# Install NGINX Ingress Controller
helm upgrade --install nginx-ingress ingress-nginx/ingress-nginx \
  --namespace nginx-ingress \
  --set controller.service.type=LoadBalancer
```

**Verify installation**:
```bash
kubectl get svc -n nginx-ingress
```

**Expected output**:
```
NAME                            TYPE           CLUSTER-IP      EXTERNAL-IP      PORT(S)
nginx-ingress-controller        LoadBalancer   10.0.1.100      34.123.45.67     80:30080/TCP,443:30443/TCP
```

---

## Step 7: Deploy Face Detection Application

### 7.1 Create Helm Values Override

Create `charts/face-detection/values-prod.yaml`:

```yaml
image:
  repository: longhd06/face-detection  # Or gcr.io/$PROJECT_ID/face-detection
  tag: latest
  pullPolicy: IfNotPresent

replicas: 1

resources:
  limits:
    memory: 500Mi
    cpu: 200m
  requests:
    memory: 256Mi
    cpu: 100m

ingress:
  enabled: true
  host: face-detection.local  # Update to your domain

env:
  - name: OTLP_GRPC_ENDPOINT
    value: "jaeger-jaeger.tracing.svc.cluster.local:4317"
```

### 7.2 Install Face Detection Helm Chart

```bash
# Install application
helm upgrade --install face-detection charts/face-detection \
  --namespace model-serving \
  --values charts/face-detection/values-prod.yaml

# Verify deployment
kubectl get pods -n model-serving
kubectl get svc -n model-serving
```

**Expected output**:
```
NAME                              READY   STATUS    RESTARTS   AGE
face-detection-5d7f9c4b5-k9m2l    1/1     Running   0          30s

NAME                    TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)
face-detection          LoadBalancer   10.0.2.50       34.234.56.78  8000:31234/TCP
```

### 7.3 Test API Endpoints

```bash
# Get service IP
export SERVICE_IP=$(kubectl get svc face-detection -n model-serving -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Health check
curl http://$SERVICE_IP:8000/health

# Face detection (requires test image)
curl -X POST http://$SERVICE_IP:8000/detect/faces/image \
  -F "image=@path/to/test_image.jpg" \
  -o result.jpg
```

---

## Step 8: Deploy Observability Stack

### 8.1 Create Monitoring Namespace

```bash
kubectl create namespace monitoring
```

### 8.2 Deploy Prometheus + Grafana

```bash
# Add Prometheus Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack
helm upgrade --install kube-prometheus-stack \
  prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set grafana.service.type=NodePort \
  --set grafana.service.nodePort=30000
```

### 8.3 Configure Prometheus Scrape Target

```bash
# Create ServiceMonitor for face-detection
kubectl apply -f - <<EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: face-detection
  namespace: model-serving
spec:
  selector:
    matchLabels:
      app: face-detection
  endpoints:
  - port: metrics
    interval: 15s
    path: /metrics
EOF
```

### 8.4 Access Grafana

```bash
# Get any node's external IP
export NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="ExternalIP")].address}')

# Grafana URL: http://$NODE_IP:30000
# Default credentials: admin / prom-operator

# Get admin password
kubectl get secret kube-prometheus-stack-grafana \
  -n monitoring \
  -o jsonpath="{.data.admin-password}" | base64 --decode
```

### 8.5 Deploy ELK Stack

```bash
# Add Elastic Helm repository
helm repo add elastic https://helm.elastic.co
helm repo update

# Create elastic-system namespace
kubectl create namespace elastic-system

# Install Elasticsearch
helm upgrade --install elasticsearch elastic/elasticsearch \
  --namespace elastic-system \
  --set replicas=1 \
  --set minimumMasterNodes=1

# Install Kibana
helm upgrade --install kibana elastic/kibana \
  --namespace elastic-system \
  --set service.type=NodePort \
  --set service.nodePort=30601

# Install Filebeat (ships logs to Elasticsearch)
helm upgrade --install filebeat elastic/filebeat \
  --namespace elastic-system \
  --set filebeatConfig.filebeat\.yml.output\.elasticsearch\.hosts=["elasticsearch-master:9200"]
```

### 8.6 Deploy Jaeger Tracing

```bash
# Add Jaeger Helm repository
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm repo update

# Install Jaeger
helm upgrade --install jaeger jaegertracing/jaeger \
  --namespace tracing \
  --set collector.service.type=ClusterIP \
  --set query.service.type=NodePort \
  --set query.service.nodePort=30686
```

**Verify all stacks**:
```bash
kubectl get pods -n monitoring
kubectl get pods -n elastic-system
kubectl get pods -n tracing
```

---

## Step 9: Verify Complete Deployment

### 9.1 Health Checks

```bash
# Check cluster health
kubectl get nodes
kubectl get pods -A

# Check services
kubectl get svc -n model-serving
kubectl get svc -n nginx-ingress
kubectl get svc -n monitoring
```

### 9.2 Test API Endpoints

```bash
# Health endpoint
curl http://$SERVICE_IP:8000/health
# Expected: { "status": "healthy" }

# Metrics endpoint
curl http://$SERVICE_IP:8000/metrics
# Expected: Prometheus-format metrics

# Detection endpoint (with image)
curl -X POST http://$SERVICE_IP:8000/detect/faces/image \
  -F "image=@sample_image.jpg" \
  -o result_annotated.jpg
# Expected: Annotated image in result_annotated.jpg
```

### 9.3 Access Monitoring Dashboards

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana** | http://NODE_IP:30000 | admin / [password] |
| **Kibana** | http://NODE_IP:30601 | elastic / [password] |
| **Jaeger UI** | http://NODE_IP:30686 | None (open access) |
| **Prometheus** | http://NODE_IP:30090 | None (open access) |

---

## Step 10: Configure Local DNS (Optional)

To use hostname instead of IP:

```bash
# Get Ingress IP
export INGRESS_IP=$(kubectl get svc nginx-ingress-controller -n nginx-ingress -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Add to /etc/hosts (Linux/macOS) or C:\Windows\System32\drivers\etc\hosts (Windows)
echo "$INGRESS_IP face-detection.local" | sudo tee -a /etc/hosts

# Test
curl http://face-detection.local/health
```

---

## Troubleshooting

### Issue: GKE Cluster Creation Fails

**Cause**: GCP quota exceeded or API not enabled

**Solution**:
```bash
# Verify APIs are enabled
gcloud services list --enabled | grep -E "compute|container"

# Request quota increase in GCP Console
# Compute → Quotas → Filter by CPU, increase limit
```

### Issue: Pod Stuck in "ImagePullBackOff"

**Cause**: Image not found or registry credentials missing

**Solution**:
```bash
# Check pod logs
kubectl describe pod <pod-name> -n model-serving

# Verify image exists in registry
docker pull longhd06/face-detection:latest

# Re-push if needed
docker push longhd06/face-detection:latest
```

### Issue: Service has no External IP

**Cause**: LoadBalancer type service pending external IP assignment

**Solution**:
```bash
# Check service status
kubectl get svc face-detection -n model-serving -w

# May take 2–5 minutes for GCP to assign external IP
# Press Ctrl+C to exit watch mode
```

### Issue: Jaeger shows no traces

**Cause**: Application not configured with correct endpoint or exporter not running

**Solution**:
```bash
# Verify Jaeger collector is running
kubectl get pods -n tracing

# Check FastAPI pod logs
kubectl logs <pod-name> -n model-serving | grep -i jaeger

# Verify OTLP_GRPC_ENDPOINT is correct
kubectl get deploy face-detection -n model-serving -o yaml | grep -i otlp
```

---

## Cleanup & Cost Management

### Remove All Resources

```bash
# Delete Kubernetes resources
kubectl delete namespace model-serving nginx-ingress monitoring elastic-system tracing

# Destroy GCP infrastructure
cd infrastructure
make destroy

# Confirm by typing 'yes'
```

### Cost Estimation

**Level 1 Monthly Cost** (~$200–300):
- GKE cluster (1× e2-medium, preemptible): ~$50
- GCE VM (1× n1-standard-1, Jenkins): ~$30
- Network egress: ~$50
- Storage (PD, Elasticsearch): ~$50–100

---

## Production Hardening (Phase 03 — L1 fundamentals)

The Helm chart `charts/face-detection/` ships with L1 production fundamentals enabled by default. Apply per-namespace prerequisites before installing.

### 1. Label namespaces (required for NetworkPolicy egress)

```bash
for ns in model-serving monitoring logging tracing istio-system; do
  kubectl label namespace "$ns" name="$ns" --overwrite
done
```

### 2. Apply ResourceQuotas

```bash
kubectl apply -f infrastructure/k8s/quotas/
kubectl get resourcequota -A
```

### 3. Install chart with hardening (defaults enabled)

```bash
helm upgrade --install face-detection charts/face-detection \
  --namespace model-serving --create-namespace
```

Enabled by default: probes (liveness 30s/30s, readiness 10s/15s init), HPA (1→3 replicas @ 70% CPU), scoped RBAC (Role, NOT cluster-admin), NetworkPolicy (deny-all + whitelist ingress from `istio-system` + egress to monitoring/tracing/logging + DNS), PDB (minAvailable=1).

### 4. Verify

```bash
kubectl describe pod -n model-serving | grep -A 5 "Liveness\|Readiness"
kubectl get hpa,pdb,networkpolicy,sa,role,rolebinding -n model-serving
```

### 5. Audit cluster-admin bindings (cleanup)

`README.md` (Jenkins setup) previously instructed creating `model-serving-admin-binding` and `cluster-admin-default-binding`. Remove after switching to scoped RBAC:

```bash
kubectl delete clusterrolebinding model-serving-admin-binding 2>/dev/null || true
kubectl delete clusterrolebinding cluster-admin-default-binding 2>/dev/null || true
# Verify nothing project-owned remains:
kubectl get clusterrolebindings -o json | jq -r '.items[] | select(.subjects[]?.namespace=="model-serving") | .metadata.name'
```

### 6. Trace sampling

`api/main.py` uses `ParentBased(TraceIdRatioBased(0.1))` — 10% root sampling, parent decision propagated. Override via env var `TRACE_SAMPLE_RATIO` (0.0–1.0).

### Deferred (out of Phase 03)

- **External Secrets Operator** — needs GCP Workload Identity. Add when production secrets needed.
- **Istio mTLS STRICT** — Phase 04 (service mesh hardening).
- **OPA Gatekeeper / Kyverno** — Phase 05 (admission control).
- **Pod Security Standards (restricted)** — Phase 06.

---

## Next Steps

1. **For Level 2**: See [docs/project-roadmap.md](./project-roadmap.md) Phase 2 (Data Engineering)
2. **For troubleshooting**: See [ADR_ARCHITECTURE_REVIEW.md](../ADR_ARCHITECTURE_REVIEW.md) action items
3. **For detailed architecture**: See [docs/system-architecture.md](./system-architecture.md)
4. **For YAGNI cut rationale**: See [docs/archive/cut-components-v0.1.md](./archive/cut-components-v0.1.md)

---

## Reference Documentation

- **Project Overview**: [docs/project-overview-pdr.md](./project-overview-pdr.md)
- **System Architecture**: [docs/system-architecture.md](./system-architecture.md)
- **Code Standards**: [docs/code-standards.md](./code-standards.md)
- **Codebase Summary**: [docs/codebase-summary.md](./codebase-summary.md)
- **Project Roadmap**: [docs/project-roadmap.md](./project-roadmap.md)

---

**Last Updated**: 2026-04-15  
**Author**: Hoàng Đức Long
