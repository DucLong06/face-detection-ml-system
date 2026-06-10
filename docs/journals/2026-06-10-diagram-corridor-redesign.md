# Diagram Corridor Redesign: Clean Vectors Built, Iteration Loop Proved Its Worth

**Date**: 2026-06-10 09:55
**Severity**: Low (shipping improvement)
**Component**: MLOps Diagrams, Architecture Visualization
**Status**: Resolved

## What Happened

Completed full redesign of MLOps architecture diagrams (1 overview + 7 drilldowns) using a new margin-corridor routing engine. Delivered 10 fresh outputs (PNG/SVG/drawio) with animatable waypoints baked into draw.io exports. Eliminated the spaghetti tangle of cross-zone edges through a disciplined left/right corridor strategy: retrain loop on left, deploy/features/telemetry on right. Zero MAJOR violations after 4 overview iterations + 2 subagent vision reviews on drilldowns.

## The Brutal Truth

The iteration loop was the real discovery. Initial instinct was to build perfect code, then render once. Instead, render-review-fix-repeat proved essential because visual design is *empirical*, not derivable. A corridor looks "clean" until you see the PNG and realize the labels pile up, or an edge intersects a zone title band.

Frustrating part: couldn't read diagrams directly due to image-read context cap — had to delegate vision reviews to subagents. This meant slower feedback cycles than ideally wanted, but forced discipline. Each review had to be explicit ("5 MAJOR found"), not vague ("looks off"). That precision actually caught real problems: edges passing through Model v2/Iter8 icons, hidden labels at Typesence, mTLS caption clipped.

The cramped zone-3 (Serving) nearly broke the layout. GE icons (KServe, Istio) are wide, vertical lanes saturated. Solved it by explicitly adding `rail_y` lanes to force edges around blockers instead of through them. That's a pattern worth remembering: when geometry gets tight, add structure early.

## Technical Details

**Corridor router** (`corridor_router.py`, ~210 LOC): margin-rail corridors with gutter routing, obstacle-aware horizontal lanes (`_free_rail`) + vertical columns with jogs (`_vleg`), centered stagger on same-row bows, blocked-row detours. Edge-level control via `corridor=` / `via=` / `rail_y=` options.

**Render engine** (`diagram_render_lib.py`, ~190 LOC): SVG/PNG/drawio emitters; node-label halos; edge labels on TOP layer with collision push-down; **drawio waypoints baked into `mxGeometry` point arrays** so PNG ↔ drawio route identically. `flowAnimation=1` on main numbered flow edges (1)→(10). Base64 icon cache + authoring guards (unknown node/rail raises clear error).

**Outputs**: 
- Overview: 58 edges, 25 animated, 4-iteration clean.
- Drilldowns (zone-1 through zone-7): 106 edges total, all waypointed, 0 regressions after round-2 vision pass.

**Iteration stats**: Overview 4 rounds (label halos, arrowhead centering, OpenMetadata repositioning, vector/keyword label nudge). Drilldowns 3 rounds; round 1 found 5 MAJOR → fixed via `rail_y` lanes + node moves → round 2: all PASS.

## What We Tried

1. **Direct hand-edit**: Rejected — pixel-control sounds clean until you realize it's unmaintainable vs builder.
2. **Edge numbering with off-page refs**: Rejected by user — requires mental joining, loses visual continuity.
3. **Zone reorder**: User explicitly rejected; corridors had to absorb long spans (prom→thanos, kserve→elk) instead.
4. **Single render pass**: Abandoned after first PNG review — visual feedback essential.

## Root Cause Analysis

Assumption that code correctness = visual correctness failed. Corridor routing can be algorithmically sound but visually tangled if label/icon collisions create visual noise. The fix: render-review loop with explicit checklists (no edges through node bodies, no interior crossings, labels staggered). Learned that schema ≠ layout; layout is empirical.

Secondary issue: drew.io waypoints originally absent from exports. Without baking coordinates into `mxGeometry` `<Array as="points">`, draw.io re-routed edges on open, breaking PNG fidelity. Fix: explicit waypoint XML generation + validation.

## Lessons Learned

1. **Visual iteration beats perfect code**: Render early, review often, fix visually first (coords), then codify (rail_y lanes, halos).
2. **Explicit constraints prevent tangling**: When zone-3 felt cramped, adding `rail_y=` lanes forced structure instead of hoping layout algorithms would find it.
3. **Image-read delegation is viable**: Couldn't read diagrams directly; delegating to subagent vision reviews with explicit "MAJOR / minor" scoring forced precision and caught real bugs.
4. **Icon geometry matters**: GE icons (KServe, Istio) are wide enough that they block lanes. Account for icon bounding boxes in corridor planning, not just node centers.
5. **Export fidelity requires baking**: Exporting to draw.io without waypoints = useless file. Bake everything upfront.

Pattern to export: margin corridors work for tangled cross-zone diagrams where reordering zones is off-limits. Left corridor for one highlight flow, right corridors for supporting flows.

## Impact

User can now iterate diagrams via `python3 newplans/diagrams/icons/overview_builder.py` and `drilldowns.py` without visual rework. PNG/SVG/drawio all route identically. README documents the corridor style and regeneration command. Diagrams are maintainable, not frozen artifacts.

No blockers to shipping; 5 untracked files + 10 diagram outputs ready for commit.

## Next Steps

1. Commit 5 py files + README + REGENERATE.md + 10 diagram outputs (user decision on timing).
2. Optional: cleanup stale diagrams under `plans/260604-2213-.../diagrams/` (scope creep; skip for now).
3. Old plans (`260420-1055`, `260604-2213`) remain unaffected; no blocking dependency.
