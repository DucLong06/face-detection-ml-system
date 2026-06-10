# Full-Card Visual Polish: Rate Limit Interrupted, Fan Offset Clamp Salvaged

**Date**: 2026-06-10 20:45
**Severity**: Low (shipping improvement)
**Component**: MLOps Overview Diagram, Card Node Styling
**Status**: Resolved (with session resume)

## What Happened

Built full-card node styling on top of the morning's corridor redesign. Delivered opt-in style flags (`cards`, `badges`, `zone_header`) gated by a new `svg_style_helpers.py` module. Verified byte-stable drilldown invariance (sorted-line diff identical across zone-1/3/6). Ran vision review: **0 MAJOR, "clean & professional"** verdict. Session halted mid-polish by rate limit; resumed, applied fan-offset clamp from code review feedback, re-rendered, confirmed.

## The Brutal Truth

The rate limit interruption was frustrating because it split a coherent polishing loop—render → review → fix → re-render. Midway through applying cosmetic fixes, token budget hit. Meant hand-off to continuation run felt choppy; the fan-offset clamp (clamping label offset to half-width of nodes) required jumping back into `corridor_router.py` logic when I'd mentally moved to docs. But the clamp *was* legit: code review caught that dynamic label width wasn't bounded, creating potential visual drift at wide nodes.

The invariance proof felt like defensive work—no user would notice if drilldowns drifted slightly—but it mattered because the engine flags *default to off*, and the guarantee that "turning them on doesn't touch drilldowns" is a contract. Verifying it cost 10 min of sorted-line diffing, but those 10 min prevent future confusion when someone asks "why does zone-4 look different?"

## Technical Details

**New module** `svg_style_helpers.py` (~75 LOC): `rounded_path()` (orthogonal arc bends with documented contract), `badge_label_svg()` (color circle + text), shadow filters.

**Flags** (default off, opt-in): `cards=True` → full white card (rounded r=10, feDropShadow). `badges=True` → `(N)` → colored circle + domain badge. `zone_header=True` → band at zone top (swimlane style drawio). Gated in `diagram_render_lib.py` via single emit path.

**Fan-offset clamp**: `cap` instance param set to 0 when label within card; label offset clamped to `half_width(node)` to prevent visual bleed at wide nodes. Verified via code review.

**Invariance proof**: Rendered zone-1/3/6 (smallest + 2 largest) drilldowns with flags off, sorted lines, diff vs baseline = 0. Semantic routing untouched.

**Vision review iteration 1**: SVG spot-check flagged "clean & professional", 0 MAJOR violations, 5 minor cosmetic (drift_score detour correct per corridor language, KServe junction readable, dash stack staggered). Fixes applied; iteration 2 re-render all PASS.

**Canvas re-space**: row pitch 116 (card 116×92 → min gap 75), canvas 2320×2300. All node coordinates rewrote in `overview_builder.py`.

## What We Tried

1. **Cosmetic polish without re-spacing**: Rejected early—card height (92px) > icon (56px), forcing row gap violation.
2. **Hand-tune all drilldown re-spacing too**: Rejected per user scope (overview only).
3. **Skip invariance check**: Rejected—opt-in flags without guardrails = future debt.

## Root Cause Analysis

Initial render passed vision review, but code review surfaced that label offset bound was unchecked. At wide nodes, dynamic offset could bleed past card edge. The fix (clamp to half-width) was surgical: 3 lines in `corridor_router.py`. But the lesson: visual correctness (iteration 1) ≠ structural correctness (code review). Code review caught a latent bug that vision review missed because vision works on *rendered* output, where clamping already happened due to SVG clipping. The invariance check mattered because it proved the engine change didn't cascade into unwanted drilldown edits.

Rate limit mid-polish meant continuation run; not ideal, but actually forced a clean separation: "polish complete → code review → apply fixes → re-verify." Coherence not lost, just async.

## Lessons Learned

1. **Opt-in style flags + invariance proof = reliable engine extension.** Flags default to off; verified drilldowns untouched. Future polishes (drilldowns, other diagrams) can reuse the engine without fear of silent breakage.
2. **Vision review + code review = complete filter.** Vision catches layout/clarity; code review catches bounds/contracts. Both needed.
3. **Rate limits aren't fatal—structure them as natural seams.** Polish → review → fixes is a natural break point. If interrupted, resume is straightforward.
4. **Sorted-line diffing is cheap insurance.** 10 min of verification = 0 future "why did this drift?" confusion.

## Impact

Overview diagram now has publish-grade card styling (full white cards, colored badges, zone headers, soft shadows). Drilldowns untouched; style engine ready for future phases. PNG/SVG/drawio all render consistently. No regressions.

Ready to commit on user signal. 5 Python files + README updated. 3 diagram outputs (01-overview.png/svg/drawio) re-rendered.

## Next Steps

1. User decision: commit 5 py + outputs, or iterate drilldowns now?
2. If iterate drilldowns: re-space each zone, run vision loop per zone, apply to all 7. Engine flags + corridor engine already proven; work is coordinate updates + visual reviews.
