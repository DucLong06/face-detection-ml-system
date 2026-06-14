# clusters/

Định nghĩa & provisioning hạ tầng cluster.

## Cấu trúc
- `k3s/` — lab cluster chính (bootstrap.sh + install scripts) — **đang dùng**
- `kind/` — sandbox local
- `gke/` — Terraform + Ansible bản v0 GKE (tham khảo)

## Đọc gì tiếp
- Sau provision → `gitops/bootstrap/` cài ArgoCD.
