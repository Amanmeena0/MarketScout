# MarketScout Product Requirements Document (PRD)

## 1. Product Overview
**MarketScout** is an autonomous multi-agent AI research platform engineered to generate comprehensive, data-driven, and highly accurate market research reports. Unlike simple chat interfaces, MarketScout operates using a multi-stage specialized agent pipeline integrated with real-time tool access via Model Context Protocol (MCP), rigorous fact verification, reflection loops, and automated PDF document delivery.

---

## 2. Core Objectives & Value Proposition
- **Automated Deep Research**: Deliver professional-grade market intelligence in minutes instead of days.
- **Zero Hallucination Guarantee**: Strictly enforce tool-based evidence gathering; factual parameters (revenue, market share, CAGR, dates) must be verified through search APIs and scrapers.
- **Structured Output Deliverables**: Generate publication-ready Markdown and downloadable PDF reports.
- **Real-Time Visibility**: Provide live progress streaming over WebSockets so users observe every step of agent planning, tool calls, and gap resolution.

---

## 3. Supported Analysis Types

MarketScout supports 6 distinct research modes, each backed by custom prompt templates and reflection rules:

1. **Industry Analysis** (`INDUSTRY_ANALYSIS`):
   - Comprehensive breakdown of market size, CAGR, growth drivers, macro trends, and value chain mapping.
2. **Barrier Assessment** (`BARRIER_ANALYSIS`):
   - Technical, financial, regulatory, and competitive moats/hurdles for new entrants.
3. **Competitive Analysis** (`COMPETITOR_ANALYSIS`):
   - Direct/indirect player matrix, feature comparisons, market share distribution, and SWOT analysis.
4. **Market Gap Analysis** (`MARKET_GAP_ANALYSIS`):
   - Unmet customer needs, underserved niches, and differentiation opportunities.
5. **Sales Forecasting** (`SALES_FORECASTING`):
   - TAM/SAM/SOM breakdown, revenue modeling drivers, and quantitative scenario forecasting.
6. **Target Market Segmentation** (`TARGET_MARKET_ANALYSIS`):
   - Demographics, psychographics, Ideal Customer Profile (ICP), and customer persona development.

---

## 4. Key Functional Requirements

### 4.1 Research Orchestration & Pipeline
- **Planning**: Generate a structured research strategy before firing tool queries.
- **Tool Routing**: Autonomous ReAct agent querying Google Search, Web Scrapers, YouTube Transcripts, Lemmy, and Bluesky.
- **Evidence Analysis**: Synthesize raw outputs into verified quantitative facts paired with source URLs.
- **Drafting & Gap-Filling**: Initial full-length report drafting followed by iterative LangGraph reflection loops ($k$ iterations) to find and research knowledge gaps.

### 4.2 API & Real-Time Communications
- **HTTP REST Endpoints**:
  - `POST /analysis`: Initialize analysis job.
  - `GET /analysis/{id}`: Fetch status and metadata.
  - `GET /reports/{id}/{file_name}`: Secure PDF document retrieval.
- **WebSocket Gateway**:
  - `/ws/research/{request_id}`: Real-time event and log stream during execution.

### 4.3 Output Generation
- Compile completed research into a structured PDF file (`MarkdownPdf`).
- Store analysis records and paths in MongoDB.

---

## 5. Non-Functional Requirements

- **Reliability & Fault Tolerance**: Automatic exponential backoff retries (`call_llm_with_backoff`) for transient HTTP 429/503 errors and LLM rate limits.
- **Performance & Token Conservation**: Automatically compress long tool outputs (>2,000 characters) via `SummarizedTool` to keep context window slim.
- **Extensibility**: Modular architecture allowing easy registration of new MCP tool servers and analysis types.
- **Security**: Strict path-traversal guards on file serving endpoints and zero execution of arbitrary unverified code.
