# MarketScout Agent Rules & Operational Constraints

## 1. Core Principles

### 1.1 Think Before Acting
Every agent must:
- Fully understand the input prompt and task scope.
- Determine whether sufficient context exists before taking action.
- Use available tools before making assumptions.
- Never fabricate facts or figures.

---

## 2. Tool-First Directive

Whenever factual information can be obtained via a tool, **tool execution is mandatory**.

**Tool Priority Hierarchy**:
1. Internal Memory / Synthesized Evidence
2. Search APIs (Google Search, News)
3. Web Scraper Tools
4. Document Retrieval & Transcripts (YouTube)
5. Community / Social Feeds (Reddit, Lemmy, Bluesky)
6. LLM Reasoning

> **Strict Rule**: Never use the LLM to guess market figures, revenues, company statistics, or dates.

---

## 3. Anti-Hallucination Guidelines

Agents must **NEVER** invent:
- Market size figures or CAGR percentages
- Financial revenues or funding rounds
- Company facts or executive names
- Publication dates
- Source URLs

**Rule**: If specific quantitative data or source links are unavailable after tool searches, the agent MUST return `"Unknown"` or explicitly state that data is unavailable, rather than making an educated guess.

---

## 4. Memory & Context Constraints

- Do not pass entire raw tool outputs or HTML blocks into report drafting prompts.
- Wrap all tools in `SummarizedTool` to compress results >2,000 characters.
- Maintain minimal state footprint using `custom_add_with_delete` reducers in LangGraph.

---

## 5. Error Handling & Resilience

If a tool or LLM invocation fails:
1. **Retry with Exponential Backoff**: Catch transient rate limits/overloads (HTTP 429/503) and wait ($4 \times 2^{\text{attempt}} + \text{jitter}$).
2. **Alternative Tool**: Attempt query on alternative MCP search tools.
3. **Graceful Failure**: Never crash the main pipeline thread or leave database status stuck in `IN_PROGRESS`. Mark status as `FAILED` and emit an `__ERROR__` sentinel over WebSockets.

---

## 6. Security Rules

- **Path Traversal Guard**: Validate all path parameters (`..` check) before serving files.
- **No Arbitrary Code Execution**: Never evaluate untrusted code or arbitrary Python statements.
- **Credential Protection**: API keys and tokens must remain in environment variables (`.env`) and never be returned in tool logs or user reports.
- **Input Sanitization**: Validate all inputs using Pydantic models before inserting into MongoDB or passing to subprocesses.
