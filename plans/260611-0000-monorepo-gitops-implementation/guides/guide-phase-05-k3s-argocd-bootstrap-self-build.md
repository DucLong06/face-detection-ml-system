# Guide Phase 5 — k3s Lab + ArgoCD Bootstrap + L1 GitOps ★ (tự làm, có test từng bước)

> **Bản chính sau B1**: cluster = k3s multi-node trên lab 7+ server 8GB. Bản kind cũ (`guide-phase-05-kind-argocd-bootstrap-self-build.md`) giữ làm sandbox laptop — cấu trúc gitops giống hệt, chỉ khác Step 1-2 và ingress.
> Tiền đề: phase 4 merge main. Quy ước: `<IP1>` = IP server đầu (control-plane), `<IPx>` = IP các server còn lại, thay bằng IP thật của bạn.
> Branch: `git checkout main && git pull && git checkout -b gitops/bootstrap-l1`

## Step 0 — Chuẩn bị 7 server (chạy trên TỪNG server, hoặc viết script lặp qua SSH)
```bash
# từ laptop, kiểm tra SSH tới từng server:
for ip in <IP1> <IP2> <IP3> <IP4> <IP5> <IP6> <IP7>; do ssh user@$ip 'hostname && free -h | head -2'; done
# trên từng server (sysctls theo finding F12/F4 — ES/Kafka/Prometheus cần):
sudo tee /etc/sysctl.d/99-mlops-lab.conf <<'EOF'
fs.inotify.max_user_instances=512
fs.inotify.max_user_watches=1048576
vm.max_map_count=262144
EOF
sudo sysctl --system
```
✅ TEST: `ssh user@<IPx> 'sysctl vm.max_map_count'` → `262144` trên cả 7 máy; các server ping được nhau (`ping <IP1>` từ IP2).
🔥 Firewall: k3s cần port 6443 (API), 8472/UDP (flannel VXLAN), 10250 — `sudo ufw allow` hoặc tắt ufw trong lab.

## Step 1 — Cài k3s: server (control-plane) trên máy 1
```bash
ssh user@<IP1>
# --disable traefik: ta dùng ingress-nginx qua GitOps (đồng nhất với plan)
# taint control-plane: etcd/apiserver không phải cạnh tranh RAM với workload (finding F11)
curl -sfL https://get.k3s.io | sh -s - server \
  --disable traefik \
  --node-taint node-role.kubernetes.io/control-plane=:NoSchedule \
  --write-kubeconfig-mode 644
sudo cat /var/lib/rancher/k3s/server/node-token   # LƯU TOKEN NÀY cho Step 2
```
✅ TEST: `sudo k3s kubectl get nodes` → 1 node `Ready,control-plane` trong ~30s.

## Step 2 — Join 6 agent
```bash
# trên TỪNG server còn lại (IP2..IP7):
curl -sfL https://get.k3s.io | K3S_URL=https://<IP1>:6443 K3S_TOKEN=<TOKEN> sh -
```
✅ TEST (trên server 1): `sudo k3s kubectl get nodes` → **7 node Ready** (1 control-plane + 6 worker).
🔥 Node NotReady: xem `journalctl -u k3s-agent -f` trên node đó — thường do token sai hoặc port 6443 bị chặn.

> **Tùy chọn (sau này):** máy dev 40GB cũng join được làm worker "to" (chạy đúng lệnh agent trên + `--node-label size=big`), cho pod béo (`nodeSelector: {size: big}`). Đổi lại: máy dev tắt/sleep = node NotReady, pod bị evict — chỉ nên join khi cần, không join mặc định.

## Step 3 — kubectl từ laptop
```bash
scp user@<IP1>:/etc/rancher/k3s/k3s.yaml ~/.kube/config-lab
sed -i 's/127.0.0.1/<IP1>/' ~/.kube/config-lab
export KUBECONFIG=~/.kube/config-lab     # thêm vào ~/.zshrc cho tiện
```
✅ TEST: `kubectl get nodes` từ laptop → 7 node. `kubectl top nodes` (k3s có metrics-server sẵn) → thấy RAM từng node — **ghi baseline này vào clusters/k3s/README.md** (sẽ so sánh sau mỗi phase).

## Step 4 — Cài ArgoCD (lệnh helm TAY duy nhất của cả dự án)
Giống guide kind cũ Step 2, không đổi:
```bash
helm repo add argo https://argoproj.github.io/argo-helm && helm repo update
helm install argocd argo/argo-cd -n argocd --create-namespace \
  -f gitops/platform/platform/argocd/values-cpu.yaml   # values: server.insecure=true
```
✅ TEST: 7 pod Running trong ns argocd; port-forward 8080 login admin OK (xem guide kind Step 2 TEST 2).

