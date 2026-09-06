import uvicorn
from fastapi import FastAPI
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from google_tools import google_mcp
from scraper_tools import scraper_mcp
from youtube_tools import youtube_mcp
from x_tools import x_mcp

app = FastAPI(title="Market Research MCP Server", version="1.0.0")

app.mount("/mcp/google",  google_mcp.sse_app())
app.mount("/mcp/scraper", scraper_mcp.sse_app())
app.mount("/mcp/youtube", youtube_mcp.sse_app())
app.mount("/mcp/x",       x_mcp.sse_app())

available_servers = []

available_servers.append("/mcp/google")
available_servers.append("/mcp/scraper")
available_servers.append("/mcp/youtube")
available_servers.append("/mcp/x")


@app.get("/")
async def root():
    return {
        "message": "Market Research MCP Server",
        "available_servers": available_servers,
        "total_servers": len(available_servers)
    }


if __name__ == "__main__":
    uvicorn.run(
        "mcp_servers.main:app",
        host="0.0.0.0",
        port=5001,
    )