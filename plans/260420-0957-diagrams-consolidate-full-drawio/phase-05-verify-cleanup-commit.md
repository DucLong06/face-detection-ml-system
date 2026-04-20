# Phase 05 — Verify, Cleanup Originals, Atomic Commit

## Context Links

- Brainstorm: `plans/reports/brainstorm-260420-0957-diagrams-consolidate-full-drawio.md` §5.5, §6, §7 (success criteria)
- Review: `newreview.md` Appendix (validation scripts)
- All prior phases 01–04 complete.

## Overview

- Priority: P2
- Status: pending
- Description: Run full validation suite, delete the 11 original `.drawio` files, update any repo references, single atomic commit + push.

## Key Insights

- Delete order: originals removed ONLY after `full.drawio` byte-for-byte preserves all 11 pages (validated via page-name assertion + desktop spot-check).
- Grep the entire repo (not just `docs/`) for references to `01-full-system-overview.drawio` etc. — likely in `docs/PLANNING_README.md` or similar index files. Rewrite those paths to `full.drawio` + relevant page name.
- Single commit keeps revert trivial. Avoid force-push.

## Requirements

### Functional
- R1. Palette compliance passes with extended ALLOWED set.
- R2. No residual references to deleted file names in repo markdown/docs.
- R3. Git working tree has: `full.drawio` + 11 `full-*.png` added; 11 `01-*..11-*.drawio` deleted; README + NEW_PLANS modified.
- R4. Single commit with conventional message.

### Non-functional
- NF1. Pre-commit hook passes (if any).
- NF2. No push to remote without user OK.

## Architecture

Verification pipeline:
```
xmllint --noout  →  11-page assertion  →  palette compliance  →
grep residuals (LangChain / app-ns / file refs)  →  git rm  →  git add  →  git commit
```

## Related Code Files

**Delete** (10 files — README.md NOT a .drawio)
- `docs/diagrams/01-full-system-overview.drawio`
- `docs/diagrams/02-batch-data-flow.drawio`
- `docs/diagrams/03-stream-data-flow.drawio`
- `docs/diagrams/04-cdc-data-flow.drawio`
- `docs/diagrams/05-ml-training-pipeline.drawio`
- `docs/diagrams/06-model-serving.drawio`
- `docs/diagrams/07-rag-pipeline.drawio`
- `docs/diagrams/08-sso-security-flow.drawio`
- `docs/diagrams/09-drift-detection.drawio`
- `docs/diagrams/10-llm-security-architecture.drawio`
- `docs/diagrams/11-enhanced-rag-pipeline.drawio`

**Keep**
- `docs/diagrams/_template.drawio`
- `docs/diagrams/full.drawio`
- `docs/diagrams/full-01.png` .. `docs/diagrams/full-11.png`
- `docs/diagrams/README.md`

**Modify** (if references found)
- `docs/PLANNING_README.md`
- any other file surfaced by grep Step 3.

## Implementation Steps

### Step 1 — XML structural validation

```bash
cd /mnt/data/mlops/Long-project/face-detect-gke
xmllint --noout docs/diagrams/full.drawio && echo "XML OK"

# Page count + names
python3 <<'EOF'
import xml.etree.ElementTree as ET
tree = ET.parse("docs/diagrams/full.drawio")
pages = tree.getroot().findall("diagram")
expected = [
    "Full System Overview", "Batch Data Flow", "Stream Data Flow",
    "CDC Data Flow", "ML Training Pipeline", "Model Serving",
    "RAG Pipeline", "SSO Security Flow", "Drift Detection",
    "LLM Security Architecture", "Enhanced RAG Pipeline",
]
got = [p.get("name") for p in pages]
assert got == expected, f"MISMATCH\nexp={expected}\ngot={got}"
print(f"OK: {len(pages)} pages in correct order")
EOF
```

### Step 2 — Palette compliance (extended ALLOWED)

