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
- **Review 260612 (CI/CD + security red-team + RAM reality-check):** [`../reports/brainstorm-review-260612-1453-cicd-security-redteam-plan-review-report.md`](../reports/brainstorm-review-260612-1453-cicd-security-redteam-plan-review-report.md) → nguồn của Validation Session 2 + 2 section "Resource Budget" & "Security Baseline" dưới.
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

## Day-by-Day Schedule (260612)
**Lịch setup theo ngày + test case + độc lập/phụ thuộc:** [`day-by-day-setup-schedule.md`](day-by-day-setup-schedule.md) (18 ngày làm việc, ~3.5-4 tuần; milestone D4 L1-GitOps + D14 drift loop ★). Sơ đồ roadmap: `newplans/diagrams/ops/op4-day-dependency-roadmap.png`.

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

### Session 2 (260612 — CI/CD + security red-team + RAM reality-check)
| # | Topic | Decision |
|---|---|---|
| 1 | CI runner | **GitHub-hosted runner** (repo public → free), KHÔNG self-hosted, KHÔNG GitLab-local. CI build nhẹ; "nhiều server" để cho cluster workloads, không phải CI. |
| 2 | Repo layout | **GIỮ monorepo** (override khuyến nghị tách config-repo). Chống loop CI↔commit = **path-filter + `[skip ci]`** trên commit bump-tag; an toàn fork-PR = **require-approval cho outside collaborator + KHÔNG secret ở PR-triggered workflow**. |
| 3 | Hardware (reconcile frontmatter) | Thực: **1 node 40GB/12core = máy DEV (intermittent, KHÔNG control-plane)** + **4-5 node 8-16GB** always-on. Always-on usable ~32-80GB; 40GB chỉ dùng burst (train). |
| 4 | Kubeflow FULL | **GIỮ** (user re-confirm) — chỉ chạy khi tắt nhóm on-demand khác (xem Resource Budget). |
| 5 | Stack scope | **Giữ full-design**, dựng từng phần **tắt-bật** theo RAM-budget. |
| 6 | Supply-chain (repo public) | CI thêm **Trivy scan + cosign sign**; ArgoCD/Kyverno **verify signature** trước deploy. |
| 7 | Bitnami charts | Verify nguồn/tag trước install — **Bitnami Secure Images 2025** đã deprecate nhiều `docker.io/bitnami/*` → có thể vỡ. Fallback: chart upstream chính chủ. |
| 8 | Backup/DR | Thêm **Velero + volume snapshot** cho MinIO/Postgres/lakeFS/ES (homelab hỏng ổ = mất data). |

## Resource Budget & On/Off Schedule (260612 — first-class)
> Sơ đồ: `newplans/diagrams/ops/op1-resource-node-onoff.png` (node topology + 4 nhóm on/off).
> Full 50-tool cần 200GB+; hardware ~80-120GB heterogeneous (40GB là dev-box burst). **Quy tắc vàng: ALWAYS-ON + tối đa 1 nhóm ON-DEMAND tại một thời điểm. KHÔNG bao giờ TRAIN + DATA-HEAVY + RAG cùng lúc.**

| Nhóm | Thành phần | RAM ~ | Khi nào bật |
|---|---|---|---|
| **ALWAYS-ON (24/7)** | k3s control + ArgoCD + Istio ambient + cert-manager + Kyverno + sealed-secrets + Keycloak + OAuth2-Proxy + Prometheus/Grafana-lite (Loki) + app serving (FastAPI/Triton-ONNX-CPU) + KServe/Knative control | **~12-20GB** | luôn (chạy trên node nhỏ ổn định, KHÔNG trên 40GB dev) |
| **ON-DEMAND: TRAIN** | Kubeflow FULL / Ray / train job | **~16-30GB** | chỉ khi train → ưu tiên schedule lên **node 40GB (cordon/uncordon)**, tắt sau |
| **ON-DEMAND: DATA-HEAVY** | Kafka(1-broker)+Flink+Trino+OpenMetadata(+ES) | **~25-40GB** | chỉ khi làm data eng (Phase 7 phần nặng), tear-down sau |
| **ON-DEMAND: RAG** | Ollama + Qdrant + Typesense + RAGFlow + NeMo + Langfuse(+ClickHouse) | **~10-18GB** | chỉ khi demo RAG (Phase 12), tắt sau |
| **EPHEMERAL** | Spark/GE/Evidently CronJob, retrain job | burst | tự sinh-hủy theo job |

**Hệ quả per-phase:** P6-P11 build & verify **tuần tự, tắt nhóm trước khi bật nhóm sau**; P7 nặng (Kafka/Trino/OpenMetadata) chỉ bật khi demo data, không để chạy nền cùng TRAIN/RAG. Mỗi JIT-guide (phase 6-12) **phải mở đầu bằng "RAM cần + nhóm phải tắt trước"**.

## Security Baseline (front-loaded — KHÔNG để phase cuối)
> Sơ đồ: `newplans/diagrams/ops/op2-security-exposure-boundary.png` (zone public/private + gates) · `newplans/diagrams/ops/op3-cicd-gitops-roundtrip.png` (CI/CD supply-chain).
> Public ingress thật → bề mặt tấn công lớn. Các gate dưới phải có TỪ phase tương ứng, không bolt-on.

| Gate | Nội dung | Phase |
|---|---|---|
| **F1 admin UI không public** | CHỈ `serving` + `Keycloak` ra public ingress. ArgoCD/Kubeflow/Grafana/Kibana/MLflow/Airflow/OpenMetadata → sau **VPN/Tailscale** hoặc OAuth2-Proxy gate. ArgoCD pin **≥3.1.2** (CVE-2025-55190/23216/55191; token built-in không hết hạn → rotate/disable admin). | P5/P6 |
| **F2 KServe endpoint** | mặc định public-không-bảo-vệ → **AuthorizationPolicy allow-list + RequestAuthentication OIDC + mTLS STRICT + rate-limit**; KEDA cap max-replica (chống DoS nuốt RAM). | P9 |
| **F3 Keycloak** | redirect_uri khai báo **chính xác, cấm wildcard** (CVE-2026-3872 path-traversal bypass); admin console **không public**; bật brute-force detection; tách admin realm. | P6 |
| **F4 secret at-rest** | bật **etcd encryption-at-rest từ P5** (đừng đợi Vault ở vòng harden); sealed-secrets cho git. | P5 |
| **F6 governance trước workload** | Kyverno ClusterPolicy (NetworkPolicy default-deny + mTLS STRICT + quota + labels) áp **P6 — TRƯỚC** khi mở T1-T5. | P6 |
| **F7 model provenance** | chỉ load model **đã sign** từ registry nội bộ (MLflow/Triton pickle = RCE vector); không pull model ngoài tùy tiện. | P8/P9 |
| **F5 CI supply-chain** | Trivy scan + cosign sign image; require-approval fork-PR; không secret ở PR workflow (repo public). | P4 |
