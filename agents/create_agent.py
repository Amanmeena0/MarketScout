import os
import asyncio
from markdown_pdf import MarkdownPdf, Section
from typing import List
from langchain_core.tools import BaseTool
from langchain_core.messages import ToolMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from config.settings import output_dir
from .utils import get_llm
from .graph import make_graph


# ------------------------------------------------------------------
# Public entry-point: caller provides an asyncio.Queue
# ------------------------------------------------------------------
async def create_agent(
    id: str,
    analysisType: str,
    user_prompt: str,
    tools: List[BaseTool],
    out_queue: asyncio.Queue,
    PROMPT: str,
    reflection_instructions_prompt,
    fill_gaps_prompt,
    merge_gaps_prompt,
) -> None:
    # Convert id to string in case it's an ObjectId
    id_str = str(id)
    try:
        llm = get_llm()

        industry_research_agent = await make_graph(
            tools=tools,
            reflection_instructions_prompt=reflection_instructions_prompt,
            fill_gaps_prompt=fill_gaps_prompt,
            merge_gaps_prompt=merge_gaps_prompt,
        )

        react_agent = create_react_agent(model=llm, tools=tools, prompt=PROMPT)

        # ----------------------------------------------------------
        # 1. Initial REACT pass
        # ----------------------------------------------------------
        init_report = ""

        async for message in react_agent.astream(
            {"messages": [{"role": "user", "content": user_prompt}]},
            {"recursion_limit": 50},
            stream_mode="values",
        ):
            last = message["messages"][-1]
            if isinstance(last, ToolMessage):
                await out_queue.put(f"Results:\n{last.content}\n")
            elif isinstance(last, AIMessage):
                await out_queue.put(last.content)
                for tc in last.tool_calls:
                    await out_queue.put(f"Tool Call:\n {tc['name']}")
                    await out_queue.put(f"Arguments:\n {tc['args']}")
                init_report = last.content

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

        print("Generating final report...")
        pdf = MarkdownPdf()
        pdf.meta["title"] = analysisType
        pdf.add_section(Section(final_report, toc=False))

        os.makedirs(f"{output_dir}/{id_str}", exist_ok=True)
        pdf.save(os.path.join(output_dir, id_str, f"{analysisType}.pdf"))

        await out_queue.put(
            f"__OUTPUT_FILE__{output_dir}/{id_str}/{analysisType}.pdf\n"
        )

    except Exception as exc:

        print(exc)
        await out_queue.put(f"__ERROR__{type(exc).__name__}: {exc}")

    finally:

        await out_queue.put(None)
