from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum
import time
import datetime


class AnalysisType(str, Enum):
    INDUSTRY_ANALYSIS = 'Industry Report',
    COMPETITOR_ANALYSIS = 'Competitor Report',
    MARKET_GAP_ANALYSIS = 'Market Gap Report',
    TARGET_MARKET_ANALYSIS = 'Target Market Report',
    BARRIER_ANALYSIS = 'Barrier Report',
    SALES_FORECASTING = 'Sales Forecast Report',


class Status(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisSchema(BaseModel):
    id: Optional[str] = Field(default=None, description="Unique identifier for the analysis", alias="_id") 
    query: str = Field(..., description="The market query or topic")
    analysis_type: AnalysisType = Field(..., description="The type of analysis to perform")
    status: Status = Field(default=Status.PENDING, description="The current status of the analysis")
    created_at: Optional[str] = Field(default=datetime.datetime.now().ctime(), description="The timestamp when the analysis was created")
    report_path: Optional[str] = Field(default=None, description="Path to the generated report file")

    class Config:
        validate_by_name = True
