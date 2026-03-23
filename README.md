<img width="1101" height="926" alt="image" src="https://github.com/user-attachments/assets/f89492f0-3399-4800-97e1-f77a5b131417" />


____

Loremaster is a RAG (Retrieval-Augmented Generation) chat app built on top of 230,000+ pages of WoW game data. User questions are matched against an Elasticsearch index, the most relevant pages are injected as context into a Claude prompt, and the response streams back to a WoW-themed chat UI.

**Tech Stack:**
- Scraper - Go 
- Data cleaning - Python, mwparserfromhell
- Database - PostgreSQL (Neon)
- Search - Elasticsearch (Elastic Cloud Serverless)
- Backend - FastAPI, Python
- Claude Haiku
- Streaming - Server-Sent Events (SSE)
- Frontend - React, Vite

**Elasticsearch Query Design:**

- Field weights (title^4, summary^2, content) boosts relevance score based on where the match is found. A match in the title is 4x more relevant than a match in the body. **Justification:** Someone searching "Arthas" probably wants the Arthas page, not every page that mentions him in passing.

- Fuzziness (AUTO) handles typos and misspellings automatically. AUTO sets the edit distance based on word length. Short words require exact matches, longer words allow 1-2 character differences. **Example:** "Arthas" still finds "Arthes", "Frostmourne" still finds "Frostmourn".

- English analyzer applies stemming and stop word removal at index and query time, which means users don't need to type exact forms of words to get relevant results. **Example:** "Running" matches "run", "the sword" strips "the".

- RRF (Reciprocal Rank Fusion) combines results from multiple retrievers by rank position rather than raw score. Currently three retrievers are run in parallel (a cross_fields BM25 query for conversational queries, a best_fields BM25 query with fuzziness for typo tolerance, and an ELSER sparse vector query for semantic understanding) and merges them using RRF so that articles ranking highly across multiple retrievers surface at the top.

- ELSER (Elastic Learned Sparse EncodeR) is a machine learning model trained by Elastic that generates sparse vector representations of text. Unlike dense embeddings, ELSER produces weighted keyword expansions that capture semantic meaning without requiring a fixed-size vector space. This allows queries like "lore about the undead king" to match articles about Arthas even without exact keyword overlap.

- BM25 (Best Match 25) is the ranking algorithm Elasticsearch uses by default. It scores documents based on term frequency (how often the word appears) and inverse document frequency (how rare the word is across all documents). Rare terms that appear frequently in a document score higher than common terms. **Example:** "Frostmourne" appearing 10 times in a page scores higher than "the" appearing 100 times.

Limitations:

The current keyword search retrieves individual articles well [but has no awareness of relationships between them.](https://github.com/emalinegayhart/Loremaster/issues/1) Quest chains, NPC storylines, and faction arcs that span multiple pages lose their continuity. Planned improvements to address this:

[x] Assess adding ELSER sparse vector search alongside the existing keyword search using RRF (Reciprocal Rank Fusion) to combine rankings, improving retrieval on conceptual and semantic queries. (eval results [here)](https://github.com/emalinegayhart/Loremaster/blob/main/evals/notebooks/results.ipynb)
[] Assess a knowledge graph to model relationships between entities (quests, NPCs, zones, factions) so the system can traverse connections rather than retrieve isolated snippets.
[] Assess implementing GraphRAG to enable graph-aware retrieval that understands narrative continuity, enabling accurate responses to questions like "walk me through the Wrathgate quest chain" (may seem a little overkill but i wanted to learn this new tech anyways :D!).

**Test Plan:**

```bash
 cp .env.example .env
 # Fill in your Neon, Elastic Cloud, and Anthropic credentials

 pip install -r requirements.txt

 # Load data (requires data/clean/pages.jsonl)
 python loader.py

 # Backend
 python -m uvicorn webapp.backend.main:app --reload --port 8080

 # Frontend
 cd webapp/frontend
 npm install
 npm run dev
 ```

 Open [http://localhost:5173](http://localhost:5173)

 **Call for Artwork**
 - If you are an artist and would like to design 3 custom emojis for this app to replace the uggo IOS defaults I'm using, [please lmk!](https://twitter.com/emzraline)

