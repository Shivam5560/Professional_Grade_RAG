# Professional RAG System — Technical Documentation

## 1. System Overview

A dual-mode Retrieval-Augmented Generation system that combines **Hybrid RAG** (Fast Mode) and **PageIndex RAG** (Think Mode) to deliver both speed-optimized and reasoning-intensive document Q&A.

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, TypeScript, React, Tailwind CSS, Zustand |
| Backend | FastAPI, Python, LlamaIndex |
| LLM | Groq Cloud — `openai/gpt-oss-20b` |
| Embeddings | Ollama — `nomic-embed-text-v2-moe` (768-dim) |
| Reranker | `BAAI/bge-reranker-v2-m3` (cross-encoder) |
| Database | PostgreSQL + pgvector |
| Search | BM25Okapi (keyword) + pgvector (semantic) |

---

## 2. Hybrid RAG vs PageIndex RAG — Comparison

### 2.1 Hybrid RAG (Fast Mode)

**How it works:** Runs BM25 keyword search and vector semantic search in parallel, fuses results using score averaging with deduplication, then reranks with a cross-encoder.

| Aspect | Detail |
|--------|--------|
| Retrieval | BM25 (lexical) + Vector (semantic), parallel |
| Fusion | Merge + deduplicate by node ID, average scores |
| Reranking | bge-reranker-v2-m3 cross-encoder, top 15 → 5 |
| Granularity | Chunk-level (512 tokens, 128 overlap) |
| Confidence | Multi-factor: retrieval (55%), coherence (25%), coverage (15%), clarity (5%) |
| LLM Calls | 1 (answer generation only) |

**Pros:**
- Fast — single LLM call, sub-second retrieval
- Lexical + semantic coverage eliminates vocabulary mismatch
- Cross-encoder reranking dramatically improves precision
- Works with any document format (PDF, TXT, MD, DOCX)

**Cons:**
- No structural awareness — treats document as flat chunks
- Context window limited to top-5 reranked chunks
- May miss answers spanning multiple sections
- No reasoning trace for user transparency

---

### 2.2 PageIndex RAG (Think Mode)

**How it works:** Builds a hierarchical tree structure (TOC) from PDFs using LLM, then uses LLM-driven tree search to navigate the hierarchy and retrieve entire sections by structural relevance.

| Aspect | Detail |
|--------|--------|
| Retrieval | LLM navigates document tree (title + summary based) |
| Structure | Auto-generated TOC → hierarchical tree → per-node summaries |
| Granularity | Section-level (full page ranges, up to 8000 chars/section) |
| Confidence | LLM self-assessment (0-100) |
| LLM Calls | 2-3 (tree search per doc + answer generation) |
| Tree Gen | Automatic on first think-mode query (PDF only) |

**Pros:**
- Structurally-aware — understands document organization
- Retrieves complete, coherent sections (not fragmented chunks)
- Step-by-step reasoning trace visible to users
- Excels at multi-part or cross-section questions

**Cons:**
- Slower — multiple LLM calls for tree navigation
- PDF-only (needs page structure for tree building)
- Tree generation is one-time cost but can take 30-60s per document
- Dependent on LLM quality for tree search accuracy

---

### 2.3 Comparison Summary

| Criteria | Hybrid RAG (Fast) | PageIndex RAG (Think) |
|----------|-------------------|----------------------|
| Speed | ~1-3s | ~5-15s |
| Precision | High (cross-encoder) | High (structural) |
| Recall | Medium (chunk boundaries) | High (full sections) |
| Transparency | Sources only | Reasoning + Sources |
| Doc Formats | PDF, TXT, MD, DOCX | PDF only |
| Best For | Factual lookup, keyword-heavy queries | Complex, multi-part, analytical queries |

---

### 2.4 Why We Use Both — Combined Architecture

The mode router (`/chat/query` with `mode: fast | think`) lets users choose the right tool:

**Combined Advantages:**
1. **Coverage** — Fast mode handles all document types; Think mode provides deep PDF analysis
2. **Speed vs Depth tradeoff** — user-controlled, not system-imposed
3. **Shared infrastructure** — same PostgreSQL DB stores both vector embeddings and tree structures
4. **Confidence calibration** — Fast uses multi-factor scoring, Think uses LLM self-assessment — both surface confidence levels to the user
5. **Fallback** — if Think mode fails (non-PDF, tree gen error), users switch to Fast mode seamlessly

---

## 3. Architecture

> See: `architecture-diagram.drawio.xml`

---

## 4. Flow Sequence

> See: `flowchart.drawio.xml`

### Fast Mode Pipeline
```
Query → Reformulate → [BM25 ∥ Vector] → Score Fusion → Reranker (15→5) → LLM → Confidence Score → Response
```

