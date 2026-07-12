import sys
import os
# Add the root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Reddit Tools")

@mcp.tool()
def get_reddit_post_data(query: str, subreddit_name: str = "all", max_posts: int = 5) -> str:
    """
    Search Reddit for posts and comments related to a specific topic using keyless public JSON endpoints.
    
    Args:
        query (str): The search term to look for
        subreddit_name (str): The subreddit to search in (default: "all")
        max_posts (int): Maximum number of posts to return (max: 10)
        
    Returns:
        str: Comprehensive Reddit sentiment and discussion analysis
    """
    try:
        if max_posts > 10:
            max_posts = 10

        # Construct the Reddit search URL
        if subreddit_name.lower() == "all":
            url = "https://www.reddit.com/search.json"
            params = {
                "q": query,
                "limit": max_posts,
                "sort": "relevance"
            }
        else:
            url = f"https://www.reddit.com/r/{subreddit_name}/search.json"
            params = {
                "q": query,
                "limit": max_posts,
                "sort": "relevance",
                "restrict_sr": "on"
            }

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 MarketScoutBot/1.0"
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return f"Error searching Reddit: HTTP {response.status_code}"

        data = response.json()
        children = data.get("data", {}).get("children", [])

        if not children:
            return f"No Reddit discussions found for '{query}'"

        analysis = f"Reddit Discussion Analysis for '{query}':\n\n"
        analysis += f"Analysis Summary:\n"
        analysis += f"- Posts analyzed: {len(children)}\n"
        analysis += f"- Subreddit: r/{subreddit_name}\n\n"
        
        total_comments = 0
        analysis += "Key Discussions:\n"
        
        for i, item in enumerate(children, 1):
            post = item.get("data", {})
            title = post.get("title", "No Title")
            subreddit = post.get("subreddit", "unknown")
            num_comments = post.get("num_comments", 0)
            permalink = post.get("permalink", "")
            post_url = f"https://www.reddit.com{permalink}"
            
            total_comments += num_comments
            analysis += f"{i}. r/{subreddit}: {title}\n"
            analysis += f"   Comments: {num_comments}\n"
            analysis += f"   URL: {post_url}\n"
            
            # Fetch comments for this post if permalink exists
            if permalink:
                try:
                    comment_url = f"https://www.reddit.com{permalink}.json"
                    comment_resp = requests.get(comment_url, headers=headers, timeout=5)
                    if comment_resp.status_code == 200:
                        comment_data = comment_resp.json()
                        # Reddit comment response is a list of two items, the second item is the comments list
                        if isinstance(comment_data, list) and len(comment_data) > 1:
                            comments_list = comment_data[1].get("data", {}).get("children", [])[:5] # limit top 5 comments
                            if comments_list:
                                analysis += "   Top Comments:\n"
                                for j, comment_item in enumerate(comments_list, 1):
                                    c_data = comment_item.get("data", {})
                                    body = c_data.get("body", "")
                                    if body:
                                        body_clean = body.replace('\n', ' ')
                                        body_snip = (body_clean[:150] + "...") if len(body_clean) > 150 else body_clean
                                        analysis += f"     {j}. {body_snip}\n"
                except Exception:
                    pass
            analysis += "\n"
            
        analysis += "Overall Insights:\n"
        analysis += f"- Total comments across posts: {total_comments}\n"
        subreddits_found = list(set([item.get("data", {}).get("subreddit", "unknown") for item in children]))
        analysis += f"- Most active discussions found in: {', '.join(subreddits_found)}\n"
        
        return analysis
    except Exception as e:
        return f"Error searching Reddit: {str(e)}"

@mcp.tool()
def find_relevant_subreddits(keywords: str, limit: int = 10) -> str:
    """
    Find subreddits relevant to specific keywords for targeted market research using public endpoints.
    
    Args:
        keywords (str): Space-separated keywords to search for
        limit (int): Maximum number of subreddits to return (default: 10)
        
    Returns:
        str: Analysis of relevant subreddits with community insights
    """
    try:
        url = "https://www.reddit.com/subreddits/search.json"
        params = {
            "q": keywords,
            "limit": limit
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 MarketScoutBot/1.0"
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return f"Error searching subreddits: HTTP {response.status_code}"
            
        data = response.json()
        children = data.get("data", {}).get("children", [])
        
        if not children:
            return f"No subreddits found for keywords: '{keywords}'"
            
        analysis = f"Relevant Subreddits Analysis for '{keywords}':\n\n"
        analysis += f"Found {len(children)} relevant communities:\n\n"
        
        for i, item in enumerate(children, 1):
            sub = item.get("data", {})
            name = sub.get("display_name", "")
            title = sub.get("title", "")
            description = sub.get("public_description", "No description available")
            subscribers = sub.get("subscribers", "Unknown")
            
            description_clean = description.replace('\n', ' ')
            description_snip = (description_clean[:120] + "...") if len(description_clean) > 120 else description_clean
            
            analysis += f"{i}. r/{name} ({title})\n"
            analysis += f"   Subscribers: {subscribers}\n"
            analysis += f"   Description: {description_snip}\n\n"
            
        analysis += "Community Insights:\n"
        analysis += f"- Total communities found: {len(children)}\n"
        analysis += f"- Search keywords: {keywords}\n"
        analysis += "- These communities can provide valuable market insights and customer feedback\n"
        
        return analysis
    except Exception as e:
        return f"Error finding subreddits: {str(e)}"

if __name__ == "__main__":
    mcp.run('streamable-http')