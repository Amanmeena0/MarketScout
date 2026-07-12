import sys
import os
# Add the mcp_server directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import praw
from config import *
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Reddit Tools")

CLIENT_ID = reddit_client_id
CLIENT_SECRET = reddit_secret
REDDIT_USERNAME = reddit_username
REDDIT_PASSWORD = reddit_password

try:
    if CLIENT_ID and CLIENT_SECRET and REDDIT_USERNAME and REDDIT_PASSWORD:
        USER_AGENT = f"MySearchScript/1.0 by u/{REDDIT_USERNAME}"
        reddit = praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            username=REDDIT_USERNAME,
            password=REDDIT_PASSWORD,
            user_agent=USER_AGENT,
        )
    else:
        reddit = None
        
except Exception as e:
    reddit = None
    




@mcp.tool()
def get_reddit_post_data(query: str, subreddit_name: str = "all", max_posts: int = 5) -> str:
    """
    Search Reddit for posts and comments related to a specific topic.
    
    Args:
        query (str): The search term to look for
        subreddit_name (str): The subreddit to search in (default: "all")
        max_posts (int): Maximum number of posts to return (max: 10)
        
    Returns:
        str: Comprehensive Reddit sentiment and discussion analysis
    """
    try:
        if not reddit:
            
            return "Error: Reddit client not initialized. Check credentials"

        if max_posts > 10:
            max_posts = 10

        subreddit = reddit.subreddit(subreddit_name)
        search_results = list(subreddit.search(query, sort='relevance', limit=max_posts))

        if not search_results:
            all_reddits = reddit.subreddit("all")
            search_results = list(all_reddits.search(query, sort='relevance', limit=max_posts))

        if not search_results:
            
            return f"No Reddit discussions found for '{query}'"

        analysis = f"Reddit Discussion Analysis for '{query}':\n\n"
        analysis += f"Analysis Summary:\n"
        analysis += f"- Posts analyzed: {len(search_results)}\n"
        analysis += f"- Subreddit: r/{subreddit_name}\n\n"
        
        total_comments = 0
        
        analysis += "Key Discussions:\n"
        
        for i, submission in enumerate(search_results, 1):
            comment_count = submission.num_comments
            total_comments += comment_count
            
            analysis += f"{i}. r/{submission.subreddit.display_name}: {submission.title}\n"
            analysis += f"   Comments: {comment_count}\n"
            analysis += f"   URL: https://reddit.com{submission.permalink}\n\n"
        
        analysis += "Key Discussions:\n"
        
        for i, submission in enumerate(search_results, 1):
            comment_count = submission.num_comments
            total_comments += comment_count
           
            analysis += f"{i}. r/{submission.subreddit.display_name}: {submission.title}\n"
            analysis += f"   Comments: {comment_count}\n"
            analysis += f"   URL: https://reddit.com{submission.permalink}\n"
            
            # Get top 10 comments
            submission.comments.replace_more(limit=0)
            top_comments = submission.comments.list()[:10]
            
            if top_comments:
                analysis += f"   Top Comments:\n"
            for j, comment in enumerate(top_comments, 1):
                comment_text = comment.body.replace('\n', ' ') # type: ignore
                analysis += f"     {j}. {comment_text}...\n"
            
            analysis += "\n"
        
        analysis += f"Overall Insights:\n"
        analysis += f"- Total comments analyzed: {total_comments}\n"
        analysis += f"- Most active discussions found in: {', '.join(set([s.subreddit.display_name for s in search_results]))}\n"
        
        
        return analysis
    except Exception as e:
        
        return f"Error searching Reddit"

@mcp.tool()
def find_relevant_subreddits(keywords: str, limit: int = 10) -> str:
    """
    Find subreddits relevant to specific keywords for targeted market research.
    
    Args:
        keywords (str): Space-separated keywords to search for
        limit (int): Maximum number of subreddits to return (default: 10)
        
    Returns:
        str: Analysis of relevant subreddits with community insights
    """
    try:
        if not reddit:
            
            return "Error: Reddit client not initialized. Check credentials"

        keywords_list = keywords.split()
        query = " ".join(keywords_list)
        
        subreddits_list = list(reddit.subreddits.search(query, limit=limit))
        subreddit_data = []
        
        for sub in subreddits_list:
            try:
                subreddit_data.append({
                    'name': sub.display_name,
                    'description': sub.public_description or 'No description available',
                    'subscribers': getattr(sub, 'subscribers', 'Unknown')
                })
            except Exception:
                
                continue  # Skip subreddits that can't be accessed
        
        if not subreddit_data:
            return f"No subreddits found for keywords: '{query}'"
        
        analysis = f"Relevant Subreddits Analysis for '{query}':\n\n"
        analysis += f"Found {len(subreddit_data)} relevant communities:\n\n"
        
        for i, sub in enumerate(subreddit_data, 1):
            analysis += f"{i}. r/{sub['name']}\n"
            analysis += f"   Subscribers: {sub['subscribers']}\n"
            analysis += f"   Description: {sub['description'][:100]}...\n\n"
        
        analysis += "Community Insights:\n"
        analysis += f"- Total communities found: {len(subreddit_data)}\n"
        analysis += f"- Search keywords: {keywords}\n"
        analysis += f"- These communities can provide valuable market insights and customer feedback\n"
        
        
        return analysis
    except Exception as e:
        
        return f"Error finding subreddits"

if __name__ == "__main__":
    mcp.run('streamable-http')