import sys
import os
# Add the mcp_server directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import requests
import json
from config import *  

def google_search(query:str)->str:
    """
    Perform a Google search for the given query.
    
    Args:
        query (str): The search query.
        
    Returns:
        str: The search results.
    """

    try:
       
        url = "https://google.serper.dev/search"

        params = json.dumps({
            "q": query 
        })

        headers = {
            'X-API-KEY': serp_dev_api_key,
            'Content-Type': 'application/json'
        }
        
        response = requests.request("POST", url, headers=headers, data=params)

        results = json.loads(response.text)

        if 'organic' not in results:
            return "No search results found"
        
        # Create a comprehensive summary
        summary = f"Search Results for '{query}':\n\n"
        
        for i, result in enumerate(results['organic'], 1):
            title = result.get('title', 'No title')
            snippet = result.get('snippet', 'No description')
            link = result.get('link', '')
            
            summary += f"{i}. {title}\n"
            summary += f"Snippet: {snippet}\n"
            summary += f"Link: {link}\n\n"
        
        # Add key insights
        summary += "Key Insights:\n"
        summary += f"- Found {len(results.get('organic', []))} relevant results\n"
        summary += f"- Related Searches : {', '.join([r.get('query', '') for r in results.get('relatedSearches', [])])}"

        
        return summary
    
    except Exception as e:
        
        return f"Error searching Google: {str(e)}"


