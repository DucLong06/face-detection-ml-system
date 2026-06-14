# kube-prometheus-stack (values-only)

Không vendor chart. ArgoCD/Helm kéo upstream lúc deploy.

- **Upstream chart:** `kube-prometheus-stack`
- **Repo:** https://prometheus-community.github.io/helm-charts
- **Pin version:** `67.4.0`
- **Namespace:** `monitoring`
- **Override:** `values.yaml`

> Update = đổi version pin. Application wiring (repoURL+targetRevision) ở phase 11 (D15).
