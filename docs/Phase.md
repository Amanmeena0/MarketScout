# MarketScout Project Phases & Roadmap

## Phase 1: Core Server & MCP Infrastructure
- [x] Setup FastAPI server framework (`server.py`) with CORS middleware.
- [x] Configure `MultiServerMCPClient` lifecycle to connect to external SSE MCP servers (Google, Reddit, Scraper, YouTube, Lemmy, Bluesky).
- [x] Establish MongoDB connection (`database/db.py`) and standard analysis schemas (`database/schema.py`).
- [x] Implement secure file serving endpoints (`/reports/{rid}/{file_id}`) with path-traversal prevention.

---

## Phase 2: Sequential Multi-Agent Pipeline
- [x] **Planner Agent**: Implemented research plan generator based on prompt and analysis mode.
- [x] **Tool Routing ReAct Agent**: Configured LangChain ReAct agent executing queries over tools.
- [x] **Evidence Analyst Agent**: Built synthesis module to extract statistics and verify URLs.
- [x] **Report Writer Agent**: Created prompt registry (`PROMPTS_REGISTRY`) covering 6 analysis modes (`INDUSTRY_ANALYSIS`, `BARRIER_ANALYSIS`, `COMPETITOR_ANALYSIS`, `MARKET_GAP_ANALYSIS`, `SALES_FORECASTING`, `TARGET_MARKET_ANALYSIS`).

---

## Phase 3: LangGraph Reflection & Gap-Filling Loop
- [x] Define `AgentState` schema with `custom_add_with_delete` reducer.
- [x] Build `find_gaps` node for auditing report drafts against reflection guidelines.
- [x] Build `continue_to_fill_gaps` node utilizing LangGraph `Send` API for map-reduce fan-out.
- [x] Build `fill_gaps` node for sub-agent ReAct gap resolution.
- [x] Build `merge_filled_gaps` node to seamlessly integrate newly researched facts back into the report draft.

---

## Phase 4: Resiliency & Context Compression
- [x] Build `SummarizedTool` wrapper to auto-compress tool responses >2,000 characters.
- [x] Implement exponential backoff retry logic (`call_llm_with_backoff`) for transient HTTP 429/503 errors.
- [x] Integrate `InMemoryRateLimiter` to protect LLM provider rate limits across concurrent requests.

---

## Phase 5: PDF Export & Live Delivery
- [x] Implement `MarkdownPdf` document exporter.
- [x] Connect real-time WebSocket log streaming (`/ws/research/{request_id}`).
- [x] Persist report paths and completion statuses in MongoDB.

---

## Phase 6: Future Roadmap & Enhancements
- [ ] Add caching layer for identical tool queries to reduce MCP API overhead.
- [ ] Support multi-format report exports (DOCX, HTML, Executive Presentation Slides).
- [ ] Implement user authentication and JWT authorization on report endpoints.
- [ ] Introduce human-in-the-loop review nodes before final PDF compilation.
