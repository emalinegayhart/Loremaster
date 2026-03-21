# Production Roadmap

## 1. Evals

**What:** Measure whether retrieval and answers are actually good, not just vibing it.

**Two layers:**

**Retrieval evals** — does ES return the right pages?
- Build a golden dataset: 50-100 question → expected page title pairs
  e.g. "Who is Arthas?" → should retrieve "Arthas Menethil"
- Metric: Recall@5 (is the right page in the top 5 results?)
- Run after any change to the index or query logic

**Answer evals** — is Claude's answer actually correct?
- Use Claude itself as a judge (LLM-as-judge pattern)
- For each question, run the full pipeline then ask Claude:
  "Given this question and this answer, rate accuracy 1-5 and explain why"
- Build a regression suite — run before every deploy

**Stack:** Python test suite, results logged to Postgres, dashboard in Kibana or a simple React page

**Why it matters:** Right now you have no idea if a change to the prompt or index improves or degrades quality. Evals make that measurable.

---

## 2. Chunking Strategy

**What:** Right now whole pages are indexed as single documents. Long pages dilute relevance — a 5000 word page about Arthas where "Frostmourne" is mentioned once will score lower than a 200 word page dedicated to it.

**Plan:**
- Split pages into chunks of ~500 tokens with 50 token overlap
- Each chunk keeps metadata: page_id, title, url, chunk_index
- Index chunks instead of full pages in ES
- At query time, retrieve top chunks then group by page and deduplicate

**Implementation:**
- Add a `chunker.py` step between the cleaner and loader
- Use tiktoken to count tokens accurately
- Update ES mapping to add chunk_index field
- Update the loader to index chunks instead of pages
- Postgres still stores full pages (source of truth unchanged)

**Why it matters:** Better retrieval precision. The right paragraph beats the right page.

---

## 3. Hybrid Search (BM25 + Embeddings)

**What:** ES keyword search (BM25) is good for exact matches — "Arthas Menethil". Embeddings are good for semantic matches — "death knight who became the Lich King". Combining both covers more ground.

**Plan:**
- Generate embeddings for each chunk using OpenAI `text-embedding-3-small` or a local model
- Store vectors in ES using `dense_vector` field (ES 8+ supports this natively)
- At query time: run BM25 search + kNN vector search in parallel
- Combine scores using Reciprocal Rank Fusion (RRF) — ES has this built in

**Implementation:**
- Add embedding generation to the loader pipeline
- Update ES mapping to add `dense_vector` field (1536 dims for OpenAI small)
- Update search query to use ES `hybrid` query with RRF
- Eval both separately and combined to confirm improvement

**Cost note:** Embedding 230k chunks at ~500 tokens each ≈ ~$3 with OpenAI small model. One-time cost.

**Why it matters:** "What sword did the Lich King use?" → BM25 might miss it, embeddings won't.

---

## 4. User Feedback Loop

**What:** Thumbs up/down on answers. Feed signal back into ranking over time.

**Plan:**

**Frontend:**
- Add 👍 👎 buttons to each assistant message after streaming completes
- On click, send feedback to `/api/feedback` endpoint

**Backend:**
- Store feedback in Postgres:
```sql
CREATE TABLE feedback (
    id           SERIAL PRIMARY KEY,
    question     TEXT NOT NULL,
    answer       TEXT NOT NULL,
    page_ids     TEXT[],
    rating       SMALLINT NOT NULL, -- 1 = thumbs up, -1 = thumbs down
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
```

**Closing the loop:**
- Short term: surface thumbs-down responses in a review dashboard so you can manually improve retrieval for those questions
- Long term: use positive feedback as training signal for reranker fine-tuning

**Why it matters:** Turns user behaviour into a signal. Every thumbs down is a retrieval or prompt failure you can diagnose.

---

## 5. Latency SLAs

**What:** Know how fast the system actually is, track regressions, set targets.

**Target SLAs:**
- ES search: p95 < 100ms
- Full response time to first token: p95 < 1500ms
- Total response (including streaming): p95 < 5000ms

**Plan:**

**Instrument the backend:**
- Add timing middleware to FastAPI that logs per-request breakdown:
  - ES search duration
  - Time to first token
  - Total streaming duration
- Log to Postgres `request_logs` table

**Dashboard:**
- Simple query over `request_logs` to show p50/p95/p99 over time
- Alert if p95 crosses threshold (email or Slack webhook)

**Quick wins if latency is too high:**
- ES: increase `number_of_replicas`, use filter cache
- Claude: switch to Haiku if not already, reduce `max_tokens`
- Streaming: ensure response is truly streaming (check TTFT not just total time)

---

## Implementation Order

```
1. Latency instrumentation   ← measure baseline before changing anything
2. Chunking                  ← biggest retrieval quality win
3. Evals                     ← now you can measure if chunking helped
4. Feedback loop             ← collect signal from real usage
5. Hybrid search             ← highest effort, biggest quality ceiling
```
