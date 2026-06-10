---
name: monorepo-gitops-implementation
date: 2026-06-11 00:00
status: pending
type: master implementation (repo restructure + CI/CD + platform T0→T6)
branch: LongHD/NewPlans
env: CPU-first k3s multi-node (lab 7+ server 8GB, ≥56GB) → GKE sau; kind = sandbox laptop tùy chọn (values-cpu / values-gpu per chart)
supersedes: [260420-1055-consolidated-plans-drawio]
---

# Plan — Monorepo GitOps Implementation (bắt đầu làm thật)

## Context Links
- Brainstorm (approved design): [`../reports/brainstorm-260611-0000-monorepo-gitops-implementation-kickoff-report.md`](../reports/brainstorm-260611-0000-monorepo-gitops-implementation-kickoff-report.md)
- Master roadmap (stack T0-T6, reference): [`../260604-2213-mlops-l2-l3-rag-complete-build/plan.md`](../260604-2213-mlops-l2-l3-rag-complete-build/plan.md)
- Per-tool steps CPU-first (reference): `newplans/implementation-steps.md` + `newplans/phase-t0..t6-*.md`
- Diagram engine: `newplans/diagrams/icons/` (corridor + card style, completed 260610)

## User Decisions (DO NOT reverse)
- **Monorepo all-in-one** tại `face-detect-gke` ("super app lab"), docs ở đây
- CI = **GitHub Actions** (bỏ Jenkins sau khi GHA xanh) · CD = **ArgoCD GitOps** (không kubectl apply tay)
- **CPU-first trên k3s lab (7+ server 8GB) → GKE sau**; kind = sandbox laptop tùy chọn; mỗi chart: base + `values-cpu.yaml` + `values-gpu.yaml` <!-- B1 260611 -->
- Red-team kiến trúc TRƯỚC, findings phải được user duyệt từng cái; update 8 hình card-style theo findings
- Tree theo **domain** (không theo phase); README tổng + README con mỗi mục, viết ngay khi xong mục
- **Validated 260611**: registry = **GHCR** · máy local ~40GB RAM · `monitoring/` vendored charts = trích values rồi XOÁ · **FULL Kubeflow** (fallback KFP-standalone nếu kẹt >2 ngày — đã chốt, không tranh cãi lại) · secrets tạm = sealed-secrets · git flow = **branch/PR vào main**, ArgoCD track main

## Target Tree (đích của restructure — chi tiết trong phase 03)
```
face-detect-gke/
├── README.md                  # kiến trúc tổng + bảng status + link README con
├── .github/workflows/         # app-ci.yaml, lint-charts.yaml
├── apps/face-detect/          # ← api/ (src/ tests/ Dockerfile README)
├── charts/                    # charts tự viết: face-detect (base + values-cpu/-gpu)
├── gitops/
│   ├── bootstrap/             # ArgoCD install + root app-of-apps (điểm vào duy nhất)
│   ├── apps/                  # Application CRDs, sync-wave T0→T6
│   └── platform/{platform,data,ml,serving,drift,rag,observability}/
├── clusters/{k3s,kind,gke}/   # k3s lab (chính) · kind sandbox · terraform+ansible (← infrastructure/)
├── pipelines/                 # airflow-dags/ kubeflow/ flink-jobs/ spark-jobs/ rag-indexing/
├── docs/                      # + docs/architecture/ (← newplans: diagrams + builders + specs)
└── plans/                     # CK plans (gitignored)
```

## Wiring (CI/CD chuẩn GitOps)
`push apps/**` → GHA: pytest → build → push registry → bot bump image tag vào `charts/face-detect/values-*.yaml` → ArgoCD auto-sync → ns `model-serving`. Platform: sửa `gitops/platform/**` → ArgoCD sync. `clusters/k3s/bootstrap.sh` = ArgoCD + root app trên cluster k3s lab (cluster provision = `clusters/k3s/install-*.sh` per server) → tất cả tự kéo.

## Execution Mode (260611)
**USER TỰ TAY LÀM để học** — Claude chỉ lên kế hoạch + guide từng bước có test. Guides chi tiết (lệnh + ✅TEST + expected output + 🔥troubleshoot) trong `guides/`:
- [`guides/guide-phase-03-restructure-self-build.md`](guides/guide-phase-03-restructure-self-build.md)
- [`guides/guide-phase-04-ci-github-actions-self-build.md`](guides/guide-phase-04-ci-github-actions-self-build.md)
- [`guides/guide-phase-05-k3s-argocd-bootstrap-self-build.md`](guides/guide-phase-05-k3s-argocd-bootstrap-self-build.md) (bản kind cũ giữ làm sandbox: `guide-phase-05-kind-argocd-bootstrap-self-build.md`)
- Guides phase 6-12: viết **just-in-time** khi user xong phase trước (tránh stale — nội dung phụ thuộc cái thực dựng). Phase 1 (red-team) + 2 (diagrams) vẫn do Claude chạy khi user yêu cầu.

