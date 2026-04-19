# Brainstorm Report — Diagram Redraw với Draw.io (match MLOps L1 style)

**Date:** 2026-04-19 13:40 ICT (updated 13:56)
**Author:** Solution Brainstormer (Claude)
**Focus:** CHỈ redraw 11 diagrams trong `images/` bằng Draw.io để match style `architecture.png` (MLOps L1). Các phần khác (namespace setup, feasibility) chỉ là reference.
**Supersedes focus of:** `brainstorm-260419-1315-phased-local-setup-mlops-l2-l3.md` (section 3 — Diagram Redraw Strategy)

**Update 13:56**:
- Nhấn mạnh **BẮT BUỘC commit `.drawio` XML source** để user load lại edit trong draw.io sau này (section 5 đã có, bổ sung rule `Compressed: OFF`).
- **Step 0 mới**: User export file `.drawio` gốc của `architecture.png` → commit `docs/diagrams/reference/` → tôi/agent dùng làm base template (extract icons + arrows + palette chính xác, không guess từ PNG).

**Update 14:00 — Lucidchart origin discovered**:
- User revealed file gốc `architecture.png` vẽ bằng Lucidchart.
- Migration path evaluated, nhưng...

**Update 14:05 — FINAL DECISION: 100% Draw.io, no migration**:
- User không export được từ Lucidchart nữa (access/license issue).
- **Decision**: Option C — vẽ lại 100% bằng Draw.io từ đầu.
- PNG `images/architecture.png` giữ làm **visual reference only** (nhìn để bắt chước style).
- KHÔNG import Lucidchart VDX, KHÔNG có `docs/diagrams/reference/*.drawio` file.
- Style extract thủ công từ PNG: palette hex qua color picker, icons chọn tương đương trong Draw.io shape library, arrows tự làm khớp.

---

## 1. Problem Statement

- 11 PNG hiện có trong `images/01_*.png` → `11_*.png` đang dense, dark-theme, khó đọc.
- User **thích style `architecture.png` MLOps L1**: light background, real brand logos, colored zone subgraphs, labeled arrows verb-based, left-to-right flow.
- Mục tiêu: **docs đẹp, dễ nhìn TRƯỚC**, update code sau.
- Animated GIF: nice-to-have, nhưng skip để tập trung chất lượng static.
- Giữ nguyên `architecture.png` (L1) — không vẽ lại.

---

## 2. Tool Decision — Draw.io (diagrams.net)

### 2.1 Lý do chọn

| Tiêu chí | Draw.io | Mermaid (rejected) |
|---|---|---|
| Match style PNG L1 | ✅ 100% (cùng tool gốc) | ⚠️ 70-80% |
| Real brand logos | ✅ native shape library | ❌ iconify partial |
| Pixel layout control | ✅ | ❌ auto-layout |
| Git-diffable | ✅ XML (mxGraphModel) | ✅ text |
| Edit trong VSCode | ✅ extension có sẵn | ✅ built-in |
| Học mới | ⚠️ UI drag-drop | ⚠️ syntax |
| GitHub README render | ⚠️ commit PNG export | ✅ native |

**Verdict**: Draw.io thắng vì ưu tiên style match. Trade-off: phải commit cả `.drawio` source + `.png` export (hoặc setup CI render — phase sau).

### 2.2 Editor options (chọn 1)

1. **VSCode extension `Draw.io Integration`** (hediet.vscode-drawio) — edit `.drawio` trực tiếp trong VSCode, no context switch. **Recommended** cho dev workflow.
2. **drawio-desktop** (Electron app) — standalone, offline, nhanh. Good cho heavy edit.
3. **app.diagrams.net web** — không cài gì, save local. Backup option.

Tất cả 3 đọc/ghi cùng format `.drawio` (XML compressed hoặc uncompressed).

---

## 3. Style Guide — Match `architecture.png`

Analysis từ `architecture.png`:

