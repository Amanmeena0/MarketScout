import sys
import os
# Add the root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Bluesky Tools")

@mcp.tool()
def search_bluesky_posts(query: str, limit: int = 5) -> str:
    """
    Search Bluesky for posts matching a keyword or topic to analyze real-time sentiment and discussions.
    
    Args:
        query (str): The search query or hashtag.
        limit (int): Maximum number of posts to return (default: 5, max: 10).
        
    Returns:
        str: Comprehensive Bluesky post analysis with sentiment summary.
    """
    if limit > 10:
        limit = 10

    url = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
    params = {
        "q": query,
        "limit": limit
    }

    try:
        headers = {"User-Agent": "MarketScoutBot/1.0"}
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return f"Error: Failed to fetch Bluesky posts. Status code: {response.status_code}"
            
        data = response.json()
        posts = data.get("posts", [])
        
        if not posts:
            return f"No Bluesky posts found for '{query}'"
            
        analysis = f"Bluesky Real-time Discussion Analysis for '{query}':\n\n"
        analysis += "Key Posts:\n"
        
        total_likes = 0
        total_reposts = 0
        total_replies = 0
        
        for i, item in enumerate(posts, 1):
            author = item.get("author", {})
            record = item.get("record", {})
            
            author_handle = author.get("handle", "unknown")
            author_name = author.get("displayName", author_handle)
            text = record.get("text", "")
            created_at = record.get("createdAt", "")
            
            likes = item.get("likeCount", 0)
            reposts = item.get("repostCount", 0)
            replies = item.get("replyCount", 0)
            
            total_likes += likes
            total_reposts += reposts
            total_replies += replies
            
            # Format clean output
            clean_text = text.replace('\n', ' ')
            post_id = item.get("uri", "").split("/")[-1]
            post_url = f"https://bsky.app/profile/{author_handle}/post/{post_id}"
            
            analysis += f"{i}. @{author_handle} ({author_name}):\n"
            analysis += f"   Text: {clean_text}\n"
            analysis += f"   Likes: {likes} | Reposts: {reposts} | Replies: {replies}\n"
            analysis += f"   Created At: {created_at}\n"
            analysis += f"   URL: {post_url}\n\n"
            
        analysis += "Engagement & Sentiment Summary:\n"
        analysis += f"- Total posts analyzed: {len(posts)}\n"
        analysis += f"- Total likes: {total_likes} (Avg: {total_likes/len(posts):.1f} per post)\n"
        analysis += f"- Total reposts: {total_reposts}\n"
        analysis += f"- Total replies: {total_replies}\n"
        
        return analysis
        
    except Exception as e:
        return f"Error searching Bluesky: {str(e)}"

if __name__ == "__main__":
    mcp.run('streamable-http')
