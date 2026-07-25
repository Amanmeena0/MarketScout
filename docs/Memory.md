# MarketScout Context & Memory Management

## 1. Memory Philosophy & Constraints

MarketScout follows a strict **Small Context** philosophy:

1. **Information Isolation**: Agents receive only the context necessary to complete their specific step.
2. **No Raw HTML / Bulk Documents**: Large web scraper outputs or HTML blocks are never passed directly to report drafting agents.
3. **Structured Compression**: Tool outputs, evidence notes, and reflection findings are summarized before entering the main context.

---

## 2. Auto-Summarization Layer (`SummarizedTool`)

To prevent token window overflow and reduce API costs, all MCP tools are wrapped in `SummarizedTool` (`agents/utils.py`).

```
                              Tool Result Received
                                        │
                                        ▼
                            Is length > 2,000 chars?
                             ├── No  ──► Return raw output
                             └── Yes ──► Pass to summarize_text()
                                               │
                                               ▼
                                  LLM Summarizer (summarization_model)
                                  Extracts facts, numbers, dates & URLs
                                               │
                                               ▼
                                  Returns compressed output (<1500 chars)
```

---

## 3. LangGraph State Memory & Garbage Collection

LangGraph maintains task state in `AgentState`. To keep the state clean across iterative reflection loops ($k$ iterations):

- **State Reset**: In `merge_filled_gaps`, returning `"filled_gaps": "DELETE"` triggers `custom_add_with_delete`, resetting the accumulated gap list to an empty array (`[]`).
- **Transient Map-Reduce State**: `kg_gap` carries single gap descriptors for parallel `Send("fill_gaps", ...)` execution without bloating global memory.

---

## 4. Rate Limiting & Transient Failure Protection

To handle concurrent agent requests and prevent HTTP 429/503 errors:

- **Global Rate Limiter**: Shared `InMemoryRateLimiter` configured via `google_rate_limit_rps`.
- **Exponential Backoff**: `call_llm_with_backoff` retries LLM invocations up to 7 times with exponential delay ($4 \times 2^{\text{attempt}} + \text{jitter}$) upon encountering transient errors (`ServiceUnavailable`, `ResourceExhausted`, `429`, `503`).

---

## 5. In-Memory Task & Queue Lifecycle

In `server.py`:
- `queues: Dict[str, asyncio.Queue]`: Tracks active WebSocket event queues.
- `tasks: Dict[str, asyncio.Task]`: Tracks background agent execution tasks.
- **Cleanup Callback**: When `create_agent` completes (or fails), `_cleanup(task)` immediately pops both queue and task references to prevent memory leaks.