### 3.1 Color palette (fixed)
| Element | Color | Hex |
|---|---|---|
| Canvas background | White | `#FFFFFF` |
| CI/CD Pipeline zone | Light yellow | `#FFF2CC` + border `#D6B656` |
| GCE zone | Light yellow | `#FFF2CC` + border `#D6B656` |
| GKE cluster zone | Light blue | `#DAE8FC` + border `#6C8EBF` |
| Namespace zones (inside GKE) | Cream | `#FFF2CC` |
| Logging namespace | Light beige | `#FFE6CC` |
| Monitoring namespace | Light beige | `#FFE6CC` |
| Arrows | Black | `#000000` 2px |
| Arrow labels | Black text on white bg | - |
| Actor icons | Default draw.io person icon | - |

### 3.2 Layout rules
- **Primary flow**: left → right (Developer → GitHub → Jenkins → ... → End User response)
- **Zones grouped** by logical concern: external actors | CI/CD | Infrastructure | K8s namespaces
- **Labeled arrows**: verb + object ("Push code", "Trigger", "Route", "Inference", "Metrics", "Traces", "Collect", "Forward", "Index", "Query")
- **Tool icons**: sử dụng draw.io built-in shape libraries:
  - `Networking > AWS > ...` — cho AWS services
  - `Networking > Kubernetes > ...` — cho K8s icons
  - Enable: `Extras → Edit Geometry → More Shapes → Networking/Cloud categories`
  - Third-party tools (Jenkins, Jaeger, Kafka, Grafana, Prometheus, ...) có sẵn trong `Networking > Apps & Systems` và community shape libraries
- **Font**: Helvetica default, 12px labels, 14px zone titles
- **Spacing**: 20px padding trong zones, 40px giữa major zones

### 3.3 Shape library bật sẵn cần
- ✅ `Networking > Cloud & Enterprise`
- ✅ `Networking > AWS 19/AWS 20`
- ✅ `Networking > GCP`
- ✅ `Networking > Kubernetes`
- ✅ `Networking > Active Directory` (cho Keycloak/SSO)
- ✅ `Software > ER` (nếu cần DB schema)

---

## 4. 11 Diagrams — Mapping & Specs

Danh sách đề xuất vẽ, thứ tự ưu tiên (1 = quan trọng nhất):

| # | Source PNG | New file | Priority | Layout | Key elements |
|---|---|---|---|---|---|
| 1 | `01_full_system_overview.png` | `01-full-system-overview.drawio` | P0 | LR, multi-zone | 16 namespaces, actors 5 roles, data flow main |
| 2 | `02_batch_data_flow.png` | `02-batch-data-flow.drawio` | P0 | LR | WIDER FACE → MinIO Bronze → Spark → Silver → GE → Gold |
| 3 | `03_stream_data_flow.png` | `03-stream-data-flow.drawio` | P1 | LR | Camera → Kafka → Flink → Redis + MinIO |
| 4 | `04_cdc_data_flow.png` | `04-cdc-data-flow.drawio` | P1 | LR | Postgres WAL → Debezium → Kafka → Spark → DW |
| 5 | `05_ml_training_pipeline.png` | `05-ml-training-pipeline.drawio` | P0 | TD | Kubeflow DAG → MLflow → Registry → KServe |
| 6 | `06_model_serving.png` | `06-model-serving.drawio` | P0 | LR | Client → Istio → KServe → Triton (ensemble: preproc→YOLO→postproc) |
| 7 | `07_rag_pipeline.png` | `07-rag-pipeline.drawio` | P2 | LR | Query → Embedding → Weaviate → Ollama → Response |
| 8 | `08_sso_security_flow.png` | `08-sso-security-flow.drawio` | P2 | Sequence/LR | 12-step OIDC: User → Istio → OAuth2 Proxy → Keycloak → ... |
| 9 | `09_drift_detection.png` | `09-drift-detection.drawio` | P1 | TD | Gold DW → Evidently → Prometheus → Alert → Airflow retrain DAG |
| 10 | `10_llm_security_architecture.png` | `10-llm-security-architecture.drawio` | P2 | LR | Input guardrails → LLM → Output guardrails → Langfuse trace |
| 11 | `11_enhanced_rag_pipeline.png` | `11-enhanced-rag-pipeline.drawio` | P2 | LR | Hybrid: Weaviate (vector) + Typesense (keyword) → Rerank → LLM |

