
import statistics
from .calculate import *

def generate_insights(values: list, dates: list, query: str) -> list:
    """Generate actionable insights from the data."""
    insights = []
    
    if not values:
        return ["No data available for analysis"]
    
    # Trend insights
    trend = calculate_trend(values)
    if trend["direction"] == "increasing":
        insights.append(f"'{query}' shows positive momentum with {trend['direction']} trend")
    elif trend["direction"] == "decreasing":
        insights.append(f"'{query}' interest is declining - consider content refresh or new angles")
    
    # Volatility insights
    volatility = calculate_volatility(values)
    if volatility["level"] == "high":
        insights.append("High volatility indicates unpredictable interest - monitor closely")
    elif volatility["level"] == "low":
        insights.append("Stable interest pattern - good for consistent content strategy")
    
    # Performance insights
    current_value = values[-1] if values else 0
    avg_value = statistics.mean(values)
    
    if current_value > avg_value * 1.1:
        insights.append("Current interest is above average - good time for content push")
    elif current_value < avg_value * 0.9:
        insights.append("Current interest is below average - opportunity for targeted campaigns")
    
    return insights


def generate_geo_insights(regions: list, query: str) -> list:
    """Generate geographic insights."""
    insights = []
    
    if not regions:
        return ["No geographic data available"]
    
    top_region = regions[0]
    insights.append(f"Highest interest in {top_region['location']} ({top_region['interest_score']})")
    
    # Find markets with potential
    high_interest = [r for r in regions if r['interest_score'] >= 75]
    if high_interest:
        insights.append(f"{len(high_interest)} high-interest markets identified for '{query}'")
    
    return insights


def generate_topic_insights(analytics: dict, query: str) -> list:
    """Generate insights from related topics analysis."""
    insights = []
    
    rising_count = len(analytics["rising_topics"])
    top_count = len(analytics["top_topics"])
    
    if rising_count > 0:
        insights.append(f"{rising_count} rising topics detected - emerging opportunities")
    
    if top_count > 0:
        insights.append(f"{top_count} established topics related to '{query}'")
    
    # Category insights
    categories = analytics["topic_categories"]
    if categories:
        top_category = max(categories.items(), key=lambda x: x[1])
        insights.append(f"Most common topic type: {top_category[0]} ({top_category[1]} topics)")
    
    return insights


def generate_query_insights(analytics: dict, query: str) -> list:
    """Generate insights from related queries analysis."""
    insights = []
    
    rising_count = len(analytics["rising_queries"])
    top_count = len(analytics["top_queries"])
    
    if rising_count > 0:
        insights.append(f"{rising_count} rising search queries - keyword expansion opportunities")
    
    if top_count > 0:
        insights.append(f"{top_count} popular related searches for content optimization")
    
    return insights

