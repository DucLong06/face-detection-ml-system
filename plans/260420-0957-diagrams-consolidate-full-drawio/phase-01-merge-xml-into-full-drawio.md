# Phase 01 — Merge 11 Diagrams into `full.drawio`

## Context Links

- Brainstorm: `plans/reports/brainstorm-260420-0957-diagrams-consolidate-full-drawio.md` §5.1
- Review: `newreview.md` Items 0.1, 1.1, 1.2
- Source files (inputs, 11 × single-page):
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
- Target: `docs/diagrams/full.drawio` (NEW)

## Overview

- Priority: P2 (blocker for phases 02–05)
- Status: pending
- Description: Concatenate 11 single-page `<diagram>` elements into one `<mxfile compressed="false">` in order 01→11. No content changes here — purely structural merge.

## Key Insights

- Each source `.drawio` has exactly one `<diagram id="dNN" name="...">` element (verified: scout confirmed all files single-page post-cleanup).
- All source files use `<mxfile host="app.diagrams.net" agent="Claude" type="device" compressed="false" version="22.1.0">` — byte-identical wrapper.
- Draw.io scopes cell IDs **per `<mxGraphModel>`** — two pages can both have `id="e1"` without collision. Verified by inspecting `_template.drawio` behavior; will be re-verified in step 6 by opening in drawio desktop.
- File sizes sum ≈ 92 KB raw; merged `full.drawio` expected ≈ 90–100 KB.

## Requirements

### Functional
- R1. `full.drawio` contains exactly 11 `<diagram>` children under the single `<mxfile>` root.
- R2. Page order matches README table: 01 Full → 02 Batch → 03 Stream → 04 CDC → 05 ML → 06 Serving → 07 RAG → 08 SSO → 09 Drift → 10 LLM Security → 11 Enhanced RAG.
- R3. Page `name` attribute preserved from source (e.g., `Full System Overview`, `CDC Data Flow`, `SSO Security Flow`, `Enhanced RAG Pipeline`).
- R4. `compressed="false"` on `<mxfile>` (no base64).
- R5. All inner `<mxGraphModel>`, `<root>`, `<mxCell>` content preserved verbatim (no whitespace normalization that breaks layout).

### Non-functional
- NF1. Output well-formed XML (`xmllint --noout` exits 0).
- NF2. Script idempotent — re-running overwrites `full.drawio` deterministically.
- NF3. No third-party deps (Python stdlib only).

## Architecture — XML Merge Structure

```
Input (×11):                          Output (×1):
<mxfile compressed="false">           <mxfile host="app.diagrams.net"
  <diagram id="d01" name="...">               agent="Claude"
    <mxGraphModel>...</mxGraphModel>          type="device"
  </diagram>                                  compressed="false"
</mxfile>                                     version="22.1.0">
                                        <diagram id="d01" name="...">...</diagram>
                                        <diagram id="d02" name="...">...</diagram>
                                        ...
                                        <diagram id="d11" name="...">...</diagram>
                                      </mxfile>
```

- ID renaming strategy: **NOT needed at merge time** (draw.io scopes IDs per `<mxGraphModel>`). Verification step at end of phase. If desktop open fails due to collision, fallback: prefix inner `id` with page number (e.g., `p01-e1`) and update all `source=`/`target=`/`parent=` refs accordingly.
- Diagram `id` attrs already unique (`d01`..`d11`) — keep as-is.

## Related Code Files

**Create**
- `/mnt/data/mlops/Long-project/face-detect-gke/docs/diagrams/full.drawio` (merged output, ~100 KB)
- `/mnt/data/mlops/Long-project/face-detect-gke/plans/260420-0957-diagrams-consolidate-full-drawio/scripts/merge-diagrams.py` (merge script, throwaway — keep for reproducibility)

**Modify**
- None

**Delete**
- None (deletion happens in phase 05)

## Implementation Steps

### Step 1 — Create merge script

Path: `plans/260420-0957-diagrams-consolidate-full-drawio/scripts/merge-diagrams.py`

