import json
import os
from typing import Dict


def _load_locations_data() -> Dict[str, str]:
    """
    Load Google Trends locations data from JSON file.
    
    Returns:
        dict: Geographic codes and their corresponding location names.
    """
    _locations_data = None

    try:
        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, "google-trends-locations.json")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            _locations_data = json.load(f)
    except FileNotFoundError:
        _locations_data = {"": "Worldwide", "US": "United States", "IN": "India"}
    except json.JSONDecodeError:
        _locations_data = {"": "Worldwide", "US": "United States", "IN": "India"}
    
    return _locations_data


def get_all_countries() -> Dict[str, str]:
    """
    Get all available countries from the locations data.
    
    Returns:
        dict: Country codes and names (excludes sub-regions).
    """
    locations = _load_locations_data()
    countries = {}
    
    for code, name in locations.items():
        # Countries don't have hyphens in their codes (sub-regions do)
        if '-' not in code and code != "":
            countries[code] = name
    
    return countries


def get_subregions_for_country(country_code: str) -> Dict[str, str]:
    """
    Get all sub-regions for a specific country.
    
    Args:
        country_code (str): The country code (e.g., 'US', 'IN', 'GB').
    
    Returns:
        dict: Sub-region codes and names for the specified country.
    """
    locations = _load_locations_data()
    subregions = {}
    
    prefix = f"{country_code}-"
    for code, name in locations.items():
        if code.startswith(prefix):
            subregions[code] = name
    
    return subregions


def search_locations(search_term: str, max_results: int = 10) -> Dict[str, str]:
    """
    Search for locations by name.
    
    Args:
        search_term (str): The search term to look for in location names.
        max_results (int): Maximum number of results to return.
    
    Returns:
        dict: Matching location codes and names.
    """
    locations = _load_locations_data()
    results = {}
    
    search_term_lower = search_term.lower()
    count = 0
    
    for code, name in locations.items():
        if search_term_lower in name.lower() and count < max_results:
            results[code] = name
            count += 1
    
    return results


def validate_geo_code(geo_code: str) -> tuple[bool, str]:
    """
    Validate if a geographic code exists in the locations data.
    
    Args:
        geo_code (str): The geographic code to validate.
    
    Returns:
        tuple: (is_valid, location_name or error_message).
    """
    locations = _load_locations_data()
    
    if geo_code in locations:
        return True, locations[geo_code]
    else:
        return False, f"Geographic code '{geo_code}' not found"




def discover_locations_by_name(location_name: str) -> str:
    """
    Help LLMs discover geographic codes by searching location names.
    
    Args:
        location_name (str): The location name to search for.
    
    Returns:
        str: Formatted results with codes and suggestions.
    """
    results = search_locations(location_name, max_results=15)
    
    if not results:
        # Try partial matching or suggestions
        suggestion_text = f"No exact matches found for '{location_name}'.\n\n"
        
        # Suggest similar sounding or partial matches
        all_locations = _load_locations_data()
        partial_matches = {}
        location_lower = location_name.lower()
        
        for code, name in all_locations.items():
            if any(word in name.lower() for word in location_lower.split()):
                partial_matches[code] = name
                if len(partial_matches) >= 10:
                    break
        
        if partial_matches:
            suggestion_text += "Possible matches:\n"
            for code, name in partial_matches.items():
                suggestion_text += f"• {code:<8} = {name}\n"
        else:
            suggestion_text += "Try searching for:\n"
            suggestion_text += "• Country names (e.g., 'United States', 'India', 'Germany')\n"
            suggestion_text += "• State names (e.g., 'California', 'Texas', 'Maharashtra')\n"
            suggestion_text += "• City names (e.g., 'London', 'Tokyo', 'Mumbai')\n"
        
        return suggestion_text
    
    response = f"Found {len(results)} matches for '{location_name}':\n\n"
    
    # Separate countries from sub-regions
    countries = {}
    subregions = {}
    
    for code, name in results.items():
        if '-' in code:
            subregions[code] = name
        else:
            countries[code] = name
    
    if countries:
        response += "🏳️ COUNTRIES:\n"
        for code, name in countries.items():
            response += f"• {code:<6} = {name}\n"
    
    if subregions:
        response += "\n📍 SUB-REGIONS:\n"
        for code, name in subregions.items():
            response += f"• {code:<8} = {name}\n"
    
    response += f"\n💡 Usage: geo=\"{list(results.keys())[0]}\""
    
    return response

