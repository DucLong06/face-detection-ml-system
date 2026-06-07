# T3 — Model Serving (L3, KServe + Triton GPU)

**Priority:** P1 · **Status:** pending · **Depends:** T2 · **Blocks:** T4 · **Sơ đồ:** `diagrams/icons/04-serving.png`

## Overview
Serving production-grade: KServe orchestration + Knative scale-to-zero + Triton/TensorRT (GPU) engine + KEDA autoscale + Flagger canary + Iter8 A/B.

## Namespace `model-serving` + Tools

| Tool | Vai trò |
|---|---|
| **KServe** | InferenceService CRD: routing, canary, autoscale, multi-framework |
| **Knative** | scale-to-zero, request-driven concurrency |
| **Triton + TensorRT** | inference engine GPU, dynamic batching, INT8, multi-model |
| **KEDA** | event-driven autoscale (request rate / Kafka lag) |
| **Flagger** | progressive canary 5→25→50→100%, auto-rollback |
| **Iter8** | A/B testing + SLO-based experiment |

## Design
- **KServe + Triton:** KServe lo orchestration, Triton lo engine (GPU, batching). Best practice.
- **Knative scale-to-zero:** model ít dùng → 0 pod, tiết kiệm GPU.
- **Online feature:** KServe pull feature từ Feast online (Redis) lúc inference.
- **Model pull:** từ MLflow registry (S3/Iceberg artifact).
- **Canary:** Flagger shift traffic theo metric (latency p95, error rate); Iter8 chạy experiment A/B có SLO.

## Build Steps
1. KServe + Knative + cert-manager (đã có) + KEDA.
2. Triton model repo trên MinIO/Iceberg (`models/onnx|tensorrt/yolov11`).
3. InferenceService (predictor: triton, GPU resources, canaryTrafficPercent).
4. Flagger Canary + metric templates; Iter8 experiment.
5. KEDA ScaledObject (Prometheus trigger).

## Success Criteria
- [ ] InferenceService Ready, infer GPU trả bbox; Triton batching ↑ throughput ~3×
- [ ] Knative scale-to-zero + scale-up đúng
- [ ] Flagger canary shift + auto-rollback; Iter8 ra quyết định A/B
- [ ] KServe pull online feature từ Feast

## Risks
- KServe↔Triton↔Knative version compat → pin + test.
- GPU contention với T2 (train) + T5 (vLLM) → MIG/time-slicing hoặc tách node pool.
