# MarketScout Software Design & System Specifications

## 1. Database Schema & Data Models

MarketScout uses Pydantic schemas for data validation and MongoDB for persistent storage.

### 1.1 `AnalysisSchema` (`database/schema.py`)

```python
class AnalysisType(str, Enum):
    INDUSTRY_ANALYSIS = "INDUSTRY_ANALYSIS"
    BARRIER_ANALYSIS = "BARRIER_ANALYSIS"
    COMPETITOR_ANALYSIS = "COMPETITOR_ANALYSIS"
    MARKET_GAP_ANALYSIS = "MARKET_GAP_ANALYSIS"
    SALES_FORECASTING = "SALES_FORECASTING"
    TARGET_MARKET_ANALYSIS = "TARGET_MARKET_ANALYSIS"

class Status(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class AnalysisSchema(BaseModel):
    id: Optional[str]
    query: str
    analysis_type: AnalysisType
    model_name: Optional[str] = None
    status: Status = Status.PENDING
    report_path: Optional[str] = None
    created_at: datetime
```

---

## 2. LangGraph State Machine Specification

### 2.1 State Object (`agents/state.py`)

```python
class AgentState(MessagesState):
    knowledge_gaps: str                           # JSON string of identified gaps
    filled_gaps: Annotated[List[str], custom_add_with_delete]  # Custom reducer list
    k: int                                        # Iteration counter
    report: str                                   # Current report draft content
    kg_gap: str                                   # Transient gap descriptor for Send API
```

### 2.2 Custom Reducer (`custom_add_with_delete`)
To prevent unbounded memory growth during reflection iterations:
```python
def custom_add_with_delete(left: List[str], right: str | List[str]) -> List[str]:
    if right == "DELETE":
        return []
    if isinstance(right, str):
        return left + [right]
    elif isinstance(right, list):
        return left + right
    return left
```

---

## 3. WebSocket Real-Time Protocol

WebSocket connections connect at `/ws/research/{request_id}`.

- **Client Connect**: Validates `request_id` in MongoDB. Rejects if analysis completed/failed or ID unknown.
- **Log Chunks**: Pushes text frames directly as agents produce logs:
  - `"Step 1: Creating detailed research plan...\n"`
  - `"Tool Call: google_search | Args: ..."`
  - `"=== Evidence Analysis ===\n..."`
  - `"__OUTPUT_FILE__/path/to/report.pdf"` (Sentinel signal upon success)
  - `"__ERROR__ExceptionName: details"` (Sentinel signal upon failure)

---

## 4. Prompt Registry & Dynamic Dispatch

The server maps `AnalysisType` enum values to prompt packages in `PROMPTS_REGISTRY`:

```python
PROMPTS_REGISTRY = {
    AnalysisType.INDUSTRY_ANALYSIS: {
        "PROMPT": INDUSTRY_PROMPT,
        "reflection_instructions_prompt": industry_reflection_instructions_prompt,
        "fill_gaps_prompt": industry_fill_gaps_prompt,
        "merge_gaps_prompt": industry_merge_gaps_prompt,
    },
    # ... additional 5 analysis types
}
```

---

## 5. Model Configuration Hierarchy

Model selection defaults to `config/settings.py` values, but supports per-request overrides via payload (`model_name`):

- `planner_model`
- `tool_routing_model`
- `summarization_model`
- `evidence_analysis_model`
- `report_writing_model`
- `report_review_model`
