import sys
import os
# Add the root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Lemmy Tools")

LEMMY_INSTANCES = [
    "https://lemmy.ml",
    "https://lemm.ee",
    "https://lemmy.world"
]

def _try_request(endpoint: str, params: dict):
    """Try requesting from a list of Lemmy instances for robustness."""
    for instance in LEMMY_INSTANCES:
        try:
            url = f"{instance}{endpoint}"
            headers = {"User-Agent": "MarketScoutBot/1.0"}
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json(), instance
        except Exception:
            continue
    return None, None

@mcp.tool()
def get_lemmy_post_data(query: str, limit: int = 5) -> str:
    """
    Search Lemmy communities for posts and discussions related to a specific topic.
    
    Args:
        query (str): The search term to look for.
        limit (int): Maximum number of posts to return (max: 10).
        
    Returns:
        str: Comprehensive Lemmy discussion and post summary.
    """
    if limit > 10:
        limit = 10

    params = {
        "q": query,
        "type_": "Posts",
        "sort": "TopAll",
        "limit": limit
    }

    data, instance = _try_request("/api/v3/search", params)
    if not data or "posts" not in data or not data["posts"]:
        return f"No Lemmy discussions found for '{query}'"

    analysis = f"Lemmy Discussion Analysis for '{query}' (via {instance}):\n\n"
    analysis += "Key Discussions:\n"
    
    for i, item in enumerate(data["posts"], 1):
        post_data = item.get("post", {})
        creator_data = item.get("creator", {})
        community_data = item.get("community", {})
        counts = item.get("counts", {})

        title = post_data.get("name", "No Title")
        body = post_data.get("body", "")
        body_snip = (body[:250] + "...") if body and len(body) > 250 else (body or "No body content")
        
        community_name = community_data.get("name", "unknown")
        creator_name = creator_data.get("name", "anonymous")
        comment_count = counts.get("comments", 0)
        post_url = post_data.get("ap_id", "")

        analysis += f"{i}. c/{community_name}: {title}\n"
        analysis += f"   Author: u/{creator_name}\n"
        analysis += f"   Comments: {comment_count}\n"
        if post_url:
            analysis += f"   URL: {post_url}\n"
        analysis += f"   Content: {body_snip}\n\n"

    analysis += "Insights Summary:\n"
    active_communities = list(set([item.get("community", {}).get("name", "unknown") for item in data["posts"]]))
    analysis += f"- Active communities: {', '.join(active_communities)}\n"
    analysis += f"- Total posts analyzed: {len(data['posts'])}\n"
    
    return analysis

@mcp.tool()
def find_relevant_lemmy_communities(keywords: str, limit: int = 10) -> str:
    """
    Find Lemmy communities relevant to specific keywords for targeted market research.
    
    Args:
        keywords (str): Space-separated keywords or single keyword to search for.
        limit (int): Maximum number of communities to return (default: 10).
        
    Returns:
        str: Analysis of relevant Lemmy communities with insights.
    """
    params = {
        "q": keywords,
        "type_": "Communities",
        "sort": "TopAll",
        "limit": limit
    }

    data, instance = _try_request("/api/v3/search", params)
    if not data or "communities" not in data or not data["communities"]:
        return f"No Lemmy communities found for '{keywords}'"

    analysis = f"Relevant Lemmy Communities for '{keywords}' (via {instance}):\n\n"
    
    for i, item in enumerate(data["communities"], 1):
        community_data = item.get("community", {})
        counts = item.get("counts", {})
        
        name = community_data.get("name", "")
        title = community_data.get("title", "")
        description = community_data.get("description", "No description available")
        description_snip = (description[:150] + "...") if description and len(description) > 150 else description
        subscribers = counts.get("subscribers", "Unknown")

        analysis += f"{i}. c/{name} ({title})\n"
        analysis += f"   Subscribers: {subscribers}\n"
        analysis += f"   Description: {description_snip}\n\n"

    return analysis

if __name__ == "__main__":
    mcp.run('streamable-http')
