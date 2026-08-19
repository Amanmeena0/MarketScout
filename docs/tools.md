# MarketScout Tools

## Tool Routing ReAct Agent & MCP Infrastructure

- **Google Tools**: General web search, news, business intelligence.
- **Web Scraper Tools**: In-depth web scraping and HTML text extraction.
- **YouTube Tools**: Video transcript processing and multimedia content extraction.
- **X (Twitter) Tools**: Recent tweet search, user handle profile lookup, user posts extraction, and tweet engagement metrics.

## Auto-Summarization Layer (`SummarizedTool`)
All MCP tools are wrapped in `SummarizedTool`. Any tool response exceeding 2,000 characters is automatically processed by `summarize_text` using `summarization_model` to preserve critical statistics, dates, URLs, and numbers while keeping context slim.

## Tool Usage Rules
- Always use tools before reasoning.
- Tool priority: Internal Memory -> Search APIs -> Web Crawling -> Document Retrieval -> Knowledge Base -> LLM Reasoning.
