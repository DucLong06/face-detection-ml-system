# Review Guide — Drawio Diagrams (for user)

**Purpose**: Hướng dẫn user verify 11 drawio diagrams đã gen, export PNG, commit lại. File này viết cho Claude session kế tiếp đọc được để tiếp tục support.

**Branch**: `docs/diagrams-drawio-redraw`
**Commit base**: `ff87dd3`

---

## 1. Setup Draw.io (5 phút, 1 lần)

Chọn 1 trong 3 cách:

### Option A — VSCode extension (Recommended)
```
1. VSCode → Extensions → search "Draw.io Integration"
2. Install `hediet.vscode-drawio`
3. Reload VSCode
4. Click vào file .drawio → mở trong tab editor native
```

### Option B — Desktop app
```
Download: https://github.com/jgraph/drawio-desktop/releases/latest
Linux: .deb / .AppImage
macOS: .dmg
Windows: .exe
```

### Option C — Web (no install)
```
https://app.diagrams.net/
→ Open Existing Diagram → Device → chọn file .drawio
```

---

## 2. Verify Checklist (15–20 phút tổng cho 11 diagrams)

### Bước 1: Open test — 2 phút
```bash
cd /mnt/data/mlops/Long-project/face-detect-gke
# Mở file đơn giản nhất trước
code docs/diagrams/02-batch-data-flow.drawio   # VSCode
# hoặc: open docs/diagrams/02-batch-data-flow.drawio  # macOS desktop app
```

**Expect**: Draw.io render được, thấy:
- Title "Face Detection MLOps — Batch Data Flow..."
- 5 zones màu orange (storage-ns, processing-ns, validation-ns, metadata-ns, orchestration-ns)
- ~10 boxes tool + 10 arrows với labels

**Nếu lỗi** (blank canvas, error message, XML parse fail):
→ Copy error message → paste vào chat, Claude fix XML.

### Bước 2: Per-diagram checklist — 1 phút/diagram

Mở lần lượt từng file, check 5 điểm:

| # | Check | Pass criteria |
|---|---|---|
| 1 | Title render đúng | Top center, 20px bold, không bị cắt |
| 2 | Zones màu đúng | Orange (namespace), green (obs), red (auth), yellow (external) |
| 3 | Nodes không overlap zones | Mọi tool box nằm TRONG zone của nó, không lệch ra ngoài |
| 4 | Arrows có label | Mọi arrow có text verb ("Push", "Query", "Route"...) readable |
| 5 | Footer render | Bottom-right "v0.1 | 2026-04-19 | longhd" |

### Bước 3: Report issues — format chuẩn

Paste vào chat theo format này để Claude action được:

```
## Diagram Review — YYYY-MM-DD

### 02-batch-data-flow.drawio
- [ ] Title OK
- [ ] Zones OK
- [x] ISSUE: `spark-bs` node overlap ra ngoài `processing-ns` zone (y=80 but zone startSize=28 → should be y≥40)
- [ ] Arrow labels OK
- [ ] Footer OK

### 03-stream-data-flow.drawio
- [x] ISSUE: Palette GKE quá xanh vs PNG L1 (user picked #B0D4F1, not #DAE8FC)
- ...
```

Claude sẽ:
- XML bug → fix cell geometry/parent refs
- Palette lệch → search-replace hex across 13 files
- Missing element → add new cell

---

## 3. Palette Adjustment (nếu cần)

Current palette (fallback, từ README.md):
```
bg:              #FFFFFF
cicd-fill:       #FFF2CC    cicd-border:     #D6B656
gke-fill:        #DAE8FC    gke-border:      #6C8EBF
ns-fill:         #FFE6CC    ns-border:       #D79B00
obs-fill:        #D5E8D4    obs-border:      #82B366
auth-fill:       #F8CECC    auth-border:     #B85450
arrow:           #000000
```

### Nếu muốn match `images/architecture.png` L1 chính xác:

1. Mở `images/architecture.png` trong color picker:
   - macOS: Preview → Tools → Rectangular Selection → đưa chuột vào zone → read color
   - Linux: `gpick` hoặc `gcolor3` (`sudo apt install gpick`)
   - Web: https://imagecolorpicker.com/ (upload ảnh)

2. Pick 7 colors và report format:
```
## Palette from architecture.png L1

bg: #______
cicd-fill: #______
cicd-border: #______
gke-fill: #______
gke-border: #______
ns-fill: #______
arrow: #______
```

3. Claude search-replace ~1 phút across 13 files.

---

## 4. Export PNG

### Option A — Manual (accurate, 2 phút/diagram × 11 = ~25 phút)

Với mỗi diagram mở trong Draw.io:
```
File → Export As → PNG...
Settings:
  Zoom: 200%
  Border Width: 10
  Background: Transparent = OFF (uncheck → white bg)
  Selection Only: OFF
  Include a copy of my diagram: OFF (giảm file size)
  Shadow: OFF
  Crop: OFF
Save to: docs/diagrams/XX-slug.png (cùng folder với .drawio)
```

### Option B — CLI batch (fast, 1 command)

Requires `drawio-desktop`:

```bash
# Linux (from repo root)
for f in docs/diagrams/*.drawio; do
  drawio --export --format png --scale 2 --border 10 --output "${f%.drawio}.png" "$f"
done
```

