# Phase 04 — PNG Export + README Refresh

## Context Links

- Brainstorm: `plans/reports/brainstorm-260420-0957-diagrams-consolidate-full-drawio.md` §5.3, §5.6
- Review: `newreview.md` Item 0.2 (PNG missing)
- Target files:
  - `docs/diagrams/full.drawio` (input; from phase 03)
  - `docs/diagrams/full-01.png` .. `docs/diagrams/full-11.png` (new)
  - `docs/diagrams/README.md` (update palette table, file naming table, export section)

## Overview

- Priority: P2
- Status: pending
- Description: Run `drawio` CLI to export 11 PNG artifacts (1 per page), zero-pad names for lexical sort, and update README to reflect new single-file model.

## Key Insights

- `drawio -x -f png` with a multi-page `.drawio` outputs **1 PNG per page**, default naming `basename-N.png` where N is page index (1-based). Not zero-padded.
- `drawio` v29 may exit non-zero on headless systems due to `vaapi` GPU init warnings — export still completes. Force `ELECTRON_DISABLE_GPU=1` + `--no-sandbox` (if needed) for stability.
- README table rewrite: single-row "all diagrams → full.drawio + per-page PNG" replaces current 11-row table.

## Requirements

### Functional
- R1. Produce 11 PNG files: `docs/diagrams/full-01.png` .. `full-11.png`.
- R2. PNG content = rendered page (white bg, 10px border, 100–200% zoom acceptable).
- R3. Update README `## Style guide — Palette` table: add `Actors zone | #F5F5F5 | #666666 | Neutral gray`.
- R4. Update README `## File naming` section: replace 11-row table with single-file model.
- R5. Update README `## How to export PNG` section: replace manual GUI steps with CLI command.

### Non-functional
- NF1. PNGs committed to repo (not gitignored).
- NF2. README stays readable; no broken markdown tables.

## Architecture — Export Pipeline

```
docs/diagrams/full.drawio  →  drawio CLI  →  full-1.png .. full-11.png
                                                 │
                                                 ▼  rename loop (seq 1..9 → 01..09)
                                             full-01.png .. full-11.png
```

## Related Code Files

**Create**
- `docs/diagrams/full-01.png` .. `full-11.png` (11 new PNGs)

**Modify**
- `docs/diagrams/README.md`

## Implementation Steps

### Step 1 — Run drawio CLI export

```bash
cd /mnt/data/mlops/Long-project/face-detect-gke/docs/diagrams
ELECTRON_DISABLE_GPU=1 drawio -x -f png -t --border 10 -o . full.drawio
# Expected output: full-1.png, full-2.png, ..., full-11.png
# --border 10 matches README instruction "Border Width: 10"
# -t = transparent=false (preserves white background inherent in diagram)
# -o .  = output dir (current)
```

If CLI fails with `vaapi` / `gpu` errors:
```bash
ELECTRON_DISABLE_GPU=1 drawio --no-sandbox -x -f png --border 10 -o . full.drawio
```

### Step 2 — Zero-pad rename (lexical sort)

```bash
cd /mnt/data/mlops/Long-project/face-detect-gke/docs/diagrams
for i in 1 2 3 4 5 6 7 8 9; do
  [ -f "full-$i.png" ] && mv "full-$i.png" "full-0$i.png"
done
# full-10.png, full-11.png already sort correctly — no rename.
ls full-*.png
# Expected: full-01.png  full-02.png  ... full-11.png (11 files)
```

### Step 3 — Verify PNG count

```bash
ls docs/diagrams/full-*.png | wc -l
# Expected: 11
```

### Step 4 — README palette table update

File: `docs/diagrams/README.md`

Locate table under `## Style guide — Palette` (currently 10 rows). Add new row just **after** "Canvas background" line and **before** "CI/CD zone":

**Before**
```markdown
| Element | Fill | Border | Notes |
|---|---|---|---|
| Canvas background | `#FFFFFF` | — | Pure white |
| CI/CD zone | `#FFF2CC` | `#D6B656` | Yellow cream |
```

**After**
```markdown
| Element | Fill | Border | Notes |
|---|---|---|---|
| Canvas background | `#FFFFFF` | — | Pure white |
| Actors zone | `#F5F5F5` | `#666666` | Neutral gray (used for page 01 Actors swimlane) |
| CI/CD zone | `#FFF2CC` | `#D6B656` | Yellow cream |
```

### Step 5 — README file naming section update

Replace the entire `## File naming` section with:

