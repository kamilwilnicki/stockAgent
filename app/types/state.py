from typing import Annotated, TypedDict, Optional
from langgraph.graph import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]
    current_messages_worker: list
    stocks_list: list
    stock_completed: Optional[list]
    stock_analysis: Optional[list]
    analysis_completed: bool
    reason_for_completed: Optional[str]
    feedback_on_work: Optional[str]
    wrong_evaluation: Optional[int]