# Face Detection MLOps — Architecture Diagrams (D2)

D2 (terrastruct) source files cho 8 architecture diagrams (post-YAGNI cut, RAG-related removed).

Replaces deprecated `docs/diagrams/` (drawio). D2 picked vì: code-first, auto-layout (no overlap), modern aesthetic, git-diff readable.

## How to render

```bash
# Install d2 (one-time):
make install-d2
# or: curl -fsSL https://d2lang.com/install.sh | sh -s --

# Build all SVGs:
make diagrams
# Output: out/*.svg

# Validate without writing:
make check

# Clean:
make clean
```

Default layout engine: **ELK** (Eclipse Layout Kernel) — best for hierarchical architecture diagrams.

## Style

Shared tokens: [`style/tokens.d2`](style/tokens.d2). Palette matches drawio v0.1 cho continuity:

| Class | Use | Fill | Stroke |
|---|---|---|---|
| `cicd` | CI/CD + external infra | `#FFF2CC` | `#D6B656` |
| `gke` | GKE cluster layer | `#DAE8FC` | `#6C8EBF` |
| `ns` | Namespace | `#FFE6CC` | `#D79B00` |
| `obs` | Observability ns | `#D5E8D4` | `#82B366` |
| `auth` | Auth/Security ns | `#F8CECC` | `#B85450` |
| `tool` | Tool box (white) | `#FFFFFF` | `#000000` |
| `store` | Storage (cylinder) | `#FFFFFF` | `#000000` |
| `actor` | User actor | `#FFFFFF` | `#000000` |
| `dashed` | Async/observability flows | — | `#666666` dashed |

## Diagrams

| # | Diagram | File | SVG |
|---|---|---|---|
| 01 | Full system overview (9 ns) | `01-full-system-overview.d2` | `out/01-full-system-overview.svg` |
| 02 | Batch data flow (Bronze→Silver→Gold) | `02-batch-data-flow.d2` | `out/02-batch-data-flow.svg` |
| 03 | Stream data flow (Kafka + Spark Streaming) | `03-stream-data-flow.d2` | `out/03-stream-data-flow.svg` |
| 04 | CDC data flow (Debezium) | `04-cdc-data-flow.d2` | `out/04-cdc-data-flow.svg` |
| 05 | ML training pipeline (Kubeflow + MLflow + Katib) | `05-ml-training-pipeline.d2` | `out/05-ml-training-pipeline.svg` |
| 06 | Model serving (FastAPI + optional KServe) | `06-model-serving.d2` | `out/06-model-serving.svg` |
| 08 | SSO security flow (12-step OIDC via Dex) | `08-sso-security-flow.d2` | `out/08-sso-security-flow.svg` |
| 09 | Drift detection (Evidently) | `09-drift-detection.d2` | `out/09-drift-detection.svg` |

**Cut from v0.1** (drawio pages 07, 10, 11): RAG Pipeline, LLM Security, Enhanced RAG — see [docs/archive/cut-components-v0.1.md](../archive/cut-components-v0.1.md).

## Why D2 (vs drawio)

| Dimension | drawio v0.1 | D2 v0.2 |
|---|---|---|
| Format | XML (semi-readable in git) | Plain text (fully git-diff friendly) |
| Layout | Manual coordinates (overlap-prone) | Auto-layout (ELK/dagre) |
| Export | drawio binary required | Single `d2` Go binary |
| CI integration | Yes (GUI fallback) | Yes (CLI-native) |
| Aesthetic | Formal, dated | Modern, professional |
| Edit ergonomics | GUI drag-drop | Text editor + LSP support |

## Edit workflow

1. Open `.d2` in any text editor (VSCode has official D2 extension)
2. `make diagrams` regenerates SVG
3. Open SVG in browser to preview
4. Commit `.d2` + SVG together

For preview-on-save: install VSCode D2 extension or run `d2 --watch <file>.d2`.

## D2 Resources

- Docs: https://d2lang.com
- Cheat sheet: https://d2lang.com/tour/intro
- Icons: built-in shapes (cylinder, person, queue, etc.); add SVG via `icon: <url>`
