# Namespace ResourceQuotas

Per-namespace resource caps for L1 hardening (Phase 03). Prevents single namespace exhausting cluster resources.

## Apply

```bash
# Label namespaces first (required for NetworkPolicy egress rules):
for ns in model-serving monitoring logging tracing; do
  kubectl label namespace "$ns" name="$ns" --overwrite
done

# Apply quotas:
kubectl apply -f infrastructure/k8s/quotas/

# Verify:
kubectl get resourcequota -A
kubectl describe resourcequota model-serving-quota -n model-serving
```

## Sizing rationale

| Namespace | CPU req | Mem req | Pods | Rationale |
|---|---|---|---|---|
| model-serving | 2 cores | 2 GiB | 10 | 1-3 FastAPI replicas (HPA) + KServe optional |
| monitoring | 3 cores | 4 GiB | 20 | Prom + Grafana + Evidently + AlertManager |
| logging | 3 cores | 6 GiB | 15 | Elasticsearch (memory-heavy) + Kibana + Filebeat DS |
| tracing | 1 core | 1 GiB | 5 | Jaeger (10% sampling, low footprint) |

For additional namespaces (data-platform, ml-platform, auth-ns, istio-system), add similar files when those workloads deploy.

## Out of Scope (Phase 03)

- External Secrets Operator setup (requires GCP Workload Identity, deferred)
- LimitRange (per-pod defaults) — add when seeing under-specified pod requests
- PriorityClass — when multi-tenant scheduling becomes concern
