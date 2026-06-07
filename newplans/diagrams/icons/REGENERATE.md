# Regenerate icon diagrams

Requires: python `diagrams` lib + system `dot` (graphviz) + `cairosvg` (for icon prep).

```bash
pip install --user --break-system-packages diagrams cairosvg
# graphviz binary: apt-get install graphviz  (or extract .deb locally if no sudo)

# 1) prepare custom tool icons -> /tmp/icons/png/
python3 prep_icons.py
# 2) render (ensure `dot` on PATH, GVBINDIR set to graphviz plugin dir)
python3 diag_overview.py     # 01-overview.png
python3 diag_sections.py     # 02..07 *.png
```

Edit the `cust()`/`Cluster()`/`Edge()` calls to adjust nodes, groups, labels, colors.
Icons: built-in via `diagrams.onprem.*`; custom logos in `/tmp/icons/png/*.png` (brand-colored simple-icons or text fallback).
