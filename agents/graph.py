import json
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage, AIMessage,ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import List
from langchain_core.tools import BaseTool
from langgraph.config import get_stream_writer
from langgraph.types import Send
from .state import *
from .utils import *


async def make_graph(
    tools: List[BaseTool],
    reflection_instructions_prompt,
    fill_gaps_prompt,
    merge_gaps_prompt,
    k: int = 2,
):

    llm = get_llm()

    react_agent = create_react_agent(
        model=llm,
        tools=tools,
        
    )
    
    async def find_gaps(state: AgentState):
        report = state['report'] 
        rf_prompt = reflection_instructions_prompt.invoke(
            {"report": report}
        )

        response = call_llm_with_backoff(
            llm, [HumanMessage(content=rf_prompt.to_string())]
        )
        response = str(response.content) if response else "No Gaps Found"

        if response.startswith("```json"):
            response = response[7:-3]  # Remove the markdown code block formatting

        return {"knowledge_gaps":response}

    async def continue_to_fill_gaps(state: AgentState):

        gaps = json.loads(state["knowledge_gaps"])
        knowledge_gaps = []
        for kg in gaps:
            section = kg['section']
            gap_description = kg['gap_description'] 
            impact = kg['impact']

            knowledge_gaps.append(section + "\n" + gap_description + "\n" + impact)

        return [Send("fill_gaps", {'kg_gap': kg}) for kg in knowledge_gaps]

    async def fill_gaps(state: AgentState):

        curr_gap = state["kg_gap"]
        
        fill_prompt = fill_gaps_prompt.invoke(
            {"gaps": curr_gap}
        )

        response = react_agent.astream(
            {"messages": [{"role": "user", "content": fill_prompt.to_string()}]},
            stream_mode=["values"],
        )
        writer = get_stream_writer()  
        ans = ""

        async for stream_mode,message  in response:
            if(stream_mode == "values"):
                last = message["messages"] # type: ignore
                if isinstance(last[-1], AIMessage):
                    ans = message["messages"][-1].content  # type: ignore
                    writer({'react_agent': message}) 
           

        return {"filled_gaps": ans}

    async def merge_filled_gaps(state: AgentState):
        filled_gaps = state["filled_gaps"]
        report = state["report"]
        
        merge_prompt = merge_gaps_prompt.invoke(
            {"report": report, "filled_gaps": filled_gaps}
        )

        response = call_llm_with_backoff(
            llm, [HumanMessage(content=merge_prompt.to_string())]
        )

        return {
            "messages": [HumanMessage(content=response.content if response else "")],
            "k": state["k"] + 1,
            "report": response.content , # type: ignore
            "filled_gaps":"DELETE"
        }

    async def route_loop(state: AgentState):
        """After merge_filled_gaps decide to iterate or finish."""
        return "find_gaps" if state["k"] < k else "final"

    async def final_node(state: AgentState):
        """Final node to return the final report."""
        return {"report": state["report"]}

    # 5.  Build the graph
    workflow = StateGraph(AgentState)
    workflow.add_node("find_gaps", find_gaps)
    workflow.add_node("fill_gaps", fill_gaps)
    workflow.add_node("merge_filled_gaps", merge_filled_gaps)
    workflow.add_node("final", final_node)
    

    workflow.set_entry_point("find_gaps")  # Start with finding gaps
    workflow.add_conditional_edges("find_gaps",continue_to_fill_gaps,['fill_gaps'])  # type: ignore
    workflow.add_edge("fill_gaps", "merge_filled_gaps")
    workflow.add_conditional_edges(
        "merge_filled_gaps", route_loop, ["find_gaps", "final"]
    )
    workflow.add_edge("final", END)

    graph = workflow.compile()
    # graph.get_graph().draw_mermaid_png(output_file_path="./graph.png")

    return graph
