# Brainstorm — Consolidate Diagrams into `full.drawio` + Apply Review Fixes

- Date: 2026-04-20 09:57 (Asia/Saigon)
- Branch: `docs/diagrams-drawio-redraw`
- Source review: `newreview.md` (v0.1, 2026-04-19)
- Related: `docs/diagrams/README.md`, `NEW_PLANS.md`
- Tooling: draw.io desktop `/usr/bin/drawio` v29.7.8 (CLI export OK)

---

## 1. Problem Statement

Current state (2026-04-20 scout):
- `docs/diagrams/full.drawio` → **không tồn tại** (user đang chuẩn bị tạo).
- `01-full-system-overview.drawio` → 283 LOC, **1 page** (review cũ nói 11 pages — đã được cleanup từ thời điểm review).
- `02-batch-data-flow.drawio` → 94 LOC, **1 page** (đã cleanup).
- `03-11` → 1 page mỗi file, hợp lệ XML.
- Chưa có file `.png` nào.

Vậy 🔴 structural (Items 0.1, 1.1, 1.2, 1.3) phần lớn đã được giải quyết từ hiện trạng, nhưng **chưa có master aggregator**. User muốn build `full.drawio` làm **single source of truth**, xoá 01-11.

Song song cần apply **9 🟠 High** còn lại: palette, content naming, arrows, labels, PNG.

## 2. User Intent (từ prompt)

> "vẽ hết tất cả vào 1 file cho tôi tôi đang copy nó là full.drawio giống trong review. giúp tôi vẽ hết trong đó và thực hiện theo bình luận"

→ Build `full.drawio` multi-page chứa 11 diagrams, xoá 01-11, áp dụng toàn bộ comment review.

## 3. Agreed Strategy (đã align qua AskUserQuestion)

| Decision | Choice | Rationale |
|---|---|---|
| File strategy | **Keep full.drawio, delete 01-11** | 1 source of truth, tránh drift. Review option B ("giữ full.drawio + xoá duplicate trong 01-*"). |
| Fix scope | **All 4 🔴 + all 9 🟠** | Close toàn bộ review v0.1. |
| PNG export | **CLI auto-export ngay** | `drawio -x -f png` deterministic, không chờ CI. |
| RAG naming | **Unify sang RAGFlow** trong 07 + 11 | Khớp NEW_PLANS.md §5 + §7. |
| app-ns rename | **app-oltp-ns** trong 04 | Rõ là OLTP DB namespace; add vào NEW_PLANS §7 ns list. |
| SSO step 11 | **Fix 08 match NEW_PLANS** | Step 9=set cookie, step 11=EnvoyFilter validates JWT. |
| Actors palette | **Add "Actors zone" row** vào README palette table | Light gray `#F5F5F5` / stroke `#666666` để không đụng CI/CD yellow. |
| 01 arrows | **Add main-flow arrows** (5-7 arrows) | 01 = topology overview có flow chính User→Gateway→API→ML→DB→Obs. |
| Delete order | **Build full.drawio xong rồi delete 01-11** | Safe, same commit. |
| Commit | **1 commit** `docs(diagrams): consolidate into full.drawio + review fixes` | Atomic change, dễ revert. |

## 4. Approaches Evaluated

### A. Keep 11 separate files, delete full.drawio (review recommendation)
- ✅ Pros: Đơn giản, PR diff nhỏ từng file, README đang khớp sẵn.
- ❌ Cons: Ngược ý user, mất khả năng xem tổng thể trong 1 tab draw.io.
- **Rejected**.

### B. Keep both (aggregator + 11 files) — current intent của review Item 0.1
- ✅ Pros: Tiện navigate.
- ❌ Cons: **Duplicate source** — drift guaranteed. Review đã warning.
- **Rejected** — vi phạm DRY.

### C. Single `full.drawio` với 11 pages, delete 01-11 (**CHOSEN**)
- ✅ Pros: 1 source, page tabs draw.io dễ navigate, export PNG/SVG mỗi page bằng CLI.
- ✅ PR review: diffable vì XML plain-text uncompressed.
- ⚠️ Cons: File lớn hơn (~60-80KB sau merge), PR review diff tập trung 1 file.
- ⚠️ README file naming table phải rewrite.
- **Chosen** — align user intent + DRY.

