# Day-by-Day Setup Schedule — face-detect MLOps (self-build, CPU-first)

> Bạn làm tay từng ngày (~1 đơn vị/ngày, max delay 1 ngày), báo kết quả → tôi viết guide JIT cho ngày kế.
> Mỗi ngày: **mục tiêu · tool · phụ thuộc · độc lập? · nhóm RAM · ✅ test case · ⏪ rollback**.
> Quy tắc RAM (xem `op1-resource-node-onoff.png`): ALWAYS-ON + **tối đa 1 nhóm ON-DEMAND**. Tắt nhóm cũ trước khi bật nhóm mới.
> Trạng thái xuất phát: Phase 1 (red-team) + Phase 2 (diagrams) = DONE. Bắt đầu từ Day 1 = Phase 3.

---

## 0. Bản đồ phụ thuộc (đọc trước — cái nào riêng biệt, cái nào nối)

> Sơ đồ màu: `newplans/diagrams/ops/op4-day-dependency-roadmap.png` (🟢 độc lập · 🔴 critical path · 🟡 gần độc lập · 🟣 milestone).

```
        ┌─ D1 restructure ─ D2 CI(GHA+Trivy+cosign) ─┐
        │                                            ├─ D4 ArgoCD+L1 GitOps ★ ─ D5 platform ─ D6 governance+VPN ─ D7 SSO ─┐
        └─ D3 k3s cluster (ĐỘC LẬP) ─────────────────┘                                                                   │
                                                                                                                          ▼
   D15 Observability (gần độc lập, kéo sớm được) ◀───────────────┐                          D8-9 Data pipeline ◀──────────┘
                                                                  │                                  │
   D16-17 RAG (ĐỘC LẬP sau D7) ◀──────────────────────────────────┤                          D10-11 ML train (TRAIN) ─ D12 Serving ─ D13-14 Drift loop ★
                                                                  │                                                              │
   D18 Streaming/CDC ext (DATA-HEAVY, làm cuối) ◀─────────────────┴──────────────────────────────────────────────────────────┘
```

**3 nhánh ĐỘC LẬP (làm xen kẽ tùy mood, không chặn nhau):**
- **A. Cluster nền** (D3) — cài k3s bất cứ lúc nào, không cần CI xong.
- **B. RAG** (D16-17) — chỉ cần platform+SSO (D7), khác domain hẳn, có thể nhảy lên làm sớm nếu chán train.
- **C. Observability** (D15) — Prometheus cần cho serving/drift nên nên kéo SỚM (làm ngay sau D6 cũng được).

**Chuỗi BẮT BUỘC nối tiếp (critical path — không đảo):**
`D1 → D2 → D4 → D5 → D6 → D7 → D8-9(data) → D10-11(train) → D12(serving) → D13-14(drift ★)`

---

## 1. Master table

