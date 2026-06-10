"""SVG helpers for the polished (hall-of-fame) diagram style:
rounded-corner edge paths, numbered circle badges, card shadow filter."""
import html
import re

BADGE_RE = re.compile(r"^\((\d+[a-z]?)\)\s*(.*)$")

SHADOW_FILTER = ('<filter id="cardshadow" x="-30%" y="-30%" width="160%" height="160%">'
                 '<feDropShadow dx="0" dy="1.5" stdDeviation="2.5" flood-color="#1f2937" flood-opacity="0.18"/>'
                 '</filter>')


def rounded_path(pts, r):
    """polyline points -> SVG path d with arcs of radius r at each bend.
    Contract: segments MUST be axis-aligned (the router's _dedupe guarantees
    orthogonal bends); a diagonal segment would place arc endpoints off-line."""
    if len(pts) < 3 or r <= 0:
        return "M " + " L ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
    d = [f"M {pts[0][0]:.0f},{pts[0][1]:.0f}"]
    for prev, cur, nxt in zip(pts, pts[1:], pts[2:]):
        l1 = abs(cur[0] - prev[0]) + abs(cur[1] - prev[1])
        l2 = abs(nxt[0] - cur[0]) + abs(nxt[1] - cur[1])
        rr = min(r, l1 / 2, l2 / 2)
        if rr < 1:                      # bend too tight: plain corner
            d.append(f"L {cur[0]:.0f},{cur[1]:.0f}")
            continue
        ux1 = 0 if cur[0] == prev[0] else (1 if cur[0] > prev[0] else -1)
        uy1 = 0 if cur[1] == prev[1] else (1 if cur[1] > prev[1] else -1)
        ux2 = 0 if nxt[0] == cur[0] else (1 if nxt[0] > cur[0] else -1)
        uy2 = 0 if nxt[1] == cur[1] else (1 if nxt[1] > cur[1] else -1)
        a = (cur[0] - ux1 * rr, cur[1] - uy1 * rr)
        b = (cur[0] + ux2 * rr, cur[1] + uy2 * rr)
        d.append(f"L {a[0]:.0f},{a[1]:.0f} Q {cur[0]:.0f},{cur[1]:.0f} {b[0]:.0f},{b[1]:.0f}")
    d.append(f"L {pts[-1][0]:.0f},{pts[-1][1]:.0f}")
    return " ".join(d)


def badge_label_svg(mx, my, label, color, halo_fill):
    """edge label rendered as colored circle badge (step number) + text.
    Returns (svg_fragment, total_width). Falls back to plain text when the
    label has no (N)/(Nx) step prefix."""
    m = BADGE_RE.match(label)
    out = []
    if not m:
        wd = len(label) * 6.4 + 10
        out.append(f'<rect x="{mx - wd / 2:.0f}" y="{my - 9:.0f}" width="{wd:.0f}" height="15" rx="3" '
                   f'fill="{halo_fill}" opacity="0.92"/>')
        out.append(f'<text x="{mx:.0f}" y="{my + 3:.0f}" text-anchor="middle" font-size="11" '
                   f'font-weight="600" fill="{color}">{html.escape(label)}</text>')
        return "".join(out), wd
    num, rest = m.group(1), m.group(2)
    tw = len(rest) * 6.6 + (8 if rest else 0)
    total = 22 + tw
    bx = mx - total / 2 + 10                       # badge circle center
    if rest:
        out.append(f'<rect x="{bx + 10:.0f}" y="{my - 9:.0f}" width="{tw:.0f}" height="15" rx="3" '
                   f'fill="{halo_fill}" opacity="0.92"/>')
    out.append(f'<circle cx="{bx:.0f}" cy="{my:.0f}" r="10" fill="{color}" stroke="#ffffff" stroke-width="1.6"/>')
    fs = 9.5 if len(num) <= 1 else 8
    out.append(f'<text x="{bx:.0f}" y="{my + 3:.0f}" text-anchor="middle" font-size="{fs}" '
               f'font-weight="700" fill="#ffffff">{html.escape(num)}</text>')
    if rest:
        out.append(f'<text x="{bx + 16:.0f}" y="{my + 3:.0f}" text-anchor="start" font-size="11" '
                   f'font-weight="600" fill="{color}">{html.escape(rest)}</text>')
    return "".join(out), total


def darken(hex_color, f=0.82):
    """darken a #rrggbb color for zone header bands"""
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return f"#{int(r * f):02x}{int(g * f):02x}{int(b * f):02x}"
