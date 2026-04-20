---
title: "Consolidate 11 Diagrams into `full.drawio` + Apply Review Fixes"
description: "Build single multi-page `docs/diagrams/full.drawio` from 11 sources, apply all 9 🟠 review fixes, export PNG, delete originals."
status: pending
priority: P2
effort: 4h
branch: docs/diagrams-drawio-redraw
tags: [docs, diagrams, drawio, review-fix, consolidation]
created: 2026-04-20
---

# Consolidate Diagrams into `full.drawio` + Review Fixes

## Context

- Brainstorm: `/mnt/data/mlops/Long-project/face-detect-gke/plans/reports/brainstorm-260420-0957-diagrams-consolidate-full-drawio.md`
- Review v0.1: `/mnt/data/mlops/Long-project/face-detect-gke/newreview.md`
- README: `/mnt/data/mlops/Long-project/face-detect-gke/docs/diagrams/README.md`
- NEW_PLANS: `/mnt/data/mlops/Long-project/face-detect-gke/NEW_PLANS.md`
- Sources: `docs/diagrams/{01..11}-*.drawio` (11 files, single-page each, plain XML)

## Constraints (Agreed — do not reopen)

1. Single source of truth: `docs/diagrams/full.drawio` (11 pages, order 01→11).
2. Delete `01-*..11-*.drawio` AFTER `full.drawio` verified.
3. `_template.drawio` stays separate.
4. Unify `LangChain` → `RAGFlow` (pages 07 + 11; 01 title unchanged — already has `RAGFlow` node).
5. CDC page 04: cell id `app-ns` → `app-oltp-ns`; NEW_PLANS §7 add row.
6. SSO page 08: re-number steps to match NEW_PLANS §5.2 (9=set cookie, 10=redirect, 11=EnvoyFilter JWT, 12=forward).
7. README palette: add row `Actors zone | #F5F5F5 | #666666 | Neutral gray`.
8. Page 01: recolor `nginx-ns-2` → namespace orange (`#FFE6CC`/`#D79B00`); recolor `actors` zone → `#F5F5F5`/`#666666`.
9. Page 01: add 5–7 main-flow orthogonal edges with labels.
10. Page 05: 6 unlabeled edges → add labels. Page 10: 6 unlabeled edges → add labels.
11. PNG export via `drawio` CLI; rename to zero-padded `full-01.png`..`full-11.png`.
12. Single atomic commit: `docs(diagrams): consolidate into full.drawio + review fixes`.

## Phases

| # | File | Status | Effort | Summary |
|---|---|---|---|---|
| 01 | [phase-01-merge-xml-into-full-drawio.md](./phase-01-merge-xml-into-full-drawio.md) | pending | 45m | Build `full.drawio` from 11 sources via Python merge script; xmllint validate. |
| 02 | [phase-02-content-fixes-rag-ns-sso.md](./phase-02-content-fixes-rag-ns-sso.md) | pending | 30m | RAGFlow rename, app-ns→app-oltp-ns, SSO 12-step fix, NEW_PLANS §7 row. |
| 03 | [phase-03-palette-arrows-edge-labels.md](./phase-03-palette-arrows-edge-labels.md) | pending | 60m | Actors/nginx-ns-2 recolor, 5–7 new page-01 edges, label 6 edges on pages 05 + 10. |
| 04 | [phase-04-png-export-and-readme-update.md](./phase-04-png-export-and-readme-update.md) | pending | 30m | `drawio` CLI PNG export, zero-pad rename, README palette/naming/export sections. |
| 05 | [phase-05-verify-cleanup-commit.md](./phase-05-verify-cleanup-commit.md) | pending | 15m | xmllint + palette compliance; delete 11 originals; single atomic commit. |

## Key Dependencies

- Tool: `/usr/bin/drawio` v29.7.8 (verified working).
- Tool: `xmllint` (from `libxml2-utils`).
- Tool: `python3` (stdlib only — `xml.etree.ElementTree`).
- Env: `ELECTRON_DISABLE_GPU=1` safety flag for headless drawio.

## Acceptance (rollup of phase success criteria)

- [ ] `full.drawio` has 11 `<diagram>` pages, `xmllint --noout` passes.
- [ ] Palette compliance script passes with ALLOWED extended to include `#F5F5F5`.
- [ ] No residual `LangChain` references in pages 07/11 (grep).
- [ ] 11 PNG files `full-01.png`..`full-11.png` committed.
- [ ] 10 files `01-*..11-*.drawio` deleted.
- [ ] README updated (palette + file naming + export sections).
- [ ] NEW_PLANS §7 includes `app-oltp-ns` row.
- [ ] Single commit landed on `docs/diagrams-drawio-redraw`.

## Unresolved Questions

1. PNG naming: zero-pad `full-01.png` chosen (lexical sort) — default drawio CLI may output `full-1.png`; rename step required.
2. Istio mesh page 12: out of scope.
3. Page 09 drift-detection edges: not flagged in review v0.1, defer.
4. `_template.drawio` keep separate: confirmed, not merged.
