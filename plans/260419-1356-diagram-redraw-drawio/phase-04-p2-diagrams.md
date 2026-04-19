---
phase: 04
title: P2 diagrams (4 RAG + SSO + LLM security, gen-XML approach)
status: pending
priority: P2
effort: ~2h
blockedBy: [01]
blocks: [05]
---

**Workflow**: giống Phase 02 (Claude gen XML → user review+tweak → export PNG → commit).

# Phase 04 — P2 Diagrams (4 RAG + SSO + LLM security)

## Context Links
- Plan: [../plan.md](./plan.md)
- Phase 02/03: previous
- Source PNGs: `images/07_rag_pipeline.png`, `11_enhanced_rag_pipeline.png`, `08_sso_security_flow.png`, `10_llm_security_architecture.png`
- Spec reference: `NEW_PLANS.md` sections 4 (RAG), 5 (SSO), 21 (LLM security), 22 (advanced LLM), 23 (KB mgmt)

## Overview
- **Priority**: P2 (LLM track 4B + security)
- **Status**: pending
- **Description**: Vẽ 4 diagrams RAG pipeline, enhanced RAG hybrid search, SSO OIDC flow, LLM guardrails.

## Architecture per Diagram

### 07-rag-pipeline (~1h)
**Flow**: `User query` → `Embedding model (all-MiniLM-L6-v2)` → `Weaviate vector search` → `Top-K chunks retrieval` → `RAGFlow / LangChain prompt composer` → `Ollama TinyLlama 1.1B generate` → `Response`
**Side**: Langfuse trace mọi bước (dashed arrows to `langfuse` observer).
**Zones**: `rag-ns` (tất cả components).
**Canvas**: 1920×1080 LR.
**Arrows labeled**: "Query", "Embed", "Vector search", "Retrieve top-K", "Compose prompt", "Generate", "Return answer", "Trace step".

### 11-enhanced-rag-pipeline (~1h)
**Delta vs 07**: thêm hybrid search branch.
**Flow**: `User query` → parallel: `Weaviate (vector)` + `Typesense (keyword/BM25)` → `Merge + Rerank (cohere-rerank or cross-encoder)` → prompt compose → Ollama → Response
**Zones**: `rag-ns`, thêm `Typesense` instance.
**Canvas**: 1920×1080.
**Arrows labeled**: "Query", "Vector search", "Keyword search", "Merge", "Rerank scores", "Top-K final", "Generate".

### 08-sso-security-flow (~1.5h)
**Kiểu**: sequence diagram hoặc LR flow with numbered steps 1–12.
**12 steps OIDC** (từ `NEW_PLANS.md` §5):
1. User request app
2. Istio Gateway intercept
3. OAuth2 Proxy check session
4. Redirect to Keycloak /auth
5. User login (username + password + 2FA)
6. Keycloak issue authorization code
7. Callback to OAuth2 Proxy
8. Proxy exchange code → access token
9. Verify JWT signature
10. Set wildcard cookie `*.face-detect.dev`
11. Forward request with user context header
12. App receive authenticated request
**Zones**: `auth-ns` (Keycloak + OAuth2 Proxy), `istio-system`, external user.
**Canvas**: 1080×1920 (vertical for sequence) HOẶC 2560×1080 (horizontal LR với 12 steps).
**Arrows**: numbered 1–12, labeled with step name.

### 10-llm-security-architecture (~1h)
**Flow**: `User query` → `Input guardrails (PII filter, prompt injection, toxicity)` → `Ollama LLM` → `Output guardrails (hallucination check, safety filter, factuality)` → `Response to user`
**Side**: `Langfuse` trace + `NeMo Guardrails / Guardrails.ai` config.
**Zones**: `rag-ns` (input/LLM/output guards), `monitoring-ns` (Langfuse).
**Canvas**: 1920×1080 LR.
**Arrows labeled**: "Raw query", "Sanitize input", "Safe prompt", "Generate", "Raw output", "Validate output", "Safe response", "Trace".

## Related Code Files

**Create**:
- `docs/diagrams/07-rag-pipeline.drawio` + `.png`
- `docs/diagrams/11-enhanced-rag-pipeline.drawio` + `.png`
- `docs/diagrams/08-sso-security-flow.drawio` + `.png`
- `docs/diagrams/10-llm-security-architecture.drawio` + `.png`

**Read only**:
- `docs/diagrams/_template.drawio`
- Previous phase outputs (consistency reference)
- `NEW_PLANS.md` sections 4, 5, 21

## Implementation Steps
Giống Phase 02/03 workflow.

**Extra**: diagram 08 SSO có thể dùng Draw.io "UML Sequence" shape library (sequenceDiagram-style lifelines) cho rõ ràng 12 steps. Hoặc horizontal LR với 12 numbered boxes.

## Todo List

- [ ] 07-rag-pipeline: draw + export + commit
- [ ] 11-enhanced-rag-pipeline: draw + export + commit (base copy từ 07, thêm hybrid branch)
- [ ] 08-sso-security-flow: chọn sequence vs LR, draw + export + commit
- [ ] 10-llm-security-architecture: draw + export + commit
- [ ] Side-by-side review với P0/P1
- [ ] Git commit batch: `docs(diagrams): add P2 RAG + SSO + LLM security diagrams`

## Success Criteria
- [ ] 4 cặp `.drawio` + `.png` trong `docs/diagrams/`
- [ ] SSO diagram thể hiện đủ 12 steps numbered
- [ ] Enhanced RAG thể hiện hybrid vs vanilla rõ ràng (có thể so sánh với 07)
- [ ] LLM security thể hiện input guard + output guard rõ ràng

## Risk Assessment

| Risk | Mitigation |
|---|---|
| SSO sequence diagram khó layout 12 steps gọn | Thử LR 2 rows (steps 1–6 row trên, 7–12 row dưới), hoặc split thành 2 sub-diagrams |
| RAGFlow dependencies không show rõ (ES + Redis + MySQL + MinIO) | Show ở 07 diagram dưới dạng "RAGFlow" box có 4 sub-icons nhỏ (hoặc note text) |
| Hybrid rerank model quá abstract | Label rõ "cross-encoder rerank" + link config file nếu có |

## Security Considerations
Diagrams chỉ show architecture — không leak credentials, secrets, internal endpoints.

## Next Steps
→ Phase 05 (docs integration + archive).
