---
phase: 01
title: Setup template + style guide (gen-XML approach)
status: pending
priority: P0
effort: ~30min (Claude) + ~5min (user palette extract)
blocks: [02, 03, 04]
---

# Phase 01 — Setup Template + Style Guide

## Context Links
- Plan: [../plan.md](./plan.md)
- Brainstorm: `plans/reports/brainstorm-260419-1340-diagram-redraw-drawio.md`
- Visual reference: `images/architecture.png`

## Overview
- **Priority**: P0 (blocks 02/03/04)
- **Status**: pending
- **Description**: User cung cấp palette hex từ PNG L1. Claude generate `_template.drawio` + `README.md` style guide dưới dạng XML.

## Key Insights
- Approach mới: Claude sinh XML directly, user không drag-drop.
- Palette là input DUY NHẤT user cần cung cấp — còn lại Claude tự ghi.
- Template `.drawio` sẽ dùng làm base khi Claude gen 11 diagrams sau.

## Requirements

### Functional
- User ship 7 hex values từ `architecture.png` (color picker).
- Claude gen `_template.drawio` với canvas 1920×1080, palette swatches, title block, footer, default styles.
- Claude gen `docs/diagrams/README.md` style guide.

### Non-Functional
- XML uncompressed, readable plain text (no base64).
- Template mở được trong Draw.io (web + desktop + VSCode extension).

## Architecture

```
docs/diagrams/
├── README.md             # Style guide (Claude generates)
└── _template.drawio      # Base XML (Claude generates)
```

## Related Code Files

**Create (by Claude)**:
- `docs/diagrams/README.md`
- `docs/diagrams/_template.drawio`

**User action**:
- Extract 7 hex from `images/architecture.png`

## Implementation Steps

### 1. User: extract palette (~5 phút)
Mở `images/architecture.png` trong:
- macOS Preview (Tools → Annotate → Shapes → Color picker) HOẶC
- Firefox DevTools (color picker built-in) HOẶC
- Online: https://imagecolorpicker.com/

Pick 7 colors → report lại trong chat:
1. Canvas background (likely white `#FFFFFF`)
2. CI/CD Pipeline zone fill (yellow-ish)
3. CI/CD Pipeline zone border (darker yellow)
4. GKE cluster zone fill (light blue)
5. GKE cluster zone border (darker blue)
6. Namespace inner zones fill (cream/orange-ish)
7. Arrow stroke (likely black `#000000`)

Format trả lời:
```
bg: #FFFFFF
cicd-fill: #FFF2CC
cicd-border: #D6B656
gke-fill: #DAE8FC
gke-border: #6C8EBF
ns-fill: #FFE6CC
arrow: #000000
```

### 2. Claude: generate files (~30 phút)
- Viết `_template.drawio` XML với mxGraphModel root, palette swatches, title/footer cells, shape library metadata.
- Viết `README.md`: style guide bảng palette, font Helvetica 12px, arrow 2px orthogonal classic, zone rounded-10px stroke-2px, instructions export PNG 1920px scale 2x.

### 3. User: verify (~5 phút)
- Mở `_template.drawio` trong Draw.io.
- Verify: palette swatches visible, title/footer render, mở lại không lỗi.
- Commit 2 files.

## Todo List

- [ ] User: color-pick 7 palette hex từ `architecture.png`, ship cho Claude
- [ ] Claude: gen `docs/diagrams/_template.drawio` XML
- [ ] Claude: gen `docs/diagrams/README.md` style guide
- [ ] User: verify template mở được trong Draw.io
- [ ] User: git commit

## Success Criteria
- [ ] `_template.drawio` mở không lỗi trong Draw.io, palette swatches visible
- [ ] `cat _template.drawio | head -5` shows plain XML readable
- [ ] README.md có đủ palette table + font + arrow + zone specs + export instructions

## Risk Assessment

| Risk | Mitigation |
|---|---|
| User pick palette sai từ PNG compressed | Claude cũng viết fallback palette hex chuẩn draw.io (FFF2CC/DAE8FC) nếu user không ship trong 5 phút |
| Shape library metadata không preserve khi edit | Test mở template lần 2 sau khi save, verify libraries vẫn enabled |
| Compressed flag accidentally true | Claude viết XML bao `<mxfile compressed="false">` explicit |

## Security Considerations
N/A.

## Next Steps
→ Sau khi template verified, Claude proceed Phase 02 gen P0 diagrams.
