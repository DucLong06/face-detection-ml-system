---
phase: 4
title: "CI: GitHub Actions thay Jenkins"
status: pending
priority: P1
effort: "3h"
dependencies: [3]
---

# Phase 4: CI — GitHub Actions Migration

## Overview
Thay Jenkins bằng GHA: PR = test; main = build→push→bump tag (nửa GitOps; ArgoCD nối ở phase 5).

## Requirements
- Functional: `.github/workflows/app-ci.yaml` (paths filter `apps/**`, `charts/face-detect/**`): job test (pytest), job build-push (đợi test), job bump-tag (yq sửa `values-cpu.yaml` image.tag=sha → commit bởi github-actions[bot] với `[skip ci]`).
- `.github/workflows/lint-charts.yaml`: `helm lint` + `helm template` mọi chart khi `charts/**`/`gitops/**` đổi.
- Registry: **GHCR** (đã chốt validation): `ghcr.io/<owner>/face-detect`, login bằng GITHUB_TOKEN, set package public để kind pull không cần cred. <!-- Updated: Validation Session 1 -->
- Non-functional: build có cache (buildx gha cache); tag = `sha-<short>` + `latest` cho main.

## Wiring
```
PR → test
main push (apps/**) → test → build+push → bump charts/face-detect/values-cpu.yaml → [phase 5: ArgoCD sync]
```
Bump bằng commit trực tiếp lên main (monorepo, single dev) — không cần PR bot. `[skip ci]` chống loop.

## Implementation Steps
1. Viết 2 workflow + cấu hình secrets (DOCKERHUB_* hoặc dùng GHCR + permissions packages:write).
2. Sửa `apps/face-detect/Dockerfile` nếu path đổi sau restructure; pytest chạy được trong container builder.
3. Push branch → xem run xanh trên GitHub; verify `docker pull ghcr.io/...` ẩn danh được (package public); verify bump commit xuất hiện.
4. Xoá `Jenkinsfile` + note migration trong `docs/` (1 dòng changelog).
5. README: `.github/` ghi vào root README mục CI/CD.

## Success Criteria
- [ ] PR mở → test chạy; main push → image mới trên registry + values bump commit
- [ ] helm lint xanh; không secret nào in ra log
- [ ] Jenkinsfile đã xoá, docs ghi nhận

## Risk Assessment
- Loop CI do bump commit → `[skip ci]` + paths-ignore `charts/**` trong app-ci.
- pytest cần model weights? → mock/skip inference test nặng trong CI (marker), giữ unit nhẹ.
