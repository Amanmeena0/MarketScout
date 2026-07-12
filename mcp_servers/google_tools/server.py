import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from mcp.server.fastmcp import FastMCP
# from tools import *
from .tools import *


mcp = FastMCP("Google Tools")

mcp.add_tool(google_search)
mcp.add_tool(search_google_shopping)
mcp.add_tool(search_google_news)
mcp.add_tool(google_trends_summary)

# if __name__ == "__main__":
#     mcp.run('streamable-http',mount_path='/mcp')