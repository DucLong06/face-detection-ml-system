# Regenerate icon diagrams

Requires: python `cairosvg` + `Pillow` (no graphviz needed — layout is hand-laid).

```bash
pip install --user --break-system-packages cairosvg pillow

# 1) prepare tool icons -> /tmp/icons/png/  (re-run after any /tmp wipe)
python3 prep_icons.py
python3 drilldown/prep_icons2.py
python3 rebuild_icons.py          # bundled logos + downloads + user logos (best quality, run last)

# 2) render
python3 overview_builder.py       # 01-overview.{png,svg,drawio}
python3 drilldown/drilldowns.py   # drilldown/zone-1..7-*.{png,svg,drawio}
```

Shared engine: `diagram_render_lib.py` (SVG/PNG/drawio emit, labels on top layer,
drawio waypoints baked + `flowAnimation=1` on main numbered edges) and
`corridor_router.py` (margin-rail corridors, gutter routing, obstacle-avoiding
jogs). Edit node coords / edges in the builder scripts; routing options per edge:
`corridor="rail-name"`, `via="above|below"` (blocked same-row detours),
`rail_y=<y>` (explicit lane for cramped zones).

> **Icon prep dependencies:** `rebuild_icons.py` additionally uses the `diagrams`
> pip package's bundled logo PNGs (auto-located) and downloads brand SVGs from
> jsDelivr — offline runs fall back to colored text tiles automatically.
