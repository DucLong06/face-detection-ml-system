# Guide Phase 5 — kind + ArgoCD Bootstrap + L1 GitOps ★ (tự làm, có test từng bước)

> Tiền đề: phase 4 merge main (image GHCR public, values-cpu có tag thật). CLI đã có sẵn trên máy: kind 0.27, helm 3.18, kubectl 1.31 ✓.
> Branch: `git checkout main && git pull && git checkout -b gitops/bootstrap-l1`

## Step 1 — kind cluster config
Tạo `clusters/kind/kind-config.yaml`:
```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: facedetect
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:           # cho phép curl http://localhost từ máy host
      - { containerPort: 80, hostPort: 80, protocol: TCP }
      - { containerPort: 443, hostPort: 443, protocol: TCP }
  - role: worker
  - role: worker
```
```bash
kind create cluster --config clusters/kind/kind-config.yaml
```
✅ TEST: `kubectl get nodes` → 3 node `Ready` (1 control-plane, 2 worker) trong ~60s.
🔥 Port 80/443 bận: `sudo lsof -i :80` — tắt service chiếm port hoặc đổi hostPort 8080/8443 (nhớ đổi URL test sau này).

## Step 2 — Cài ArgoCD (lệnh helm TAY duy nhất — mọi thứ sau qua GitOps)
Tạo `gitops/platform/platform/argocd/values-cpu.yaml`:
```yaml
configs:
  params:
    server.insecure: true        # truy cập qua port-forward, khỏi TLS local
```
```bash
helm repo add argo https://argoproj.github.io/argo-helm && helm repo update
helm install argocd argo/argo-cd -n argocd --create-namespace \
  -f gitops/platform/platform/argocd/values-cpu.yaml
```
✅ TEST 1: `kubectl -n argocd get pods` → 7 pod `Running` (server, repo-server, application-controller, dex, redis, notifications, applicationset) sau ~2 phút.
✅ TEST 2 (UI):
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d; echo
kubectl -n argocd port-forward svc/argocd-server 8080:80 &
```
→ mở http://localhost:8080, login `admin`/<password trên> thành công.

## Step 3 — Namespaces qua GitOps (Application đầu tiên)
Tạo `gitops/platform/platform/namespaces/namespaces.yaml` (raw manifests, đủ ns đợt đầu):
```yaml
apiVersion: v1
kind: Namespace
metadata: { name: model-serving, labels: { domain: serving } }
---
apiVersion: v1
kind: Namespace
metadata: { name: ingress, labels: { domain: platform } }
```
Tạo `gitops/apps/00-namespaces.yaml`:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: namespaces
  namespace: argocd
  annotations: { argocd.argoproj.io/sync-wave: "0" }
spec:
  project: default
  source:
    repoURL: https://github.com/DucLong06/face-detect-gke.git
    targetRevision: main
    path: gitops/platform/platform/namespaces
  destination: { server: https://kubernetes.default.svc }
  syncPolicy:
    automated: { prune: true, selfHeal: true }
```
**Repo private?** Tạo token đọc-repo (Settings→Developer→fine-grained PAT, content:read) rồi:
```bash
kubectl -n argocd create secret generic repo-face-detect \
  --from-literal=type=git --from-literal=url=https://github.com/DucLong06/face-detect-gke.git \
  --from-literal=username=DucLong06 --from-literal=password=<PAT>
kubectl -n argocd label secret repo-face-detect argocd.argoproj.io/secret-type=repository
```

