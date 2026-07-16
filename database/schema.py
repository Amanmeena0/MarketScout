from typing import Optional, Any
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


class CreateAnalysisRequest(BaseModel):
    query: str = Field(..., description="The market query or topic")
    analysis_type: AnalysisType = Field(..., description="The type of analysis to perform")
    model_name: Optional[str] = Field(default=None, description="Optional LLM model override for this analysis")

    @field_validator("analysis_type", mode="before")
    @classmethod
    def validate_analysis_type(cls, value: Any) -> AnalysisType:
        if isinstance(value, str):
            return AnalysisType.from_stable_id(value)
        return value


class AnalysisSchema(BaseModel):
    id: Optional[str] = Field(default=None, description="Unique identifier for the analysis", alias="_id") 
    query: str = Field(..., description="The market query or topic")
    analysis_type: AnalysisType = Field(..., description="The type of analysis to perform")
    model_name: Optional[str] = Field(default=None, description="Optional LLM model override for this analysis")
    status: Status = Field(default=Status.PENDING, description="The current status of the analysis")
    created_at: Optional[str] = Field(
        default_factory=lambda: datetime.datetime.now().ctime(), 
        description="The timestamp when the analysis was created"
    )
    report_path: Optional[str] = Field(default=None, description="Path to the generated report file")

    @field_validator("analysis_type", mode="before")
    @classmethod
    def validate_analysis_type(cls, value: Any) -> AnalysisType:
        if isinstance(value, str):
            return AnalysisType.from_stable_id(value)
        return value

    class Config:
        validate_by_name = True
