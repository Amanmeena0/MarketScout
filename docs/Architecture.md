# MarketScout Architecture

## System Pipeline
1. **Stage 1: Planner Agent** - Generates Research Strategy.
2. **Stage 2: Tool Routing ReAct Agent** - Utilizes MCP Tools (Google, Web Scraper, YouTube, X).
3. **Stage 3: Evidence Analyst Agent** - Synthesizes & Verifies Facts.
4. **Stage 4: Report Writer Agent** - Creates Initial Comprehensive Draft.
5. **Stage 5: LangGraph Reflection & Gap-Filling** - Audits for gaps, spawns gap-filling agents, and merges filled gaps recursively.
6. **Stage 6: PDF Export & Delivery** - MarkdownPdf, MongoDB & WebSocket Stream.

## Architecture Guidelines
- **Orchestrated Control Flow**: Agents do not communicate directly.
- **Asynchronous Log Streaming**: Execution steps stream logs in real time over WebSockets.
- **Resilience**: LLM calls utilize `call_llm_with_backoff` and an `InMemoryRateLimiter`.
