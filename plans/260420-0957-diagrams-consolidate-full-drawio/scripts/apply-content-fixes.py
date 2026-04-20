#!/usr/bin/env python3
"""Apply phase-02 content fixes to docs/diagrams/full.drawio.

1. Page 07 (RAG Pipeline): title + langchain cell — LangChain → RAGFlow.
2. Page 11 (Enhanced RAG Pipeline): composer cell — LangChain → RAGFlow.
3. Page 04 (CDC Data Flow): app-ns → app-oltp-ns (cell id + label + parent refs).
4. Page 08 (SSO Security Flow): rewrite s2 steps 7-12 + edge labels e6, e7.
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


# --- Page 07: RAG Pipeline ---
p07 = page("RAG Pipeline")
cell(p07, "title").set(
    "value",
    "Face Detection MLOps — RAG Pipeline (Ollama + Weaviate + RAGFlow)",
)
cell(p07, "langchain").set(
    "value",
    "RAGFlow\n(prompt composer)\ntemplate + context",
)

# --- Page 11: Enhanced RAG Pipeline ---
p11 = page("Enhanced RAG Pipeline")
cell(p11, "composer").set(
    "value",
    "RAGFlow\nPrompt Composer\n(system + context + Q)",
)

# --- Page 04: CDC Data Flow — app-ns → app-oltp-ns (page-scoped) ---
p04 = page("CDC Data Flow")
for c in p04.iter("mxCell"):
    if c.get("id") == "app-ns":
        c.set("id", "app-oltp-ns")
        c.set("value", "app-oltp-ns")
    if c.get("parent") == "app-ns":
        c.set("parent", "app-oltp-ns")

# --- Page 08: SSO Security Flow — steps 7-12 rewrite + edge labels ---
p08 = page("SSO Security Flow")
cell(p08, "s2").set(
    "value",
    "7. Keycloak issues authorization code\n"
    "8. Callback → OAuth2 Proxy exchanges code → JWT\n"
    "9. Proxy sets wildcard session cookie *.face-detect.dev\n"
    "10. Proxy redirects browser back to /app\n"
    "11. EnvoyFilter validates JWT (RS256) on each request\n"
    "12. Forward request with X-Auth-User claims header",
)
cell(p08, "e6").set("value", "8-9. Exchange code\n+ set cookie")
cell(p08, "e7").set("value", "10. Redirect\n12. Forward with claims")

tree.write(SRC, encoding="UTF-8", xml_declaration=False)
print(f"OK: applied content fixes to {SRC}")
