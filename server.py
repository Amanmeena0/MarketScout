import asyncio

import os
from bson import ObjectId
from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from uvicorn import run

from config.settings import output_dir
from database.db import db
from agents.create_agent import create_agent
from database.schema import AnalysisSchema, AnalysisType, Status 
from prompts.industry import *
from prompts.barrier_assessment import *
from prompts.competitive_analysis import *
from prompts.market_gap import *
from prompts.sales_forecast import *
from prompts.target_market_segmentation import *


# ---------- lifespan: MCP client ----------
class McpState:
    tools: List[BaseTool] = []


MCP_BASE = "http://localhost:5000"


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = MultiServerMCPClient(
        {
            "google_tools": {"url": f"{MCP_BASE}/mcp/google/sse", "transport": "sse"},
            "reddit_tools": {"url": f"{MCP_BASE}/mcp/reddit/sse", "transport": "sse"},
            "scraper_tools": {"url": f"{MCP_BASE}/mcp/scraper/sse", "transport": "sse"},
            "youtube_tools": {"url": f"{MCP_BASE}/mcp/youtube/sse", "transport": "sse"},
        }
    )
    McpState.tools = await client.get_tools()

    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- global queues & tasks ----------
queues: Dict[str, asyncio.Queue] = {}
tasks: Dict[str, asyncio.Task] = {}


# ---------- HTTP: start the job ----------
class ResearchRequest(BaseModel):
    user_prompt: str


# ---------- WebSocket ----------
@app.websocket("/ws/research/{request_id}")
async def websocket_research(websocket: WebSocket, request_id: str):
    await websocket.accept()

    analysis = db.analyses.find_one({"_id": ObjectId(request_id)})
    print(f"WebSocket connection for analysis {request_id} with status {analysis}")
    if not analysis:
        await websocket.close(code=1008, reason="No analysis found for this id")
        return

    if analysis["status"] == Status.COMPLETED:
        await websocket.close(code=1008, reason="Analysis already completed")
        return

    if analysis["status"] == Status.FAILED:
        await websocket.close(code=1008, reason="Analysis failed")
        return

    q = queues.get(request_id)

    if not q:
        await websocket.close(code=1008, reason="Unknown id")
        return

    try:
        while True:
            chunk = await q.get()
            if chunk is None:  # sentinel
                await websocket.close()
                break
            await websocket.send_text(chunk)
    except WebSocketDisconnect:
        # client closed tab – task keeps running
        pass


@app.get("/reports/{rid}/{file_id}")
def serve_user_file(
    rid: str,
    file_id: str,
):
    # 1. Path traversal guard
    if ".." in file_id:
        raise HTTPException(status_code=400, detail="Bad path")

    # 2. Authorization: token sub must match url user_id
    # if token_user != user_id:
    #     raise HTTPException(status_code=403, detail="Forbidden")

    # 3. Build safe path
    file_path = os.path.join(output_dir, rid, file_id)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path)


@app.get("/analysis/{analysis_id}")
def get_analysis(analysis_id: str):
    try:
        object_id = ObjectId(analysis_id)
        analysis = db.analyses.find_one({"_id": object_id})

        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")

        # Convert ObjectId back to string for JSON serialization
        analysis["_id"] = str(analysis["_id"])
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid analysis ID format: {str(e)}"
        )