**P0 (4 diagrams)**: full overview + batch + training + serving — core coursework.
**P1 (3)**: stream + CDC + drift — data engineering + ML quality.
**P2 (4)**: rag + sso + llm-security + enhanced-rag — 4B track + security.

---

## 5. File Layout

**Rule**: CẢ HAI `.drawio` source + `.png` export đều commit — không commit PNG mà thiếu source (không maintain được sau này).

**Setting bắt buộc khi save `.drawio`**: `File → Properties → Compressed: OFF` — XML plain text dễ git diff/merge. Default draw.io save compressed (base64+deflate) — không diff được, phải tắt.

```
docs/diagrams/
├── README.md                              # Index + style guide + legend + palette
├── _template.drawio                       # Base template, built from scratch in Draw.io
├── 01-full-system-overview.drawio         # Source
├── 01-full-system-overview.png            # Exported 1920px wide
├── 02-batch-data-flow.drawio
├── 02-batch-data-flow.png
├── 03-stream-data-flow.drawio
├── 03-stream-data-flow.png
├── 04-cdc-data-flow.drawio
├── 04-cdc-data-flow.png
├── 05-ml-training-pipeline.drawio
├── 05-ml-training-pipeline.png
├── 06-model-serving.drawio
├── 06-model-serving.png
├── 07-rag-pipeline.drawio
├── 07-rag-pipeline.png
├── 08-sso-security-flow.drawio
├── 08-sso-security-flow.png
├── 09-drift-detection.drawio
├── 09-drift-detection.png
├── 10-llm-security-architecture.drawio
├── 10-llm-security-architecture.png
└── 11-enhanced-rag-pipeline.drawio
└── 11-enhanced-rag-pipeline.png
```

- **Source** `.drawio`: git-diffable XML (uncompressed để diff clean — set File → Properties → uncheck "Compressed").
- **Export** `.png`: 1920px wide, white background, 2x DPI cho retina → file ~300–500KB/ảnh.
- **`_template.drawio`**: file trống có sẵn 16 namespace zones + color palette + shape libraries enabled — copy làm base cho mỗi diagram, đảm bảo consistency.

---

## 6. Migration Plan — 4 Steps

### Step 0: Style extraction từ PNG (~20 phút, 1 lần)

Không có reference `.drawio` → extract style thủ công từ `images/architecture.png`:

1. Mở `images/architecture.png` trong tool có color picker (Preview macOS, Windows Paint, Firefox DevTools, online colorpicker).
2. Pick hex cho: CI/CD zone, GCE zone, GKE zone, namespace zones, arrows, text, background.
3. Ghi vào `docs/diagrams/README.md` dưới section "Color palette" (section 3.1 của report này là draft).
4. Identify tool logos visible trong PNG: Jenkins butler, Docker whale, GitHub Octocat, NGINX, Jaeger, Elasticsearch, Kibana, Logstash/Beats, Prometheus, Grafana, Ansible, Terraform, K8s wheel.
5. Tìm equivalents trong Draw.io shape library:
   - Enable libraries: `Networking > Kubernetes`, `Networking > Cloud & Enterprise`, `Software`, `Apps > icons` (nếu có).
   - Cho tools thiếu (Jenkins, Jaeger, Kafka, Flink, MinIO, Airflow, DataHub, MLflow, Kubeflow, KServe, Triton, Keycloak, Ollama, Weaviate, RAGFlow, Langfuse, Evidently): search Google Images cho official SVG logo → drag-drop vào Draw.io canvas (Draw.io chấp nhận SVG paste làm shape).