## Step 4 — Root app-of-apps (điểm vào duy nhất)
Tạo `gitops/bootstrap/root-app.yaml`:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: { name: root, namespace: argocd }
spec:
  project: default
  source:
    repoURL: https://github.com/DucLong06/face-detect-gke.git
    targetRevision: main
    path: gitops/apps          # root chỉ trỏ thư mục Application CRDs
  destination: { server: https://kubernetes.default.svc }
  syncPolicy:
    automated: { prune: true, selfHeal: true }
```
**Push các file gitops lên branch, mở PR, merge main TRƯỚC** (ArgoCD đọc từ main), rồi:
```bash
kubectl apply -f gitops/bootstrap/root-app.yaml
```
✅ TEST: `kubectl -n argocd get applications` → `root` + `namespaces` đều `Synced/Healthy`; `kubectl get ns model-serving ingress` → tồn tại.
🔥 `ComparisonError ... repository not found`: repo private chưa khai secret Step 3, hoặc sai repoURL.
🔥 App `OutOfSync` mãi: xem `kubectl -n argocd describe application namespaces | tail -20` — thường do path sai.

## Step 5 — Ingress controller (wave 1)
Tạo `gitops/apps/01-ingress-nginx.yaml` — Application loại **helm chart upstream**:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ingress-nginx
  namespace: argocd
  annotations: { argocd.argoproj.io/sync-wave: "1" }
spec:
  project: default
  source:
    repoURL: https://kubernetes.github.io/ingress-nginx
    chart: ingress-nginx
    targetRevision: 4.12.1
    helm:
      valuesObject:
        controller:
          hostPort: { enabled: true }          # pattern kind chính thức
          nodeSelector: { ingress-ready: "true" }
          tolerations: [{ key: node-role.kubernetes.io/control-plane, operator: Exists, effect: NoSchedule }]
          service: { type: ClusterIP }
  destination: { server: https://kubernetes.default.svc, namespace: ingress }
  syncPolicy:
    automated: { prune: true, selfHeal: true }
    syncOptions: [CreateNamespace=false]
```
(PR → merge → ArgoCD tự sync.)
✅ TEST: `kubectl -n ingress get pods` → controller Running; `curl -s http://localhost` → `404 Not Found` từ nginx (controller sống, chưa có route — đúng).

## Step 6 — face-detect qua GitOps (wave 2)
Soát `charts/face-detect`: deployment dùng `image.repository:image.tag` từ values; thêm `ingress` template nếu chart cũ chưa có (host: `face.localtest.me` — domain này tự trỏ 127.0.0.1, khỏi sửa /etc/hosts). Tạo `gitops/apps/02-face-detect.yaml`:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: face-detect
  namespace: argocd
  annotations: { argocd.argoproj.io/sync-wave: "2" }
spec:
  project: default
  source:
    repoURL: https://github.com/DucLong06/face-detect-gke.git
    targetRevision: main
    path: charts/face-detect
    helm: { valueFiles: [values-cpu.yaml] }
  destination: { server: https://kubernetes.default.svc, namespace: model-serving }
  syncPolicy:
    automated: { prune: true, selfHeal: true }
```
✅ TEST 1: `kubectl -n model-serving get pods` → face-detect Running, image = `ghcr.io/duclong06/face-detect:sha-...` (`kubectl -n model-serving get pod -o jsonpath='{.items[0].spec.containers[0].image}'`).
✅ TEST 2 (e2e inference):
```bash
curl -s -X POST -F "file=@apps/face-detect/tests/test_face.jpg" http://face.localtest.me/detect | head -c 300
```
→ JSON bbox. (Endpoint/field xem `apps/face-detect/src/main.py` — chỉnh lệnh theo route thật.)

## Step 7 — CI round-trip (GitOps khép vòng)
Sửa 1 dòng vô hại trong `apps/face-detect/src/main.py` (vd version string) → commit lên main (qua PR) → đo giờ:
✅ TEST: trong <10 phút: GHA xanh → commit bump xuất hiện → `kubectl -n model-serving get pods -w` thấy pod mới rollout → curl trả version mới. KHÔNG gõ lệnh kubectl apply nào.

## Step 8 — Gói thành bootstrap.sh + test idempotent + test máy-trắng
Tạo `clusters/kind/bootstrap.sh` (gói Step 1→4: kind create nếu chưa có → helm install argocd nếu chưa có → apply root-app; `set -euo pipefail`).
✅ TEST 1 (idempotent): chạy `./clusters/kind/bootstrap.sh` lần 2 → không lỗi, không phá gì.
✅ TEST 2 (máy trắng — TEST QUAN TRỌNG NHẤT PHASE):
```bash
kind delete cluster --name facedetect && ./clusters/kind/bootstrap.sh
# đợi ~5 phút
kubectl -n argocd get applications && curl -s -X POST -F "file=@apps/face-detect/tests/test_face.jpg" http://face.localtest.me/detect
```
→ mọi Application Healthy + inference OK, từ con số 0.

## Step 9 — README + DoD
Viết `clusters/kind/README.md` (yêu cầu máy, bootstrap, teardown) + `gitops/README.md` (app-of-apps là gì, sync-wave, thêm app mới thế nào) + cập nhật root README quickstart.
✅ Definition of Done:
- [ ] Máy trắng → 1 lệnh → app serve request (Step 8 TEST 2)
- [ ] CI round-trip < 10 phút không kubectl tay (Step 7)
- [ ] `kubectl -n argocd get applications` toàn Healthy/Synced
- [ ] 2 README viết xong, root README cập nhật, status Platform → 🔄

## 📚 Học trong phase này
kind networking (extraPortMappings/hostPort) · ArgoCD: Application CRD, app-of-apps, sync-wave, automated prune/selfHeal · helm valueFiles vs valuesObject · localtest.me trick · vì sao chỉ root-app được apply tay.
