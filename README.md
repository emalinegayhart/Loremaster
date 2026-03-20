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
