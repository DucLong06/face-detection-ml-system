# Face Detection MLOps — Architecture Diagrams (DEPRECATED)

> **2026-05-21**: This drawio-based folder is **deprecated**. Active diagrams migrated to D2 at `docs/diagrams-d2/`. This folder kept for audit trail until v0.2 release.
>
> **Scope cut**: pages 07 (RAG Pipeline), 10 (LLM Security), 11 (Enhanced RAG) removed per YAGNI audit. See [docs/archive/cut-components-v0.1.md](../archive/cut-components-v0.1.md).

Draw.io source files + style guide cho 8 architecture diagrams (MLOps L1+L2+L3+SSO, RAG cut).

## How to edit

**VSCode**: install extension `hediet.vscode-drawio`, open any `.drawio` file.
**Desktop**: install `drawio-desktop` from https://github.com/jgraph/drawio-desktop/releases.
**Web**: https://app.diagrams.net/ → Open from Device.

## How to export PNG

**CLI (preferred, deterministic):**

```bash
cd docs/diagrams
# Multi-page export — one PNG per page (drawio v29 requires -p <idx> per page):
for i in 1 2 3 4 5 6 7 8 9 10 11; do
  OUT=$(printf 'full-%02d.png' $i)
  ELECTRON_DISABLE_GPU=1 drawio --no-sandbox -x -f png -t --border 10 \
    -p $i -o "$OUT" full.drawio
done
ls full-*.png  # 11 files: full-01.png .. full-11.png
```

**GUI fallback (draw.io desktop / web):**
`File → Export As → PNG` → Zoom 200%, Border Width 10, Background White, Shadow off.
Repeat for each of 11 pages; save as `full-NN.png`.

## Save rule (CRITICAL)

`File → Properties → Compressed: OFF` — XML plain text để git diff. Default Draw.io compress base64 → không diff được.

Verify: `head -5 xx.drawio` phải thấy `<mxfile>` readable, không base64 blob.

## Style guide — Palette (fallback standard Draw.io)

| Element | Fill | Border | Notes |
|---|---|---|---|
| Canvas background | `#FFFFFF` | — | Pure white |
| Actors zone | `#F5F5F5` | `#666666` | Neutral gray (used for page 01 Actors swimlane) |
| CI/CD zone | `#FFF2CC` | `#D6B656` | Yellow cream |
| GCE VM zone | `#FFF2CC` | `#D6B656` | Same as CI/CD |
| GKE cluster zone | `#DAE8FC` | `#6C8EBF` | Light blue |
| Namespace (default) | `#FFE6CC` | `#D79B00` | Light orange |
| Logging/Observability ns | `#D5E8D4` | `#82B366` | Light green |
| Auth/Security ns | `#F8CECC` | `#B85450` | Light red/pink |
| Node (tool box) | `#FFFFFF` | `#000000` | White fill, black border |
| Actor (user) | `#FFFFFF` | `#000000` | `shape=actor` |
| Arrow stroke | `#000000` | — | 2px orthogonal classic arrowhead |

**Nếu user ship palette từ `architecture.png`** → update bảng trên, regenerate XMLs (search-replace hex across files).

## Style guide — Typography

- Font family: Helvetica (Draw.io default)
- Title: 18px bold
- Zone label: 14px bold
- Node label: 11px regular
- Arrow label: 10px regular, `labelBackgroundColor=#ffffff` để readable khi cross arrows
- Footer: 10px gray `#666666`

## Style guide — Arrow

- Type: orthogonal (`edgeStyle=orthogonalEdgeStyle`)
- Thickness: 2px
- End: classic arrowhead
- Color: black `#000000`
- Label: verb-based ("Push", "Route", "Inference", "Publish", "Query", "Trace")
- Dashed: observability/async flows (`dashed=1`)

## File naming

Single master file: `full.drawio` — multi-page, 11 diagrams.
PNG exports: `full-XX.png` (one per page, zero-padded for lexical sort).

| # | Diagram | Page name (in `full.drawio`) | PNG | Status |
|---|---|---|---|---|
| 01 | Full system overview (9 ns post-cut) | `Full System Overview` | `full-01.png` | active |
| 02 | Batch data flow (Bronze→Silver→Gold) | `Batch Data Flow` | `full-02.png` | active |
| 03 | Stream data flow (Kafka+Spark Streaming) | `Stream Data Flow` | `full-03.png` | active |
| 04 | CDC data flow (Debezium from `app-oltp-ns`) | `CDC Data Flow` | `full-04.png` | active |
| 05 | ML training pipeline (Kubeflow+MLflow+Katib) | `ML Training Pipeline` | `full-05.png` | active |
| 06 | Model serving (FastAPI + optional KServe) | `Model Serving` | `full-06.png` | active |
| ~~07~~ | ~~RAG pipeline~~ | — | — | **CUT** (YAGNI) |
| 08 | SSO security flow (12-step OIDC) | `SSO Security Flow` | `full-08.png` | active |
| 09 | Drift detection (Evidently) | `Drift Detection` | `full-09.png` | active |
| ~~10~~ | ~~LLM security architecture~~ | — | — | **CUT** (YAGNI) |
| ~~11~~ | ~~Enhanced RAG~~ | — | — | **CUT** (YAGNI) |

Template: `_template.drawio` (skeleton for new diagrams; not merged into `full.drawio`).

## Icon notes

- Tools dùng rounded rectangles + text labels ở v0.1 (gen-XML từ Claude).
- Post-import: user có thể swap sang SVG logos official (Jenkins, Kafka, Airflow, Ollama, ...) trong Draw.io.
- K8s built-in shapes dùng khi có (`shape=mxgraph.kubernetes.icons.*`).

## Notes

- `v0.1` = initial Claude-generated skeleton. Visual polish là user responsibility.
- Layout auto-generated, positions có thể overlap — user nudge trong Draw.io.
- Source `.drawio` là truth, PNG chỉ là artifact export.
