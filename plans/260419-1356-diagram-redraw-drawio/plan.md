---
status: pending
created: 2026-04-19
plan_id: 260419-1356-diagram-redraw-drawio
type: docs-refresh
priority: medium
owner: longhd
---

# Plan — Diagram Redraw với Draw.io (Option C from scratch)

## Goal
Redraw 11 architecture diagrams (`images/01-11_*.png`) bằng Draw.io để docs dễ đọc, consistent style, git-trackable. Match visual style `images/architecture.png` (MLOps L1 Lucidchart origin). Giữ `architecture.png` nguyên vẹn.

**Approach (updated 15:10)**: Claude generate `.drawio` XML files trực tiếp (zones + colors + arrows + labels + K8s/AWS built-in stencil icons where available, text-box placeholders cho tools ngoài). User import vào Draw.io → review → tinh chỉnh positioning + swap placeholder sang SVG logo official nếu muốn. Effort giảm từ 14–18h manual → **6–8h review+tweak**.

## Context
- Brainstorm: `plans/reports/brainstorm-260419-1340-diagram-redraw-drawio.md`
- Visual reference: `images/architecture.png`
- Source PNGs thay thế: `images/01_*.png` → `images/11_*.png`
- Docs cần update reference: `NEW_PLANS.md`, `README_EXTENDED.md`
- Tool: Draw.io via VSCode extension `hediet.vscode-drawio` hoặc desktop app
- Constraint: `.drawio` save với `Compressed: OFF`, commit cả `.drawio` + `.png` (1920px, scale 2x)

## Phases

| # | Phase | Status | Effort (gen-XML) | Output |
|---|---|---|---|---|
| 01 | [Setup template + style guide](./phase-01-setup-template-and-style-guide.md) | pending | ~30min (user 5min) | `docs/diagrams/README.md` + `_template.drawio` |
| 02 | [P0 diagrams (4)](./phase-02-p0-diagrams.md) | pending | ~2–3h (Claude gen + user review) | batch, serving, training, full-overview |
| 03 | [P1 diagrams (3)](./phase-03-p1-diagrams.md) | pending | ~1.5h | stream, cdc, drift |
| 04 | [P2 diagrams (4)](./phase-04-p2-diagrams.md) | pending | ~2h | rag, enhanced-rag, sso, llm-security |
| 05 | [Docs integration + archive](./phase-05-docs-integration-archive.md) | pending | ~1h | updated refs, PNG archived |
| 06 | [Optional CI auto-render](./phase-06-optional-ci-auto-render.md) | optional | ~2h | GitHub Action drawio→png |

**Total (gen-XML)**: 6–8h core + 2h optional. Chia 2–3 sessions.

## Key Dependencies
- Phase 01 blocks Phase 02/03/04 (template required).
- Phase 02/03/04 parallel-safe (different files, no conflict).
- Phase 05 blocked until Phase 02 minimum done (need ≥4 PNG exports to update docs).
- Phase 06 optional, independent.

## Decision Defaults (locked)
- **Generation approach**: Claude gen `.drawio` XML, user import + tweak. KHÔNG manual draw from scratch.
- **Icons**: built-in Draw.io K8s/AWS/Cloud shape library stencils khi có → fallback text-box placeholder. Real SVG logos là Phase 2 optional (user swap manually nếu muốn polish).
- **PNG cũ (`images/01-11_*.png`)**: move sang `images/archive/` (không xoá — giữ audit trail).
- **`architecture.png`**: KHÔNG đụng tới.
- **Style uniformity**: tất cả 11 diagrams dùng chung palette (yellow/blue zones), không accent color riêng per topic.
- **Diagram 01 (full-system)**: 1 ảnh duy nhất, layout scale to canvas 2560×1440 nếu cần. Không tách layered view (giữ compact giống `architecture.png` L1).

## Success Criteria
- [ ] 11 cặp `.drawio` + `.png` commit trong `docs/diagrams/`
- [ ] `_template.drawio` + `README.md` style guide tồn tại
- [ ] `NEW_PLANS.md` + `README_EXTENDED.md` tất cả reference trỏ `docs/diagrams/*.png`
- [ ] `images/01-11_*.png` moved to `images/archive/`
- [ ] Side-by-side review: 11 diagrams mới consistent style với nhau + giống `architecture.png` L1
- [ ] PR review: đồng nghiệp hiểu flow chỉ nhìn diagram không cần đọc text

## Next Steps
Bắt đầu Phase 01 (setup). Xong Phase 01 mới unblock các phase sau.
