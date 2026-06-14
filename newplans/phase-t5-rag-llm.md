# T5 — RAG / LLM (L3 · AI Track 4B, best-of-breed)

**Priority:** P2 (cuối/song song) · **Status:** pending · **Depends:** T1,T6 · **Sơ đồ:** `diagrams/icons/06-rag.png`

> Khác domain face-detect — namespace `rag` riêng, có thể tách repo (open question #4).

## Overview
RAG hỏi-đáp trên metadata/reports/runbooks, dùng LLM serving **vLLM (GPU)**, vector **Qdrant**, hybrid keyword **Typesense**, guardrails **NeMo**, observability **Langfuse**.

## Namespace `rag` + Tools

| Tool | Vai trò |
|---|---|
| **vLLM** | LLM serving GPU (paged-attention, throughput cao) — Llama/Qwen |
| **RAGFlow** | RAG orchestrator (chunk/retrieve/generate) |
| **Qdrant** | vector DB (semantic search, hybrid built-in) |
| **Typesense** | keyword/faceted search |
| **NeMo Guardrails** | safety: jailbreak, hallucination, PII check |
| **Langfuse** | LLM observability (trace, token, cost, eval) |

## Design
- **Pipeline:** query → RAGFlow → embed (BGE/MiniLM) → Qdrant (vector) + Typesense (keyword) → context → NeMo Guardrails (input) → vLLM generate → Guardrails (output) → Langfuse trace → response.
- **Nguồn index:** OpenMetadata (catalog/lineage) + DW reports + runbooks + api docs.
- **GPU:** vLLM dùng chung GPU node pool với Triton (T3) + Ray (T2) → cần kế hoạch phân bổ.
- **Governance:** truy cập RAG theo role SSO (chỉ role được phép hỏi data nhạy cảm).

## Build Steps
1. vLLM serving (model + GPU).
2. Qdrant + Typesense + schema/collections.
3. Ingest docs (OpenMetadata + DW) → embed → index.
4. RAGFlow orchestration + NeMo Guardrails.
5. Langfuse trace.

## Success Criteria
- [ ] RAG trả lời đúng câu hỏi metadata; retrieval < 300ms
- [ ] Guardrails chặn jailbreak/PII
- [ ] Langfuse log trace/cost đầy đủ

## Risks
- vLLM + RAGFlow + Qdrant + guardrails nặng GPU/RAM → namespace quota rộng.
- Domain mismatch → cân nhắc tách repo riêng.
