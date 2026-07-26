import sys
import os
import json

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import requests
from requests_oauthlib import OAuth1
from config import (
    x_bearer_token,
    x_api_key,
    x_api_secret,
    x_access_token,
    x_access_token_secret,
    serp_dev_api_key,
)
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("X Tools")

X_API_BASE = "https://api.twitter.com/2"


def _get_auth():
    """
    Returns (auth_obj, headers_dict) depending on available credentials.
    Supports both OAuth 1.0a User Context and Bearer Token.
    """
    if x_api_key and x_api_secret and x_access_token and x_access_token_secret:
        return OAuth1(x_api_key, x_api_secret, x_access_token, x_access_token_secret), {"User-Agent": "MarketScout/1.0"}
    
    if x_bearer_token:
        headers = {
            "Authorization": f"Bearer {x_bearer_token}",
            "User-Agent": "MarketScout/1.0"
        }
        return None, headers

    return None, None


def _serp_fallback_search(search_query: str, header_title: str, max_results: int = 10) -> str:
    """Fallback search using SERP web indexing when official X API v2 is restricted (Free Tier)."""
    if not serp_dev_api_key:
        return ""
    try:
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": f"site:x.com {search_query}"})
        headers = {
            "X-API-KEY": serp_dev_api_key,
            "Content-Type": "application/json"
        }
        res = requests.post(url, headers=headers, data=payload, timeout=10)
        if res.status_code != 200:
            return ""
        
        data = res.json()
        organic = data.get("organic", [])
        if not organic:
            return ""

        analysis = f"{header_title} (via X Web Fallback):\n\n"
        for i, item in enumerate(organic[:max_results], 1):
            title = item.get("title", "No title")
            snippet = item.get("snippet", "No summary")
            link = item.get("link", "")
            analysis += f"{i}. {title}\n"
            analysis += f"   Snippet: {snippet}\n"
            analysis += f"   URL: {link}\n\n"
        return analysis
    except Exception:
        return ""


def _format_error(status_code: int, response_text: str, action: str, fallback_query: str = "") -> str:
    """Format API errors with helpful troubleshooting hints, with automatic SERP fallback for 403 Free Tier limits."""
    if status_code == 403 and fallback_query:
        fallback_res = _serp_fallback_search(fallback_query, f"X Results for '{fallback_query}'")
        if fallback_res:
            return (
                f"[Note: Official X API v2 returned 403 (Free Tier restricted API access). "
                f"Switched to Web Indexing for X data.]\n\n" + fallback_res
            )

    msg = f"Error {action}: HTTP {status_code} - {response_text}"
    if status_code == 403:
        msg += (
            "\n\nTroubleshooting 403 Forbidden on X API:\n"
            "Note: X API v2 Free Tier ($0/mo) restricts search & read endpoints ('client-not-enrolled').\n"
            "Official read endpoints require X API Basic Tier ($100/mo) or Pro Tier.\n"
            "Ensure your App is attached to a Project in https://developer.x.com."
        )
    elif status_code == 401:
        msg += "\n\nTroubleshooting 401 Unauthorized: Please check if your X_BEARER_TOKEN or API Keys are correct and not expired."
    elif status_code == 429:
        msg += "\n\nTroubleshooting 429 Rate Limit: You have exceeded the X API rate limit. Please wait a few minutes before retrying."
    return msg


