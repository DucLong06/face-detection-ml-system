# Phase 02 — Content Fixes: RAGFlow Rename + `app-oltp-ns` + SSO 12-Step

## Context Links

- Brainstorm: `plans/reports/brainstorm-260420-0957-diagrams-consolidate-full-drawio.md` §5.2 (items 1–3), §5.4
- Review: `newreview.md` Items 7.1 (RAGFlow), 7.2 (app-ns), 7.3 (SSO step 11)
- NEW_PLANS: `NEW_PLANS.md` §5.2 (SSO 12-step @ lines 609–636), §7 (namespace breakdown)
- Target file: `docs/diagrams/full.drawio` (from phase 01)
- Target file: `NEW_PLANS.md` (§7 add row)

## Overview

- Priority: P2
- Status: pending
- Description: 3 content corrections applied to merged `full.drawio` + 1 NEW_PLANS update. All textual — no layout change.

## Key Insights

- Page 07 `title` and `langchain` cell both say "LangChain" — rename to "RAGFlow" (cell `id="langchain"` kept for edge-ref stability; only `value=` changes).
- Page 11 `composer` cell says "LangChain Prompt Composer" — rename to "RAGFlow Prompt Composer".
- Page 01 title says `... LangChain ...`? Re-check: line 7 = `Full System Overview (16 Namespaces · L1 + L2 + L3 + RAG + SSO)` — no LangChain. `rag2` cell already labeled `RAGFlow`. **No change needed on page 01**; only 07 + 11.
- Page 04 cell `id="app-ns"` with `value="app-ns (OLTP)"` — rename `id` → `app-oltp-ns`, `value` → `app-oltp-ns (OLTP)`. No edges reference `app-ns` as source/target (verified — edges use `app-pg`, `wal`, etc.). Parent refs on children use literal string `"app-ns"` → must rewrite.
- Page 08 cells `s1` and `s2` contain the 12 SSO steps as multi-line text inside `value="..."`. Current step 11 = "Set wildcard cookie" (wrong). NEW_PLANS §5.2 order: step 9=set cookie; step 10=redirect to /app; step 11=EnvoyFilter validates JWT; step 12=forward request with claims.
- NEW_PLANS §7 namespace list: add line for `app-oltp-ns`.

## Requirements

### Functional
- R1. Page 07: "LangChain" → "RAGFlow" in both title (line 7 `value="..."`) and `langchain` cell `value=`.
- R2. Page 11: "LangChain" → "RAGFlow" in `composer` cell `value=`.
- R3. Page 04: cell `id="app-ns"` → `id="app-oltp-ns"`; `value="app-ns (OLTP)"` → `value="app-oltp-ns"`. Children with `parent="app-ns"` → `parent="app-oltp-ns"`.
- R4. Page 08: rewrite `s1` cell (steps 1–6) and `s2` cell (steps 7–12) to match NEW_PLANS §5.2 step numbering. Edge labels `e7` (currently "11-12. Forward...") must not refer to obsolete numbers — rewrite to "10. Redirect / 12. Forward".
- R5. `NEW_PLANS.md` §7 add row `app-oltp-ns ← Application OLTP DB (PostgreSQL logical replication source)`.

### Non-functional
- NF1. XML still well-formed (`xmllint --noout` pass).
- NF2. All replacements scoped to the correct page — NO global sed on `app-ns` (string appears elsewhere as substring in e.g., `auth-ns`, `rag-ns` — must use exact token match with word boundaries / quotes).

## Architecture — Change Strategy

- Use **Python ElementTree** rather than sed because:
  - `app-ns` vs `auth-ns`/`rag-ns`/`app-pg` conflict risk with plain string replace.
  - Page-scoped changes require `<diagram name="...">` targeting.
  - `parent="app-ns"` attr update needs attr-level rewrite, not string swap.
- Page 08 step text is multi-line via `&#xa;` entity — preserve entity encoding in Python string literal.

## Related Code Files