```markdown
## File naming

Single master file: `full.drawio` — multi-page, 11 diagrams.
PNG exports: `full-XX.png` (one per page, zero-padded for lexical sort).

| # | Diagram | Page name (in `full.drawio`) | PNG |
|---|---|---|---|
| 01 | Full system overview (all 16 ns) | `Full System Overview` | `full-01.png` |
| 02 | Batch data flow (Bronze→Silver→Gold) | `Batch Data Flow` | `full-02.png` |
| 03 | Stream data flow (Kafka+Flink) | `Stream Data Flow` | `full-03.png` |
| 04 | CDC data flow (Debezium from `app-oltp-ns`) | `CDC Data Flow` | `full-04.png` |
| 05 | ML training pipeline (Kubeflow+MLflow+Katib) | `ML Training Pipeline` | `full-05.png` |
| 06 | Model serving (KServe+Triton) | `Model Serving` | `full-06.png` |
| 07 | RAG pipeline (Ollama+Weaviate+RAGFlow) | `RAG Pipeline` | `full-07.png` |
| 08 | SSO security flow (12-step OIDC) | `SSO Security Flow` | `full-08.png` |
| 09 | Drift detection (Evidently) | `Drift Detection` | `full-09.png` |
| 10 | LLM security architecture (guardrails) | `LLM Security Architecture` | `full-10.png` |
| 11 | Enhanced RAG (hybrid search + rerank) | `Enhanced RAG Pipeline` | `full-11.png` |

Template: `_template.drawio` (skeleton for new diagrams; not merged into `full.drawio`).
```

### Step 6 — README export section update

Replace the entire `## How to export PNG` section with:

```markdown
## How to export PNG

**CLI (preferred, deterministic):**

```bash
cd docs/diagrams
ELECTRON_DISABLE_GPU=1 drawio -x -f png -t --border 10 -o . full.drawio
# Outputs: full-1.png .. full-11.png
# Zero-pad for lexical sort:
for i in 1 2 3 4 5 6 7 8 9; do
  [ -f "full-$i.png" ] && mv "full-$i.png" "full-0$i.png"
done
ls full-*.png  # 11 files: full-01.png .. full-11.png
```

**GUI fallback (draw.io desktop / web):**
`File → Export As → PNG` → Zoom 200%, Border Width 10, Background White, Shadow off.
Repeat for each of 11 pages; save as `full-NN.png`.
```

### Step 7 — Verify README markdown

```bash
# Sanity: tables still render (no missing pipes)
grep -c '^|' docs/diagrams/README.md
# Expected: ≥ 20 (palette ~11 rows + file naming ~13 rows including header+separator)
```

## Todo List

- [ ] Step 1 — run `drawio` CLI export.
- [ ] Step 2 — zero-pad rename.
- [ ] Step 3 — verify 11 PNGs.
- [ ] Step 4 — README palette row add.
- [ ] Step 5 — README file naming rewrite.
- [ ] Step 6 — README export section rewrite.
- [ ] Step 7 — README markdown sanity check.

## Success Criteria

- [ ] `ls docs/diagrams/full-*.png | wc -l` → `11`.
- [ ] README palette table contains "Actors zone" row with `#F5F5F5`.
- [ ] README file naming table references `full.drawio` + `full-XX.png` (not `01-*.drawio`).
- [ ] README export section shows CLI command with `ELECTRON_DISABLE_GPU=1` + `drawio -x -f png`.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| `drawio` CLI exit non-zero (vaapi) but PNGs exported | High | 🟢 | Rely on file existence check in Step 3, not exit code. |
| PNG export produces only 1 page (CLI version doesn't split multi-page) | Low | 🔴 | Pre-flight: verify `drawio` v29.7.8 splits multi-page. If fails, fallback: loop `-p <idx>` 1..11. |
| Rename loop runs before CLI finishes (race on headless) | Low | 🟠 | CLI is synchronous. Run sequentially. |
| Markdown table break (missing `|`) | Medium | 🟢 | Review via render preview or grep count. |
| Large PNG files bloat git history | Medium | 🟢 | Expected 100–500 KB each; 11 PNGs ~3–5 MB total. Acceptable. If user concerned, defer PNGs to git-lfs (out of scope). |

### Fallback: per-page export loop

If the single-command export does NOT split pages:

```bash
for i in $(seq 1 11); do
  ELECTRON_DISABLE_GPU=1 drawio -x -f png -t --border 10 -p $i \
    -o "docs/diagrams/full-$(printf '%02d' $i).png" docs/diagrams/full.drawio
done
```

(`-p` flag is 1-indexed in drawio CLI v29; verified via `drawio --help`.)

## Security Considerations

- None.

## Next Steps

- Phase 05: final verification, delete 11 source `.drawio`, single atomic commit.