### Think Mode Pipeline
```
Query → Get Trees → (Auto-gen if needed) → LLM Tree Search → Retrieve Sections → LLM + Reasoning → Confidence → Response
```

---

## 5. Implementation Details

### 5.1 Embedding Pipeline

**Model:** `nomic-embed-text-v2-moe` via Ollama (768 dimensions)

Documents are chunked using `SentenceSplitter` (512 tokens, 128 overlap), embedded, and stored in PostgreSQL via pgvector. User-level isolation is enforced — each query filters by `user_id`.

### 5.2 Hybrid Retrieval (Fast Mode)

```python
# Parallel retrieval with user-scoped filtering
vector_nodes = vector_store.retrieve(query, top_k=15, user_id=user_id)
bm25_nodes = bm25_service.search(query, top_k=15, user_id=user_id)

# Merge + deduplicate by node_id, average scores for overlaps
for node in bm25_nodes:
    if node_id in node_dict:
        node_dict[node_id].score = (node_dict[node_id].score + node.score) / 2

# Rerank top results with cross-encoder
reranked = reranker._postprocess_nodes(retrieved, query_str=query)
```

### 5.3 Tree Generation (Think Mode)

```python
# PDF → Pages → LLM-generated TOC → Hierarchical tree → Summaries
pages = get_page_texts(pdf_path)                  # Extract all pages
toc = groq_llm_call(GENERATE_TOC_PROMPT)           # LLM builds TOC
tree = _build_tree_from_flat(toc, total_pages)     # Flat → hierarchy
_attach_text_to_nodes(tree, pages)                 # Attach page text
await _generate_summaries(tree, groq_service)      # LLM summarizes each node
```

### 5.4 LLM Tree Search (Think Mode)

The LLM receives the tree structure (titles + summaries, no full text) and selects 1-5 most relevant nodes via step-by-step reasoning:

```python
search_prompt = TREE_SEARCH_PROMPT.format(
    tree_structure=tree_no_text, query=query
)
# Returns: { "reasoning": "...", "selected_node_ids": [...], "confidence": "high" }
```

### 5.5 Confidence Scoring

| Mode | Method | Components |
|------|--------|-----------|
| Fast | Multi-factor weighted | Retrieval quality (55%), Answer coherence (25%), Source coverage (15%), Query clarity (5%) |
| Think | LLM self-assessment | LLM outputs `CONFIDENCE: XX` (0-100) at end of response, extracted and cleaned |

### 5.6 Reranker

**Model:** `BAAI/bge-reranker-v2-m3`

Supports two modes:
- **Local:** `SentenceTransformerRerank` — runs on same machine
- **Remote:** Lightning.ai hosted service — offloads compute

Reduces 15 retrieved chunks to 5 highest-relevance results using cross-encoder scoring (considers query-document pairs jointly, not independently).

---

## 6. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Dual-mode over single pipeline | Different query types need different retrieval strategies |
| BM25 + Vector fusion (not either-or) | Eliminates vocabulary mismatch problem; BM25 catches exact terms, vector catches semantics |
| Cross-encoder reranker after fusion | Bi-encoder retrieval is fast but imprecise; cross-encoder is slow but highly accurate — combining gives best of both |
| LLM-generated trees (not rule-based) | Rule-based TOC extraction fails on inconsistent PDFs; LLM handles arbitrary document structures |
| pgvector (not standalone vector DB) | Single database for vectors + metadata + sessions + trees — simpler ops, transactional consistency |
| Groq for LLM (not self-hosted) | ~750 tok/s inference speed; no GPU infrastructure needed |
| nomic-embed-text-v2-moe for embeddings | MoE architecture — strong performance with efficient inference via Ollama |
| User-scoped document isolation | Every query filters by `user_id` — multi-tenant safe at the data layer |

---

## 7. Real-World Accuracy Benchmark — Hybrid RAG vs PageIndex RAG

### 7.1 Test Setup

Both RAG modes were evaluated against the **same PDF** (Disney Q1 FY2025 Earnings Report) with identical queries designed to extract financial metrics, segment performance, and strategic details across 10 categories.

**Evaluation criteria:** Completeness (was the data retrieved?) and Accuracy (was it correct?).

---

### 7.2 Per-Section Accuracy Scores

