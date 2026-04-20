#!/usr/bin/env python3
"""Merge 11 single-page .drawio files into docs/diagrams/full.drawio."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

DIAG_DIR = Path("docs/diagrams")
ORDER = [
    "01-full-system-overview.drawio",
    "02-batch-data-flow.drawio",
    "03-stream-data-flow.drawio",
    "04-cdc-data-flow.drawio",
    "05-ml-training-pipeline.drawio",
    "06-model-serving.drawio",
    "07-rag-pipeline.drawio",
    "08-sso-security-flow.drawio",
    "09-drift-detection.drawio",
    "10-llm-security-architecture.drawio",
    "11-enhanced-rag-pipeline.drawio",
]
OUT = DIAG_DIR / "full.drawio"


def main():
    root = ET.Element("mxfile", attrib={
        "host": "app.diagrams.net",
        "agent": "Claude",
        "type": "device",
        "compressed": "false",
        "version": "22.1.0",
    })
    for fname in ORDER:
        fpath = DIAG_DIR / fname
        if not fpath.exists():
            sys.exit(f"FAIL: source missing: {fpath}")
        src_tree = ET.parse(fpath)
        src_root = src_tree.getroot()
        diagrams = src_root.findall("diagram")
        if len(diagrams) != 1:
            sys.exit(f"FAIL: {fname} has {len(diagrams)} diagrams (expected 1)")
        root.append(diagrams[0])
    ET.indent(root, space="  ", level=0)
    tree = ET.ElementTree(root)
    tree.write(OUT, encoding="UTF-8", xml_declaration=False)
    print(f"OK: wrote {OUT} with {len(root.findall('diagram'))} pages")


if __name__ == "__main__":
    main()
