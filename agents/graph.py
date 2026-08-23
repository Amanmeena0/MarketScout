import json
import asyncio
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import List, Optional
from langchain_core.tools import BaseTool, Tool
from langgraph.config import get_stream_writer
from langgraph.types import Send
import logging
from .state import *
from .utils import *

logger = logging.getLogger("market_scout.graph")



async def make_graph(
    tools: List[BaseTool],
    reflection_instructions_prompt,
    fill_gaps_prompt,
    merge_gaps_prompt,
    model_name: Optional[str] = None,
    k: int = 3,
):
    # Resolve specialized models or respect global override
    find_gaps_llm = get_llm(model_name=model_name or report_review_model)
    tool_routing_llm = get_llm(model_name=model_name or tool_routing_model)
    report_writing_llm = get_llm(model_name=model_name or report_writing_model)

    # Wrap tools with summarization capability
    summarized_tools = wrap_tools_with_summarizer(tools)

    react_agent = create_react_agent(
        model=tool_routing_llm,
        tools=summarized_tools,
    )
    
    async def find_gaps(state: AgentState):
        logger.info("Executing node: find_gaps (iteration %d/%d)", state.get("k", 0), k)
        report = state['report'] 
        rf_prompt = reflection_instructions_prompt.invoke(
            {"report": report}
        )

        response = call_llm_with_backoff(
            find_gaps_llm, [HumanMessage(content=rf_prompt.to_string())]
        )
        response = str(response.content) if response else "No Gaps Found"

        if response.startswith("```json"):
            response = response[7:-3]  # Remove the markdown code block formatting

        return {"knowledge_gaps": response}

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
        logger.info("Executing node: fill_gaps for gap: %s", curr_gap[:100] + "..." if len(curr_gap) > 100 else curr_gap)
        
        try:
            fill_prompt = fill_gaps_prompt.invoke(
                {"gaps": curr_gap}
            )

            response = react_agent.astream(
                {"messages": [{"role": "user", "content": fill_prompt.to_string()}]},
                stream_mode=["values"],
            )
            writer = get_stream_writer()  
            ans = ""

            async for stream_mode, message in response:
                if stream_mode == "values":
                    last = message["messages"] # type: ignore
                    if isinstance(last[-1], AIMessage):
                        ans = message["messages"][-1].content  # type: ignore
                        writer({'react_agent': message}) 

            return {"filled_gaps": ans}
        except Exception as e:
            logger.warning("Error while filling gap '%s': %s", curr_gap[:60], e)
            return {"filled_gaps": f"Gap investigation note: Could not complete search for '{curr_gap[:100]}...' due to transient error ({e})."}

    async def merge_filled_gaps(state: AgentState):
        logger.info("Executing node: merge_filled_gaps")
        filled_gaps = state["filled_gaps"]
        report = state["report"]
        
        merge_prompt = merge_gaps_prompt.invoke(
            {"report": report, "filled_gaps": filled_gaps}
        )

        response = call_llm_with_backoff(
            report_writing_llm, [HumanMessage(content=merge_prompt.to_string())]
        )

        return {
            "messages": [HumanMessage(content=response.content if response else "")],
            "k": state["k"] + 1,
            "report": response.content, # type: ignore
            "filled_gaps": "DELETE"
        }

    async def route_loop(state: AgentState):
        """After merge_filled_gaps decide to iterate or finish."""
        return "find_gaps" if state["k"] < k else "final"

    async def final_node(state: AgentState):
        """Final node to return the final report."""
        logger.info("Executing node: final_node")
        return {"report": state["report"]}

    # Build the graph
    workflow = StateGraph(AgentState)
    workflow.add_node("find_gaps", find_gaps)
    workflow.add_node("fill_gaps", fill_gaps)
    workflow.add_node("merge_filled_gaps", merge_filled_gaps)
    workflow.add_node("final", final_node)

    workflow.set_entry_point("find_gaps")  # Start with finding gaps
    workflow.add_conditional_edges("find_gaps", continue_to_fill_gaps, ['fill_gaps'])  # type: ignore
    workflow.add_edge("fill_gaps", "merge_filled_gaps")
    workflow.add_conditional_edges(
        "merge_filled_gaps", route_loop, ["find_gaps", "final"]
    )
    workflow.add_edge("final", END)

    graph = workflow.compile()
    return graph