@mcp.tool()
def search_x_tweets(query: str, max_results: int = 10) -> str:
    """
    Search recent tweets on X (formerly Twitter) for market research, trends, sentiment, or brand mentions.

    Args:
        query (str): The search term or topic on X
        max_results (int): Number of results to return (default: 10, max: 100)

    Returns:
        str: Formatted analysis of recent X tweets with metrics
    """
    auth, headers = _get_auth()
    if not auth and not headers:
        fallback_res = _serp_fallback_search(query, f"X Tweets for '{query}'", max_results)
        if fallback_res:
            return fallback_res
        return "Error: X_BEARER_TOKEN or OAuth credentials not set, and web fallback unavailable."

    try:
        limit = max(10, min(100, max_results))
        params = {
            "query": query,
            "max_results": limit,
            "tweet.fields": "created_at,public_metrics,lang",
            "expansions": "author_id",
            "user.fields": "name,username,verified,public_metrics"
        }
        resp = requests.get(f"{X_API_BASE}/tweets/search/recent", auth=auth, headers=headers, params=params, timeout=10)

        if resp.status_code != 200:
            return _format_error(resp.status_code, resp.text, "searching X tweets", fallback_query=query)

        data = resp.json()
        tweets = data.get("data", [])
        if not tweets:
            fallback_res = _serp_fallback_search(query, f"X Tweets for '{query}'", max_results)
            return fallback_res or f"No recent X tweets found for query: '{query}'"

        users_by_id = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

        analysis = f"X (Twitter) Search Analysis for '{query}':\n\n"
        analysis += f"Found {len(tweets)} recent tweets:\n\n"

        for i, t in enumerate(tweets, 1):
            author_info = users_by_id.get(t.get("author_id"), {})
            handle = f"@{author_info.get('username', 'unknown')}"
            name = author_info.get("name", "Unknown")
            text = t.get("text", "").replace("\n", " ")
            created_at = t.get("created_at", "N/A")
            metrics = t.get("public_metrics", {})

            analysis += f"{i}. [{handle} ({name}) - {created_at}]\n"
            analysis += f"   Content: {text}\n"
            analysis += (
                f"   Metrics: Likes: {metrics.get('like_count', 0)} | "
                f"Retweets: {metrics.get('retweet_count', 0)} | "
                f"Replies: {metrics.get('reply_count', 0)} | "
                f"Quotes: {metrics.get('quote_count', 0)} | "
                f"Impressions: {metrics.get('impression_count', 0)}\n\n"
            )

        return analysis
    except Exception as e:
        fallback_res = _serp_fallback_search(query, f"X Tweets for '{query}'", max_results)
        return fallback_res or f"Error searching X tweets: {str(e)}"


@mcp.tool()
def get_x_user_tweets(username: str, max_results: int = 10) -> str:
    """
    Fetch recent tweets posted by a specific X (Twitter) handle (e.g. brand, competitor, or executive).

    Args:
        username (str): The X handle without '@' (e.g., 'OpenAI', 'elonmusk')
        max_results (int): Number of tweets to fetch (default: 10, max: 100)

    Returns:
        str: Analysis of recent tweets from the specified X user
    """
    clean_user = username.lstrip("@").strip()
    auth, headers = _get_auth()
    if not auth and not headers:
        fallback_res = _serp_fallback_search(f"from:{clean_user}", f"Recent X Tweets from @{clean_user}", max_results)
        return fallback_res or "Error: Credentials not set and fallback unavailable."

    try:
        user_resp = requests.get(f"{X_API_BASE}/users/by/username/{clean_user}", auth=auth, headers=headers, timeout=10)
        if user_resp.status_code != 200:
            return _format_error(user_resp.status_code, user_resp.text, f"fetching user profile for '@{clean_user}'", fallback_query=f"{clean_user}")

        user_data = user_resp.json().get("data")
        if not user_data:
            return f"User '@{clean_user}' not found on X."

        user_id = user_data["id"]
        limit = max(10, min(100, max_results))
        params = {
            "max_results": limit,
            "tweet.fields": "created_at,public_metrics,lang"
        }
        tweets_resp = requests.get(f"{X_API_BASE}/users/{user_id}/tweets", auth=auth, headers=headers, params=params, timeout=10)
        if tweets_resp.status_code != 200:
            return _format_error(tweets_resp.status_code, tweets_resp.text, f"fetching tweets for '@{clean_user}'", fallback_query=f"{clean_user}")

        tweets_data = tweets_resp.json()
        tweets = tweets_data.get("data", [])
        if not tweets:
            return f"No recent tweets found for user '@{clean_user}'."

        analysis = f"Recent X Tweets for @{clean_user} ({user_data.get('name', '')}):\n\n"
        for i, t in enumerate(tweets, 1):
            text = t.get("text", "").replace("\n", " ")
            created_at = t.get("created_at", "N/A")
            metrics = t.get("public_metrics", {})
            analysis += f"{i}. [{created_at}]\n"
            analysis += f"   Content: {text}\n"
            analysis += (
                f"   Metrics: Likes: {metrics.get('like_count', 0)} | "
                f"Retweets: {metrics.get('retweet_count', 0)} | "
                f"Replies: {metrics.get('reply_count', 0)}\n\n"
            )

        return analysis
    except Exception as e:
        fallback_res = _serp_fallback_search(f"{clean_user}", f"Recent X Tweets for @{clean_user}", max_results)
        return fallback_res or f"Error fetching user tweets for '@{username}': {str(e)}"