6. Arrows: observe PNG → pick style (straight vs orthogonal), thickness (2px), arrowhead (classic/open), label placement (above/below line).

### Step 1: Template setup (~30 phút, 1 lần)
- Cài VSCode extension `hediet.vscode-drawio` HOẶC desktop `drawio-desktop`.
- Tạo `docs/diagrams/README.md` với:
  - Style guide đầy đủ (palette + rules section 3 của report này)
  - Legend of icons used với SVG source paths
  - Instruction: how to open/edit `.drawio` + how to export PNG
- Tạo `docs/diagrams/_template.drawio` **from scratch** trong Draw.io:
  - Canvas size: 1920×1080 base (scale up cho diagram phức tạp)
  - Background: `#FFFFFF`
  - Color palette swatches ở góc trái làm reference khi edit
  - Title block top: "Face Detection MLOps — [Diagram Name]"
  - Footer: `version | YYYY-MM-DD | author`
  - Enable shape libraries (lưu trong file properties)
  - Zone container style default: rounded-corner rectangle, 2px stroke, label top-left
  - Arrow style default: orthogonal, 2px black, classic arrowhead, 12px label font
  - File → Properties → Compressed: OFF
- Commit `_template.drawio`.

### Step 2: Draw P0 diagrams (~5–7h work — cao hơn Option A do vẽ from scratch)
Thứ tự: **02 batch** (đơn giản nhất, practice Draw.io + workflow trước) → **06 serving** → **05 training** → **01 full overview** (khó nhất, để cuối sau khi đã quen tool).

Mỗi diagram:
1. Copy `_template.drawio` → rename theo pattern `XX-{slug}.drawio`.
2. Sketch layout trên giấy/whiteboard trước (tiết kiệm thời gian reorganize trong Draw.io).
3. Drag-drop icons từ shape library (hoặc paste SVG logos từ Step 0).
4. Vẽ zone containers + labels.
5. Label arrows verb-based (match style PNG L1: "Push code", "Route", "Inference", "Index", "Query"...).
6. So sánh side-by-side với `images/architecture.png` → chỉnh style cho consistent.
7. Export PNG 1920px, white background, scale 2x.
8. Update reference trong `NEW_PLANS.md` + `README_EXTENDED.md`.

### Step 3: Draw P1 diagrams (~3–4h)
03 stream → 04 cdc → 09 drift.

### Step 4: Draw P2 diagrams (~4–5h)
07 rag → 11 enhanced rag → 08 sso → 10 llm security.

### Step 5 (optional): CI/CD render
GitHub Action dùng `jgraph/drawio-export` Docker image render `.drawio` → `.png` tự động khi push. Không cần commit PNG thủ công. **Skip trong MVP**, làm sau.

**Total estimate**: 14–18h thiết kế cho 11 diagrams (Option C from scratch, cao hơn Option A khoảng 2–3h). Chia 3–5 sessions.

---

## 7. Success Metrics

- [ ] `docs/diagrams/README.md` có style guide đầy đủ (palette + rules + library list)
- [ ] `_template.drawio` có sẵn palette + shape libraries preset
- [ ] 4 P0 diagrams done, export PNG 1920px, embed trong `NEW_PLANS.md`
- [ ] 3 P1 diagrams done
- [ ] 4 P2 diagrams done
- [ ] Cả 11 reference trong `NEW_PLANS.md` trỏ tới `docs/diagrams/*.png` (không phải `images/*.png` cũ)
- [ ] 11 diagrams consistent về color palette + icon style (spot-check so sánh 2 diagram bất kỳ)
- [ ] `architecture.png` MLOps L1 giữ nguyên, link trong `README.md` không đổi
- [ ] `images/01-11_*.png` cũ: move sang `images/archive/` HOẶC xoá (tiết kiệm ~3MB)
- [ ] PR review: đồng nghiệp có thể hiểu flow chỉ bằng nhìn diagram (không đọc text)

---