@app.post("/analysis")
async def create_analysis(req: Request):
    if not McpState.tools:
        raise HTTPException(status_code=503, detail="MCP tools unavailable")

    data = await req.json()

    if "query" not in data:
        raise HTTPException(status_code=400, detail="Missing query")

    if "analysis_type" not in data:
        raise HTTPException(status_code=400, detail="Missing analysis_type")

    doc = AnalysisSchema(
        query=data["query"],
        analysis_type=data["analysis_type"],
        status=Status.PENDING,
    )

    # Convert to dict for MongoDB insertion (without the id field)
    doc_dict = doc.model_dump(exclude={"id"}, by_alias=False)
    result = db.analyses.insert_one(doc_dict)
    
    # Convert ObjectId to string for use as keys and parameters
    analysis_id = str(result.inserted_id)
    
    q: asyncio.Queue = asyncio.Queue()
    queues[analysis_id] = q

    task = None
    if doc.analysis_type == AnalysisType.INDUSTRY_ANALYSIS:
        task = asyncio.create_task(
            create_agent(
                id=analysis_id,
                analysisType=doc.analysis_type,
                user_prompt=doc.query,
                tools=McpState.tools,
                out_queue=q,
                PROMPT=INDUSTRY_PROMPT,
                reflection_instructions_prompt=industry_reflection_instructions_prompt,
                fill_gaps_prompt=industry_fill_gaps_prompt,
                merge_gaps_prompt=industry_merge_gaps_prompt,
            )
        )
    elif doc.analysis_type == AnalysisType.BARRIER_ANALYSIS:
        task = asyncio.create_task(
            create_agent(
                id=analysis_id,
                analysisType=doc.analysis_type,
                user_prompt=doc.query,
                tools=McpState.tools,
                out_queue=q,
                PROMPT=BARRIER_ASSESSMENT_PROMPT,
                reflection_instructions_prompt=barrier_assessment_reflection_instructions_prompt,
                fill_gaps_prompt=barrier_assessment_fill_gaps_prompt,
                merge_gaps_prompt=barrier_assessment_merge_gaps_prompt,
            )
        )
    elif doc.analysis_type == AnalysisType.COMPETITOR_ANALYSIS:
        task = asyncio.create_task(
            create_agent(
                id=analysis_id,
                analysisType=doc.analysis_type,
                user_prompt=doc.query,
                tools=McpState.tools,
                out_queue=q,
                PROMPT=COMPETITIVE_ANALYSIS_PROMPT,
                reflection_instructions_prompt=competitive_analysis_reflection_instructions_prompt,
                fill_gaps_prompt=competitive_analysis_fill_gaps_prompt,
                merge_gaps_prompt=competitive_analysis_merge_gaps_prompt,
            )
        )
    elif doc.analysis_type == AnalysisType.MARKET_GAP_ANALYSIS:
        task = asyncio.create_task(
            create_agent(
                id=analysis_id,
                analysisType=doc.analysis_type,
                user_prompt=doc.query,
                tools=McpState.tools,
                out_queue=q,
                PROMPT=MARKET_GAP_PROMPT,
                reflection_instructions_prompt=market_gap_reflection_instructions_prompt,
                fill_gaps_prompt=market_gap_fill_gaps_prompt,
                merge_gaps_prompt=market_gap_merge_gaps_prompt,
            )
        )
    elif doc.analysis_type == AnalysisType.SALES_FORECASTING:
        task = asyncio.create_task(
            create_agent(
                id=analysis_id,
                analysisType=doc.analysis_type,
                user_prompt=doc.query,
                tools=McpState.tools,
                out_queue=q,
                PROMPT=SALES_FORECAST_PROMPT,
                reflection_instructions_prompt=sales_forecast_reflection_instructions_prompt,
                fill_gaps_prompt=sales_forecast_fill_gaps_prompt,
                merge_gaps_prompt=sales_forecast_merge_gaps_prompt,
            )
        )
    elif doc.analysis_type == AnalysisType.TARGET_MARKET_ANALYSIS:
        task = asyncio.create_task(
            create_agent(
                id=analysis_id,
                analysisType=doc.analysis_type,
                user_prompt=doc.query,
                tools=McpState.tools,
                out_queue=q,
                PROMPT=TARGET_MARKET_SEGMENTATION_PROMPT,
                reflection_instructions_prompt=target_market_segmentation_reflection_instructions_prompt,
                fill_gaps_prompt=target_market_segmentation_fill_gaps_prompt,
                merge_gaps_prompt=target_market_segmentation_merge_gaps_prompt,
            )
        )
    
    if task is None:
        raise HTTPException(status_code=400, detail="Unsupported analysis type")
    
    tasks[analysis_id] = task

    # clean up when done
    def _cleanup(t):
        db.analyses.update_one(
            {"_id": result.inserted_id},
            {"$set": {"status": Status.COMPLETED, "report_path": f"{analysis_id}/{doc.analysis_type}.pdf"}}
        )
        queues.pop(analysis_id, None)
        tasks.pop(analysis_id, None)
        

    task.add_done_callback(_cleanup)

    return {"id": str(result.inserted_id), "status": "created"}


if __name__ == "__main__":
    run("server:app", host="0.0.0.0", port=8000, reload=True)
