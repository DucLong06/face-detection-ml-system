---
phase: 05
title: Docs integration + archive
status: pending
priority: P1
effort: ~1h
blockedBy: [02, 03, 04]
---

# Phase 05 — Docs Integration + Archive

## Context Links
- Plan: [../plan.md](./plan.md)
- Previous phases: 02, 03, 04 (all 11 diagrams done)
- Files to update: `NEW_PLANS.md`, `README_EXTENDED.md`
- Files to archive: `images/01_*.png` → `images/11_*.png`

## Overview
- **Priority**: P1
- **Status**: pending (blocked until all 11 diagrams done)
- **Description**: Update markdown references sang diagrams mới, archive PNG cũ.

## Key Insights
- `architecture.png` L1 **giữ nguyên**, không archive.
- `data_pipeline_architecture.png`, `full_system_architecture.png`, `serving_rag_architecture.png`, `data_engineering_pipeline.html` trong `images/` là artifacts cũ — cân nhắc archive hoặc xoá (user decide).

## Requirements

### Functional
- Mọi reference `![](images/01_*.png)` trong `NEW_PLANS.md` + `README_EXTENDED.md` → đổi sang `![](docs/diagrams/XX-slug.png)`.
- `images/01-11_*.png` moved to `images/archive/`.
- Git history preserved (dùng `git mv`, không `rm + add`).

### Non-Functional
- Markdown render đúng trên GitHub sau update (verify via preview hoặc `grip`).
- Broken link check pass.

## Related Code Files

**Modify**:
- `NEW_PLANS.md` — section 10 + inline references
- `README_EXTENDED.md` — architecture sections

**Move**:
- `images/01_full_system_overview.png` → `images/archive/`
- `images/02_batch_data_flow.png` → `images/archive/`
- `images/03_stream_data_flow.png` → `images/archive/`
- `images/04_cdc_data_flow.png` → `images/archive/`
- `images/05_ml_training_pipeline.png` → `images/archive/`
- `images/06_model_serving.png` → `images/archive/`
- `images/07_rag_pipeline.png` → `images/archive/`
- `images/08_sso_security_flow.png` → `images/archive/`
- `images/09_drift_detection.png` → `images/archive/`
- `images/10_llm_security_architecture.png` → `images/archive/`
- `images/11_enhanced_rag_pipeline.png` → `images/archive/`

**Keep untouched**:
- `images/architecture.png` (MLOps L1 reference, in `README.md`)

## Implementation Steps

### 1. Find all references (~5 phút)
```bash
grep -rn "images/0[1-9]_\|images/1[01]_" NEW_PLANS.md README_EXTENDED.md
```
List all matches.

### 2. Replace references (~15 phút)
Mapping:
| Old | New |
|---|---|
| `images/01_full_system_overview.png` | `docs/diagrams/01-full-system-overview.png` |
| `images/02_batch_data_flow.png` | `docs/diagrams/02-batch-data-flow.png` |
| `images/03_stream_data_flow.png` | `docs/diagrams/03-stream-data-flow.png` |
| `images/04_cdc_data_flow.png` | `docs/diagrams/04-cdc-data-flow.png` |
| `images/05_ml_training_pipeline.png` | `docs/diagrams/05-ml-training-pipeline.png` |
| `images/06_model_serving.png` | `docs/diagrams/06-model-serving.png` |
| `images/07_rag_pipeline.png` | `docs/diagrams/07-rag-pipeline.png` |
| `images/08_sso_security_flow.png` | `docs/diagrams/08-sso-security-flow.png` |
| `images/09_drift_detection.png` | `docs/diagrams/09-drift-detection.png` |
| `images/10_llm_security_architecture.png` | `docs/diagrams/10-llm-security-architecture.png` |
| `images/11_enhanced_rag_pipeline.png` | `docs/diagrams/11-enhanced-rag-pipeline.png` |

Dùng `sed` hoặc VSCode find-replace across files.

### 3. Add `.drawio` source link trong captions (~10 phút)
Mẫu: `![01 Full System Overview](docs/diagrams/01-full-system-overview.png)  \n_Source: [`01-full-system-overview.drawio`](docs/diagrams/01-full-system-overview.drawio)_`

### 4. Archive PNG cũ (~5 phút)
```bash
mkdir -p images/archive
git mv images/0{1..9}_*.png images/11_*.png images/10_*.png images/archive/
```
(adjust glob cho shell)

### 5. Verify (~10 phút)
- Preview `NEW_PLANS.md` + `README_EXTENDED.md` trong GitHub (push to branch) hoặc local `grip`.
- Check no broken image links.
- Check no remaining `images/01-11_*.png` references.

### 6. Commit
```bash
git add NEW_PLANS.md README_EXTENDED.md docs/diagrams/ images/archive/
git commit -m "docs: migrate architecture diagrams to docs/diagrams, archive old PNGs"
```

## Todo List

- [ ] Grep all old PNG references
- [ ] Find-replace 11 mappings across `NEW_PLANS.md` + `README_EXTENDED.md`
- [ ] Add `.drawio` source link trong captions
- [ ] `git mv` 11 PNGs to `images/archive/`
- [ ] Verify render trên GitHub preview
- [ ] Verify no broken links (manual click all diagrams)
- [ ] Git commit

## Success Criteria
- [ ] `grep -c "images/0[1-9]_\|images/1[01]_" NEW_PLANS.md README_EXTENDED.md` = 0 (no old refs)
- [ ] 11 PNGs visible trong `images/archive/`
- [ ] GitHub preview render đúng 11 diagrams tại vị trí mới
- [ ] `images/architecture.png` vẫn link đúng trong `README.md`

## Risk Assessment

| Risk | Mitigation |
|---|---|
| Missed reference (ví dụ trong HTML files `architecture_design.html`) | Grep wider: `grep -rn "images/0[1-9]_\|images/1[01]_" . --include="*.md" --include="*.html"` |
| Git blame lost khi `git mv` | `git log --follow` vẫn trace được; chấp nhận trade-off |
| Caption text không update | Spot-check 3 captions random |

## Security Considerations
N/A.

## Next Steps
→ Phase 06 (optional CI auto-render) hoặc kết thúc plan.
