---
phase: 12
title: "T5 RAG/LLM"
status: pending
priority: P3
effort: "2-3d"
dependencies: [6]
---

# Phase 12: T5 RAG/LLM (track độc lập, làm sau hoặc song song)

## Overview
RAG 2 phase theo sơ đồ zone-5: A-offline indexing (docs/runbooks/metadata → embed → Qdrant + Typesense), B-online query (RAGFlow → hybrid retrieve → merge/rerank → Guardrails → Ollama CPU [vLLM khi GPU] → Langfuse). Spec: `docs/architecture/phase-t5-rag-llm.md`. Phụ thuộc tối thiểu: phase 6 (cluster nền) — không cần data/ml stack; OpenMetadata index (dashed) là optional.

## Tools (gitops/platform/rag/) — sync-wave 9
| Tool | CPU profile |
|---|---|
| Qdrant | 🟢 nhẹ |
| Typesense | 🟢 |
| Ollama (values-cpu) / vLLM (values-gpu) | 🟡 model nhỏ (qwen2.5:3b / phi-3) |
| RAGFlow | orchestrator + embed (BGE-small CPU) |
| NeMo Guardrails | wrap in+out |
| Langfuse | PG backend (dùng PG T1 nếu có, không thì PG riêng nhẹ) |

## Implementation Steps
1. Qdrant + Typesense + Ollama (pull model nhỏ) — smoke từng cái.
2. Indexing job `pipelines/rag-indexing/`: chunk docs/ của chính repo (README + runbooks) → embed → upsert cả 2 store.
3. RAGFlow + Guardrails config (rails: từ chối ngoài scope, PII mask) + Langfuse key.
4. E2E: hỏi "drift loop hoạt động thế nào?" → trả lời có trích nguồn từ docs repo; trace + cost hiện trên Langfuse.
5. README rag domain (kiến trúc + cách re-index + chỗ đổi sang vLLM GPU).

## Success Criteria
- [ ] Query e2e trả lời đúng tài liệu repo, có citation
- [ ] Guardrails chặn 1 câu out-of-scope (test)
- [ ] Langfuse ghi trace/cost; re-index lặp lại được
- [ ] README rag viết xong

## Risk Assessment
- LLM CPU chậm → model 3B + max_tokens thấp; đây là track demo, không SLA.
- RAGFlow nặng/khó config → fallback đã bàn trong research 260604: thay bằng pipeline tự viết (LlamaIndex) nếu kẹt >1 ngày — hỏi user trước khi đổi.

## Red-Team Adjudicated Updates (260611)
- B7/O10: Langfuse **v3** = PG + **ClickHouse** + Redis + S3 (Redis/MinIO reuse T1 → dependency thêm P7a; sửa claim "chỉ cần phase 6").
- F10: RAGFlow chạy config Infinity-lite; với lab ≥56GB không cần park T1/T2; fallback LlamaIndex (>1 ngày kẹt) pre-written — hỏi user trước khi đổi.
