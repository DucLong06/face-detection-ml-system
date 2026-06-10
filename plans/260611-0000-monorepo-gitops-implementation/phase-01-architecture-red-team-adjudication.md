---
phase: 1
title: "Architecture red-team + user adjudication"
status: completed
priority: P1
effort: "3h"
dependencies: []
---

# Phase 1: Architecture Red-Team + User Adjudication

## Overview
Reviewers đối kháng soát toàn bộ thiết kế (master plan + 8 sơ đồ + implementation-steps) TRƯỚC khi xây. Output = findings report; user duyệt từng finding (apply / reject / defer) — không tự sửa thiết kế đã chốt.

## Requirements
- Functional: report findings phân loại severity + khuyến nghị cụ thể; bảng adjudication để user tick.
- Non-functional: mỗi finding phải trace tới failure mode thật (rule `review-audit-self-decision.md` §2), không YAGNI-drift các quyết định user đã chốt (§3).

## Attack Surfaces (mỗi reviewer 1 lens)
1. **CPU-first feasibility**: từng tool trong 7 domain chạy nổi trên kind 1 máy? Lưu ý: **full Kubeflow đã được user CHỐT** (validation 260611, có fallback >2 ngày) — red-team chỉ soát execution risk của nó, không đề xuất reverse. <!-- Updated: Validation Session 1 --> Soát luôn: Istio ambient trên kind, Strimzi + Flink + Spark đồng thời (RAM budget), OpenMetadata (nặng), Thanos (cần object store → MinIO).
2. **Thứ tự dựng & dependency ngầm**: sync-wave T0→T6 có vòng phụ thuộc nào? (vd KServe cần cert-manager + Knative; Feast cần Redis từ T1; Thanos cần MinIO từ T1 nhưng nằm T6).
3. **SPOF + tool chồng chéo**: 2 GE instance? Airflow vs Argo Events vs KFP trigger trùng vai? Iter8 + Flagger cùng canary? Typesense + Qdrant đều cần?
4. **GitOps/secret flow**: bot bump tag race; secrets khi chưa có Vault (phase 6 defer) — SOPS/sealed-secrets tạm?

## Inputs (reviewers đọc)
`plans/260604-2213-.../plan.md`, `newplans/implementation-steps.md`, `newplans/phase-t0..t6-*.md`, `newplans/README.md`, 8 PNG sơ đồ, brainstorm report 260611.

## Implementation Steps
1. Spawn 2-3 reviewer subagents theo lens trên (advisory, không sửa file).
2. Tổng hợp findings → `plans/reports/from-red-team-to-user-architecture-findings-adjudication-report.md`: bảng [ID | finding | severity | đề xuất | quyết định user: ___].
3. AskUserQuestion theo nhóm finding CRITICAL/MAJOR → ghi quyết định vào bảng.
4. Findings được APPLY → liệt kê file/diagram/phase bị ảnh hưởng (input cho phase 2 + chỉnh phase 6-12 nếu cần).

## Success Criteria
- [ ] Report findings với 100% mục được user adjudicate
- [ ] Danh sách thay đổi áp vào hình (phase 2) + plan (phase 6-12) rõ ràng
- [ ] Không finding nào tự ý reverse quyết định user đã chốt

## Risk Assessment
- Reviewer over-flag theo lý thuyết → bắt buộc trace failure mode thật trước khi đưa vào bảng.