## 8. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Draw.io shape library thiếu icon (Debezium, Ollama, Weaviate, ...) | Plan A: paste SVG logo official từ brand website → drag vào Draw.io canvas. Plan B: dùng generic K8s pod icon + text label. Quyết định theo open question #1 |
| Style extract từ PNG không chính xác (color picker sai lệch ~5%) | Test 1 diagram P0 trước, review side-by-side với PNG L1. Điều chỉnh palette trong `README.md` trước khi vẽ 10 diagrams còn lại |
| 14–18h effort vượt budget user | Làm P0 only (4 diagrams ~6h) làm MVP, P1/P2 làm sau nếu còn thời gian |
| 11 diagrams inconsistent về style | Dùng `_template.drawio` làm base + review cuối theo checklist style guide |
| File `.drawio` compressed → git diff không đọc được | Set `File → Properties → Compressed: OFF` trước khi save |
| PNG export không retina-sharp | Export với scale 2x, width 1920px minimum |
| VSCode extension conflict với GitHub preview | Commit cả `.drawio` + `.png`, README embed `.png` (GitHub render) |
| User thay đổi kiến trúc sau khi vẽ | Source `.drawio` là truth, re-export PNG dễ dàng. Chỉ sửa `.drawio`, không đụng PNG |

---

## 9. Deliverables (nếu tiếp tục plan)

1. `docs/diagrams/README.md` — style guide + legend + palette (extracted manually từ PNG L1)
2. `docs/diagrams/_template.drawio` — base template built from scratch trong Draw.io
3. 11 `.drawio` source files (uncompressed XML, git-diffable)
4. 11 `.png` exported files (1920px)
5. Updated references trong `NEW_PLANS.md` + `README_EXTENDED.md`
6. Archive cũ: `images/archive/` hoặc xoá
7. (Optional Phase 2) GitHub Action auto-render drawio→png

**Note**: `images/architecture.png` MLOps L1 giữ nguyên làm visual reference lâu dài. Không có `.drawio` source cho file này (Lucidchart origin, không recover được).

---

## 10. Open Questions

1. **SVG logos nguồn**: OK với việc tìm SVG logo official từ Google Images / brand websites (Jenkins, Kafka, ...) cho tools không có trong Draw.io built-in library, hay prefer dùng generic K8s pod icon + text label để tránh license concern?
2. **`architecture.png` MLOps L1 style match tuyệt đối**: bạn muốn 11 diagram mới màu palette giống hệt (yellow/blue zones), hay mỗi diagram có accent color riêng theo chủ đề (vd: data engineering = xanh lá, ML pipeline = tím)?
3. **Archive hay xoá PNG cũ**: giữ `images/01-11_*.png` trong `images/archive/` hay delete hẳn (sạch hơn, tiết kiệm 3MB)?
4. **CI auto-render**: có muốn setup GitHub Action `drawio-export` ngay hay làm manual export tạm?
5. **Full-system overview (diagram 01)**: 16 namespaces + 5 actor roles + data flow chính — nếu nhồi hết → 1 ảnh rất phức tạp. Tách thành 2 ảnh "layered view" (infra layer + application layer) dễ đọc hơn không?
6. **Brand asset permission**: bạn có quan tâm license của các logo (Jenkins, Grafana, Ollama, ...) không? Draw.io shape library là official Apache 2.0, nhưng tool logos thuộc các dự án riêng — cho coursework academic thường OK.
7. **Deadline coursework**: có cứng không? Nếu gấp → làm P0 trước (4 diagrams ~6h), P1/P2 sau.

---

## 11. Not in scope (reference only)

Các phần sau TRONG BÁO CÁO CŨ (`260419-1315`) giữ làm reference, **KHÔNG làm bây giờ** theo yêu cầu user:
- Phase local setup (Kind cluster, 5 phase rollout)
- Docker prune + disk cleanup
- Feasibility analysis resource
- Web research MLOps 2026 industry alignment

User sẽ tự làm phần implementation sau.
