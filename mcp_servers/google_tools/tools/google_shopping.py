import sys
import os
# Add the mcp_server directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from config import *
from serpapi import GoogleSearch

def search_google_shopping(query: str, sort_by: str = 'relevance', min_price = None, max_price  = None, condition = None, location = None, num_results: int = 10) -> str:
    """
    Search Google Shopping for products with comprehensive filtering options.
    
    Args:
        query (str): The product or term to search for
        sort_by (str): Sorting order ('relevance', 'price_low_to_high', 'price_high_to_low', 'rating')
        min_price (float): Minimum price filter
        max_price (float): Maximum price filter
        condition (str): Product condition ('new', 'used')
        location (str): Location for search
        num_results (int): Number of results to return (default: 10)
        
    Returns:
        str: Market analysis summary of product pricing and availability
    """
    try:
        
        params = {
            "engine": "google_shopping",
            "q": query,
            "api_key": serp_api_key,
            "num": num_results,
        }

        if location:
            params["location"] = location

        tbs_params = []
        sort_map = {
            'relevance': 'p_ord:rv',
            'price_low_to_high': 'p_ord:p',
            'price_high_to_low': 'p_ord:pd',
            'rating': 'p_ord:r'
        }
        if sort_by and sort_by in sort_map:
            tbs_params.append(sort_map[sort_by])

        if min_price is not None or max_price is not None:
            tbs_params.append('price:1')
            if min_price is not None:
                tbs_params.append(f'ppr_min:{min_price}')
            if max_price is not None:
                tbs_params.append(f'ppr_max:{max_price}')

        condition_map = {'new': 'cond:c', 'used': 'cond:u'}
        if condition and condition in condition_map:
            tbs_params.append(condition_map[condition])

        if tbs_params:
            params['tbs'] = ",".join(tbs_params)

        search = GoogleSearch(params)
        results = search.get_dict()

        if "error" in results:
            return f"SerpApi Error: {results['error']}"

        # Create market analysis summary
        if 'shopping_results' not in results:
            return f"No shopping results found for '{query}'"
        
        shopping_data = results['shopping_results']
        analysis = f"Market Analysis for '{query}':\n\n"
        
        # Price analysis
        prices = []
        top_sellers = []
        
        for item in shopping_data:
            if 'price' in item:
                price_str = item['price'].replace('$', '').replace(',', '')
                try:
                    price = float(price_str)
                    prices.append(price)
                except:
                    pass
            
            if 'source' in item:
                top_sellers.append(item['source'])
        
        if prices:
            analysis += f"Price Analysis:\n"
            analysis += f"- Price range: ${min(prices):.2f} - ${max(prices):.2f}\n"
            analysis += f"- Average price: ${sum(prices)/len(prices):.2f}\n"
            analysis += f"- Total products analyzed: {len(shopping_data)}\n\n"
        
        if top_sellers:
            unique_sellers = list(set(top_sellers))
            analysis += f"Top Sellers: {', '.join(unique_sellers)}\n\n"
        
        # Product highlights
        analysis += "Product Highlights:\n"
        for i, item in enumerate(shopping_data[:10], 1):
            title = item.get('title', 'No title')
            price = item.get('price', 'Price not available')
            rating = item.get('rating', 'No rating')
            
            analysis += f"{i}. {title}\n"
            analysis += f"   Price: {price} | Rating: {rating}\n"
        
        
        
        return analysis
    except Exception as e:
        
        return f"Error searching Google Shopping"
