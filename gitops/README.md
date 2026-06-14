# gitops/

Nguồn sự thật khai báo cho ArgoCD (pull-based GitOps). Không `kubectl apply` tay.

## Cấu trúc
- `bootstrap/` — cài ArgoCD + root app-of-apps (điểm vào duy nhất)
- `apps/` — Application CRDs, sync-wave T0→T6
- `platform/` — components theo tier:
  - `platform/` (nền: ingress…) · `data/` · `ml/` · `serving/` · `drift/` · `rag/` · `observability/`

## Đọc gì tiếp
- Bootstrap cluster: `clusters/k3s/` (phase 5).