### D. Full.drawio master + 11 files auto-generated
- ✅ Pros: Single source.
- ❌ Cons: draw.io CLI không split multi-page → single-page `.drawio`. Phải manual split hoặc script XML. YAGNI.
- **Rejected**.

## 5. Final Solution — Spec

### 5.1 `docs/diagrams/full.drawio` (new master)
- `<mxfile compressed="false">` với 11 `<diagram>` pages theo đúng order 01→11.
- Page names khớp README table (`Full System Overview`, `Batch Data Flow`, ..., `Enhanced RAG Pipeline`).
- Mỗi page = nội dung hiện tại của 01-11 sau khi apply 🟠 fixes bên dưới.

### 5.2 Content fixes (áp dụng vào các pages tương ứng)

| # | Review Item | Page | Change |
|---|---|---|---|
| 1 | 7.1 | 07 Rag, 11 Enhanced RAG, 01 Full | LangChain → RAGFlow (name + links) |
| 2 | 7.2 | 04 CDC | `app-ns` → `app-oltp-ns` (cell id + label). Also NEW_PLANS §7 add row. |
| 3 | 7.3 | 08 SSO | Steps reordered: s1 label current s1-6; s2 label current s7-10 with step 9 = set cookie + step 10 = redirect + step 11 = EnvoyFilter validates JWT + step 12 = forward. |
| 4 | 2.1 | 01 Full (Actors zone) | fill `#F5F5F5`, stroke `#666666`. README palette add "Actors zone" row. |
| 5 | 2.2 | 01 Full (nginx-ns-2) | fill `#FFE6CC`, stroke `#D79B00` (namespace orange, không phải auth red). |
| 6 | 6.1 | 01 Full | Add 5-7 main-flow edges: `a1 (End User) → nginx → api-gateway → ml-serving → postgres/redis`, `ml-serving → observability (dashed)`. Labels: "HTTPS", "Route", "gRPC Inference", "Persist", "Trace". |
| 7 | 3.1 | 05 ML Training (14 edges) | Add labels ở 6 edges chưa có: "Pull features", "Train", "Log metrics", "Register", "Deploy", "Trigger". |
| 8 | 3.1 | 10 LLM Security (12 edges) | Add labels ở 6 edges guardrail chain: "Classify", "Redact PII", "Check policy", "Allow/Block", "Log", "Audit". |

### 5.3 README updates

- **Palette table**: Add row `Actors zone | #F5F5F5 | #666666 | Neutral gray`.
- **File naming table**: Rewrite.
  ```
  | # | Diagram | Page name | File |
  |---|---------|-----------|------|
  | — | All diagrams | (11 pages) | full.drawio (+ full.png per page) |
  ```
- **How to export PNG**: Update CLI command.
  ```bash
  drawio -x -f png -t -o docs/diagrams/ docs/diagrams/full.drawio
  # Draw.io xuất 1 PNG per page → full-01.png, full-02.png, ...
  # Verify: ls docs/diagrams/full-*.png
  ```
- **Note**: Ghi rõ `full.drawio` là master, 01-11 removed.

### 5.4 NEW_PLANS.md updates
- §7 namespace breakdown: add `app-oltp-ns ← Application OLTP DB (PostgreSQL logical replication source)`.
- No other change (RAGFlow, EnvoyFilter steps đã đúng trong NEW_PLANS).

### 5.5 Deletion list
```
docs/diagrams/01-full-system-overview.drawio
docs/diagrams/02-batch-data-flow.drawio
docs/diagrams/03-stream-data-flow.drawio
docs/diagrams/04-cdc-data-flow.drawio
docs/diagrams/05-ml-training-pipeline.drawio
docs/diagrams/06-model-serving.drawio
docs/diagrams/07-rag-pipeline.drawio
docs/diagrams/08-sso-security-flow.drawio
docs/diagrams/09-drift-detection.drawio
docs/diagrams/10-llm-security-architecture.drawio
docs/diagrams/11-enhanced-rag-pipeline.drawio
```
_Template._template.drawio giữ lại (new diagram skeleton).