```bash
python3 <<'EOF'
import re
ALLOWED = {
    "#FFFFFF", "#FFF2CC", "#D6B656",
    "#DAE8FC", "#6C8EBF", "#FFE6CC", "#D79B00",
    "#D5E8D4", "#82B366", "#F8CECC", "#B85450",
    "#000000", "#666666", "#ffffff",
    "#E1D5E7", "#9673A6",
    "#F5F5F5",  # NEW: Actors zone
    "none",
}
with open("docs/diagrams/full.drawio") as f:
    content = f.read()
found = set(re.findall(r"#[0-9A-Fa-f]{6}", content))
violations = found - ALLOWED
if violations:
    print(f"VIOLATIONS: {sorted(violations)}")
    raise SystemExit(1)
print(f"OK: all {len(found)} hex codes within ALLOWED palette")
EOF
```

### Step 3 — Residual content checks

```bash
# LangChain should not remain in pages 07/11 (global check)
LANGCHAIN_COUNT=$(grep -c "LangChain" docs/diagrams/full.drawio || true)
[ "$LANGCHAIN_COUNT" -eq 0 ] && echo "OK: no LangChain residue" || echo "FAIL: $LANGCHAIN_COUNT LangChain references"

# Page 04 uses app-oltp-ns; page 08 still has app-ns (generic target-app swimlane)
grep -q 'id="app-oltp-ns"' docs/diagrams/full.drawio && echo "OK: app-oltp-ns present"
grep -q 'id="app-ns"' docs/diagrams/full.drawio && echo "OK: app-ns still present (page 08 target-app)"

# SSO step 11 text
grep -q "EnvoyFilter validates JWT" docs/diagrams/full.drawio && echo "OK: SSO step 11 correct"

# Page 01 has 5+ edges with main-e prefix
grep -c 'id="main-e' docs/diagrams/full.drawio  # expect 5
```

### Step 4 — Repo-wide reference grep

```bash
cd /mnt/data/mlops/Long-project/face-detect-gke
# Search for references to old file names
grep -rn --include="*.md" \
  -e "01-full-system-overview\.drawio" \
  -e "02-batch-data-flow\.drawio" \
  -e "03-stream-data-flow\.drawio" \
  -e "04-cdc-data-flow\.drawio" \
  -e "05-ml-training-pipeline\.drawio" \
  -e "06-model-serving\.drawio" \
  -e "07-rag-pipeline\.drawio" \
  -e "08-sso-security-flow\.drawio" \
  -e "09-drift-detection\.drawio" \
  -e "10-llm-security-architecture\.drawio" \
  -e "11-enhanced-rag-pipeline\.drawio" \
  docs/ README.md NEW_PLANS.md 2>/dev/null
# For each hit, rewrite path to "docs/diagrams/full.drawio (page NN)"
```

### Step 5 — Delete originals

```bash
cd /mnt/data/mlops/Long-project/face-detect-gke
git rm docs/diagrams/01-full-system-overview.drawio \
       docs/diagrams/02-batch-data-flow.drawio \
       docs/diagrams/03-stream-data-flow.drawio \
       docs/diagrams/04-cdc-data-flow.drawio \
       docs/diagrams/05-ml-training-pipeline.drawio \
       docs/diagrams/06-model-serving.drawio \
       docs/diagrams/07-rag-pipeline.drawio \
       docs/diagrams/08-sso-security-flow.drawio \
       docs/diagrams/09-drift-detection.drawio \
       docs/diagrams/10-llm-security-architecture.drawio \
       docs/diagrams/11-enhanced-rag-pipeline.drawio
```

### Step 6 — Stage all changes

```bash
git add docs/diagrams/full.drawio
git add docs/diagrams/full-*.png
git add docs/diagrams/README.md
git add NEW_PLANS.md
# Any files modified by Step 4 grep fix:
# git add docs/PLANNING_README.md ...
git status
# Verify: 11 deletions, ~14 additions/modifications
```

### Step 7 — Atomic commit