| Day | Phase | Mục tiêu | Tool chính | Phụ thuộc | Độc lập? | Nhóm RAM | ✅ Test "xong" |
|---|---|---|---|---|---|---|---|
| **D1** | 3 | Monorepo restructure + README skeleton | git, tree | — | 🟢 độc lập | ~0 (local) | tree đúng · `docker build apps/face-detect` pass · push branch |
| **D2** | 4 | CI: pytest+Trivy+build+cosign+push GHCR | GitHub Actions, Trivy, cosign | D1 | 🟢 (chỉ cần code) | ~0 (cloud) | push → workflow xanh · image **signed** trên GHCR · Trivy report |
| **D3** | 5a | Cài k3s lab multi-node | k3s | — | 🟢 **độc lập** | ALWAYS-ON nền | `kubectl get nodes` đủ node Ready · 1 control + n worker |
| **D4** | 5b | ArgoCD bootstrap + app-of-apps + deploy L1 ★ | ArgoCD, Helm | D2+D3 | 🔴 nối | ALWAYS-ON | `argocd app` Healthy · `curl /detect` ra bbox · **L1 chạy GitOps** |
| **D5** | 6a | Mesh + TLS + secrets nền | Istio ambient, cert-manager, sealed-secrets | D4 | 🔴 nối | ALWAYS-ON | mTLS STRICT bật · sealed-secret round-trip · cert issued |
| **D6** | 6b | Governance + VPN admin (F4/F6) | Kyverno, etcd-encryption, Tailscale | D5 | 🔴 nối | ALWAYS-ON | policy chặn pod thiếu label/quota · admin UI **chỉ** qua Tailscale · etcd enc on |
| **D7** | 6c | SSO (F3) | Keycloak, OAuth2-Proxy | D5 | 🟡 (song song D6) | ALWAYS-ON | login 1 lần vào ArgoCD UI · redirect_uri exact · admin console không public |
| **D8** | 7a | Data: lưu trữ + version | MinIO, lakeFS+Iceberg, Postgres, Redis | D6 | 🔴 nối | **DATA-HEAVY** | MinIO up · lakeFS commit/branch · bucket Bronze |
| **D9** | 7b | Data: medallion + quality | Spark (Bronze→Silver→Gold), Great Expectations | D8 | 🔴 nối | DATA-HEAVY | query Iceberg Gold ra rows · GE 2 gate pass |
| **D10** | 8a | ML: tracking + pipeline | MLflow, Kubeflow FULL | D9 + **tắt DATA-HEAVY** | 🔴 nối | **TRAIN** | MLflow UI · Kubeflow pipeline chạy 1 step |
| **D11** | 8b | Train YOLOv11 → ONNX | Kubeflow, (Ray), ONNX export, Feast | D10 | 🔴 nối | TRAIN | model versioned MLflow + file ONNX · Feast offline/online |
| **D12** | 9 | Serving nâng cấp (F2) | KServe+Knative, Triton-ONNX, KEDA, Flagger | D11 + D4 | 🔴 nối | ALWAYS-ON+ | InferenceService Ready · canary shift · AuthZ+rate-limit chặn |
| **D13** | 10a | Drift detect + alert | Prometheus, Grafana, Evidently, Alibi | D12 | 🔴 nối | ALWAYS-ON | drift_score lên Prometheus · Grafana dashboard · alert fire |
| **D14** | 10b | Đóng vòng lặp retrain ★ | Alertmanager→Argo Events→retrain→canary→approve | D13+D11 | 🔴 nối | TRAIN (burst) | inject drift → alert <5min → retrain auto → canary → **bạn approve** → promote |
| **D15** | 11 | Observability đầy đủ | ELK/Loki, Jaeger+OTel | D6 (kéo sớm được) | 🟡 gần độc lập | ALWAYS-ON | logs+traces tập trung · 1 SSO cookie mọi UI |
| **D16** | 12a | RAG hạ tầng | Ollama, Qdrant, Typesense | D7 + **tắt TRAIN/DATA** | 🟢 **độc lập** | **RAG** | Ollama trả lời · Qdrant collection · embed index |
| **D17** | 12b | RAG orchestrate + guard | RAGFlow, NeMo Guardrails, Langfuse | D16 | 🟢 độc lập | RAG | hỏi-đáp metadata · guardrails chặn jailbreak · Langfuse trace |
| **D18** | 7-ext | Streaming + CDC + catalog | Kafka(Strimzi), Debezium, Flink, Trino, OpenMetadata | D9 + **tắt nhóm khác** | 🟡 làm cuối | DATA-HEAVY | CDC→Kafka→Flink validate · Trino SQL · OpenMetadata lineage |

**Tổng:** 18 ngày làm việc + buffer. Với "max delay 1 ngày/đơn vị" → lịch thực tế **~3.5–4 tuần**. Mốc ăn điểm: **D4** (L1 GitOps) và **D14** (drift loop ★).

---

## 2. Chi tiết + test case từng ngày

