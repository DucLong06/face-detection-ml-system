# Face Detection MLOps — Architecture Diagrams

Draw.io source files + style guide cho 11 architecture diagrams (MLOps L1+L2+L3+RAG+SSO).

## How to edit

**VSCode**: install extension `hediet.vscode-drawio`, open any `.drawio` file.
**Desktop**: install `drawio-desktop` from https://github.com/jgraph/drawio-desktop/releases.
**Web**: https://app.diagrams.net/ → Open from Device.

## How to export PNG

`File → Export As → PNG` → options:
- Zoom: 200%
- Border Width: 10
- Background: White (uncheck Transparent)
- Shadow: off
- Selection only: off

Save PNG cùng folder với `.drawio` (same basename).

## Save rule (CRITICAL)

`File → Properties → Compressed: OFF` — XML plain text để git diff. Default Draw.io compress base64 → không diff được.

Verify: `head -5 xx.drawio` phải thấy `<mxfile>` readable, không base64 blob.

## Style guide — Palette (fallback standard Draw.io)

| Element | Fill | Border | Notes |
|---|---|---|---|
| Canvas background | `#FFFFFF` | — | Pure white |
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

Pattern: `XX-descriptive-slug.drawio` + matching `.png`.

| # | Diagram | File |
|---|---|---|
| 01 | Full system overview (all 16 ns) | `01-full-system-overview.{drawio,png}` |
| 02 | Batch data flow (Bronze→Silver→Gold) | `02-batch-data-flow.{drawio,png}` |
| 03 | Stream data flow (Kafka+Flink) | `03-stream-data-flow.{drawio,png}` |
| 04 | CDC data flow (Debezium) | `04-cdc-data-flow.{drawio,png}` |
| 05 | ML training pipeline (Kubeflow+MLflow+Katib) | `05-ml-training-pipeline.{drawio,png}` |
| 06 | Model serving (KServe+Triton) | `06-model-serving.{drawio,png}` |
| 07 | RAG pipeline (Ollama+Weaviate) | `07-rag-pipeline.{drawio,png}` |
| 08 | SSO security flow (12-step OIDC) | `08-sso-security-flow.{drawio,png}` |
| 09 | Drift detection (Evidently) | `09-drift-detection.{drawio,png}` |
| 10 | LLM security architecture (guardrails) | `10-llm-security-architecture.{drawio,png}` |
| 11 | Enhanced RAG (hybrid search + rerank) | `11-enhanced-rag-pipeline.{drawio,png}` |

## Icon notes

- Tools dùng rounded rectangles + text labels ở v0.1 (gen-XML từ Claude).
- Post-import: user có thể swap sang SVG logos official (Jenkins, Kafka, Airflow, Ollama, ...) trong Draw.io.
- K8s built-in shapes dùng khi có (`shape=mxgraph.kubernetes.icons.*`).

## Notes

- `v0.1` = initial Claude-generated skeleton. Visual polish là user responsibility.
- Layout auto-generated, positions có thể overlap — user nudge trong Draw.io.
- Source `.drawio` là truth, PNG chỉ là artifact export.