**Modify**
- `/mnt/data/mlops/Long-project/face-detect-gke/docs/diagrams/full.drawio`
- `/mnt/data/mlops/Long-project/face-detect-gke/NEW_PLANS.md`

**Create**
- `/mnt/data/mlops/Long-project/face-detect-gke/plans/260420-0957-diagrams-consolidate-full-drawio/scripts/apply-content-fixes.py`

## Implementation Steps

### Step 1 — RAGFlow rename (pages 07 + 11)

Script section:
```python
import xml.etree.ElementTree as ET
tree = ET.parse("docs/diagrams/full.drawio")
root = tree.getroot()

def page(name):
    for d in root.findall("diagram"):
        if d.get("name") == name:
            return d
    raise KeyError(name)

def cell(diagram, cid):
    for c in diagram.iter("mxCell"):
        if c.get("id") == cid:
            return c
    raise KeyError(cid)

# Page 07
p07 = page("RAG Pipeline")
cell(p07, "title").set("value",
    "Face Detection MLOps — RAG Pipeline (Ollama + Weaviate + RAGFlow)")
cell(p07, "langchain").set("value",
    "RAGFlow&#xa;(prompt composer)&#xa;template + context")
# Note: keep cell id="langchain" to avoid edge-ref rewrites.
# Edges e4 (target=langchain), e5 (source=langchain), e7 (source=langchain) unchanged.

# Page 11
p11 = page("Enhanced RAG Pipeline")
cell(p11, "composer").set("value",
    "RAGFlow&#xa;Prompt Composer&#xa;(system + context + Q)")
```

**Before/after** (page 07 `langchain` cell):
```xml
<!-- BEFORE -->
<mxCell id="langchain" value="LangChain&#xa;(prompt composer)&#xa;template + context" ...>
<!-- AFTER -->
<mxCell id="langchain" value="RAGFlow&#xa;(prompt composer)&#xa;template + context" ...>
```

### Step 2 — `app-ns` → `app-oltp-ns` (page 04)

```python
# Page 04
p04 = page("CDC Data Flow")
for c in p04.iter("mxCell"):
    if c.get("id") == "app-ns":
        c.set("id", "app-oltp-ns")
        c.set("value", "app-oltp-ns")  # label
    if c.get("parent") == "app-ns":
        c.set("parent", "app-oltp-ns")
```

**Before/after**:
```xml
<!-- BEFORE -->
<mxCell id="app-ns" value="app-ns (OLTP)" style="swimlane;..." parent="1">
<mxCell id="app-pg" ... parent="app-ns">
<mxCell id="wal"    ... parent="app-ns">
<!-- AFTER -->
<mxCell id="app-oltp-ns" value="app-oltp-ns" style="swimlane;..." parent="1">
<mxCell id="app-pg" ... parent="app-oltp-ns">
<mxCell id="wal"    ... parent="app-oltp-ns">
```

Verification:
```bash
grep -c '"app-ns"' docs/diagrams/full.drawio
# expected: 0 on page 04 (page 08 has id="app-ns" DIFFERENT cell — for the "target app (any ns)" swimlane. Must NOT rename that one.)
```

**Important gotcha:** Page 08 also has `<mxCell id="app-ns" value="target app (any ns)" ...>`. That's a **different semantic** (generic target-app ns on SSO page), and must NOT be renamed. Scope rename strictly to page 04 via ElementTree per-page targeting.

### Step 3 — SSO 12-step rewrite (page 08)

Current `s1` steps 1–6 already correct per NEW_PLANS (1. request → 6. submit creds). Keep as-is.

Current `s2` (steps 7–12) — rewrite:
```python
p08 = page("SSO Security Flow")
cell(p08, "s2").set("value",
    "7. Keycloak issues authorization code&#xa;"
    "8. Callback → OAuth2 Proxy exchanges code → JWT&#xa;"
    "9. Proxy sets wildcard session cookie *.face-detect.dev&#xa;"
    "10. Proxy redirects browser back to /app&#xa;"
    "11. EnvoyFilter validates JWT (RS256) on each request&#xa;"
    "12. Forward request with X-Auth-User claims header"
)
# Also fix edge e7 label (currently "11-12. Forward..." → "10+12. Redirect & Forward")
cell(p08, "e7").set("value",
    "10. Redirect&#xa;12. Forward with claims"
)
# Edge e6 (currently "8-10. Token exchange + JWT verify") → "8-9. Exchange + set cookie"
cell(p08, "e6").set("value",
    "8-9. Exchange code&#xa;+ set cookie"
)
```

