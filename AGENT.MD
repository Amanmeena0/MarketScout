# MarketScout Agent Guide

## Overview

MarketScout is a multi-agent AI research platform designed to produce high-quality market research reports using a collection of specialized agents. Every agent has a single responsibility and communicates through structured data instead of free-form conversations.

The system prioritizes:

- Modularity
- Reliability
- Reproducibility
- Tool-first reasoning
- Low resource consumption
- Easy extensibility

---

# Core Principles

## 1. Think Before Acting

Every agent must:

- Understand the request.
- Determine whether enough information exists.
- Use available tools before making assumptions.
- Never fabricate facts.

---

## 2. Tool First

Whenever information can be obtained through a tool, the tool must be used.

Priority:

1. Internal Memory
2. Search APIs
3. Web Crawling
4. Document Retrieval
5. Knowledge Base
6. LLM Reasoning

Never use the LLM to guess factual information.

---

## 3. Small Context

Agents should only receive information relevant to their task.

Avoid passing:

- Entire conversations
- Huge documents
- Irrelevant tool outputs

Instead:

- Summarize
- Compress
- Filter

---

## 4. Structured Outputs

Every agent returns structured JSON.

Never return paragraphs unless explicitly generating reports.

Example:

```json
{
  "task": "...",
  "status": "...",
  "confidence": 0.94,
  "result": {}
}
```

---

# Agent Pipeline

```
                              User Request (Query + Analysis Type)
                                                │
                                                ▼
                                    Stage 1: Planner Agent
                                 (Generates Research Strategy)
                                                │
                                                ▼
                              Stage 2: Tool Routing ReAct Agent
                             (MCP Tools: Google, Reddit, YouTube,
                              Web Scraper, Lemmy, Bluesky, etc.)
                                                │
                                                ▼
                                Stage 3: Evidence Analyst Agent
                                (Synthesizes & Verifies Facts)
                                                │
                                                ▼
                                Stage 4: Report Writer Agent
                                (Initial Comprehensive Draft)
                                                │
                                                ▼
             ┌─────────────────────────────────────────────────────────────┐
             │         Stage 5: LangGraph Reflection & Gap-Filling         │
             │                                                             │
             │                   ┌───────────────────┐                     │
             │                   │   find_gaps Node  │                     │
             │                   │(Audits for Gaps)  │                     │
             │                   └─────────┬─────────┘                     │
             │                             │                               │
             │                             ▼                               │
             │                   continue_to_fill_gaps                     │
             │                   (Fan-out Send per Gap)                    │
             │                             │                               │
             │                             ▼                               │
             │                   ┌───────────────────┐                     │
             │                   │  fill_gaps Node   │                     │
             │                   │(ReAct Tool Agent) │                     │
             │                   └─────────┬─────────┘                     │
             │                             │                               │
             │                             ▼                               │
             │                   ┌───────────────────┐                     │
             │                   │ merge_filled_gaps │                     │
             │                   │ (Integrate Info)  │                     │
             │                   └─────────┬─────────┘                     │
             │                             │                               │
             │                             ▼                               │
             │                      route_loop (k < K?) ───(Yes)───────────┘
             │                             │ (No)
             │                             ▼
             │                        final Node
             └─────────────────────────────┬───────────────────────────────┘
                                           │
                                           ▼
                               Stage 6: PDF Export & Delivery
                        (MarkdownPdf, MongoDB & WebSocket Stream)
```

---

# Supported Analysis Types

MarketScout supports specialized research analysis modes, each powered by tailored system prompts and reflection guidelines:

1. **Industry Analysis** (`INDUSTRY_ANALYSIS`): Deep-dive into market size, CAGR, growth drivers, key trends, and ecosystem mapping.
2. **Barrier Assessment** (`BARRIER_ANALYSIS`): Evaluates capital requirements, regulatory hurdles, technical complexities, and moat strength.
3. **Competitive Analysis** (`COMPETITOR_ANALYSIS`): Direct/indirect competitor profiling, feature comparison matrix, market positioning, and SWOT analysis.
4. **Market Gap Analysis** (`MARKET_GAP_ANALYSIS`): Identifies unserved customer needs, market white spaces, underserved niches, and differentiation vectors.
5. **Sales Forecasting** (`SALES_FORECASTING`): Quantitative projections, revenue modeling drivers, TAM/SAM/SOM breakdown, and growth trajectory scenarios.
6. **Target Market Segmentation** (`TARGET_MARKET_ANALYSIS`): Demographic, geographic, behavioral segmentation, customer personas, and ICP (Ideal Customer Profile) mapping.

---

# Agent Responsibilities & Architecture

---

## 1. Planner Agent

### Model Config
`planner_model` (e.g. `gemini-2.5-flash` or custom LLM override)

### Responsibility
- Analyzes user prompt and selected analysis type.
- Outlines a detailed, structured research strategy.
- Defines key questions to answer, target metrics/data points, and report sections.

