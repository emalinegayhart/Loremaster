<img width="1081" height="921" alt="image" src="https://github.com/user-attachments/assets/e9f0b05e-78ff-4d18-b05e-560a1c44d18c" />

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

- Field weights (title^4, summary^2, content) boosts relevance score based on where the match is found. A match in the title is 4x more relevant than a match in the body. Justification: Someone searching "Arthas" probably wants the Arthas page, not every page that mentions him in passing.

- Fuzziness (AUTO) handles typos and misspellings automatically. AUTO sets the edit distance based on word length. Short words require exact matches, longer words allow 1-2 character differences. Example: "Arthas" still finds "Arthes", "Frostmourne" still finds "Frostmourn".

- English analyzer applies stemming and stop word removal at index and query time, which means users don't need to type exact forms of words to get relevant results. Example: "Running" matches "run", "the sword" strips "the".

- best_fields multi-match type takes the highest scoring field rather than summing all fields. This prevents a document from ranking highly just because it mentions the search term across many fields — the best single match wins.

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

