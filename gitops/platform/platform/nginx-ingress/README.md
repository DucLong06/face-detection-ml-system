# nginx-ingress (values-only)

KHÔNG vendor chart. ArgoCD/Helm kéo upstream lúc deploy.

- **Upstream chart:** `nginx-ingress` (repo `https://helm.nginx.com/stable`)
- **Pin version:** `1.4.0` (appVersion 3.7.0)
- **Override:** `values.yaml` (chỉ phần khác default)

> Wiring ArgoCD Application (repoURL + targetRevision 1.4.0 + valueFiles) làm ở phase 4/5.
> Update chart = đổi version pin, không đụng template.
