"""Shared renderer for swimlane diagrams: SVG + PNG + draw.io with baked
waypoints (draw.io shows the same routing as the PNG) and optional
flowAnimation on main-flow edges. Used by overview_builder.py and
drilldown/drilldowns.py."""
import base64
import html

import cairosvg

from corridor_router import Router, label_xy
from svg_style_helpers import SHADOW_FILTER, badge_label_svg, darken, rounded_path

_B64_CACHE = {}


def _b64(path):
    if path not in _B64_CACHE:
        _B64_CACHE[path] = base64.b64encode(open(path, "rb").read()).decode()
    return _B64_CACHE[path]


class Diagram:
    def __init__(self, W, H, title, zones, icon_dir="/tmp/icons/png",
                 iw=56, ih=56, aw=124, ah=54, subtitle="",
                 cards=False, badges=False, zone_header=False, corner_r=0,
                 card_h=92, card_icon=44, card_min_w=116, role_caption=False):
        self.W, self.H, self.title, self.zones = W, H, title, zones
        self.icon_dir, self.iw, self.ih, self.aw, self.ah = icon_dir, iw, ih, aw, ah
        # polished style (opt-in; default off keeps legacy output byte-stable)
        self.subtitle = subtitle
        self.cards, self.badges, self.zone_header, self.corner_r = cards, badges, zone_header, corner_r
        # card metrics are parametric so layouts can scale cards up; defaults
        # keep prior renders (drilldowns) pixel-identical
        self.card_h, self.card_icon, self.card_min_w = card_h, card_icon, card_min_w
        self.role_caption = role_caption  # line 1 bold name, lines 2+ gray role
        self.hl = {}      # id -> fill for highlighted cards (e.g. medallion tiers)
        self.nodes = {}   # id -> (x, y, kind, icon_or_fill, label)
        self.edges = []   # dicts
        self.legend_items, self.legend_pos = [], None
        self._router = None

    # ---- authoring API ----
    def icon(self, nid, x, y, icon, label, hl=None):
        self.nodes[nid] = (x, y, 'i', icon, label)
        if hl:
            self.hl[nid] = hl

    def card(self, nid, x, y, fill, label):
        """colored actor/source box (End User, data sources...) — distinct from
        the `cards=True` style flag, which turns ICON nodes into white cards"""
        self.nodes[nid] = (x, y, 'a', fill, label)

    def edge(self, src, dst, label="", color="#5b6472", dashed=False,
             corridor=None, main=False, width=None, via=None, rail_y=None):
        self.edges.append(dict(src=src, dst=dst, label=label, color=color,
                               dashed=dashed, corridor=corridor, main=main,
                               via=via, rail_y=rail_y, width=width or (2.6 if main else 1.6)))

    def rail(self, name, x):
        self._rails = getattr(self, "_rails", {})
        self._rails[name] = x

    def legend(self, items, x, y):
        """items: [(color, dashed, text)]"""
        self.legend_items, self.legend_pos = items, (x, y)

    # ---- geometry ----
    def _wh(self, nid):
        if nid not in self.nodes:
            raise ValueError(f"edge references unknown node id '{nid}'")
        x, y, k, _, label = self.nodes[nid]
        if k == 'i' and self.cards:
            w = max(self.card_min_w, max(len(ln) for ln in label.split("\n")) * 6.2 + 18)
            return (x, y, w, self.card_h)
        return (x, y, self.iw if k == 'i' else self.aw, self.ih if k == 'i' else self.ah)

    def _routed(self):
        r = Router(self.zones, {nid: self._wh(nid) for nid in self.nodes},
                   cap=0 if self.cards else 26)
        for name, x in getattr(self, "_rails", {}).items():
            r.rail(name, x)
        out = []
        for e in self.edges:
            out.append((e, r.route(e['src'], e['dst'], e['corridor'], e['via'], e['rail_y'])))
        return out

    def _zone_fill(self, yy):
        for x, y, w, h, t, fill, st in self.zones:
            if y <= yy <= y + h:
                return fill
        return "#ffffff"

    # ---- SVG / PNG ----
    def svg(self):
        bg = "#fafbfc" if self.cards else "#ffffff"
        L = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
             f'viewBox="0 0 {self.W} {self.H}" font-family="DejaVu Sans, Arial, sans-serif">',
             f'<rect width="{self.W}" height="{self.H}" fill="{bg}"/>', '<defs>']
        for c in sorted({e['color'] for e in self.edges}):   # sorted -> deterministic output
            L.append(f'<marker id="m{c.replace("#", "")}" markerWidth="9" markerHeight="7" refX="8" refY="3.5" '
                     f'orient="auto"><polygon points="0 0,9 3.5,0 7" fill="{c}"/></marker>')
        if self.cards:
            L.append(SHADOW_FILTER)
        L.append('</defs>')
        ty = 44 if self.subtitle else 40
        L.append(f'<text x="{self.W / 2}" y="{ty}" text-anchor="middle" font-size="30" font-weight="700" '
                 f'fill="#1f2937">{html.escape(self.title)}</text>')
        if self.subtitle:
            L.append(f'<text x="{self.W / 2}" y="72" text-anchor="middle" font-size="15" '
                     f'fill="#6b7280">{html.escape(self.subtitle)}</text>')
        for x, y, w, h, t, fill, st in self.zones:
            L.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" stroke="{st}" stroke-width="1.4"/>')
            if self.zone_header:
                hc = darken(st)
                L.append(f'<path d="M {x + 14},{y} H {x + w - 14} Q {x + w},{y} {x + w},{y + 14} V {y + 30} '
                         f'H {x} V {y + 14} Q {x},{y} {x + 14},{y} Z" fill="{hc}"/>')
                L.append(f'<text x="{x + 16}" y="{y + 21}" font-size="15" font-weight="700" '
                         f'fill="#ffffff">{html.escape(t)}</text>')
            else:
                L.append(f'<text x="{x + 16}" y="{y + 24}" font-size="16" font-weight="700" fill="#384150">{html.escape(t)}</text>')
        routed = self._routed()
        for e, pts in routed:
            da = ' stroke-dasharray="6,5"' if e['dashed'] else ''
            if self.corner_r:
                d = rounded_path(pts, self.corner_r)
                L.append(f'<path d="{d}" fill="none" stroke="{e["color"]}" stroke-width="{e["width"]}"{da} '
                         f'stroke-linejoin="round" marker-end="url(#m{e["color"].replace("#", "")})"/>')
            else:
                path = " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)
                L.append(f'<polyline points="{path}" fill="none" stroke="{e["color"]}" stroke-width="{e["width"]}"{da} '
                         f'stroke-linejoin="round" marker-end="url(#m{e["color"].replace("#", "")})"/>')
        for nid, (x, y, k, ic, label) in self.nodes.items():
            if k == 'i' and self.cards:
                _, _, cw, ch = self._wh(nid)
                lines = label.split("\n")
                fill = self.hl.get(nid, "#ffffff")
                stroke = darken(self.hl[nid]) if nid in self.hl else "#dfe3ea"
                L.append(f'<rect x="{x - cw / 2:.0f}" y="{y - ch / 2:.0f}" width="{cw:.0f}" height="{ch}" rx="10" '
                         f'fill="{fill}" stroke="{stroke}" stroke-width="1" filter="url(#cardshadow)"/>')
                isz = self.card_icon
                # isz // 2 keeps the old int/float emission semantics so legacy
                # renders (drilldowns) stay byte-identical at the default size
                L.append(f'<image x="{x - isz // 2}" y="{y - ch / 2 + 8:.0f}" width="{isz}" height="{isz}" '
                         f'xlink:href="data:image/png;base64,{_b64(f"{self.icon_dir}/{ic}.png")}"/>')
                ty0 = y - ch / 2 + isz + 20 + (6 if len(lines) == 1 else 0)
                for i, ln in enumerate(lines):
                    if self.role_caption:        # bold name line + gray role caption lines
                        fs, fw, fc = (11.5, 700, "#1f2937") if i == 0 else (9.5, 500, "#6b7280")
                        L.append(f'<text x="{x}" y="{ty0 + i * 13:.0f}" text-anchor="middle" '
                                 f'font-size="{fs}" font-weight="{fw}" fill="{fc}">{html.escape(ln)}</text>')
                    else:                        # legacy uniform lines (drilldowns)
                        L.append(f'<text x="{x}" y="{ty0 + i * 12:.0f}" text-anchor="middle" '
                                 f'font-size="10.5" font-weight="600" fill="#2b3240">{html.escape(ln)}</text>')
            elif k == 'i':
                L.append(f'<image x="{x - self.iw / 2}" y="{y - self.ih / 2}" width="{self.iw}" height="{self.ih}" '
                         f'xlink:href="data:image/png;base64,{_b64(f"{self.icon_dir}/{ic}.png")}"/>')
                for i, ln in enumerate(label.split("\n")):
                    ty = y + self.ih / 2 + 13 + i * 12
                    wd = len(ln) * 6.2 + 6   # halo so crossing lines hide behind the text
                    L.append(f'<rect x="{x - wd / 2:.0f}" y="{ty - 10:.0f}" width="{wd:.0f}" height="13" rx="2" '
                             f'fill="{self._zone_fill(y)}" opacity="0.93"/>')
                    L.append(f'<text x="{x}" y="{ty:.0f}" text-anchor="middle" '
                             f'font-size="10.5" font-weight="600" fill="#2b3240">{html.escape(ln)}</text>')
            else:
                shadow = ' filter="url(#cardshadow)"' if self.cards else ''
                rx = 10 if self.cards else 9       # keep legacy output byte-stable
                L.append(f'<rect x="{x - self.aw / 2}" y="{y - self.ah / 2}" width="{self.aw}" height="{self.ah}" rx="{rx}" '
                         f'fill="{ic}" stroke="#8a93a3" stroke-width="1.3"{shadow}/>')
                lines = label.split("\n")
                y0 = y - (len(lines) - 1) * 7
                for i, ln in enumerate(lines):
                    L.append(f'<text x="{x}" y="{y0 + i * 14 + 4:.0f}" text-anchor="middle" font-size="11" '
                             f'font-weight="700" fill="#2b3240">{html.escape(ln)}</text>')
        placed = []                                 # edge labels on the very top layer
        for e, pts in routed:
            if not e['label']:
                continue
            mx, my = label_xy(pts, bool(e['corridor']))
            wd = len(e['label']) * 6.4 + 10 + (14 if self.badges else 0)
            while any(abs(my - py) < 15 and abs(mx - px) < (wd + pw) / 2 for px, py, pw in placed):
                my += 16
            placed.append((mx, my, wd))
            if self.badges:
                frag, _ = badge_label_svg(mx, my, e['label'], e['color'], self._zone_fill(my))
                L.append(frag)
            else:
                L.append(f'<rect x="{mx - wd / 2:.0f}" y="{my - 9:.0f}" width="{wd:.0f}" height="15" rx="3" '
                         f'fill="{self._zone_fill(my)}" opacity="0.92"/>')
                L.append(f'<text x="{mx:.0f}" y="{my + 3:.0f}" text-anchor="middle" font-size="11" font-weight="600" '
                         f'fill="{e["color"]}">{html.escape(e["label"])}</text>')
        if self.legend_items:
            lx, ly = self.legend_pos
            lh = 20 * len(self.legend_items) + 16
            lw = 78 + max(len(t) for _, _, t in self.legend_items) * 6.6
            L.append(f'<rect x="{lx}" y="{ly}" width="{lw:.0f}" height="{lh}" rx="8" fill="#ffffff" stroke="#9aa4b2" stroke-width="1"/>')
            for i, (c, dashed, txt) in enumerate(self.legend_items):
                yy = ly + 18 + i * 20
                da = ' stroke-dasharray="6,5"' if dashed else ''
                L.append(f'<line x1="{lx + 12}" y1="{yy}" x2="{lx + 52}" y2="{yy}" stroke="{c}" stroke-width="2.4"{da}/>')
                L.append(f'<text x="{lx + 60}" y="{yy + 4}" font-size="11.5" fill="#2b3240">{html.escape(txt)}</text>')
        L.append('</svg>')
        return "\n".join(L)

    def write(self, outbase, png_width=2400, drawio_name=None):
        s = self.svg()
        open(f"{outbase}.svg", "w").write(s)
        cairosvg.svg2png(bytestring=s.encode(), write_to=f"{outbase}.png", output_width=png_width)
        open(f"{outbase}.drawio", "w").write(self.drawio(drawio_name or outbase.rsplit("/", 1)[-1]))

    # ---- draw.io (waypoints baked so it matches the PNG) ----
    def drawio(self, name):
        cells = ['<mxCell id="0"/>', '<mxCell id="1" parent="0"/>']
        cid, ref = 2, {}
        for x, y, w, h, t, fill, st in self.zones:
            if self.zone_header:
                zstyle = (f"swimlane;startSize=30;rounded=1;fontSize=15;fontStyle=1;fontColor=#ffffff;"
                          f"fillColor={darken(st)};swimlaneFillColor={fill};strokeColor={st};horizontal=1;")
            else:
                zstyle = (f"rounded=1;fillColor={fill};strokeColor={st};verticalAlign=top;align=left;"
                          f"spacingLeft=14;spacingTop=6;fontSize=15;fontStyle=1;")
            cells.append(f'<mxCell id="z{cid}" value="{html.escape(t)}" style="{zstyle}" vertex="1" parent="1">'
                         f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
            cid += 1
        for nid, (x, y, k, ic, label) in self.nodes.items():
            ref[nid] = f"n{cid}"
            lbl = html.escape(label.replace(chr(10), " "))
            if k == 'i' and self.cards:
                _, _, cw, ch = self._wh(nid)
                cfill = self.hl.get(nid, "#ffffff")
                cstroke = darken(self.hl[nid]) if nid in self.hl else "#dfe3ea"
                style = (f"rounded=1;fillColor={cfill};strokeColor={cstroke};shadow=1;"
                         f"image=data:image/png,{_b64(f'{self.icon_dir}/{ic}.png')};"
                         f"imageWidth={self.card_icon};imageHeight={self.card_icon};imageAlign=center;imageVerticalAlign=top;"
                         f"verticalAlign=bottom;spacingBottom=8;fontSize=10;fontStyle=1;whiteSpace=wrap;")
                cells.append(f'<mxCell id="{ref[nid]}" value="{lbl}" style="{style}" vertex="1" parent="1">'
                             f'<mxGeometry x="{x - cw / 2:.0f}" y="{y - ch / 2:.0f}" width="{cw:.0f}" height="{ch}" as="geometry"/></mxCell>')
            elif k == 'i':
                style = (f"shape=image;verticalLabelPosition=bottom;verticalAlign=top;imageAspect=0;"
                         f"image=data:image/png,{_b64(f'{self.icon_dir}/{ic}.png')};fontSize=10;")
                cells.append(f'<mxCell id="{ref[nid]}" value="{lbl}" style="{style}" vertex="1" parent="1">'
                             f'<mxGeometry x="{x - self.iw / 2}" y="{y - self.ih / 2}" width="{self.iw}" height="{self.ih}" as="geometry"/></mxCell>')
            else:
                shadow = "shadow=1;" if self.cards else ""
                cells.append(f'<mxCell id="{ref[nid]}" value="{lbl}" style="rounded=1;fillColor={ic};strokeColor=#8a93a3;'
                             f'{shadow}fontSize=11;fontStyle=1;whiteSpace=wrap;" vertex="1" parent="1">'
                             f'<mxGeometry x="{x - self.aw / 2}" y="{y - self.ah / 2}" width="{self.aw}" height="{self.ah}" as="geometry"/></mxCell>')
            cid += 1
        for e, pts in self._routed():
            (sx, sy, sw, sh), (tx, ty, tw, th) = self._wh(e['src']), self._wh(e['dst'])
            ex = (pts[0][0] - (sx - sw / 2)) / sw
            ey = (pts[0][1] - (sy - sh / 2)) / sh
            nx = (pts[-1][0] - (tx - tw / 2)) / tw
            ny = (pts[-1][1] - (ty - th / 2)) / th
            anim = "flowAnimation=1;" if e['main'] else ""
            da = "dashed=1;" if e['dashed'] else ""
            style = (f"edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor={e['color']};strokeWidth={e['width']};"
                     f"{da}{anim}fontSize=10;endArrow=block;html=1;"
                     f"exitX={ex:.3f};exitY={ey:.3f};exitDx=0;exitDy=0;entryX={nx:.3f};entryY={ny:.3f};entryDx=0;entryDy=0;")
            way = "".join(f'<mxPoint x="{x:.0f}" y="{y:.0f}"/>' for x, y in pts[1:-1])
            cells.append(f'<mxCell id="e{cid}" value="{html.escape(e["label"])}" style="{style}" edge="1" parent="1" '
                         f'source="{ref[e["src"]]}" target="{ref[e["dst"]]}">'
                         f'<mxGeometry relative="1" as="geometry"><Array as="points">{way}</Array></mxGeometry></mxCell>')
            cid += 1
        model = (f'<mxGraphModel dx="1600" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" '
                 f'arrows="1" fold="1" page="1" pageScale="1" pageWidth="{self.W}" pageHeight="{self.H}">'
                 f'<root>{"".join(cells)}</root></mxGraphModel>')
        return f'<mxfile host="app.diagrams.net"><diagram name="{html.escape(name)}" id="{html.escape(name)}">{model}</diagram></mxfile>'