macOS app path:
```bash
DRAWIO="/Applications/draw.io.app/Contents/MacOS/draw.io"
for f in docs/diagrams/*.drawio; do
  "$DRAWIO" --export --format png --scale 2 --border 10 --output "${f%.drawio}.png" "$f"
done
```

Verify:
```bash
ls -lh docs/diagrams/*.png
# Expected: 11 PNG files, mỗi ~200–500KB
```

### Option C — CI auto-render (Phase 06 plan)

Setup GitHub Action `jgraph/drawio-export`. Skip cho MVP — xem `phase-06-optional-ci-auto-render.md`.

---

## 5. Commit Workflow

### Nếu chỉ export PNG (không sửa XML):

```bash
git add docs/diagrams/*.png
git commit -m "docs(diagrams): export PNG from drawio sources"
git push
```

### Nếu có sửa XML + export PNG:

```bash
git add docs/diagrams/
git commit -m "docs(diagrams): fix <issue description> + regenerate PNG"
git push
```

### Nếu palette adjusted (Claude vừa search-replace):

```bash
git add docs/diagrams/*.drawio docs/diagrams/README.md docs/diagrams/*.png
git commit -m "docs(diagrams): adjust palette to match L1 architecture"
git push
```

### Commit message convention

Format: `docs(diagrams): <short action in imperative>`
- ✅ `docs(diagrams): fix overlapping nodes in batch-data-flow`
- ✅ `docs(diagrams): export PNG 1920px for all 11 diagrams`
- ✅ `docs(diagrams): adjust palette to match L1 reference`
- ❌ `updated diagrams` (too vague)
- ❌ `fixed stuff` (no scope)

---

## 6. After Review — Next Steps

### Phase 05 (docs integration):
```bash
# Grep old refs
grep -rn "images/0[1-9]_\|images/1[01]_" NEW_PLANS.md README_EXTENDED.md

# Replace với sed (test trước với --dry-run nếu có)
sed -i '' 's|images/01_full_system_overview\.png|docs/diagrams/01-full-system-overview.png|g' NEW_PLANS.md README_EXTENDED.md
# ... 10 mapping khác, xem phase-05-docs-integration-archive.md section 2

# Archive PNG cũ
mkdir -p images/archive
git mv images/0{1..9}_*.png images/1{0,1}_*.png images/archive/

# Commit
git add NEW_PLANS.md README_EXTENDED.md images/
git commit -m "docs: migrate architecture diagrams refs to docs/diagrams, archive old PNGs"
git push
```

### Tạo PR:
```bash
gh pr create --base main \
  --title "docs: drawio architecture diagrams (11 diagrams L1+L2+L3+RAG+SSO)" \
  --body-file plans/260419-1356-diagram-redraw-drawio/plan.md
```

---

## 7. For Next Claude Session

Nếu mở session mới để tiếp tục support:

### Context Claude cần đọc:
```
1. plans/260419-1356-diagram-redraw-drawio/plan.md           # overview
2. plans/260419-1356-diagram-redraw-drawio/review-guide.md   # this file
3. docs/diagrams/README.md                                    # palette + style
4. Latest git log: git log --oneline -5
```

### Common user requests + Claude actions:

| User says | Claude action |
|---|---|
| "diagram XX bị lỗi render" | Open `docs/diagrams/XX-*.drawio`, parse XML, locate issue, Edit file, commit |
| "palette lệch, đây là hex..." | Search-replace hex across 13 files via MultiEdit, update README.md |
| "thêm tool Y vào diagram XX" | Edit XX-*.drawio, add `<mxCell>` + edge, keep same style |
| "export PNG hết" | Provide bash script (section 4 Option B), user run local |
| "tạo PR" | `gh pr create` với title + body từ plan.md |
| "merge xong rồi, xoá branch" | `git branch -D docs/diagrams-drawio-redraw` + `git push origin --delete ...` (confirm trước) |

### Files Claude CAN modify:
- `docs/diagrams/*.drawio` (source of truth)
- `docs/diagrams/README.md` (style guide)
- `docs/diagrams/*.png` (regenerate only, don't edit manually)
- `plans/260419-1356-diagram-redraw-drawio/*.md` (plan updates)
- `NEW_PLANS.md`, `README_EXTENDED.md` (Phase 05 refs)

### Files Claude MUST NOT touch:
- `images/architecture.png` (L1 reference, sacred)
- `images/01-11_*.png` until Phase 05 archive (preserve audit trail until confirmed)
- `.claude/` config (user domain)
- Other untracked work (datapipeline/, etc.)

---

## 8. Known Limitations (v0.1)

1. **Text placeholders thay real logos**: nodes là rounded rectangles with text, không phải Jenkins butler / Docker whale / etc. Polish Phase 2 nếu cần.
2. **Layout auto, không pixel-perfect**: nodes có thể overlap nhẹ, user nudge trong Draw.io.
3. **Palette fallback**: chưa match 100% với `architecture.png` L1 cho đến khi user ship hex thực tế.
4. **No PNG exports committed**: user phải export local rồi commit (hoặc setup Phase 06 CI).
5. **Animated arrows**: không có (user đã chọn skip).

---

## 9. Contact / Follow-up

- Plan owner: `longhd`
- Reports: `plans/reports/brainstorm-260419-1315-*.md` + `brainstorm-260419-1340-*.md`
- Questions? Paste diagram screenshot + issue description vào chat → Claude debug XML.