> Mỗi ngày tôi sẽ viết guide JIT (lệnh + expected output + troubleshoot) TRƯỚC khi bạn làm. Dưới là khung test "Definition of Done" để bạn tự check.

### D1 — Monorepo restructure (🟢 độc lập)
- **Làm:** chuyển `api/`→`apps/face-detect/`, tạo `charts/ gitops/ clusters/ pipelines/ docs/`, README skeleton.
- **✅ Test:** `tree -L 2` khớp target tree · `cd apps/face-detect && docker build .` OK · `pytest` cũ vẫn pass · commit + push branch, không lộ secret (`git secrets`/grep).
- **⏪ Rollback:** branch riêng, chưa merge main → `git checkout main`.

### D2 — CI GitHub Actions (🟢, cần D1)
- **Làm:** `.github/workflows/app-ci.yaml`: checkout→pytest→Trivy scan→docker build→**cosign sign**→push GHCR→bot bump tag (path-filter + `[skip ci]`).
- **✅ Test:** push commit `apps/**` → Actions xanh · `cosign verify ghcr.io/<you>/face-detect@sha` OK · Trivy không CRITICAL chưa fix · bump tag commit có `[skip ci]` (không loop).
- **⏪ Rollback:** Jenkins cũ vẫn còn tới khi GHA xanh ổn định mới gỡ.

### D3 — k3s cluster (🟢 ĐỘC LẬP — làm bất cứ lúc nào)
- **Làm:** cài k3s control trên 1 node nhỏ ổn định (KHÔNG phải máy dev 40GB), join 4-5 worker. Máy dev 40GB join dạng worker, **cordon sẵn** (chỉ uncordon khi train).
- **✅ Test:** `kubectl get nodes` tất cả Ready · node dev có taint/cordon · `kubectl run test --image=nginx` chạy.
- **⏪ Rollback:** `k3s-uninstall.sh` sạch.

### D4 — ArgoCD + L1 GitOps ★ (🔴 cần D2+D3)
- **Làm:** `clusters/k3s/bootstrap.sh` (2 input: GITHUB_PAT + sealed-key) cài ArgoCD + root app-of-apps trỏ `gitops/` → tự kéo face-detect.
- **✅ Test:** `kubectl get applications -n argocd` Healthy/Synced · `curl http://face.<lab>/detect` ra bbox · đổi 1 dòng values → push → ArgoCD tự sync < 3min.
- **⏪ Rollback:** `argocd app delete` + namespace; image vẫn trên GHCR.

### D5 — Platform nền: mesh+TLS+secrets (🔴 cần D4)
- **Làm:** Istio ambient, cert-manager (self-signed/lab CA), sealed-secrets controller.
- **✅ Test:** `istioctl x ztunnel-config` thấy workload · PeerAuthentication STRICT · seal 1 secret → commit → unseal đúng trong cluster · cert Ready.
- **⏪ Rollback:** ArgoCD app disable từng cái.

### D6 — Governance + VPN admin (🔴 cần D5 · F4/F6)
- **Làm:** Kyverno ClusterPolicy (default-deny NetworkPolicy, mTLS STRICT, ResourceQuota, labels bắt buộc); bật etcd encryption-at-rest; Tailscale subnet-router cho admin UI.
- **✅ Test:** tạo pod thiếu label/quota → **bị Kyverno từ chối** · ArgoCD/Grafana UI **không** truy cập được từ ngoài, **chỉ** qua Tailscale · `kubectl get secret -o yaml` trong etcd đã mã hóa.
- **⏪ Rollback:** policy ở mode `Audit` trước, `Enforce` sau khi xanh.

### D7 — SSO Keycloak (🟡 song song D6 · F3)
- **Làm:** Keycloak + OAuth2-Proxy, 6 realm role, redirect_uri **exact** (cấm wildcard), brute-force on, admin console nội bộ.
- **✅ Test:** login 1 lần → vào ArgoCD UI qua OIDC · thử redirect_uri lạ → bị từ chối · admin console Keycloak không mở ra public.
- **⏪ Rollback:** giữ ArgoCD local admin tới khi SSO xanh.

