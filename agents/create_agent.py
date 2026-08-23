import os
import asyncio
import logging
from markdown_pdf import MarkdownPdf, Section
from typing import List, Any, Optional

logger = logging.getLogger("market_scout.agent")
from langchain_core.tools import BaseTool
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from config.settings import output_dir
from database.storage import get_storage
from database.memory import record_tool_evidence, record_draft_report
from database.schema import AnalysisType, Status
from .utils import (
    get_llm,
    wrap_tools_with_summarizer,
    extract_llm_text,
    planner_model,
    tool_routing_model,
    evidence_analysis_model,
    report_writing_model,
)
from .graph import make_graph


# ------------------------------------------------------------------
# Public entry-point: caller provides an asyncio.Queue
# ------------------------------------------------------------------
async def create_agent(
    id: str,
    analysisType: AnalysisType,
    user_prompt: str,
    tools: List[BaseTool],
    out_queue: asyncio.Queue,
    PROMPT: Any,
    reflection_instructions_prompt: Any,
    fill_gaps_prompt: Any,
    merge_gaps_prompt: Any,
    model_name: Optional[str] = None,
    k: int = 3,
) -> None:
    id_str = str(id)
    storage = get_storage()
    logger.info("Starting agent creation for analysis ID: %s, type: %s, k iterations: %d", id_str, analysisType, k)
    try:
        # 1. Update status to IN_PROGRESS in Storage
        storage.update_analysis(id_str, {"status": Status.IN_PROGRESS.value})

        # Resolve specialized component models or respect global override
        planner_llm = get_llm(model_name=model_name or planner_model)
        tool_routing_llm = get_llm(model_name=model_name or tool_routing_model)
        evidence_analysis_llm = get_llm(model_name=model_name or evidence_analysis_model)
        report_writing_llm = get_llm(model_name=model_name or report_writing_model)

        # Wrap tools for the initial pass too to auto-summarize long outputs
        summarized_tools = wrap_tools_with_summarizer(tools)

        industry_research_agent = await make_graph(
            tools=tools,
            reflection_instructions_prompt=reflection_instructions_prompt,
            fill_gaps_prompt=fill_gaps_prompt,
            merge_gaps_prompt=merge_gaps_prompt,
            model_name=model_name,
            k=k,
        )

        # ----------------------------------------------------------
        # Step 1. PLANNER Step
        # ----------------------------------------------------------
        logger.info("[%s] Step 1: Creating detailed research plan", id_str)
        await out_queue.put("Step 1: Creating detailed research plan...\n")
        plan_prompt = (
            f"You are a master research planner. Given the user query: '{user_prompt}', create a highly detailed, "
            f"structured research plan and search strategy. Outline the key questions we need to answer, specific "
            f"data points/statistics to search for, and the sections of the report to target. Return ONLY the markdown plan."
        )
        plan_msg = await planner_llm.ainvoke([HumanMessage(content=plan_prompt)])
        research_plan = extract_llm_text(plan_msg)
        await out_queue.put(f"=== Research Plan ===\n{research_plan}\n\n")

        # ----------------------------------------------------------
        # Step 2. TOOL ROUTING Step (ReAct agent gathers evidence)
        # ----------------------------------------------------------
        logger.info("[%s] Step 2: Executing tool routing to gather evidence", id_str)
        await out_queue.put("Step 2: Executing tool routing to gather evidence...\n")
        agent_guideline = (
            f"{PROMPT}\n\n"
            f"You have been provided with the following research plan:\n{research_plan}\n\n"
            f"Your critical task is to use your tools to execute this research plan and gather all required evidence. "
            f"Do not draft the final report. Instead, output a detailed, structured collection of all facts, numbers, "
            f"URLs, and evidence you found from the tools."
        )
        react_agent = create_react_agent(model=tool_routing_llm, tools=summarized_tools, prompt=agent_guideline)
        
        gathered_evidence = []
        last_tool_call_info = {}
        async for message in react_agent.astream(
            {"messages": [{"role": "user", "content": f"Execute research plan for: {user_prompt}"}]},
            {"recursion_limit": 50},
            stream_mode="values",
        ):
            last = message["messages"][-1]
            if isinstance(last, ToolMessage):
                last_content_str = extract_llm_text(last.content)
                await out_queue.put(f"Results:\n{last_content_str}\n")
                gathered_evidence.append(f"Tool Result ({last.name}): {last_content_str}")
                
                # Real-Time Evidence Persistence
                record_tool_evidence(
                    analysis_id=id_str,
                    stage="initial_research",
                    tool_name=last.name or last_tool_call_info.get("name", "tool"),
                    tool_args=last_tool_call_info.get("args", {}),
                    tool_result=last_content_str,
                )
            elif isinstance(last, AIMessage):
                last_ai_text = extract_llm_text(last.content)
                await out_queue.put(last_ai_text)
                for tc in last.tool_calls:
                    await out_queue.put(f"Tool Call:\n {tc['name']}")
                    await out_queue.put(f"Arguments:\n {tc['args']}")
                    last_tool_call_info = {"name": tc["name"], "args": tc["args"]}
                gathered_evidence.append(last_ai_text)
                
        evidence_raw_text = "\n\n".join(gathered_evidence)

        # ----------------------------------------------------------
        # Step 3. EVIDENCE ANALYSIS Step (Synthesizes facts)
        # ----------------------------------------------------------
        logger.info("[%s] Step 3: Conducting deep evidence analysis and synthesis", id_str)
        await out_queue.put("\nStep 3: Conducting deep evidence analysis and synthesis...\n")
        analysis_prompt = (
            f"You are a Senior Evidence Analyst. Meticulously analyze all the raw tool outputs and evidence gathered "
            f"during our research on '{user_prompt}':\n\n"
            f"Gathered Evidence:\n{evidence_raw_text}\n\n"
            f"Extract, verify, and synthesize a comprehensive summary of key quantitative facts, figures, market player shares, "
            f"regulatory requirements, and links. Ensure every key claim has a corresponding citation URL."
        )
        analysis_msg = await evidence_analysis_llm.ainvoke([HumanMessage(content=analysis_prompt)])
        evidence_synthesis = extract_llm_text(analysis_msg)
        await out_queue.put(f"=== Evidence Analysis ===\n{evidence_synthesis}\n\n")

        # ----------------------------------------------------------
        # Step 4. REPORT WRITING Step (Drafts the first report)
        # ----------------------------------------------------------
        logger.info("[%s] Step 4: Writing initial comprehensive report", id_str)
        await out_queue.put("Step 4: Writing initial comprehensive report...\n")
        writing_prompt = (
            f"You are a professional report writer. Write a comprehensive, detailed markdown report for the query: '{user_prompt}'.\n"
            f"Use the synthesized evidence analysis:\n{evidence_synthesis}\n\n"
            f"Your report must follow these guidelines:\n{PROMPT}\n\n"
            f"Write the initial comprehensive draft containing all required sections."
        )
        writing_msg = await report_writing_llm.ainvoke([HumanMessage(content=writing_prompt)])
        init_report = extract_llm_text(writing_msg)
        
        # Real-time draft report persistence
        record_draft_report(id_str, init_report)
        await out_queue.put("\nInitial Draft Report Generated.\n")

        # ----------------------------------------------------------
        # LangGraph: Iterative review and gap filling
        # ----------------------------------------------------------
        final_report = ""

        async for mode, message in industry_research_agent.astream(
            {
                "knowledge_gaps": "",
                "k": 0,
                "report": init_report,
                "kg_gap": "",
            },  # type: ignore
            stream_mode=["updates", "messages", "custom"],
        ):
            if mode == "messages":
                msg, metadata = message[0], message[1]
                if msg.content and metadata["langgraph_node"] != "merge_filled_gaps" or metadata["langgraph_node"] == "find_gaps":  # type: ignore
                    await out_queue.put(msg.content)  # type: ignore

            if mode == "updates":
                if "final" in message:
                    final_report = message["final"]["report"]  # type: ignore
                if "merge_filled_gaps" in message:
                    await out_queue.put(
                        "=" * 30 + "Merging the gathered Resources" + "=" * 30 + "\n"
                    )
                    # Update intermediate report iteration in storage
                    intermediate = message["merge_filled_gaps"].get("report")
                    if intermediate:
                        record_draft_report(id_str, intermediate)
            else:
                if "react_agent" in message:
                    msg = message["react_agent"]["messages"][-1]  # type: ignore
                    await out_queue.put(msg.content)  # type: ignore
                else:
                    chunk, meta = message[0], message[1]
                    node = meta["langgraph_node"]  # type: ignore

                    if node == "tools":
                        await out_queue.put("Tool Call:\n")
                        await out_queue.put(chunk.content + "\n")  # type: ignore

        logger.info("[%s] Generating final report PDF...", id_str)
        pdf = MarkdownPdf()
        pdf.meta["title"] = analysisType.value
        pdf.add_section(Section(final_report or init_report, toc=False))

        os.makedirs(f"{output_dir}/{id_str}", exist_ok=True)
        pdf_filename = f"{analysisType.value}.pdf"
        pdf_path = os.path.join(output_dir, id_str, pdf_filename)
        pdf.save(pdf_path)

        # 2. Update status to COMPLETED in Storage
        storage.update_analysis(
            id_str,
            {
                "status": Status.COMPLETED.value,
                "report_path": f"{id_str}/{pdf_filename}",
                "draft_report": final_report or init_report,
            }
        )

        await out_queue.put(
            f"__OUTPUT_FILE__{output_dir}/{id_str}/{pdf_filename}\n"
        )
        logger.info("[%s] Agent execution completed successfully. Report saved at %s", id_str, pdf_path)

    except Exception as exc:
        logger.error("[%s] Agent execution failed: %s", id_str, exc, exc_info=True)
        # 3. Update status to FAILED while leaving all evidence intact
        storage.update_analysis(
            id_str,
            {
                "status": Status.FAILED.value,
                "error_details": f"{type(exc).__name__}: {exc}"
            }
        )
        await out_queue.put(f"__ERROR__{type(exc).__name__}: {exc}")

    finally:
        await out_queue.put(None)
