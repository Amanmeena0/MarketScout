import asyncio
import os
import logging
from bson import ObjectId
from bson.errors import InvalidId
from contextlib import asynccontextmanager
from typing import Dict, List

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from uvicorn import run

from config.settings import output_dir
from database.db import db
from agents.create_agent import create_agent
from database.schema import AnalysisSchema, AnalysisType, Status, CreateAnalysisRequest
from prompts.industry import *
from prompts.barrier_assessment import *
from prompts.competitive_analysis import *
from prompts.market_gap import *
from prompts.sales_forecast import *
from prompts.target_market_segmentation import *

# ---------- structured logging setup ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("market_scout")


# ---------- lifespan: MCP client ----------
class McpState:
    tools: List[BaseTool] = []


MCP_BASE = "http://localhost:5001"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing MCP client and fetching tools")
    client = MultiServerMCPClient(
        {
            "google_tools": {"url": f"{MCP_BASE}/mcp/google/sse", "transport": "sse"},
            "scraper_tools": {"url": f"{MCP_BASE}/mcp/scraper/sse", "transport": "sse"},
            "youtube_tools": {"url": f"{MCP_BASE}/mcp/youtube/sse", "transport": "sse"},
            "x_tools": {"url": f"{MCP_BASE}/mcp/x/sse", "transport": "sse"},
        }
    )
    McpState.tools = await client.get_tools()
    logger.info("Successfully fetched %d MCP tools", len(McpState.tools))

    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- exception handlers ----------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    logger.exception("Unexpected error occurred: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please check the logs."}
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
    logger.info("WebSocket connection requested for analysis %s (status: %s)", request_id, analysis.get("status") if analysis else "None")
    
    if not analysis:
        logger.warning("WebSocket closed: No analysis found for id %s", request_id)
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
        logger.info("WebSocket disconnected for analysis %s", request_id)
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
        logger.warning("Report file not found: %s", file_path)
        raise HTTPException(status_code=404, detail="File not found")

    logger.info("Serving report file: %s", file_path)
    return FileResponse(file_path)


@app.get("/analysis/{analysis_id}")
def get_analysis(analysis_id: str):
    try:
        object_id = ObjectId(analysis_id)
    except InvalidId:
        raise HTTPException(
            status_code=400, detail="Invalid analysis ID format"
        )

    analysis = db.analyses.find_one({"_id": object_id})
    if not analysis:
        logger.warning("Analysis not found: %s", analysis_id)
        raise HTTPException(status_code=404, detail="Analysis not found")

    logger.debug("Fetched analysis: %s", analysis_id)

    # Convert ObjectId back to string for JSON serialization
    analysis["_id"] = str(analysis["_id"])
    return analysis


# ---------- Prompt configurations registry ----------
PROMPTS_REGISTRY = {
    AnalysisType.INDUSTRY_ANALYSIS: {
        "PROMPT": INDUSTRY_PROMPT,
        "reflection_instructions_prompt": industry_reflection_instructions_prompt,
        "fill_gaps_prompt": industry_fill_gaps_prompt,
        "merge_gaps_prompt": industry_merge_gaps_prompt,
    },
    AnalysisType.BARRIER_ANALYSIS: {
        "PROMPT": BARRIER_ASSESSMENT_PROMPT,
        "reflection_instructions_prompt": barrier_assessment_reflection_instructions_prompt,
        "fill_gaps_prompt": barrier_assessment_fill_gaps_prompt,
        "merge_gaps_prompt": barrier_assessment_merge_gaps_prompt,
    },
    AnalysisType.COMPETITOR_ANALYSIS: {
        "PROMPT": COMPETITIVE_ANALYSIS_PROMPT,
        "reflection_instructions_prompt": competitive_analysis_reflection_instructions_prompt,
        "fill_gaps_prompt": competitive_analysis_fill_gaps_prompt,
        "merge_gaps_prompt": competitive_analysis_merge_gaps_prompt,
    },
    AnalysisType.MARKET_GAP_ANALYSIS: {
        "PROMPT": MARKET_GAP_PROMPT,
        "reflection_instructions_prompt": market_gap_reflection_instructions_prompt,
        "fill_gaps_prompt": market_gap_fill_gaps_prompt,
        "merge_gaps_prompt": market_gap_merge_gaps_prompt,
    },
    AnalysisType.SALES_FORECASTING: {
        "PROMPT": SALES_FORECAST_PROMPT,
        "reflection_instructions_prompt": sales_forecast_reflection_instructions_prompt,
        "fill_gaps_prompt": sales_forecast_fill_gaps_prompt,
        "merge_gaps_prompt": sales_forecast_merge_gaps_prompt,
    },
    AnalysisType.TARGET_MARKET_ANALYSIS: {
        "PROMPT": TARGET_MARKET_SEGMENTATION_PROMPT,
        "reflection_instructions_prompt": target_market_segmentation_reflection_instructions_prompt,
        "fill_gaps_prompt": target_market_segmentation_fill_gaps_prompt,
        "merge_gaps_prompt": target_market_segmentation_merge_gaps_prompt,
    },
}


@app.post("/analysis")
async def create_analysis(payload: CreateAnalysisRequest):
    logger.info("Received request to create analysis of type %s: %s", payload.analysis_type, payload.query)
    if not McpState.tools:
        logger.error("Analysis creation failed: MCP tools unavailable")
        raise HTTPException(status_code=503, detail="MCP tools unavailable")

    doc = AnalysisSchema(
        query=payload.query,
        analysis_type=payload.analysis_type,
        model_name=payload.model_name,
        status=Status.PENDING,
    )

    # Convert to dict for MongoDB insertion (without the id field)
    doc_dict = doc.model_dump(exclude={"id"}, by_alias=False)
    result = db.analyses.insert_one(doc_dict)
    
    # Convert ObjectId to string for use as keys and parameters
    analysis_id = str(result.inserted_id)
    logger.info("Created analysis document with ID: %s", analysis_id)
    
    q: asyncio.Queue = asyncio.Queue()
    queues[analysis_id] = q

    prompts_config = PROMPTS_REGISTRY.get(doc.analysis_type)
    if not prompts_config:
        logger.error("Unsupported analysis type: %s", doc.analysis_type)
        raise HTTPException(status_code=400, detail="Unsupported analysis type")

    task = asyncio.create_task(
        create_agent(
            id=analysis_id,
            analysisType=doc.analysis_type,
            user_prompt=doc.query,
            tools=McpState.tools,
            out_queue=q,
            PROMPT=prompts_config["PROMPT"],
            reflection_instructions_prompt=prompts_config["reflection_instructions_prompt"],
            fill_gaps_prompt=prompts_config["fill_gaps_prompt"],
            merge_gaps_prompt=prompts_config["merge_gaps_prompt"],
            model_name=doc.model_name,
        )
    )
    
    tasks[analysis_id] = task
    logger.info("Started background task for analysis %s", analysis_id)

    # clean up when done
    def _cleanup(t):
        logger.info("Cleaning up queues and tasks for analysis %s", analysis_id)
        queues.pop(analysis_id, None)
        tasks.pop(analysis_id, None)

    task.add_done_callback(_cleanup)

    return {"id": analysis_id, "status": "created"}


if __name__ == "__main__":
    run("server:app", host="0.0.0.0", port=8000, reload=True)
