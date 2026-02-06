from pydantic import BaseModel, Field
from typing import Optional, List


class EvaluatorAnalysis(BaseModel):
    analysis_completed: bool = Field(description="A boolean value indicating if the analysis of a stock is analysed correctly, or there were no information about a specific stock")
    analysis_completed_reason: Optional[str] = Field(description="A summary of why does the evaulator think that the analysis of a stock is completed")

class GuardRailAnalysis(BaseModel):
    guardrail_analysis_completed: bool = Field(description="A boolean value indicating if a user included more or equal to 6 stocks in its prompt. If yes give True back. If he gave 1,2,3,4,5 stocks return False")
    guardrail_analysis_completed_reason: Optional[str] = Field(description="A summary of why does the guardrail thinks that the analysis should not be done")
    list_of_stocks: List[str] = Field(description="A list of all stocks that the user wants to analyze")

class SummaryAnalysis(BaseModel):
    summary: str = Field(description="a summary of input in html format. Add colors and font sizes for better outcome")