```python
#!/usr/bin/env python3
"""Merge 11 single-page .drawio files into docs/diagrams/full.drawio."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

DIAG_DIR = Path("docs/diagrams")
ORDER = [
    "01-full-system-overview.drawio",
    "02-batch-data-flow.drawio",
    "03-stream-data-flow.drawio",
    "04-cdc-data-flow.drawio",
    "05-ml-training-pipeline.drawio",
    "06-model-serving.drawio",
    "07-rag-pipeline.drawio",
    "08-sso-security-flow.drawio",
    "09-drift-detection.drawio",
    "10-llm-security-architecture.drawio",
    "11-enhanced-rag-pipeline.drawio",
]
OUT = DIAG_DIR / "full.drawio"

def main():
    # Build new root mxfile
    root = ET.Element("mxfile", attrib={
        "host": "app.diagrams.net",
        "agent": "Claude",
        "type": "device",
        "compressed": "false",
        "version": "22.1.0",
    })
    for fname in ORDER:
        fpath = DIAG_DIR / fname
        if not fpath.exists():
            sys.exit(f"FAIL: source missing: {fpath}")
        src_tree = ET.parse(fpath)
        src_root = src_tree.getroot()
        diagrams = src_root.findall("diagram")
        if len(diagrams) != 1:
            sys.exit(f"FAIL: {fname} has {len(diagrams)} diagrams (expected 1)")
        root.append(diagrams[0])
    # Indent for readability (Python 3.9+)
    ET.indent(root, space="  ", level=0)
    tree = ET.ElementTree(root)
    tree.write(OUT, encoding="UTF-8", xml_declaration=False)
    print(f"OK: wrote {OUT} with {len(root.findall('diagram'))} pages")

if __name__ == "__main__":
    main()
```

### Step 2 — Run from repo root

```bash
cd /mnt/data/mlops/Long-project/face-detect-gke
mkdir -p plans/260420-0957-diagrams-consolidate-full-drawio/scripts
# write script (see Step 1)
python3 plans/260420-0957-diagrams-consolidate-full-drawio/scripts/merge-diagrams.py
# Expected output: OK: wrote docs/diagrams/full.drawio with 11 pages
```

### Step 3 — Validate XML

```bash
xmllint --noout docs/diagrams/full.drawio && echo "XML OK"
xmllint --format docs/diagrams/full.drawio | wc -l
# Expected: ~1200–1400 formatted lines
```

### Step 4 — Assert 11 pages

```bash
python3 -c '
import xml.etree.ElementTree as ET
t = ET.parse("docs/diagrams/full.drawio")
pages = t.getroot().findall("diagram")
assert len(pages) == 11, f"got {len(pages)} pages"
names = [p.get("name") for p in pages]
print("\n".join(names))
'
```

Expected stdout:
```
Full System Overview
Batch Data Flow
Stream Data Flow
CDC Data Flow
ML Training Pipeline
Model Serving
RAG Pipeline
SSO Security Flow
Drift Detection
LLM Security Architecture
Enhanced RAG Pipeline
```

### Step 5 — Check `compressed="false"` attr preserved

```bash
head -1 docs/diagrams/full.drawio | grep -q 'compressed="false"' && echo "PLAIN OK"
```

### Step 6 — Open in draw.io desktop (manual / optional)

```bash
ELECTRON_DISABLE_GPU=1 drawio docs/diagrams/full.drawio &
# Tab through all 11 pages — verify no broken edges, no red "missing source/target" warnings.
```

If collisions detected (rare): run fallback ID-prefix script (see Risk Assessment).

## Todo List

- [ ] Create `plans/260420-0957-diagrams-consolidate-full-drawio/scripts/` dir.
- [ ] Write `merge-diagrams.py`.
- [ ] Run merge; produce `docs/diagrams/full.drawio`.
- [ ] `xmllint --noout` pass.
- [ ] Assert 11 pages with expected names.
- [ ] Assert `compressed="false"`.
- [ ] (Optional) desktop open — tab through 11 pages, spot-check.

## Success Criteria

- [ ] `docs/diagrams/full.drawio` exists, size 90–110 KB.
- [ ] `xmllint --noout docs/diagrams/full.drawio` exits 0.
- [ ] Python assertion script prints 11 page names in correct order.
- [ ] Desktop open renders all 11 pages with no broken-edge warnings.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Cell ID collision across pages breaks draw.io parse | Low | 🔴 Blocker | Draw.io scopes IDs per `<mxGraphModel>` — confirmed by inspection. Fallback: ID-prefix script that rewrites `id=`/`source=`/`target=`/`parent=` with `pNN-` prefix. |
| ElementTree drops XML comments / whitespace in nested `<mxGraphModel>` | Low | 🟠 Layout off | Source files have no comments; whitespace is cosmetic. `ET.indent` reformats cleanly. |
| Script run from wrong CWD → relative paths break | Medium | 🟠 | Script uses `Path("docs/diagrams")` — MUST run from repo root. Doc'd in Step 2. |
| Source file missing or >1 page | Low | 🔴 | Script explicit `sys.exit()` with clear FAIL msg. |

## Security Considerations

- No secrets in `.drawio` files (verified — content is architecture names only). No impact.

## Next Steps

- Phase 02: apply content fixes (RAGFlow rename, SSO 12-step, `app-oltp-ns`) via sed/Python on the merged `full.drawio`.
