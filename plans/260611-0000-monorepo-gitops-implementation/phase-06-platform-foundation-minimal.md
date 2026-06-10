---
phase: 6
title: "T0 Platform foundation (minimal)"
status: pending
priority: P2
effort: "1d"
dependencies: [5]
---

# Phase 6: T0 Platform Foundation (Minimal trước, hoãn phần nặng)

## Overview
Nền tảng cluster mức đủ dùng cho T1-T4: cert-manager, Kyverno (+policy baseline), secrets tạm. **Hoãn có chủ đích**: Istio ambient, Vault+ESO, Keycloak SSO → bật ở vòng harden sau khi loop T4 chạy (đúng tinh thần implementation-steps "hoãn được"; red-team phase 1 có thể điều chỉnh).

## Tools & values (gitops/platform/platform/)
| Tool | Chart upstream | Ghi chú CPU |
|---|---|---|
| cert-manager | jetstack/cert-manager | crds.enabled=true; self-signed ClusterIssuer cho local |
| Kyverno | kyverno/kyverno | ClusterPolicy: require labels/requests-limits per ns, baseline PSS |
| secrets tạm | **sealed-secrets** (bitnami) | thay Vault giai đoạn local; secret → SealedSecret commit được vào git |

## Implementation Steps
1. Mỗi tool: thư mục `gitops/platform/platform/<tool>/{values-cpu.yaml,README.md}` + 1 Application trong `gitops/apps/` (sync-wave 1).
2. Kyverno policies để audit-mode trước, enforce sau 1 tuần chạy.
3. Sealed-secrets: seal registry-cred + (sau này) DB creds; doc quy trình seal trong README.
4. Cập nhật namespaces manifest: thêm ns các domain sắp tới (data-*, ml-platform...) kèm labels.
5. Root README bảng status: Platform = 🔄→✅ (minimal), ghi rõ mục hoãn.

## Success Criteria
- [ ] 3 Application Healthy; policy audit không fail app L1
- [ ] 1 SealedSecret round-trip (seal→commit→ArgoCD→pod đọc được)
- [ ] README platform domain ghi rõ minimal vs deferred

## Risk Assessment
- Kyverno enforce sớm chặn chart upstream → audit-mode trước.
- Quyết định hoãn Istio/Vault/Keycloak là thay đổi so với sơ đồ T0 đầy đủ → đã ghi rõ "deferred", sơ đồ giữ nguyên (kiến trúc đích), README đánh dấu trạng thái.

## Red-Team Adjudicated Updates (260611)
- O1: dòng "hoãn Istio" sửa thành "Istio đến cùng Kubeflow ở P8, istio-system do KF sở hữu" (+3-5GB vào budget P8).
- S1/O4: step BẮT BUỘC sau khi cài sealed-secrets: backup private key ra NGOÀI git (`kubectl get secret -n kube-system -l sealedsecrets.bitnami.com/sealed-secrets-key -o yaml > <outside>/sealed-key-backup.yaml`); backup lại sau mỗi rotation (30d); bootstrap restore key TRƯỚC controller.
- F11: thêm 3 PriorityClass (platform-critical/observability/workload) + ResourceQuota per-ns + requests=limits cho stateful JVM.
- F11b+S8+O11: Kyverno `failurePolicy: Ignore`; enforce theo SCOPE (chỉ ns tự viết chart) và chỉ SAU khi P10 xanh; PolicyException tracked git.
