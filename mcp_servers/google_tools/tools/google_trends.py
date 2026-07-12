import sys
import os
# Add the mcp_server directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from serpapi import GoogleSearch
from enum import Enum
from config import  *
from typing import Optional
from .google_trends_helper import *

 
class DataType(Enum):
    TIMESERIES = "TIMESERIES"
    GEO_MAP_0 = "GEO_MAP_0"
    RELATED_TOPICS = "RELATED_TOPICS"
    RELATED_QUERIES = "RELATED_QUERIES"


def _analyze_trends_data(query: str, data_type: DataType, geo: Optional[str] = None, region: Optional[str] = None) -> dict:
    """
    Perform a Google Trends search for the given query.

    Args:
        query (str): The search query.
        data_type (DataType): Parameter defines the type of search you want to do. Available options:
            TIMESERIES - Interest over time (default) - Accepts both single and multiple queries per search.
            GEO_MAP_0 - Interest by region - Accepts only single query per search.
            RELATED_TOPICS - Related topics - Accepts only single query per search.
            RELATED_QUERIES - Related queries - Accepts only single query per search.

        geo (str, optional): Geographic location (e.g., 'US' for United States, 'IN' for India). Defaults to Worldwide if not specified.
        region (str, optional): Sub-region level for geographic data. Available options:
                               'COUNTRY' - Country level
                               'REGION' - Subregion/State level  
                               'DMA' - Metro area level
                               'CITY' - City level
                               Only works with GEO_MAP and GEO_MAP_0 data types.
    Returns:
        dict: Analytical Summary of the given query trends.
    """

    try:
        # Validate geographic code if provided
        if geo:
            is_valid, location_name = validate_geo_code(geo)
            if not is_valid:
                return {"error": f"Invalid geographic code: {location_name}"}
        
        params = {
            "engine": "google_trends",
            "q": query,
            "data_type": data_type.name,
            "api_key": serp_api_key,
        }
        
        # Add geographic parameters if specified
        if geo:
            params["geo"] = geo
        if region and data_type == DataType.GEO_MAP_0:
            params["region"] = region

        search = GoogleSearch(params)
        results = search.get_dict()
        
        if data_type == DataType.TIMESERIES:
            return analyze_timeseries(query, results)
        elif data_type == DataType.GEO_MAP_0:
            return analyze_geographic(query, results)
        elif data_type == DataType.RELATED_TOPICS:
            return analyze_related_topics(query, results)
        elif data_type == DataType.RELATED_QUERIES:
            return analyze_related_queries(query, results)
        else:
            return {"error": "Analytics not yet implemented for this data type"}
            
    except Exception as e:
        return {"error": f"Analytics failed: {str(e)}"}


def google_trends_summary(query: str, data_type: DataType, geo: Optional[str] = None, region: Optional[str] = None) -> str:
    """
    Perform a Google Trends search for the given query.

    Args:
        query (str): The search query.
        data_type (DataType): Parameter defines the type of search you want to do. Available options:
            TIMESERIES - Interest over time (default) - Accepts both single and multiple queries per search.
            GEO_MAP_0 - Interest by region - Accepts only single query per search.
            RELATED_TOPICS - Related topics - Accepts only single query per search.
            RELATED_QUERIES - Related queries - Accepts only single query per search.

        geo (str, optional): Geographic location (e.g., 'US' for United States, 'IN' for India). Defaults to Worldwide if not specified.
        region (str, optional): Sub-region level for geographic data. Available options:
                               'COUNTRY' - Country level
                               'REGION' - Subregion/State level  
                               'DMA' - Metro area level
                               'CITY' - City level
                               Only works with GEO_MAP_0 data type.
    
    Returns:
        str: Formatted analytics summary.
    """
    analytics_data = _analyze_trends_data(query, data_type, geo, region)
    
    if "error" in analytics_data:
        
        return f"Analytics Error: {analytics_data['error']}"
    
    if data_type == DataType.TIMESERIES:
        return format_timeseries_summary(analytics_data)
    elif data_type == DataType.GEO_MAP_0:
        return format_geographic_summary(analytics_data)
    elif data_type == DataType.RELATED_TOPICS:
        return format_topics_summary(analytics_data)
    elif data_type == DataType.RELATED_QUERIES:
        return format_queries_summary(analytics_data)
    else:
        
        return "Summary formatting not yet implemented for this data type"