| # | Section | Hybrid RAG | PageIndex RAG | Winner |
|---|---------|-----------|---------------|--------|
| 1 | **Financial Overview** (Revenue, EPS, Income) | **20%** — 4/4 metrics "Not disclosed" | **100%** | PageIndex |
| 2 | **Segment Performance** (Entertainment, Sports, Experiences) | **30%** — Revenue & OI missing | **100%** | PageIndex |
| 3 | **DTC Metrics** (Subscribers, ARPU, Revenue) | **40%** — Subscribers only, no ARPU/OI | **100%** | PageIndex |
| 4 | **Star India Transaction** | **60%** — Financial impact only | **100%** | PageIndex |
| 5 | **Parks & Experiences** | **95%** | **100%** | Tie |
| 6 | **Guidance & Outlook** | **100%** | **100%** | Tie |
| 7 | **Cash Flow & Capital** | **100%** | **100%** | Tie |
| 8 | **Strategic Highlights** | **95%** | **100%** | Tie |
| 9 | **Special Items & Adjustments** | **70%** — Missed legal settlement | **100%** | PageIndex |
| 10 | **Cross-Segment Analysis** | **0%** — Complete failure | **100%** | PageIndex |

---

### 7.3 Overall Results

| Metric | Hybrid RAG | PageIndex RAG |
|--------|-----------|---------------|
| **Overall Completeness** | **55-60%** | **98-100%** |
| **Critical Metrics Captured** | **45%** | **100%** |
| **Non-Critical Metrics Captured** | **85%** | **100%** |
| **Numerical Errors** | 0 (accurate when retrieved) | 0 |

> **Key Insight:** Hybrid RAG never produced incorrect numbers — it simply **failed to retrieve** them. When data was retrieved, it was accurate. The gap is entirely about **coverage**, not correctness.

---

### 7.4 What Hybrid RAG Missed Entirely

| Critical Data Point | Actual Value | Hybrid RAG Output |
|--------------------|--------------|--------------------|
| Total Revenue | $24.7B (+5% YoY) | "Not disclosed in the excerpt" |
| Entertainment Revenue | $10,872M (+9%) | Not retrieved |
| Entertainment Operating Income | $1,703M (+95%) | Not retrieved |
| DTC Operating Income | $293M (vs -$138M prior year) | Not retrieved |
| All ARPU Metrics | Disney+ $7.99, Hulu $12.52, ESPN+ $6.36 | Not retrieved |
| Sports Revenue | $4,850M | Not retrieved |
| Experiences Revenue | $9,415M (+3%) | Not retrieved |
| Star India Ownership | 37% Disney, 56% RIL, 7% third party | Not retrieved |
| Corporate Expense Increase | $152M (legal settlement) | Not retrieved |
| Advertising Revenue Growth | ESPN +15%, DTC +16% | Not retrieved |

---

### 7.5 Root Cause Analysis

#### Why Hybrid RAG Failed on Coverage

| Root Cause | Explanation |
|------------|------------|
| **Chunk boundary fragmentation** | Financial tables split across chunks, breaking context — a row header in one chunk, values in another |
| **Semantic similarity mismatch** | Query about "revenue" didn't rank high enough against chunks where revenue appeared inside dense tables |
| **Top-K truncation** | With top_k=15 → rerank to 5, critical chunks got cut if they scored below threshold |
| **Flat document model** | No awareness that "Financial Highlights" section on page 2 contains all key metrics — treated equally with boilerplate text |

#### Why PageIndex RAG Succeeded

| Root Cause | Explanation |
|------------|------------|
| **Structural navigation** | LLM identified "Financial Highlights" and "Segment Results" as relevant sections by title/summary, then retrieved entire sections |
| **Complete section retrieval** | Retrieved full page ranges (e.g., pages 2-4) — tables stayed intact with headers and values together |
| **No chunk boundary problem** | Section-level granularity means no data fragmentation |
| **Reasoning-driven selection** | LLM reasoned about which sections to read, not just pattern-matched keywords |

---

### 7.6 When Each Mode Wins

| Scenario | Best Mode | Why |
|----------|-----------|-----|
| "What was Disney's Q1 revenue?" | **Think** | Needs specific metric from financial table |
| "Summarize the hurricane impact on parks" | **Fast** | Keyword "hurricane" matches directly; self-contained in one passage |
| "Compare DTC vs Sports profitability" | **Think** | Needs cross-section data from multiple tables |
| "What did the CEO say about streaming?" | **Fast** | Quote retrieval works well with semantic similarity |
| "Full segment breakdown with YoY changes" | **Think** | Requires structured table data across sections |
| "Is there a legal settlement mentioned?" | **Fast** | Keyword match on "legal settlement" is effective |

---

### 7.7 Why Both Together > Either Alone

```
Hybrid RAG alone:  55-60% coverage  |  Fast    |  All formats
PageIndex alone:   98-100% coverage  |  Slow    |  PDF only
Both combined:     98-100% coverage  |  Adaptive|  All formats
```

The dual-mode architecture eliminates each approach's weakness:
- Hybrid RAG's **coverage gap** is solved by PageIndex for complex/structured queries
- PageIndex's **speed and format limitation** is solved by Hybrid RAG for quick lookups and non-PDF documents
- Users **choose the right tool** for the query type — no system-imposed tradeoff