**Before/after** (`s2`):
```
BEFORE:                                  AFTER:
7. Keycloak issues authorization code    7. Keycloak issues authorization code
8. Callback → OAuth2 Proxy               8. Callback → OAuth2 Proxy exchanges code → JWT
9. Proxy exchanges code → access token   9. Proxy sets wildcard session cookie *.face-detect.dev
10. Verify JWT signature (RS256)         10. Proxy redirects browser back to /app
11. Set wildcard cookie *.face-detect.dev 11. EnvoyFilter validates JWT (RS256) on each request
12. Forward request with X-Auth-User header 12. Forward request with X-Auth-User claims header
```

### Step 4 — Save and validate

```python
tree.write("docs/diagrams/full.drawio", encoding="UTF-8", xml_declaration=False)
```

```bash
xmllint --noout docs/diagrams/full.drawio && echo "XML OK"
# Ensure no LangChain residual in pages 07/11:
grep -c "LangChain" docs/diagrams/full.drawio
# Expected: 0 (page 01 already uses "RAGFlow"; pages 07+11 now fixed)
# Ensure app-oltp-ns applied on page 04 ONLY:
grep -c '"app-oltp-ns"' docs/diagrams/full.drawio
# Expected: ≥4 (1 id on swimlane + 2 parent refs on children + 1 label repeat in value)
```

### Step 5 — NEW_PLANS.md §7 add row

Locate §7 namespace table/list (lines ~640–700 per context — verify offset). Add:

```markdown
- `app-oltp-ns` — Application OLTP DB (PostgreSQL wal_level=logical; Debezium logical replication source; see diagram 04 CDC Data Flow).
```

Use Edit tool (not sed) to insert just after the existing `app-ns` or nearest matching row.

## Todo List

- [ ] Write `apply-content-fixes.py` script.
- [ ] Step 1 — RAGFlow rename on pages 07 + 11.
- [ ] Step 2 — `app-ns` → `app-oltp-ns` on page 04 (scoped).
- [ ] Step 3 — SSO page 08 steps 7–12 rewrite + edge labels e6, e7.
- [ ] Step 4 — save, xmllint, grep residuals.
- [ ] Step 5 — NEW_PLANS.md §7 add `app-oltp-ns` row.

## Success Criteria

- [ ] `grep -c LangChain docs/diagrams/full.drawio` → `0`.
- [ ] Page 04 has `id="app-oltp-ns"`, page 08 still has `id="app-ns"` (generic target).
- [ ] Page 08 step 11 text contains exactly "EnvoyFilter validates JWT".
- [ ] `NEW_PLANS.md` §7 contains `app-oltp-ns` bullet.
- [ ] `xmllint --noout` pass.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Global sed on `app-ns` corrupts page 08 target-app swimlane | Medium | 🟠 | Use page-scoped ET; explicit test that page 08 still has `id="app-ns"`. |
| `&#xa;` entity double-escaped after ET.write | Low | 🟠 Layout | ET preserves `&#xa;` as numeric char ref → draw.io decodes to newline. Verify by opening desktop. |
| Edge label rewrite breaks edge routing | Low | 🟢 | Only `value=` changes; `source=`/`target=` untouched. |
| NEW_PLANS §7 offset drift from prompt context | Medium | 🟢 | Use grep/Edit on anchor text (`app-ns` or `storage-ns`) rather than line number. |

## Security Considerations

- No secrets in diagram text. No impact.

## Next Steps

- Phase 03: palette recolors + page 01 main-flow edges + page 05/10 edge labels.