```bash
git commit -m "$(cat <<'EOF'
docs(diagrams): consolidate into full.drawio + review fixes

- Merge 11 single-page .drawio files into docs/diagrams/full.drawio (multi-page)
- Delete originals 01-*..11-*.drawio (single source of truth)
- Export 11 PNG artifacts full-01.png..full-11.png via drawio CLI
- Rename LangChain → RAGFlow on pages 07 + 11 (align with NEW_PLANS §5)
- CDC page 04: app-ns → app-oltp-ns (cell id + label); add row in NEW_PLANS §7
- SSO page 08: re-number 12-step flow (9=set cookie, 10=redirect,
  11=EnvoyFilter validates JWT, 12=forward) per NEW_PLANS §5.2
- Page 01: recolor Actors zone (#F5F5F5/#666666 neutral gray)
- Page 01: recolor nginx-ns-2 (#FFE6CC/#D79B00 namespace orange)
- Page 01: add 5 main-flow edges (User→NGINX→Serving→DB/Cache/Trace)
- Page 05: label 6 pipeline edges (Preprocess/Train/Evaluate/Promote/Export/Canary)
- Page 10: label 6 guardrail edges (Classify/Detect injection/Toxicity/etc.)
- README: add Actors zone palette row; rewrite file naming table + export section
EOF
)"
```

### Step 8 — Post-commit verification

```bash
git log -1 --stat
git status  # should be clean
# Optional: re-run palette + structural checks on committed HEAD
```

### Step 9 — Push (ONLY if user requests)

```bash
# Do NOT push unless user explicitly confirms.
# git push origin docs/diagrams-drawio-redraw
```

## Todo List

- [ ] Step 1 — XML structural validation.
- [ ] Step 2 — palette compliance.
- [ ] Step 3 — residual content checks (LangChain, app-oltp-ns, EnvoyFilter, main-e).
- [ ] Step 4 — repo-wide grep for old filenames; fix references if found.
- [ ] Step 5 — `git rm` 11 originals.
- [ ] Step 6 — stage all changes.
- [ ] Step 7 — atomic commit.
- [ ] Step 8 — verify commit.
- [ ] Step 9 — (deferred) push — user-approved only.

## Success Criteria

- [ ] `xmllint --noout docs/diagrams/full.drawio` passes.
- [ ] 11 pages in correct order, page-name assertion passes.
- [ ] Palette compliance passes with extended ALLOWED (`#F5F5F5`).
- [ ] Grep shows 0 LangChain, 0 references to deleted filenames in `docs/`.
- [ ] `git log -1 --stat` shows 10 `D docs/diagrams/NN-*.drawio`, 1 `A docs/diagrams/full.drawio`, 11 `A docs/diagrams/full-*.png`, `M docs/diagrams/README.md`, `M NEW_PLANS.md`.
- [ ] Commit message follows conventional format, no AI refs.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Pre-commit hook rejects large PNG total | Low | 🟠 | Check hook config; if hook blocks, defer PNGs to separate commit (still same PR). |
| `git rm` runs before `full.drawio` verified | Low | 🔴 Data loss | Step order enforced: validation (1–4) MUST precede `git rm` (5). |
| Hidden reference in non-md file (yml, py) | Low | 🟢 | Grep in Step 4 scoped to md; expand to yml/py if user reports broken link. |
| Accidental push to main | Low | 🔴 | Step 9 gated behind user approval; `git push origin docs/diagrams-drawio-redraw` explicit. |
| Commit message contains AI reference | Low | 🟢 | Heredoc drafted here, no "Claude"/"Anthropic" strings. |

## Security Considerations

- No secrets in any diagram XML. No impact.

## Next Steps

- Open PR (out of scope — user task).
- Future phase (out of this plan): CI PNG auto-render workflow (deferred from review Item 0.2).

---

## Post-merge cleanup (optional)

- Remove `plans/260420-0957-diagrams-consolidate-full-drawio/scripts/*.py` if ephemeral; or move to `docs/diagrams/scripts/` if keeping for reproducibility.
