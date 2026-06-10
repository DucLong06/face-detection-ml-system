---
phase: 3
title: "Monorepo restructure + README skeleton"
status: pending
priority: P1
effort: "4h"
dependencies: [2]
---

# Phase 3: Monorepo Restructure + README Skeleton

## Overview
Dựng cây thư mục đích bằng `git mv` (giữ history), dọn rác, tạo README skeleton mọi cấp — KHÔNG đụng runtime/code logic.

## Target Tree & Mapping (chuẩn từ plan.md)
| Từ | Đến | Ghi chú |
|---|---|---|
| `api/` | `apps/face-detect/` | main.py+my_yolo.py → `src/`, test_*.py → `tests/`, dockerfile → `Dockerfile` (xoá bản root nếu trùng), README giữ |
| `charts/face-detection` | `charts/face-detect/` | đổi tên thống nhất; thêm `values-cpu.yaml`/`values-gpu.yaml` stub |
| `charts/nginx-ingress` | `gitops/platform/platform/nginx-ingress/` | values-only (chart upstream) |
| `infrastructure/` | `clusters/gke/` | terraform/ ansible/ Makefile; **credentials/ + ssh_key*: KHÔNG git mv — kiểm tra gitignore, di chuyển ngoài git** |
| `datapipeline/` | `pipelines/_legacy-datapipeline/` | giữ tham khảo, lọc dần ở phase 7 |
| `newplans/` | `docs/architecture/` | diagrams+builders+phase-specs+README kiến trúc; sửa OUTDIR builders (đã dùng `__file__` ✓ tự theo) |
| `monitoring/` (vendored kube-prometheus-stack/jaeger/ELK charts thời L1) | trích values hữu ích → `gitops/platform/observability/_legacy-values/` rồi **xoá** | <!-- Updated: Validation Session 1 --> |
| `models/ scripts/ custom_images/ notebooks/ .vscode/` | xoá (rỗng) | |
| `repomix-output.xml` (18MB) | xoá + gitignore pattern | |
| `NEWREADME.md`, `newreview.md` | nội dung còn giá trị → merge vào docs/, xoá file | |
| `Jenkinsfile` | giữ đến hết phase 4, xoá khi GHA xanh | |
| (mới) | `gitops/{bootstrap,apps,platform/*}/`, `clusters/kind/`, `pipelines/*/`, `.github/workflows/` | mỗi dir có README.md skeleton |

## README hierarchy (skeleton ngay phase này, fill dần)
- Root `README.md`: hình overview + bảng 7 domain (status: ⬜/🔄/✅) + link README con + quickstart bootstrap.
- README con cấp 1: `apps/ charts/ gitops/ clusters/ pipelines/ docs/` — mục đích, cấu trúc, "đọc gì tiếp".
- Quy ước: xong mục nào fill README mục đó (success criteria các phase sau đều có dòng README).

## Implementation Steps
1. Tạo branch `restructure/monorepo-gitops` từ LongHD/NewPlans; kết phase = **PR vào main** (flow đã chốt: mỗi phase 1 branch+PR, ArgoCD/CI track main). <!-- Updated: Validation Session 1 -->
2. `git mv` theo bảng (từng nhóm 1 commit: apps / charts / clusters / docs / cleanup).
3. Quét đường dẫn gãy: grep refs `api/`, `infrastructure/`, `newplans/` trong *.md, *.py, Dockerfile, charts → sửa; chạy link-check script README (đã có pattern từ plan 260610).
4. Render lại 8 hình từ vị trí mới (builders dùng `__file__` → chỉ cần icons prep) — smoke proof tree mới sống.
5. Root README + README con skeleton; cập nhật `.gitignore` (credentials, repomix, /tmp artifacts).
6. Commit + (không merge vội) — phase 4 tiếp trên branch này.

## Success Criteria
- [ ] Tree đích đúng plan.md; `git log --follow` giữ history file chính
- [ ] 0 link/path gãy (script check); builders render OK từ chỗ mới
- [ ] Không credential nào nằm trong git (kiểm `git ls-files | grep -iE "credential|ssh|secret"`)
- [ ] Root README + ≥6 README con skeleton

## Risk Assessment
- Path gãy ngầm trong docs cũ → grep sweep + link check bắt buộc trước commit cuối.
- credentials/ssh_key đã từng bị track? → kiểm history, nếu có thì lên kế hoạch riêng (BFG) — report cho user, không tự rewrite history.
