---
phase: 9
title: "T3 Serving"
status: pending
priority: P1
effort: "2d"
dependencies: [8]
---

# Phase 9: T3 Serving

## Overview
Nâng serving L1 (Deployment thường) lên KServe InferenceService: Knative scale-to-zero, model từ MinIO store (T2), Feast online features, KEDA scale, Flagger canary. Spec: `docs/architecture/phase-t3-serving.md`.

## Tools (gitops/platform/serving/) — sync-wave 6
| Tool | Ghi chú CPU |
|---|---|
| Knative serving | bắt buộc trước KServe |
| KServe | InferenceService runtime ONNX-CPU (Triton 🔵 chỉ đổi runtime khi GPU); storageUri = MinIO model store |
| KEDA | scale theo RPS/queue |
| Flagger | canary trên KServe service mesh-less (nginx provider local) |
| Iter8 | defer được — bật cùng vòng harden (red-team quyết) |

## Migration app
`charts/face-detect` (Deployment) → giữ làm "L1 mode"; thêm `gitops/apps/face-detect-isvc.yaml` (InferenceService manifest trong `gitops/platform/serving/face-detect/`). Chạy song song 1 thời gian rồi cắt ingress sang KServe; predictor load ONNX từ MinIO thay vì bake trong image → image app chỉ còn pre/post-process (transformer).

## Implementation Steps
1. Knative + KServe + cert-manager dependency check; KEDA, Flagger.
2. InferenceService values-cpu: ONNX runtime, transformer container từ image CI.
3. Wire Feast online (redis) vào transformer (feature enrich) — demo đơn giản 1 feature.
4. Flagger canary: đẩy model v2 (từ T2 run khác) → canary 10%→100% theo metric Prometheus (cần phase 11 tối thiểu: kube-prometheus-stack — kéo sớm nếu chưa có).
5. E2E: curl qua ingress → KServe trả bbox; scale-to-zero rồi cold-start OK; canary promote/rollback demo.
6. README serving domain.

## Success Criteria
- [ ] InferenceService Ready, serve đúng kết quả như L1
- [ ] Scale-to-zero + cold start < 60s CPU
- [ ] 1 canary promote + 1 rollback có chủ đích
- [ ] README serving viết xong

## Risk Assessment
- Flagger cần metrics → dependency chéo phase 11: cài kube-prometheus-stack TRƯỚC bước 4 (ghi rõ ở phase 11 note).
- KServe trên kind hay kẹt webhook/cert → cert-manager đã có (phase 6), follow KServe quickstart kind chính thức.

## Red-Team Adjudicated Updates (260611)
- B2: Knative+KServe cài standalone với **net-istio** (reuse Istio từ P8). Bỏ phương án Kourier/nginx route.
- B3: canary model = **KServe-native canaryTrafficPercent** trên ISVC; Flagger demo canary chỉ trên L1 Deployment (nginx provider) để học Flagger.
- B4: Iter8 GIỮ nhưng CHỈ offline/shadow SLO assessment — cấm traffic-shifting mode (Flagger độc quyền runtime traffic).
- O9: KEDA demo trên workload non-Knative (transformer/Kafka consumer); dependencies thêm: 11a phải xong trước step 4.
- F6: preload runtime image các node (k3s: registry pull OK, vẫn nên pre-pull), progress-deadline 600s; tiêu chí cold-start đo sau first-pull.
