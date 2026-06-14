# kibana (values-only)

Không vendor chart. ArgoCD/Helm kéo upstream lúc deploy.

- **Upstream chart:** `kibana`
- **Repo:** https://helm.elastic.co
- **Pin version:** `8.5.1`
- **Namespace:** `logging`
- **Override:** `values.yaml`

> Update = đổi version pin. Application wiring (repoURL+targetRevision) ở phase 11 (D15).
