# charts/

Helm charts tự viết cho app (không chứa chart upstream — upstream để ở `gitops/platform/`).

## Cấu trúc
- `face-detect/` — chart serve model (release name: `model-serving`)
  - `values-cpu.yaml` / `values-gpu.yaml` — profile theo hạ tầng

## Đọc gì tiếp
- GitOps sync: `gitops/apps/` trỏ chart này.