### D8-9 — Data pipeline (🔴 cần D6 · DATA-HEAVY)
- **Làm D8:** MinIO + lakeFS(Iceberg REST catalog) + Postgres + Redis. **D9:** Spark medallion Bronze→Silver→Gold + GE 2 gate.
- **✅ Test:** `lakefs branch` tạo+commit · Trino/Spark query Iceberg Gold ra rows · GE report 2 gate pass · drop data bẩn → GE fail đúng.
- **⏪ Rollback:** Velero snapshot trước; ArgoCD disable nhóm data.
- **⚠️ RAM:** đây là nhóm nặng — đảm bảo chưa bật TRAIN/RAG.

### D10-11 — ML platform + train (🔴 cần D9 · TRAIN — TẮT DATA-HEAVY trước)
- **Làm:** MLflow + Kubeflow FULL; pipeline load Gold→train YOLOv11→eval→register MLflow→export ONNX; Feast.
- **✅ Test:** Kubeflow pipeline DAG chạy hết · model + metrics trong MLflow · file `.onnx` tồn tại · Feast lấy feature online (Redis) khớp offline.
- **⚠️ RAM:** `kubectl cordon` các node nhỏ giữ ALWAYS-ON, `uncordon` node dev 40GB cho train job; xong **tắt Kubeflow** để nhường D12.
- **⏪ Rollback:** fallback KFP-standalone nếu Kubeflow full kẹt >2 ngày (đã chốt).

### D12 — Serving nâng cấp (🔴 cần D11+D4 · F2)
- **Làm:** KServe+Knative, InferenceService Triton-ONNX-CPU, KEDA, Flagger; AuthorizationPolicy allow-list + OIDC + rate-limit.
- **✅ Test:** InferenceService Ready, infer ra bbox · Flagger canary 5%→100% chạy · gọi không token → **401** · flood → rate-limit chặn · KEDA scale theo load.
- **⏪ Rollback:** giữ FastAPI L1 song song; canary auto-rollback nếu lỗi.

### D13-14 — Drift loop ★ (🔴 cần D12+D11)
- **Làm D13:** kube-prometheus-stack + Evidently CronJob (drift_score) + Alibi. **D14:** Alertmanager→webhook→Argo Events→retrain pipeline (D11)→MLflow Staging→KServe canary→**human approve**→promote/rollback.
- **✅ Test (kịch bản đầy đủ):** inject chunk data drift → Evidently drift_score vượt ngưỡng → Prometheus alert <5min → Argo Events trigger retrain → model mới Staging → canary 5% → **bạn bấm approve** → promote 100% / hoặc reject → rollback. **Đây là phần ăn điểm.**
- **⚠️ RAM:** retrain bật TRAIN tạm thời (burst node dev), xong tắt.
- **⏪ Rollback:** approval gate = bạn kiểm soát; reject → giữ model cũ.

### D15 — Observability (🟡 gần độc lập — nên kéo sớm sau D6)
- **Làm:** ELK (hoặc Loki nếu RAM căng) + Jaeger + OTel Collector + Grafana dashboards (drift/serving).
- **✅ Test:** log app full-text search trong Kibana/Loki · trace request xuyên Istio trong Jaeger · 1 SSO cookie vào mọi UI.
- **Note:** Prometheus thực ra cần từ D13 → phần metrics kéo sớm; ELK/Jaeger để D15.

### D16-17 — RAG (🟢 ĐỘC LẬP sau D7 · RAG — TẮT TRAIN/DATA trước)
- **Làm D16:** Ollama (Qwen2.5-0.5B/TinyLlama GGUF) + Qdrant + Typesense + embed. **D17:** RAGFlow + NeMo Guardrails + Langfuse.
- **✅ Test:** hỏi metadata → câu trả lời có dẫn nguồn · prompt jailbreak → guardrails chặn · Langfuse log trace+cost · hybrid search (vector+keyword) trả kết quả.
- **⏪ Rollback:** khác domain, disable cả nhóm rag không ảnh hưởng serving.

