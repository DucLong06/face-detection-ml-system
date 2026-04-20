#!/usr/bin/env python3
"""Apply phase-03 visual fixes to docs/diagrams/full.drawio.

1. Page 01: recolor actors (neutral gray) + nginx-ns-2 (namespace orange).
2. Page 01: inject 5 main-flow edges (a1→gw5→ms1→st2/st3/trace1).
3. Page 05: label edges e3..e8.
4. Page 10: label edges e2,e3,e4,e7,e8,e9.
"""
import xml.etree.ElementTree as ET
from pathlib import Path

SRC = Path("docs/diagrams/full.drawio")
tree = ET.parse(SRC)
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


def graph_root(diagram):
    return diagram.find(".//root")


# --- Page 01: Full System Overview ---
p01 = page("Full System Overview")

# Actors zone recolor
actors = cell(p01, "actors")
st = actors.get("style")
st = st.replace("fillColor=#FFF2CC", "fillColor=#F5F5F5")
st = st.replace("strokeColor=#D6B656", "strokeColor=#666666")
actors.set("style", st)

# nginx-ns-2 recolor
nginx = cell(p01, "nginx-ns-2")
st = nginx.get("style")
st = st.replace("fillColor=#F8CECC", "fillColor=#FFE6CC")
st = st.replace("strokeColor=#B85450", "strokeColor=#D79B00")
nginx.set("style", st)

# Add 5 main-flow edges
EDGES_P01 = [
    ("main-e1", "a1",  "gw5",    "1. HTTPS",   False),
    ("main-e2", "gw5", "ms1",    "2. Route",   False),
    ("main-e3", "ms1", "st2",    "3. Persist", False),
    ("main-e4", "ms1", "st3",    "4. Cache",   False),
    ("main-e5", "ms1", "trace1", "Trace",      True),
]
g01 = graph_root(p01)
for eid, src, tgt, label, dashed in EDGES_P01:
    style = ("edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=classic;"
             "strokeWidth=2;fontSize=10;labelBackgroundColor=#ffffff;")
    if dashed:
        style += "dashed=1;"
    mx = ET.SubElement(g01, "mxCell", attrib={
        "id": eid, "value": label, "style": style,
        "edge": "1", "parent": "1", "source": src, "target": tgt,
    })
    ET.SubElement(mx, "mxGeometry", attrib={"relative": "1", "as": "geometry"})


# --- Page 05: ML Training Pipeline ---
p05 = page("ML Training Pipeline")
LABELS_05 = {
    "e3": "Preprocess", "e4": "Train", "e5": "Evaluate",
    "e6": "Promote",    "e7": "Export", "e8": "Canary",
}
for cid, lbl in LABELS_05.items():
    c = cell(p05, cid)
    c.set("value", lbl)
    st = c.get("style", "")
    if "fontSize=" not in st:
        st += "fontSize=10;"
    if "labelBackgroundColor=" not in st:
        st += "labelBackgroundColor=#ffffff;"
    c.set("style", st)


# --- Page 10: LLM Security Architecture ---
p10 = page("LLM Security Architecture")
LABELS_10 = {
    "e2": "Classify",     "e3": "Detect injection", "e4": "Toxicity in",
    "e7": "Ground check", "e8": "Allow/Block",      "e9": "Redact PII",
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


tree.write(SRC, encoding="UTF-8", xml_declaration=False)
print(f"OK: applied visual fixes to {SRC}")
