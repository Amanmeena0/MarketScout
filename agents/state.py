from operator import add
from langgraph.graph import  MessagesState
from typing import List,Any,Annotated

def custom_add_with_delete(left: List[str], right: str | List[str]) -> List[str]:
   
    if right == "DELETE":
        return []
    
    if isinstance(right, str):
        return left + [right]
    elif isinstance(right, list):
        return left + right
    else:
        return left

class AgentState(MessagesState):
    knowledge_gaps:str 
    filled_gaps:Annotated[List[str], custom_add_with_delete]
    k : int 
    report : str
    kg_gap: str 
