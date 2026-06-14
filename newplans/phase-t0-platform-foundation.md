# T0 — Platform Foundation

**Priority:** P0 (blocks all) · **Status:** pending · **Sơ đồ:** `diagrams/icons/07-platform-observability.png`, `08-namespace-topology.png`

## Overview
Nền tảng cluster: service mesh (mTLS), SSO/IdP, GitOps, policy-as-code, secrets, isolation. L1 hardening (probes/HPA/RBAC/NetworkPolicy/PDB/quota) đã làm → mở rộng cho ~20 namespace.

## Namespaces + Tools (best-of-breed)

| Namespace | Tool | Vai trò |
|---|---|---|
| `istio-system` | **Istio (ambient mode)** | mesh sidecar-less, mTLS STRICT, gateway (Gateway API), traffic policy |
| `auth` | **Keycloak** + **OAuth2 Proxy** | OIDC IdP, 6 realm roles, SSO `*.face-detect.dev` |
| `argocd` | **ArgoCD** | GitOps — deploy declarative toàn cluster từ Git |
| `kyverno` | **Kyverno** | policy-as-code — ép governance baseline mọi namespace |
| `vault` + `external-secrets` | **Vault + ESO** | secret tập trung, rotation, audit; sync vào K8s Secret |
| `cert-manager` | **cert-manager** | TLS cert tự động |

## Governance baseline (Kyverno ép cho MỌI namespace)
ResourceQuota + LimitRange · NetworkPolicy default-deny + allow-list · Istio PeerAuthentication mTLS STRICT · AuthorizationPolicy · scoped RBAC + ServiceAccount riêng (no cluster-admin) · PodDisruptionBudget (stateful) · labels `team/tier/cost-center/data-classification` · PriorityClass.

## Build Steps
1. Cluster + namespaces (20) + labels chuẩn.
2. Istio ambient (ztunnel + istiod) + Gateway API.
3. cert-manager + Vault + ESO.
4. ArgoCD (app-of-apps: mọi track deploy qua đây).
5. Kyverno policies (cluster policies ép baseline).
6. Keycloak realm + 6 roles + clients + OAuth2 Proxy.

## Success Criteria
- [ ] `kubectl get peerauthentication,networkpolicy,resourcequota -A` đủ entry mỗi namespace
- [ ] Kyverno block pod vi phạm baseline (test)
- [ ] ArgoCD sync xanh toàn bộ app
- [ ] SSO 1 cookie cho ≥2 UI; role giới hạn đúng

## Risks
- Istio ambient mode còn mới → fallback sidecar mode nếu cần.
- ArgoCD app-of-apps phức tạp → bắt đầu vài app, mở rộng dần.