### D18 — Streaming/CDC extension (🟡 làm cuối · DATA-HEAVY)
- **Làm:** Kafka(Strimzi) + Schema Registry + Debezium(CDC) + Flink(validate) + Trino + OpenMetadata(catalog+lineage+RBAC).
- **✅ Test:** đổi row App DB → Debezium→Kafka→Flink validate→Iceberg · Trino federated query · OpenMetadata thấy column-lineage + RBAC theo SSO.
- **⚠️ RAM:** nặng nhất — chỉ bật khi tắt TRAIN/RAG; có thể để 1-broker.

---

## 3. Nguyên tắc vận hành hằng ngày
1. **Bắt đầu ngày:** `kubectl top nodes` kiểm RAM còn trống; xác định nhóm hôm nay, tắt nhóm on-demand không dùng.
2. **Mọi thay đổi qua git → ArgoCD**, không `kubectl apply` tay (trừ bootstrap D4).
3. **Xong phase:** chạy test case ở trên → nếu xanh, viết README mục đó + commit; báo tôi để viết guide ngày kế.
4. **Kẹt >0.5 ngày 1 bước:** báo tôi (log + lệnh đã chạy) → tôi debug, không tự loay hoay quá lâu.
5. **Trước nhóm DATA-HEAVY/TRAIN:** chạy Velero backup nhóm stateful.

## 4. Phần "kế hoạch" (planning effort — tôi làm)
- Trước mỗi ngày 🔴/🟡 nặng: tôi viết guide JIT (~0.5 ngày của tôi, không tính vào ngày của bạn) — bạn chỉ cần báo "xong D_n" là tôi ra guide D_(n+1).
- Guide D3/D4/D5 ưu tiên viết trước (critical path tới milestone ★ D4).
- Mỗi tuần: 1 lần review tiến độ + chỉnh lịch theo thực tế delay.

## 5. Resolved (khóa 260612) + còn 1 việc

**Hardware (đã rõ):** nhiều server **≤16GB/con** xin được + 1 máy **dev 40GB** (PC hiện tại). Allocation khóa:
| Vai trò | Máy | Ghi chú |
|---|---|---|
| Control-plane 24/7 | 1 server 16GB **dedicated** | k3s server + ArgoCD + Istio. KHÔNG dùng máy dev |
| ALWAYS-ON workers | 2-3 × 16GB | mesh/secrets/Prometheus-lite/serving L1 |
| ON-DEMAND workers | còn lại × 16GB | bật/tắt theo nhóm DATA/TRAIN/RAG |
| Fat-workload burst | **máy dev 40GB** | cordon sẵn; uncordon khi pod >14GB (Ray/Kubeflow/ES/train job) |

> Ràng buộc: node ≤16GB → 1 pod đơn KHÔNG xin nổi >~14GB trừ khi ép lên node dev 40GB (dùng nodeSelector/taint). Component nặng → pin lên node dev.

**Domain/DNS:** chưa có → **không blocker tới D12**. D1-D11 dùng `sslip.io`/`nip.io` (wildcard DNS free) + Tailscale MagicDNS cho admin. D12 mới mua 1 domain rẻ Cloudflare + cert-manager Let's Encrypt. Placeholder `*.face-detect.dev` thay bằng domain thật khi có.

**Tailscale:** VPN mesh (WireGuard) free, cho admin UI truy cập riêng tư không cần public IP — cài **D6**. Chưa có account → tạo free ở D6 (đăng nhập Google/GitHub).

**Còn 1 việc cần bạn:** chọn **ngày bắt đầu D1** (để gắn lịch thật). Bảng hiện dùng D1..D18 tương đối — bạn báo ngày start, tôi map ra ngày dương lịch.