### 5.6 PNG export workflow
```bash
cd docs/diagrams
drawio -x -f png -t --border 10 -o . full.drawio
# outputs full-1.png, full-2.png, ..., full-11.png
# Optional: rename to full-01.png .. full-11.png
for i in $(seq 1 9); do mv full-$i.png full-0$i.png 2>/dev/null; done
```

## 6. Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Merge 11 files thành multi-page XML sai structure → draw.io không mở được | 🔴 Blocker | Validate bằng `xmllint --noout full.drawio` + mở desktop kiểm tra trước commit. |
| Cell IDs trùng nhau giữa các pages (e.g., `a1`, `e1`) | 🟠 | draw.io scope IDs theo `<mxGraphModel>` nên không collide — verified via _template. Nhưng cần test. |
| PNG export CLI fail headless (vaapi error đã thấy) | 🟠 | `--no-sandbox` flag + set `ELECTRON_DISABLE_GPU=1`. Fallback: user export từ desktop UI. |
| Git history lost khi delete 01-11 | 🟢 Low | `git mv` không áp dụng (merge 11→1). History via git log preserved ở commit trước. |
| README/NEW_PLANS drift nếu chỉ fix diagram | 🟠 | Same-commit update cả 3 file. Include trong commit message checklist. |
| User sau này edit nhầm deleted file name trong docs | 🟢 Low | Grep `01-full-system-overview` trong repo → replace hết references. |

## 7. Success Criteria

- [ ] `full.drawio` có đúng 11 pages, `xmllint --noout` pass.
- [ ] Mở `full.drawio` trong draw.io desktop → all 11 pages render đúng, không broken edges.
- [ ] Palette compliance script (review Appendix) pass — no hex ngoài ALLOWED set (sau khi cập nhật ALLOWED với `#F5F5F5`, `#666666`).
- [ ] 01 Full Overview có ≥5 main-flow edges với labels.
- [ ] 05 page và 10 page không còn unlabeled edges.
- [ ] 07 và 11 không còn chuỗi "LangChain" (grep).
- [ ] 08 SSO step 11 = "EnvoyFilter validates JWT".
- [ ] 04 page cell id = `app-oltp-ns`; NEW_PLANS §7 có row tương ứng.
- [ ] nginx-ns-2 cell có `fillColor=#FFE6CC;strokeColor=#D79B00`.
- [ ] Actors zone fill `#F5F5F5`.
- [ ] README palette + file naming tables updated.
- [ ] 11 PNG files (`full-01.png`..`full-11.png`) exported và commit.
- [ ] 10 file 01-11.drawio đã deleted.
- [ ] 1 commit atomic: `docs(diagrams): consolidate into full.drawio + review fixes`.

## 8. Implementation Hints

- **XML merge approach**: Script Python/Node đọc 11 files, extract `<diagram>` element, wrap vào single `<mxfile compressed="false">`. Rename duplicate IDs nếu cần (prefix page number).
- **Order tuân theo README table (01→11)**.
- **Before/after snapshot**: `xmllint --format full.drawio | wc -l` (expect 400-600 dòng).
- **Palette validation**: chạy Python script trong review Appendix với ALLOWED cập nhật.

## 9. Out of Scope

- CI/CD auto-render PNG (review Item 0.2 alternative — defer đến Phase 06).
- Swap rounded-rect → official SVG logos (README note `v0.1`).
- Position nudging / visual polish (user responsibility per README).

## 10. Next Steps

- Option A: Chạy `/plan` để generate detailed phase-by-phase implementation plan.
- Option B: Brainstorm-only, user tự implement bằng draw.io desktop UI.

## 11. Unresolved Questions

1. **PNG output naming**: `full-01.png` zero-padded hay `full-1.png` default của drawio CLI? (chọn zero-pad cho lexical sort)
2. **Istio mesh diagram**: NEW_PLANS §5 có mention Istio sidecar — có cần thêm diagram 12 Istio mesh trong scope lần này không? (mặc định **không**, ngoài review v0.1)
3. **Drift detection page 09** có 11 edges nhưng review không flag — có cần review bổ sung các edges này không?
4. **_template.drawio**: giữ nguyên hay merge luôn vào full.drawio làm page 00 "Template"? (default **giữ riêng** — template không phải diagram production)