## Phases

| # | Phase | Status | File |
|---|-------|--------|------|
| 1 | Architecture red-team + user adjudication | completed | `phase-01-architecture-red-team-adjudication.md` |
| 2 | Diagrams: card style 7 drilldown + findings | completed | `phase-02-diagrams-card-style-all-drilldowns.md` |
| 3 | Monorepo restructure + README skeleton | pending | `phase-03-monorepo-restructure-readme-skeleton.md` |
| 4 | CI: GitHub Actions thay Jenkins | pending | `phase-04-ci-github-actions-migration.md` |
| 5 | k3s + ArgoCD bootstrap + L1 GitOps ★ | pending | `phase-05-kind-argocd-bootstrap-gitops-l1.md` |
| 6 | T0 Platform foundation (minimal) | pending | `phase-06-platform-foundation-minimal.md` |
| 7 | T1 Data pipeline (L2) | pending | `phase-07-data-pipeline-l2.md` |
| 8 | T2 ML platform | pending | `phase-08-ml-platform.md` |
| 9 | T3 Serving | pending | `phase-09-serving.md` |
| 10 | T4 Drift→Retrain loop ★ | pending | `phase-10-drift-retrain-loop.md` |
| 11 | T6 Observability | pending | `phase-11-observability.md` |
| 12 | T5 RAG/LLM | pending | `phase-12-rag-llm.md` |

## Critical Path & Dependencies
1→2 (findings sửa hình) → 3 (tree) → 4 (CI) → 5 (★ milestone L1-on-GitOps) → 6 → 7 → 8 → 9 → 10 (★ centerpiece) → 11; 12 độc lập sau 6 (cần GPU? chạy Ollama CPU). Phase 11 có thể kéo sớm song song 7-10 (Prometheus cần cho 9/10).

## Success Criteria (top-level)
- Findings red-team được user adjudicate 100%; 8/8 hình card-style pass vision checklist.
- Từ lab sạch: cài k3s theo guide + `clusters/k3s/bootstrap.sh` (2 input: GITHUB_PAT + sealed-key backup) → ArgoCD + face-detect serve request; CI round-trip < 10 phút.
- Root README + README con mỗi thư mục cấp 1; mỗi phase xong có README mục đó.
- Mọi deploy qua ArgoCD; `kubectl get applications -n argocd` xanh sau mỗi phase.

## Validation Log

### Session 1 (260611, 6 câu — mode prompt)
| # | Topic | Decision |
|---|---|---|
| 1 | Registry | **GHCR** (GITHUB_TOKEN, image public cho kind pull) |
| 2 | RAM local | **~40GB** → OpenMetadata/ELK bật được có kiểm soát |
| 3 | `monitoring/` vendored charts (plan ghi sai "rỗng") | Trích values hữu ích → **xoá**, dùng upstream qua ArgoCD |
| 4 | Kubeflow | **FULL Kubeflow** (user reversal so với default KFP-standalone); fallback KFP-standalone nếu kẹt >2 ngày |
| 5 | Secrets local | Sealed-secrets, migrate Vault ở vòng harden |
| 6 | Git flow | Branch mới + PR vào **main**; mỗi phase 1 branch/PR; ArgoCD + CI track main |

### Verification Results
- Claims checked: 15 path claims + credential scan
- Verified: 15 | Failed: 0 (1 sai lệch nội dung: monitoring/ không rỗng → đã adjudicate ở câu 3)
- Tracked sensitive files: chỉ template chart vendored + 2 gif — không có credential thật

### Red-team adjudication (260611 — phase 1 DONE)
Gói A (23 fix) áp toàn bộ; B1 **k3s lab 7+ server thay kind**; B2 KF-minus-serving + Istio-by-KF; B3 KServe-native canary; B4 giữ Iter8 shadow-only; B5 bootstrap 2-input + seed-data; B6 trigger rule; B7 Langfuse v3+ClickHouse; B8 resolved-by-B1. Chi tiết: `reports/from-red-team-to-user-architecture-findings-adjudication-report.md`. Diagrams: không cần sửa nội dung → Phase 2 completed.
