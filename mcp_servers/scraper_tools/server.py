import sys
import os
# Add the mcp_server directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import asyncio
from crawl4ai import AsyncWebCrawler
from config import * 

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Web Scraper Tools")

@mcp.tool()
def scrape_website_to_markdown(url: str, include_links: bool = True, include_images: bool = False) -> str:
    """
    Scrape a website and return its content in clean markdown format.
    
    Args:
        url (str): The URL to scrape
        include_links (bool): Whether to include links in the markdown (default: True)
        include_images (bool): Whether to include images in the markdown (default: False)
        
    Returns:
        str: Website content in markdown format with analysis summary
    """
    try:
        async def crawl_url():
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(
                    url=url,
                    include_images=include_images,
                    include_links=include_links
                )
                return result
        
        # Run the async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(crawl_url())
        loop.close()
        
        if not result.success: # type: ignore
            
            return f"Error: Failed to scrape {url}. Status: {result.status_code}" # type: ignore
        
        # Get the markdown content
        markdown_content = result.markdown # type: ignore
        
        if not markdown_content:
            return f"Error: No content extracted from {url}"
        
        # Create analysis summary
        analysis = f"Website Content Analysis for: {url}\n"
        
        # Add metadata
        analysis += f"**URL:** {url}\n"
        analysis += f"**Status:** Successfully scraped\n"
        analysis += f"**Content Length:** {len(markdown_content)} characters\n"
        analysis += f"**Word Count:** {len(markdown_content.split())} words\n\n"

        # Add any additional analysis here

        analysis += "**Content:**\n\n"
        analysis += markdown_content

        
        
        return analysis
        
    except Exception as e:
        
        return f"Error scraping website {url}"

