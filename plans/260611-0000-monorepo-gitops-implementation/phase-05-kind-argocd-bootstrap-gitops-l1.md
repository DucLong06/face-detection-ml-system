---
phase: 5
title: "kind + ArgoCD bootstrap + L1 GitOps ★"
status: pending
priority: P1
effort: "1d"
dependencies: [4]
---

# Phase 5: kind + ArgoCD Bootstrap + L1 GitOps ★ MILESTONE

## Overview
Milestone quan trọng nhất: từ máy trắng → 1 lệnh dựng cluster kind có ArgoCD, root app-of-apps kéo face-detect lên `model-serving`, CI round-trip end-to-end.

## Architecture
```
bootstrap.sh:
  kind create cluster --config clusters/kind/kind-config.yaml   # 1 control + 2 worker
  helm install argocd argo/argo-cd -n argocd --create-namespace -f gitops/platform/platform/argocd/values-cpu.yaml
  kubectl apply -f gitops/bootstrap/root-app.yaml               # Application → gitops/apps/
root-app (app-of-apps) → gitops/apps/*.yaml (mỗi file 1 Application, annotation sync-wave):
  wave 0: namespaces (+ labels chuẩn)        wave 1: nginx-ingress
  wave 2: face-detect (charts/face-detect, values-cpu)
```
CI bump tag (phase 4) → ArgoCD auto-sync (`automated: {prune: true, selfHeal: true}`) → rollout.

## Related Code Files
- Create: `clusters/kind/{kind-config.yaml,bootstrap.sh,README.md}`
- Create: `gitops/bootstrap/{root-app.yaml,README.md}`; `gitops/apps/{namespaces,nginx-ingress,face-detect}.yaml`
- Create: `gitops/platform/platform/argocd/values-cpu.yaml`
- Modify: `charts/face-detect/` — values-cpu hoàn chỉnh (resources nhỏ, ingress host `face.localtest.me`, probe)

## Implementation Steps
1. kind-config: extraPortMappings 80/443 → ingress hoạt động local.
2. Namespaces manifest đủ map plan (model-serving trước; còn lại thêm dần per phase).
3. Chart face-detect: image từ registry phase 4; service+ingress; values-gpu stub (nodeSelector gpu, runtime onnx→tensorrt) chưa dùng.
4. bootstrap.sh idempotent (chạy lại không vỡ); README kind ghi rõ yêu cầu máy (CPU/RAM).
5. E2E: bootstrap từ đầu → `curl face.localtest.me/detect` (ảnh test) trả bbox; sửa code → push → pod mới tự lên (đo thời gian round-trip).
6. README: root README quickstart trỏ bootstrap; `gitops/README.md` giải thích app-of-apps + sync-wave.

## Success Criteria
- [ ] Máy trắng → `./clusters/kind/bootstrap.sh` → app serve được request (1 lệnh)
- [ ] CI round-trip push→pod mới < 10 phút, không kubectl tay
- [ ] `kubectl get applications -n argocd` toàn Healthy/Synced
- [ ] README kind + gitops viết xong

## Risk Assessment
- ArgoCD Application targetRevision = **main** (flow PR đã chốt); repo private → deploy key trong bootstrap, doc rõ. <!-- Updated: Validation Session 1 -->
- Ingress kind đặc thù (hostPort) → dùng pattern chính thức kind + nginx; localtest.me khỏi sửa /etc/hosts.

## Red-Team Adjudicated Updates (260611)
- **B1: cluster chính = k3s multi-node trên 7+ server 8GB** (thay kind). Guide mới: `guides/guide-phase-05-k3s-argocd-bootstrap-self-build.md`. kind giữ làm sandbox laptop tùy chọn.
- B5: bootstrap contract 2-input (GITHUB_PAT + sealed-key backup) — bootstrap.sh nhận env/flag, restore key trước khi cài sealed-secrets controller.
- S4: root-app tự quản (copy vào gitops/apps/). S5: namespaces app Prune=false + rule scratch-ns vào gitops/README.