@mcp.tool()
def get_x_user_profile(username: str) -> str:
    """
    Fetch profile details and public metrics (followers, following, tweet count, bio) for an X handle.

    Args:
        username (str): The X handle without '@' (e.g., 'Google', 'Microsoft')

    Returns:
        str: Detailed profile metrics and information for the user
    """
    clean_user = username.lstrip("@").strip()
    auth, headers = _get_auth()
    if not auth and not headers:
        fallback_res = _serp_fallback_search(f"{clean_user}", f"X Profile for @{clean_user}")
        return fallback_res or "Error: Credentials not set and fallback unavailable."

    try:
        params = {
            "user.fields": "description,created_at,public_metrics,verified,location,url"
        }
        resp = requests.get(f"{X_API_BASE}/users/by/username/{clean_user}", auth=auth, headers=headers, params=params, timeout=10)
        if resp.status_code != 200:
            return _format_error(resp.status_code, resp.text, f"fetching X profile for '@{clean_user}'", fallback_query=f"{clean_user}")

        user = resp.json().get("data")
        if not user:
            return f"User '@{clean_user}' not found on X."

        metrics = user.get("public_metrics", {})
        analysis = f"X Profile Details for @{clean_user}:\n\n"
        analysis += f"**Name:** {user.get('name', 'N/A')}\n"
        analysis += f"**Username:** @{user.get('username', clean_user)}\n"
        analysis += f"**Verified:** {user.get('verified', False)}\n"
        analysis += f"**Bio:** {user.get('description', 'N/A')}\n"
        analysis += f"**Location:** {user.get('location', 'N/A')}\n"
        analysis += f"**Website:** {user.get('url', 'N/A')}\n"
        analysis += f"**Account Created:** {user.get('created_at', 'N/A')}\n\n"
        analysis += "**Public Metrics:**\n"
        analysis += f"- Followers Count: {metrics.get('followers_count', 0):,}\n"
        analysis += f"- Following Count: {metrics.get('following_count', 0):,}\n"
        analysis += f"- Total Tweets: {metrics.get('tweet_count', 0):,}\n"
        analysis += f"- Listed Count: {metrics.get('listed_count', 0):,}\n"

        return analysis
    except Exception as e:
        fallback_res = _serp_fallback_search(f"{clean_user}", f"X Profile for @{clean_user}")
        return fallback_res or f"Error fetching X profile for '@{username}': {str(e)}"


@mcp.tool()
def get_x_tweet_metrics(tweet_id: str) -> str:
    """
    Fetch details and engagement metrics (likes, retweets, replies, quotes, impressions) for a specific tweet ID.

    Args:
        tweet_id (str): The numerical ID of the tweet

    Returns:
        str: Tweet engagement details and metrics
    """
    clean_id = tweet_id.strip()
    auth, headers = _get_auth()
    if not auth and not headers:
        fallback_res = _serp_fallback_search(f"status/{clean_id}", f"X Tweet ID {clean_id}")
        return fallback_res or "Error: Credentials not set and fallback unavailable."

    try:
        params = {
            "tweet.fields": "created_at,public_metrics,lang,author_id",
            "expansions": "author_id",
            "user.fields": "name,username"
        }
        resp = requests.get(f"{X_API_BASE}/tweets/{clean_id}", auth=auth, headers=headers, params=params, timeout=10)
        if resp.status_code != 200:
            return _format_error(resp.status_code, resp.text, f"fetching tweet metrics for ID '{clean_id}'", fallback_query=f"status/{clean_id}")

        data = resp.json()
        tweet = data.get("data")
        if not tweet:
            return f"Tweet ID '{clean_id}' not found."

        users_by_id = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
        author = users_by_id.get(tweet.get("author_id"), {})
        metrics = tweet.get("public_metrics", {})

        analysis = f"X Tweet Analysis for ID {clean_id}:\n\n"
        analysis += f"**Author:** @{author.get('username', 'unknown')} ({author.get('name', 'Unknown')})\n"
        analysis += f"**Created At:** {tweet.get('created_at', 'N/A')}\n"
        analysis += f"**Language:** {tweet.get('lang', 'N/A')}\n"
        analysis += f"**Content:** {tweet.get('text', '')}\n\n"
        analysis += "**Engagement Metrics:**\n"
        analysis += f"- Likes: {metrics.get('like_count', 0):,}\n"
        analysis += f"- Retweets: {metrics.get('retweet_count', 0):,}\n"
        analysis += f"- Replies: {metrics.get('reply_count', 0):,}\n"
        analysis += f"- Quotes: {metrics.get('quote_count', 0):,}\n"
        analysis += f"- Impressions: {metrics.get('impression_count', 0):,}\n"

        return analysis
    except Exception as e:
        fallback_res = _serp_fallback_search(f"status/{clean_id}", f"X Tweet ID {clean_id}")
        return fallback_res or f"Error fetching tweet metrics for ID '{tweet_id}': {str(e)}"
