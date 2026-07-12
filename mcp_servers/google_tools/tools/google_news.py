import sys
import os
# Add the mcp_server directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import json
from typing import Optional
import requests
from config import *

def search_google_news(
    query: str,
    location: Optional[str] = None,
    time_period: Optional[str] = None,
    num_results: int = 10,
) -> str:
    """
    Search Google News for recent articles and news coverage.

    Args:
        query (str): The topic or keyword to search for
        location (str): Location for the search
        sort_by (str): Sorting order ('relevance' or 'date')
        time_period (str): Time frame ('past_hour', 'past_day', 'past_week', 'past_month', 'past_year')
        num_results (int): Number of articles to return (default: 10)

    Returns:
        str: Comprehensive news analysis with sentiment and coverage summary
    """
    try:

        url = "https://google.serper.dev/news"

        payload = {"q": query, "gl": "en"}

        if location:
            payload["location"] = location

        if time_period:

            time_map = {
                "past_hour": "qdr:h",
                "past_day": "qdr:d",
                "past_week": "qdr:w",
                "past_month": "qdr:m",
                "past_year": "qdr:y",
            }

            payload["tbs"] = time_map.get(time_period, "qdr:y")

        if num_results:
            payload["num"] = str(num_results)

        headers = {
            "X-API-KEY": serp_dev_api_key,
            "Content-Type": "application/json",
        }

        response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
        results = json.loads(response.text)

        if "news" not in results:
            return f"No news results found for '{query}'"

        organic_results = results["news"]

        # Build comprehensive summary
        summary_parts = []
        
        if location:
            summary_parts.append(f"Location: {location}")
        if time_period:
            summary_parts.append(f"Time Period: {time_period}")
            
        summary_parts.append(f"Total Results: {len(organic_results)}")
        summary_parts.append("")
        summary_parts.append("ARTICLES FOUND:")
        summary_parts.append("")
        
        for i, article in enumerate(organic_results, 1):
            title = article.get("title", "No title")
            link = article.get("link", "No link")
            snippet = article.get("snippet", "No description")
            
            summary_parts.append(f"{i}. {title}")
            summary_parts.append(f"   Link: {link}")
            summary_parts.append(f"   Description: {snippet}")
            
            # Include sitelinks if available
            sitelinks = article.get("sitelinks", [])
            if sitelinks:
                summary_parts.append("   Related Links:")
                for sitelink in sitelinks[:3]:  # Limit to first 3 sitelinks
                    sitelink_title = sitelink.get("title", "No title")
                    sitelink_url = sitelink.get("link", "No link")
                    summary_parts.append(f"     - {sitelink_title}: {sitelink_url}")
            
            summary_parts.append("")
        
        return "\n".join(summary_parts)
    except Exception as e:
        return f"Error searching Google News"
