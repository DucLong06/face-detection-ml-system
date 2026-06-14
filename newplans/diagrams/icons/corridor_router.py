"""Edge routing for swimlane diagrams with margin corridors.

Routing rules:
- corridor edge  -> exit top/bottom, horizontals only inside gutters, long
                    vertical run on the margin rail (circuit-board style).
- same-row edge  -> straight bow; if a third node blocks the row, detour
                    through the nearest gutter (or just outside the zone).
- cross-row edge -> one horizontal rail between the rows; the rail and both
                    vertical columns are obstacle-checked and shifted to free
                    space (with small jogs) so lines never cross node bodies.
"""
CAP = 26   # caption strip below an icon that lines must also avoid


class Router:
    def __init__(self, zones, nodes_wh, cap=CAP):
        """zones: [(x, y, w, h, ...)] ; nodes_wh: id -> (cx, cy, w, h);
        cap: extra clearance below nodes for external captions (0 = labels inside node)"""
        self.nwh = nodes_wh
        self.zones = zones
        self.cap = cap
        # horizontal gutter rails = vertical midpoints of gaps between zones
        self.gut = []
        zs = sorted(zones, key=lambda z: z[1])
        for a, b in zip(zs, zs[1:]):
            bot, top = a[1] + a[3], b[1]
            if top > bot:
                self.gut.append((bot + top) / 2)
        self.rails = {}
        self._use = {}           # stagger counters (rails / gutters / fans)

    def rail(self, name, x):
        self.rails[name] = x

    # ---- primitives ----
    def _anchor(self, nid):
        x, y, w, h = self.nwh[nid]
        return dict(x=x, y=y, w=w, h=h,
                    l=(x - w / 2, y), r=(x + w / 2, y),
                    t=(x, y - h / 2), b=(x, y + h / 2))

    def _stag(self, key, step):
        """centered spread: 0, -s, +s, -2s, +2s, ..."""
        n = self._use.get(key, 0)
        self._use[key] = n + 1
        return ((n + 1) // 2) * step * (-1 if n % 2 else 1) if n else 0

    def _gut_toward(self, y, down):
        cands = [g for g in self.gut if (g > y if down else g < y)]
        return (min(cands) if down else max(cands)) if cands else None

    def _fan(self, nid, side, pt):
        """spread arrows sharing one top/bottom anchor; clamped to the node
        half-width so the 6th+ edge on a side cannot land off the node body"""
        off = self._stag(f"fan.{nid}.{side}", 12)
        lim = self.nwh[nid][2] / 2 - 8
        return (pt[0] + max(-lim, min(lim, off)), pt[1])

    def _zone_edge(self, y, below):
        """outer edge of the zone stack containing y (for outside-zone detours)"""
        es = [z[1] + z[3] if below else z[1] for z in self.zones if z[1] - 6 <= y <= z[1] + z[3] + 6]
        base = (max(es) if below else min(es)) if es else y
        return base + 22 if below else base - 22

    # ---- obstacle checks ----
    def _blocked_h(self, y, x0, x1, skip, pad=12):
        lo, hi = min(x0, x1), max(x0, x1)
        for nid, (x, yy, w, h) in self.nwh.items():
            if nid in skip:
                continue
            if x - w / 2 - pad < hi and x + w / 2 + pad > lo and \
               yy - h / 2 - pad < y < yy + h / 2 + pad + self.cap:
                return True
        return False

    def _blocked_v(self, x, y0, y1, skip, pad=10):
        lo, hi = min(y0, y1), max(y0, y1)
        for nid, (xx, yy, w, h) in self.nwh.items():
            if nid in skip:
                continue
            if yy - h / 2 - pad < hi and yy + h / 2 + pad + self.cap > lo and \
               xx - w / 2 - pad < x < xx + w / 2 + pad:
                return True
        return False

    def _free_rail(self, y, x0, x1, lo, hi, skip):
        """free horizontal lane near y; search inside [lo,hi] first, then outside"""
        inside = [o for o in (0, -22, 22, -44, 44, -66, 66, -88, 88) if lo <= y + o <= hi]
        outside = [o for o in range(-44, -200, -22)] + [o for o in range(44, 200, 22)]
        for o in inside + [o for o in outside if not lo <= y + o <= hi]:
            if not self._blocked_h(y + o, x0, x1, skip):
                return y + o
        return y

    def _free_col(self, x, y0, y1, skip, clamp=None):
        """free vertical lane near x; optionally clamped to a node's width"""
        for o in (0, -30, 30, -60, 60, -90, 90, -130, 130):
            if clamp and abs(o) > clamp:
                continue
            if not self._blocked_v(x + o, y0, y1, skip):
                return x + o
        return x

    @staticmethod
    def _dedupe(pts):
        out = [pts[0]]
        for p in pts[1:]:
            if p != out[-1]:
                out.append(p)
        keep = [out[0]]
        for a, b, c in zip(out, out[1:], out[2:]):
            if not ((a[0] == b[0] == c[0]) or (a[1] == b[1] == c[1])):
                keep.append(b)
        keep.append(out[-1])
        return keep

    def _row_blocked(self, src, dst, a, b):
        lo, hi = min(a['x'], b['x']), max(a['x'], b['x'])
        band = (min(a['y'], b['y']) - 14, max(a['y'], b['y']) + 14)
        for nid, (x, y, w, h) in self.nwh.items():
            if nid in (src, dst):
                continue
            if lo < x < hi and not (y + h / 2 + 14 < band[0] or y - h / 2 - 14 > band[1]):
                return True
        return False

    # ---- vertical leg with obstacle-avoiding jog ----
    def _vleg(self, nid, pt, rail, skip):
        """points from a node's top/bottom anchor to the rail, jogging around
        any node parked in the column; returns list ending at (x, rail)"""
        x, y = pt
        if not self._blocked_v(x, y, rail, skip):
            return [pt, (x, rail)]
        a = self._anchor(nid)
        lane = self._free_col(x, y, rail, skip)
        jog = y + 12 if rail > y else y - 12
        return [pt, (x, jog), (lane, jog), (lane, rail)]

    # ---- main ----
    def route(self, src, dst, corridor=None, via=None, rail_y=None):
        a, b = self._anchor(src), self._anchor(dst)
        skip = {src, dst}
        if rail_y is not None:                 # explicit horizontal lane (cramped zones)
            g = rail_y + self._stag(f"gut.{round(rail_y)}", 10)
            ds, de = g > a['y'], g > b['y']
            start = self._fan(src, 'b' if ds else 't', a['b'] if ds else a['t'])
            end = self._fan(dst, 'b' if de else 't', b['b'] if de else b['t'])
            return self._dedupe(self._vleg(src, start, g, skip) + self._vleg(dst, end, g, skip)[::-1])
        if corridor:
            if corridor not in self.rails:
                raise ValueError(f"edge {src}->{dst}: corridor rail '{corridor}' not registered")
            rx = self.rails[corridor] + self._stag(f"rail.{corridor}", 9)
            down = b['y'] > a['y']
            g1 = self._gut_toward(a['y'], down)
            g2 = self._gut_toward(b['y'], not down)
            start = self._fan(src, 'b' if down else 't', a['b'] if down else a['t'])
            end = self._fan(dst, 't' if down else 'b', b['t'] if down else b['b'])
            if g1 is None:
                g1 = self._zone_edge(a['y'], down)
            one_gutter = g2 is None or abs(g2 - g1) < 20   # compare raw, stagger after
            g1 += self._stag(f"gut.{round(g1)}", 10)
            head = self._vleg(src, start, g1, skip)
            if one_gutter:                         # adjacent zones: one gutter is enough
                tail = self._vleg(dst, end, g1, skip)
                return self._dedupe(head + tail[::-1])
            g2 += self._stag(f"gut.{round(g2)}", 10)
            tail = self._vleg(dst, end, g2, skip)
            return self._dedupe(head + [(rx, g1), (rx, g2)] + tail[::-1])
        dx, dy = b['x'] - a['x'], b['y'] - a['y']
        row_blk = self._row_blocked(src, dst, a, b)
        if abs(dy) < 40 or (abs(dy) < 72 and abs(dx) > 120 and not row_blk):
            if not row_blk:
                p0, p1 = (a['r'], b['l']) if dx >= 0 else (a['l'], b['r'])
                mx = (p0[0] + p1[0]) / 2
                return self._dedupe([p0, (mx, p0[1]), (mx, p1[1]), p1])
            up = via != 'below'                # blocked row: detour via gutter
            g = self._gut_toward(min(a['y'], b['y']) if up else max(a['y'], b['y']), not up)
            if g is None:
                g = self._zone_edge(a['y'], not up)
            g += self._stag(f"gut.{round(g)}", 10)
            start = self._fan(src, 't' if up else 'b', a['t'] if up else a['b'])
            end = self._fan(dst, 't' if up else 'b', b['t'] if up else b['b'])
            return self._dedupe(self._vleg(src, start, g, skip) + self._vleg(dst, end, g, skip)[::-1])
        down = dy > 0
        start = self._fan(src, 'b' if down else 't', a['b'] if down else a['t'])
        end = self._fan(dst, 't' if down else 'b', b['t'] if down else b['b'])
        gs = self._gut_between(a['y'], b['y'])
        if gs:
            rail = (gs[0] if down else gs[-1]) + self._stag(f"gut.{round(gs[0] if down else gs[-1])}", 10)
        else:
            lo = min(start[1], end[1]) + 10
            hi = max(start[1], end[1]) - 10
            rail = self._free_rail((start[1] + end[1]) / 2, start[0], end[0], lo, hi, skip)
            rail += self._stag(f"band.{round(rail)}", 8)
        return self._dedupe(self._vleg(src, start, rail, skip) + self._vleg(dst, end, rail, skip)[::-1])

    def _gut_between(self, y0, y1):
        lo, hi = min(y0, y1), max(y0, y1)
        return [g for g in self.gut if lo < g < hi]


def label_xy(pts, corridor_edge=False):
    """Label sits on a horizontal segment: entry stub for corridor edges
    (the rail run itself stays clean), else the longest horizontal segment."""
    segs = [(p, q) for p, q in zip(pts, pts[1:]) if abs(q[1] - p[1]) < 2 and abs(q[0] - p[0]) > 8]
    if not segs:
        return pts[len(pts) // 2]
    seg = segs[-1] if corridor_edge else max(segs, key=lambda s: abs(s[1][0] - s[0][0]))
    (x0, y0), (x1, _) = seg
    return ((x0 + x1) / 2, y0)
