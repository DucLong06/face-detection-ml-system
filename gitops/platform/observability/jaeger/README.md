# jaeger (values-only)

Không vendor chart. ArgoCD/Helm kéo upstream lúc deploy.

- **Upstream chart:** `jaeger`
- **Repo:** https://jaegertracing.github.io/helm-charts
- **Pin version:** `3.3.2`
- **Namespace:** `tracing`
- **Override:** `values.yaml`

> Update = đổi version pin. Application wiring (repoURL+targetRevision) ở phase 11 (D15).