---

## 2. Tool Routing ReAct Agent & MCP Infrastructure

### Model Config
`tool_routing_model`

### Tool Ecosystem (MultiServer MCP Client)
- **Google Tools**: General web search, news, business intelligence.
- **Reddit Tools**: Community discussions, user pain points, sentiment analysis.
- **Web Scraper Tools**: In-depth web scraping and HTML text extraction.
- **YouTube Tools**: Video transcript processing and multimedia content extraction.
- **Lemmy & Bluesky Tools**: Alternative social media data collection.

### Auto-Summarization Layer (`SummarizedTool`)
- All MCP tools are wrapped in `SummarizedTool`.
- Any tool response exceeding 2,000 characters is automatically processed by `summarize_text` using `summarization_model` to preserve critical statistics, dates, URLs, and numbers while keeping context slim.

---

## 3. Evidence Analyst Agent

### Model Config
`evidence_analysis_model`

### Responsibility
- Synthesizes raw tool execution output into clean factual evidence.
- Verifies market numbers, company metrics, and player market shares.
- Maps every core claim directly to citation URLs.

---

## 4. Report Writer Agent

### Model Config
`report_writing_model`

### Responsibility
- Generates the initial full-length Markdown report according to prompt registry guidelines.
- Re-invoked during gap-filling merges (`merge_filled_gaps`) to seamlessly integrate newly researched findings back into the report.

---

## 5. LangGraph Reflection & Knowledge Gap-Filling Subgraph

### Model Config
`report_review_model` (Gap detection), `tool_routing_model` (Gap resolution), `report_writing_model` (Merging)

### Nodes & Execution Flow
- **`find_gaps` Node**: Evaluates the report draft using reflection guidelines; outputs structured JSON containing detected `knowledge_gaps`.
- **`continue_to_fill_gaps` Node**: Uses LangGraph `Send` API to map-reduce / fan-out parallel research workers for each knowledge gap.
- **`fill_gaps` Node**: Spawns ReAct agents with MCP tools to research specific missing data.
- **`merge_filled_gaps` Node**: Combines newly retrieved evidence into the report draft and increments iteration counter `k`.
- **`route_loop`**: Evaluates whether `k < K` (runs up to max iterations) to determine if another gap-filling cycle is needed or to proceed to `final`.

---

## 6. PDF Export & Service Delivery

### Responsibility
- Compiles the final Markdown report into a formatted PDF using `MarkdownPdf`.
- Stores the PDF artifact in `output_dir/{analysis_id}/{analysis_type}.pdf`.
- Updates MongoDB analysis state (`IN_PROGRESS` → `COMPLETED` or `FAILED`).
- Streams real-time progress logs and file output paths over WebSockets.

---

# Communication & Execution Rules

- **Orchestrated Control Flow**: Agents do not talk to each other directly; execution is controlled via `create_agent` multi-stage pipeline and the LangGraph state machine.
- **Asynchronous Log Streaming**: Execution steps stream logs in real time to an `asyncio.Queue` connected to WebSocket endpoints (`/ws/research/{request_id}`).
- **Resilience & Rate Limiting**: LLM calls utilize `call_llm_with_backoff` with exponential backoff retry logic and an `InMemoryRateLimiter` to handle transient API overload errors (e.g., HTTP 429/503).

---

# Memory Rules

Agents should:

Store

- Search summaries
- Tool outputs
- Intermediate summaries

Do not store

- Raw HTML
- Huge PDFs
- Duplicate information

---

# Tool Usage Rules

Always use tools before reasoning.

Example:

Wrong:

LLM guesses revenue.

Correct:

Search revenue

↓

Verify

↓

Return

---

# Hallucination Prevention

Never invent:

- Statistics
- Company facts
- Funding
- Dates
- URLs
- Financial numbers
- Market sizes

If unavailable:

Return

```
Unknown
```

rather than guessing.

---

# Error Handling

If a tool fails:

Retry

↓

Alternative Tool

↓

Cached Result

↓

Graceful Failure

Never crash the pipeline.

---

# Logging

Every agent should log:

- Start time
- End time
- Execution duration
- Tools used
- Success/failure
- Token usage (if applicable)
- Errors
- Retry count

---

# Performance Guidelines

Prefer:

Parallel execution

Independent subtasks

Cached results

Incremental summarization

Avoid:

Repeated searches

Repeated crawling

Duplicate LLM calls

Huge prompts

Massive contexts

---

# Security

Never execute arbitrary code.

Never expose API keys.

Never leak internal prompts.

Never trust user-provided URLs.

Validate all external inputs.

Sanitize tool outputs.

---

# Success Criteria

A successful MarketScout execution should:

✓ Answer the user's objective completely

✓ Cite reliable sources

✓ Avoid hallucinations

✓ Produce structured outputs

✓ Be reproducible

✓ Minimize unnecessary LLM usage

✓ Handle failures gracefully

✓ Generate a polished, professional market research report