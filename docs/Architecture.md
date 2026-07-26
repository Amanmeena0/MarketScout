# MarketScout System Architecture

## 1. High-Level Architecture Overview

MarketScout is built around a decoupled, multi-stage agentic workflow powered by **FastAPI**, **LangChain**, **LangGraph**, and **Model Context Protocol (MCP)**. Execution is coordinated through an asynchronous control loop that streams live status updates over WebSockets and persists final reports to MongoDB and disk.

```
                              ┌────────────────────────┐
                              │      FastAPI App       │
                              │ (server.py - Port 8000)│
                              └───────────┬────────────┘
                                          │
                  ┌───────────────────────┼───────────────────────┐
                  ▼                       ▼                       ▼
          REST Endpoints          WebSocket Server         MongoDB Database
         (/analysis, /reports)   (/ws/research/{id})       (analyses collection)
                  │                       │
                  └───────────────────────┼───────────────────────┘
                                          │
                                          ▼
                               ┌─────────────────────┐
                               │ create_agent Worker │
                               └──────────┬──────────┘
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            ▼                             ▼                             ▼
   MultiServerMCPClient        Sequential Agent Pipeline        LangGraph Gap-Filling
   (Port 5001 SSE Tools)       (Planner, Tool, Evidence,        Reflection Subgraph
   - Google Search              Report Writer)                  - find_gaps
   - Reddit                                                     - fill_gaps
   - Web Scraper                                                - merge_filled_gaps
   - YouTube Transcripts                                        - route_loop
   - Lemmy / Bluesky
                                          │
                                          ▼
                                 PDF Exporter & Delivery
                                 (MarkdownPdf -> output_dir)
```

---

## 2. Technical Stack

| Component | Technology / Library | Purpose |
|---|---|---|
| **Web Server** | FastAPI, Uvicorn | Async HTTP APIs and WebSocket streaming gateway |
| **Agent Orchestration** | LangGraph, LangChain Core | State machine orchestration, map-reduce fan-out, ReAct loops |
| **Tool Integration** | MultiServerMCPClient (`langchain_mcp_adapters`) | Standardized Model Context Protocol (MCP) tool integration |
| **LLM Provider** | `ChatGoogleGenerativeAI` / `ChatHuggingFace` | Multi-model agent reasoning with rate limiting and exponential backoff |
| **Database** | MongoDB (`pymongo`) | Storing analysis state (`PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`) |
| **Export Engine** | `MarkdownPdf` | Converting final Markdown reports into PDF documents |
| **Auto-Summarization** | Custom `SummarizedTool` wrapper | Truncates and synthesizes long tool results (>2000 chars) |

---

## 3. The 6-Stage Execution Pipeline

```
                                  User Query + Analysis Type
                                               │
                                               ▼
                                   Stage 1: Planner Agent
                                   (Model: planner_model)
                                               │
                                               ▼
                                 Stage 2: Tool Routing ReAct
                               (Model: tool_routing_model + MCP)
                                               │
                                               ▼
                                  Stage 3: Evidence Analyst
                             (Model: evidence_analysis_model)
                                               │
                                               ▼
                                    Stage 4: Report Writer
                                (Model: report_writing_model)
                                               │
                                               ▼
                         ┌───────────────────────────────────────────┐
                         │ Stage 5: LangGraph Gap-Filling Subgraph   │
                         │                                           │
                         │             ┌───────────┐                 │
                         │             │ find_gaps │                 │
                         │             └─────┬─────┘                 │
                         │                   │                       │
                         │                   ▼                       │
                         │        continue_to_fill_gaps              │
                         │         (LangGraph Send API)              │
                         │                   │                       │
                         │                   ▼                       │
                         │             ┌───────────┐                 │
                         │             │ fill_gaps │                 │
                         │             └─────┬─────┘                 │
                         │                   │                       │
                         │                   ▼                       │
                         │         ┌───────────────────┐             │
                         │         │ merge_filled_gaps │             │
                         │         └─────────┬─────────┘             │
                         │                   │                       │
                         │                   ▼                       │
                         │        route_loop (k < K?) ──(Yes)────────┘
                         │                   │ (No)
                         │                   ▼
                         │             ┌───────────┐                 │
                         │             │   final   │                 │
                         │             └─────┬─────┘                 │
                         └───────────────────┼───────────────────────┘
                                             │
                                             ▼
                              Stage 6: PDF Export & Delivery
```

### Stage Details
1. **Planner Step**: Takes user prompt and creates a detailed markdown research strategy.
2. **Tool Routing Step**: ReAct agent executes queries across MCP tools to gather raw evidence.
3. **Evidence Analysis Step**: Synthesizes raw tool outputs, verifying statistics and mapping claims to source URLs.
4. **Report Writing Step**: Produces initial full draft according to selected `PROMPTS_REGISTRY` guidelines.
5. **Reflection Subgraph**: Audits draft report for gaps, fans out parallel tool sub-agents (`Send("fill_gaps", ...)`), merges findings back into report state, and loops for $k$ iterations.
6. **Delivery**: Compiles PDF to `output_dir/{id}/{analysis_type}.pdf`, updates MongoDB, and closes WebSocket.

---

## 4. Multi-Server MCP Tool Integration Architecture

The MCP client connects to external SSE endpoints defined in `lifespan`:

```python
{
    "google_tools": {"url": "http://localhost:5001/mcp/google/sse", "transport": "sse"},
    "reddit_tools": {"url": "http://localhost:5001/mcp/reddit/sse", "transport": "sse"},
    "scraper_tools": {"url": "http://localhost:5001/mcp/scraper/sse", "transport": "sse"},
    "youtube_tools": {"url": "http://localhost:5001/mcp/youtube/sse", "transport": "sse"},
}
```

All MCP tools pass through `wrap_tools_with_summarizer()`, ensuring responses stay compact and within context bounds.

---

## 5. Security & Path Protection

- **File Serving Guard**: `/reports/{rid}/{file_id}` explicitly checks for path traversal attack strings (`..`) before serving files from `output_dir`.
- **Database Sanitization**: Uses MongoDB `ObjectId` validation on path variables.