## Step 5 — Repo secret + root app-of-apps
Giống guide kind Steps 3-4 (namespaces / root-app / PAT nếu repo private) — **2 khác biệt theo adjudication**:
1. **S4**: root-app.yaml COPY thêm vào `gitops/apps/root-app.yaml` (root tự quản chính nó — sửa root trong git là cluster tự cập nhật).
2. **S5**: app `namespaces` KHÔNG bật prune:
```yaml
  syncPolicy:
    automated: { selfHeal: true }        # KHÔNG prune — xoá nhầm ns = mất PVC cascade
    syncOptions: [Prune=false]
```
```bash
kubectl apply -f gitops/bootstrap/root-app.yaml   # lần áp tay DUY NHẤT
```
✅ TEST: `kubectl -n argocd get applications` → root + namespaces `Synced/Healthy`; thử sửa root-app.yaml trong git (vd thêm label) → merge → tự cập nhật không cần apply tay (test S4).

## Step 6 — ingress-nginx (khác kind: dùng LoadBalancer/klipper thay hostPort)
`gitops/apps/01-ingress-nginx.yaml` — values phần controller:
```yaml
        controller:
          service: { type: LoadBalancer }   # k3s klipper-lb tự cấp IP node
```
✅ TEST: `kubectl -n ingress get svc` → EXTERNAL-IP = IP các node (klipper); `curl -s http://<IP1>` → `404 Not Found` từ nginx.

## Step 7 — face-detect qua GitOps
Giống guide kind Step 6, đổi host ingress sang **nip.io** (DNS magic trỏ về IP nhúng trong tên):
```yaml
# charts/face-detect/values-cpu.yaml
ingress: { host: face.<IP1>.nip.io }
```
✅ TEST 1: pod Running ở `model-serving`, image `ghcr.io/duclong06/face-detect:sha-...`.
✅ TEST 2: `curl -s -X POST -F "file=@apps/face-detect/tests/test_face.jpg" http://face.<IP1>.nip.io/detect | head -c 300` → JSON bbox.
🔥 ImagePullBackOff: package GHCR chưa public (guide 04 Step 5 TEST 2) hoặc cần imagePullSecret.

## Step 8 — CI round-trip
Giống guide kind Step 7: sửa 1 dòng → PR → merge → đo: GHA xanh → bump commit → pod mới rollout → curl version mới.
✅ TEST: < 10 phút, không gõ kubectl.

## Step 9 — bootstrap.sh theo contract B5 (2 input ngoài git)
`clusters/k3s/bootstrap.sh` — chỉ lo phần TRÊN cluster (cluster provision = Steps 0-2, ghi thành `clusters/k3s/install-server.sh` + `install-agent.sh`):
```bash
#!/usr/bin/env bash
set -euo pipefail
# Input 1: GITHUB_PAT (env) — repo secret cho ArgoCD (nếu repo private)
# Input 2: SEALED_KEY_BACKUP (env, path) — restore TRƯỚC khi sealed-secrets controller cài (phase 6+)
[ -n "${SEALED_KEY_BACKUP:-}" ] && kubectl apply -f "$SEALED_KEY_BACKUP"
helm upgrade --install argocd argo/argo-cd -n argocd --create-namespace \
  -f gitops/platform/platform/argocd/values-cpu.yaml
[ -n "${GITHUB_PAT:-}" ] && kubectl -n argocd create secret generic repo-face-detect \
  --from-literal=type=git --from-literal=url=https://github.com/DucLong06/face-detection-ml-system.git \
  --from-literal=username=DucLong06 --from-literal=password="$GITHUB_PAT" \
  --dry-run=client -o yaml | kubectl apply -f - && \
  kubectl -n argocd label secret repo-face-detect argocd.argoproj.io/secret-type=repository --overwrite
kubectl apply -f gitops/bootstrap/root-app.yaml
```
✅ TEST 1 (idempotent): chạy lần 2 → không lỗi.
✅ TEST 2 (lab trắng — TEST QUAN TRỌNG NHẤT): uninstall k3s cả 7 máy (`/usr/local/bin/k3s-uninstall.sh` server, `k3s-agent-uninstall.sh` agents) → chạy lại install scripts + `GITHUB_PAT=... ./clusters/k3s/bootstrap.sh` → ~10 phút sau mọi Application Healthy + curl inference OK.

## Step 10 — README + DoD
`clusters/k3s/README.md`: topology 7 node + bảng IP + RAM baseline + install/teardown + 2-input contract. `gitops/README.md`: app-of-apps, sync-wave, rule scratch-ns (S5), cách thêm app.
✅ Definition of Done:
- [ ] 7 node Ready, kubectl từ laptop
- [ ] Lab trắng → install scripts + bootstrap.sh (2 input) → app serve request
- [ ] CI round-trip < 10 phút
- [ ] Applications toàn Healthy/Synced; root tự quản
- [ ] 2 README xong, RAM baseline ghi lại

## 📚 Học trong phase này
k3s server/agent + token join · taint control-plane · flannel VXLAN port · klipper-lb vs hostPort · nip.io · ArgoCD app-of-apps/sync-wave/selfHeal-vs-prune · contract bootstrap 2-input.
