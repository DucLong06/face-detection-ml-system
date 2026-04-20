# Phase 03 — Palette Recolor + Page 01 Main-Flow Arrows + Edge Labels (05, 10)

## Context Links

- Brainstorm: `plans/reports/brainstorm-260420-0957-diagrams-consolidate-full-drawio.md` §5.2 (items 4–8)
- Review: `newreview.md` Items 2.1 (Actors palette), 2.2 (nginx-ns-2), 3.1 (edge labels 05+10), 6.1 (page 01 main-flow arrows)
- Target: `docs/diagrams/full.drawio` (from phase 02)
- Source inspection: page 01 has cells `a1, gw1..gw5, ms1, s1..s4, st2, st3, mon1, mon2, mon3` — map to main-flow.

## Overview

- Priority: P2
- Status: pending
- Description: Visual + semantic fixes — recolor 2 zones, inject 5 new orthogonal edges on page 01, label 6 edges on page 05, label 6 edges on page 10.

## Key Insights

- Page 01 `actors` zone currently fill `#FFF2CC`/stroke `#D6B656` — conflicts with CI/CD yellow. Reviewer fix: `#F5F5F5`/`#666666` (neutral gray).
- Page 01 `nginx-ns-2` currently fill `#F8CECC`/stroke `#B85450` (auth red) — wrong semantic (it's a namespace, not auth). Fix: `#FFE6CC`/`#D79B00` (namespace orange).
- Page 01 has **0 edges** — only zones/nodes. Add 5 representative main-flow edges. Avoid over-crowding: 5 edges, not 10.
- Page 05: 14 total edges; 6 inner pipeline edges (`e3..e8`, between step1..step7) have empty `value=""`. Keep `e3..e8` labels short to avoid clutter in nested swimlane.
- Page 10: 12 total edges; 6 inner guardrail-chain edges (`e2, e3, e4, e7, e8, e9`) have empty `value=""`. Label with action verbs per review.

## Requirements

### Functional
- R1. Page 01 `actors` cell: `fillColor=#F5F5F5;strokeColor=#666666`.
- R2. Page 01 `nginx-ns-2` cell: `fillColor=#FFE6CC;strokeColor=#D79B00`.
- R3. Page 01: add 5 orthogonal edges (solid, 2px, classic arrowhead), all children of `parent="1"` (page root), with labels.
- R4. Page 05: label 6 edges — steps 1→2 "Preprocess", 2→3 "Augment", 3→4 "Train", 4→5 "Evaluate", 5→6 "Promote", 6→7 "Export".  Alternative label set per review: "Pull features / Train / Log metrics / Register / Deploy / Trigger" — see mapping table below.
- R5. Page 10: label 6 edges — `e2` "Classify", `e3` "Inject check", `e4` "Toxicity scan", `e7` "Ground check", `e8` "Block toxic", `e9` "Redact PII".  Alternative label set per review: "Classify / Redact PII / Check policy / Allow-Block / Log / Audit".

### Non-functional
- NF1. XML well-formed.
- NF2. New edge IDs on page 01 unique within page (e.g., `main-e1..main-e5`).
- NF3. Palette compliance: `#F5F5F5` + `#666666` added to ALLOWED set in verification script.

## Architecture — Edge Routing Strategy

### Page 01 new edges

Target cells (verified from source):
- `a1` — End User (actor)
- `gw5` — NGINX Ingress (front door, L1 legacy; or use `gw1` Istio Gateway for L2)
- `ms1` — FastAPI + YOLOv11 (L1 legacy serving)
- `s1` — KServe (L2 serving)
- `st2` — PostgreSQL DW
- `st3` — Redis
- `trace1` — Jaeger (observability)

Edge plan (5 edges, mix of L1 legacy + L2 target path):

| ID | Source | Target | Label | Style |
|---|---|---|---|---|
| `main-e1` | `a1` | `gw5` | "1. HTTPS" | solid |
| `main-e2` | `gw5` | `ms1` | "2. Route" | solid |
| `main-e3` | `ms1` | `st2` | "3. Persist" | solid |
| `main-e4` | `ms1` | `st3` | "4. Cache" | solid |
| `main-e5` | `ms1` | `trace1` | "Trace" | dashed |

**Note:** `ms1` (FastAPI + YOLOv11) is used as serving node for v0.1. Can later add `main-e6/e7` for L2 path (a1→gw1→s1) if user requests.

**XML snippets** (insert just before `<mxCell id="footer" ...>`):

```xml
<mxCell id="main-e1" value="1. HTTPS" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=classic;strokeWidth=2;fontSize=10;labelBackgroundColor=#ffffff;" edge="1" parent="1" source="a1" target="gw5">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
<mxCell id="main-e2" value="2. Route" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=classic;strokeWidth=2;fontSize=10;labelBackgroundColor=#ffffff;" edge="1" parent="1" source="gw5" target="ms1">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
<mxCell id="main-e3" value="3. Persist" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=classic;strokeWidth=2;fontSize=10;labelBackgroundColor=#ffffff;" edge="1" parent="1" source="ms1" target="st2">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
<mxCell id="main-e4" value="4. Cache" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=classic;strokeWidth=2;fontSize=10;labelBackgroundColor=#ffffff;" edge="1" parent="1" source="ms1" target="st3">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
<mxCell id="main-e5" value="Trace" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=classic;strokeWidth=2;fontSize=10;dashed=1;labelBackgroundColor=#ffffff;" edge="1" parent="1" source="ms1" target="trace1">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

### Page 05 edge labels (6 unlabeled → labeled)

Currently `e3..e8` are inside `kf-pipeline` parent (the DAG swimlane) with empty labels.

| Edge | Source → Target | New Label |
|---|---|---|
| `e3` | step1 → step2 | "Preprocess" |
| `e4` | step2 → step3 | "Train" |
| `e5` | step3 → step4 | "Evaluate" |
| `e6` | step4 → step5 | "Promote" |
| `e7` | step5 → step6 | "Export" |
| `e8` | step6 → step7 | "Canary" |

Per-review alternate vocabulary ("Pull features / Train / Log metrics / Register / Deploy / Trigger"): these already exist on OUTER edges (e1 "Load features", e10 "Log metrics", e11 "Register model", e14 "Canary deploy"). Inner edges use flow-verbs as above to avoid label duplication.

### Page 10 edge labels (6 unlabeled → labeled)

| Edge | Source → Target | New Label |
|---|---|---|
| `e2` | pii → injection | "Classify" |
| `e3` | injection → tox-in | "Detect injection" |
| `e4` | tox-in → rate-limit | "Toxicity in" |
| `e7` | hallucination → tox-out | "Ground check" |
| `e8` | tox-out → factuality | "Allow/Block" |
| `e9` | factuality → pii-out | "Redact PII" |

## Related Code Files

**Modify**
- `/mnt/data/mlops/Long-project/face-detect-gke/docs/diagrams/full.drawio`

**Create**
- `/mnt/data/mlops/Long-project/face-detect-gke/plans/260420-0957-diagrams-consolidate-full-drawio/scripts/apply-visual-fixes.py`

## Implementation Steps

### Step 1 — Script scaffolding

```python
import xml.etree.ElementTree as ET
tree = ET.parse("docs/diagrams/full.drawio")
root = tree.getroot()

def page(name):
    return next(d for d in root.findall("diagram") if d.get("name") == name)
def cell(d, cid):
    return next(c for c in d.iter("mxCell") if c.get("id") == cid)
def graph_root(d):
    return d.find(".//root")  # <root> under <mxGraphModel>
```

### Step 2 — Page 01 recolors

```python
p01 = page("Full System Overview")
# Actors zone: swap yellow → neutral gray
actors = cell(p01, "actors")
st = actors.get("style")
st = st.replace("fillColor=#FFF2CC", "fillColor=#F5F5F5")
st = st.replace("strokeColor=#D6B656", "strokeColor=#666666")
actors.set("style", st)

# nginx-ns-2: swap auth-red → namespace-orange
nginx = cell(p01, "nginx-ns-2")
st = nginx.get("style")
st = st.replace("fillColor=#F8CECC", "fillColor=#FFE6CC")
st = st.replace("strokeColor=#B85450", "strokeColor=#D79B00")
nginx.set("style", st)
```

### Step 3 — Page 01 add 5 main-flow edges

```python
EDGES = [
    ("main-e1", "a1",  "gw5",   "1. HTTPS",   False),
    ("main-e2", "gw5", "ms1",   "2. Route",   False),
    ("main-e3", "ms1", "st2",   "3. Persist", False),
    ("main-e4", "ms1", "st3",   "4. Cache",   False),
    ("main-e5", "ms1", "trace1","Trace",       True),
]
g = graph_root(p01)
for eid, src, tgt, label, dashed in EDGES:
    style = ("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=classic;"
             "strokeWidth=2;fontSize=10;labelBackgroundColor=#ffffff;")
    if dashed:
        style += "dashed=1;"
    mx = ET.SubElement(g, "mxCell", attrib={
        "id": eid, "value": label, "style": style,
        "edge": "1", "parent": "1", "source": src, "target": tgt,
    })
    ET.SubElement(mx, "mxGeometry", attrib={"relative": "1", "as": "geometry"})
```

### Step 4 — Page 05 label edges

```python
p05 = page("ML Training Pipeline")
LABELS_05 = {
    "e3": "Preprocess", "e4": "Train", "e5": "Evaluate",
    "e6": "Promote",    "e7": "Export", "e8": "Canary",
}
for cid, lbl in LABELS_05.items():
    c = cell(p05, cid)
    c.set("value", lbl)
    # Ensure label-friendly style
    st = c.get("style", "")
    if "fontSize=" not in st:
        st += "fontSize=10;"
    if "labelBackgroundColor=" not in st:
        st += "labelBackgroundColor=#ffffff;"
    c.set("style", st)
```

### Step 5 — Page 10 label edges

```python
p10 = page("LLM Security Architecture")
LABELS_10 = {
    "e2": "Classify",      "e3": "Detect injection", "e4": "Toxicity in",
    "e7": "Ground check",  "e8": "Allow/Block",      "e9": "Redact PII",
}
for cid, lbl in LABELS_10.items():
    c = cell(p10, cid)
    c.set("value", lbl)
    st = c.get("style", "")
    if "fontSize=" not in st:
        st += "fontSize=10;"
    if "labelBackgroundColor=" not in st:
        st += "labelBackgroundColor=#ffffff;"
    c.set("style", st)
```

### Step 6 — Save and validate

```python
tree.write("docs/diagrams/full.drawio", encoding="UTF-8", xml_declaration=False)
```

```bash
xmllint --noout docs/diagrams/full.drawio && echo "XML OK"

# Spot-check page 01 has 5 new edges
python3 -c '
import xml.etree.ElementTree as ET
t = ET.parse("docs/diagrams/full.drawio")
for d in t.getroot().findall("diagram"):
    if d.get("name") == "Full System Overview":
        edges = [c for c in d.iter("mxCell") if c.get("edge") == "1"]
        print(f"Page 01 edges: {len(edges)}")
        for e in edges:
            print(f"  {e.get(\"id\")}: {e.get(\"source\")}→{e.get(\"target\")} [{e.get(\"value\")}]")
'
# Expected: 5 edges main-e1..main-e5
```

### Step 7 — Desktop visual check (optional)

```bash
ELECTRON_DISABLE_GPU=1 drawio docs/diagrams/full.drawio &
# Tab page 01: verify new edges don't overlap zones badly. Page 05 + 10: verify labels readable.
```

If edges route awkwardly, user can nudge in desktop UI (layout polish is user responsibility per README).

## Todo List

- [ ] Write `apply-visual-fixes.py`.
- [ ] Step 2 — actors + nginx-ns-2 recolor on page 01.
- [ ] Step 3 — add 5 edges to page 01.
- [ ] Step 4 — label 6 edges on page 05.
- [ ] Step 5 — label 6 edges on page 10.
- [ ] Step 6 — save, xmllint, count-assertion.
- [ ] Step 7 — (optional) desktop spot-check.

## Success Criteria

- [ ] Page 01 `actors` style contains `#F5F5F5` + `#666666`.
- [ ] Page 01 `nginx-ns-2` style contains `#FFE6CC` + `#D79B00`.
- [ ] Page 01 contains exactly 5 edge cells (`main-e1`..`main-e5`), each with non-empty `value=`.
- [ ] Page 05 edges `e3..e8` all have `value` ≠ empty.
- [ ] Page 10 edges `e2,e3,e4,e7,e8,e9` all have `value` ≠ empty.
- [ ] `xmllint --noout` pass.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| New edges on page 01 route through zones → visual mess | High | 🟢 Cosmetic | User responsibility to nudge in draw.io UI (per README note). |
| Cell ID typo in source/target → "broken edge" indicator | Low | 🟠 | Script uses `cell()` lookup before referencing; fails loud. |
| Palette hex changed but same-color appears elsewhere (global sub risk) | Low | 🟠 | Step 2 operates on specific cell's `style` attr only, not global text. |
| fontSize/labelBackgroundColor already present → duplicate keys | Low | 🟢 | Guard `if "fontSize=" not in st`. |

## Security Considerations

- None (cosmetic).

## Next Steps

- Phase 04: PNG export + README refresh (palette/naming/export).
