from typing import Optional, Any, Dict, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import datetime


class AnalysisType(str, Enum):
    INDUSTRY_ANALYSIS = 'Industry Report'
    COMPETITOR_ANALYSIS = 'Competitor Report'
    MARKET_GAP_ANALYSIS = 'Market Gap Report'
    TARGET_MARKET_ANALYSIS = 'Target Market Report'
    BARRIER_ANALYSIS = 'Barrier Report'
    SALES_FORECASTING = 'Sales Forecast Report'

    @property
    def stable_id(self) -> str:
        _stable_ids = {
            AnalysisType.INDUSTRY_ANALYSIS: 'industry_analysis',
            AnalysisType.COMPETITOR_ANALYSIS: 'competitor_analysis',
            AnalysisType.MARKET_GAP_ANALYSIS: 'market_gap_analysis',
            AnalysisType.TARGET_MARKET_ANALYSIS: 'target_market_analysis',
            AnalysisType.BARRIER_ANALYSIS: 'barrier_analysis',
            AnalysisType.SALES_FORECASTING: 'sales_forecasting',
        }
        return _stable_ids[self]

    @classmethod
    def from_stable_id(cls, value: str) -> "AnalysisType":
        _from_stable_id = {
            'industry_analysis': cls.INDUSTRY_ANALYSIS,
            'competitor_analysis': cls.COMPETITOR_ANALYSIS,
            'market_gap_analysis': cls.MARKET_GAP_ANALYSIS,
            'target_market_analysis': cls.TARGET_MARKET_ANALYSIS,
            'target_market_segmentation': cls.TARGET_MARKET_ANALYSIS,
            'barrier_analysis': cls.BARRIER_ANALYSIS,
            'sales_forecasting': cls.SALES_FORECASTING,
            'sales_forecast': cls.SALES_FORECASTING,
        }
        if value in _from_stable_id:
            return _from_stable_id[value]
        
        # Fallback to checking by value (e.g. 'Industry Report') or key name (e.g. 'INDUSTRY_ANALYSIS')
        for member in cls:
            if member.value.lower() == value.lower() or member.name.lower() == value.lower():
                return member
                
        raise ValueError(
            f"Unknown analysis type '{value}'. "
            f"Expected one of: {', '.join(list(_from_stable_id.keys()))}"
        )


class Status(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ResearchDepth(str, Enum):
    QUICK = "quick"
    COMPREHENSIVE = "comprehensive"
    DEEP_RESEARCH = "deep_research"

    @property
    def iterations_count(self) -> int:
        mapping = {
            ResearchDepth.QUICK: 2,
            ResearchDepth.COMPREHENSIVE: 3,
            ResearchDepth.DEEP_RESEARCH: 5,
        }
        return mapping.get(self, 3)

    @classmethod
    def from_value(cls, value: Optional[str]) -> "ResearchDepth":
        if not value:
            return cls.COMPREHENSIVE
        v = str(value).lower().strip()
        if v in ("quick", "2"):
            return cls.QUICK
        elif v in ("deep_research", "deep", "deepresearch", "5"):
            return cls.DEEP_RESEARCH
        return cls.COMPREHENSIVE


class ResearchObjective(BaseModel):
    type: Optional[str] = Field(default="understand_market", description="Objective identifier")
    description: Optional[str] = Field(default=None, description="Human readable label")
    custom_objective: Optional[str] = Field(default=None, description="Custom user objective if type == 'other'")


class ResearchContext(BaseModel):
    geography: Optional[str] = None
    target_customer: Optional[str] = None
    business_stage: Optional[str] = None
    time_horizon: Optional[str] = None
    business_model: Optional[str] = None
    investment_range: Optional[str] = None
    competitors: Optional[Any] = None
    comparison_criteria: Optional[List[str]] = None
    gap_types: Optional[List[str]] = None
    barrier_categories: Optional[List[str]] = None
    forecast_period: Optional[str] = None
    current_sales: Optional[str] = None
    historical_sales_data: Optional[str] = None
    assumptions: Optional[str] = None

    class Config:
        extra = "allow"


class CreateAnalysisRequest(BaseModel):
    market_topic: Optional[str] = Field(default=None, description="User query / market topic")
    query: Optional[str] = Field(default=None, description="Backward compatibility query string")
    analysis_type: AnalysisType = Field(..., description="The type of analysis to perform")
    geography: Optional[str] = Field(default="Global", description="Geography focus")
    objective: Optional[ResearchObjective] = Field(default_factory=ResearchObjective)
    decision_question: Optional[str] = Field(default=None, description="Concrete business decision question")
    context: Optional[ResearchContext] = Field(default_factory=ResearchContext)
    analysis_parameters: Optional[Dict[str, Any]] = Field(default_factory=dict)
    research_depth: Optional[ResearchDepth] = Field(default=ResearchDepth.COMPREHENSIVE)
    additional_context: Optional[str] = Field(default=None, description="Free-form constraints or notes")
    model_name: Optional[str] = Field(default=None, description="Optional LLM model override")

    @field_validator("analysis_type", mode="before")
    @classmethod
    def validate_analysis_type(cls, value: Any) -> AnalysisType:
        if isinstance(value, str):
            return AnalysisType.from_stable_id(value)
        return value

    @field_validator("research_depth", mode="before")
    @classmethod
    def validate_research_depth(cls, value: Any) -> ResearchDepth:
        if isinstance(value, ResearchDepth):
            return value
        return ResearchDepth.from_value(value)

    @property
    def effective_topic(self) -> str:
        return self.market_topic or self.query or "Market Analysis"

    @property
    def k_iterations(self) -> int:
        depth = self.research_depth or ResearchDepth.COMPREHENSIVE
        return depth.iterations_count


class SearchEvidenceItem(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now().ctime())
    stage: str = "initial_research"  # 'initial_research' or 'fill_gaps'
    tool_name: str
    query_or_url: str = ""
    content_snippet: str = ""
    extracted_urls: List[str] = []


class AnalysisSchema(BaseModel):
    id: Optional[str] = Field(default=None, description="Unique identifier for the analysis", alias="_id")
    query: str = Field(..., description="The market query or topic")
    market_topic: Optional[str] = Field(default=None)
    analysis_type: AnalysisType = Field(..., description="The type of analysis to perform")
    geography: Optional[str] = Field(default="Global")
    objective: Optional[Dict[str, Any]] = None
    decision_question: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    analysis_parameters: Optional[Dict[str, Any]] = None
    research_depth: Optional[str] = "comprehensive"
    additional_context: Optional[str] = None
    model_name: Optional[str] = Field(default=None, description="Optional LLM model override for this analysis")
    status: Status = Field(default=Status.PENDING, description="The current status of the analysis")
    created_at: Optional[str] = Field(
        default_factory=lambda: datetime.datetime.now().ctime(), 
        description="The timestamp when the analysis was created"
    )
    report_path: Optional[str] = Field(default=None, description="Path to the generated report file")
    draft_report: Optional[str] = Field(default=None, description="Intermediate report draft markdown")
    evidence: List[SearchEvidenceItem] = Field(default_factory=list, description="Real-time search outputs & extracted URLs")
    error_details: Optional[str] = Field(default=None, description="Diagnostic error details if failed")

    @field_validator("analysis_type", mode="before")
    @classmethod
    def validate_analysis_type(cls, value: Any) -> AnalysisType:
        if isinstance(value, str):
            return AnalysisType.from_stable_id(value)
        return value

    class Config:
        validate_by_name = True
        extra = "allow"
