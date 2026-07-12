

import statistics
from .calculate import *
from .insights import *

def analyze_timeseries(query: str, results: dict) -> dict:
    """Analyze timeseries data for trends, patterns, and insights."""
    if 'interest_over_time' not in results:
        return {"error": "No timeseries data available"}
    
    interest_data = results['interest_over_time']
    timeline_data = interest_data.get('timeline_data', [])
    
    if not timeline_data:
        return {"error": "No timeline data available"}
    
    # Extract values and dates
    values = []
    dates = []
    for period in timeline_data:
        for value in period['values']:
            values.append(int(value['extracted_value']))
            dates.append(period['date'])
    
    if not values:
        return {"error": "No data values found"}
    
    # Statistical analysis
    analytics = {
        "query": query,
        "data_type": "timeseries",
        "period_count": len(values),
        "date_range": {
            "start": dates[0] if dates else None,
            "end": dates[-1] if dates else None
        },
        "statistics": {
            "mean": round(statistics.mean(values), 2),
            "median": statistics.median(values),
            "mode": statistics.mode(values) if len(set(values)) < len(values) else None,
            "std_dev": round(statistics.stdev(values) if len(values) > 1 else 0, 2),
            "min": min(values),
            "max": max(values),
            "range": max(values) - min(values)
        },
        "trend_analysis": calculate_trend(values),
        "volatility": calculate_volatility(values),
        "seasonal_patterns": detect_patterns(values, dates),
        "performance_periods": identify_performance_periods(values, dates),
        "insights": generate_insights(values, dates, query)
    }
    
    return analytics


def analyze_geographic(query: str, results: dict) -> dict:
    """Analyze geographic distribution of interest."""
    
    if "interest_by_region" not in results:
        return {"error": "No geographic data available"}
    
    geo_data = results['interest_by_region']
    
    # Extract and sort regions by interest
    regions = []
    for region in geo_data:
        regions.append({
            "location": region['location'],
            "geo_code": region['geo'],
            "interest_score": int(region['extracted_value'])
        })
    
    regions.sort(key=lambda x: x['interest_score'], reverse=True)
    
    values = [r['interest_score'] for r in regions]
    
    analytics = {
        "query": query,
        "data_type": "geographic",
        "total_regions": len(regions),
        "top_regions": regions[:10],
        "bottom_regions": regions[-5:] if len(regions) > 5 else [],
        "statistics": {
            "mean_interest": round(statistics.mean(values), 2),
            "median_interest": statistics.median(values),
            "max_interest": max(values),
            "min_interest": min(values)
        },
        "distribution": {
            "high_interest_regions": len([r for r in regions if r['interest_score'] >= 75]),
            "medium_interest_regions": len([r for r in regions if 25 <= r['interest_score'] < 75]),
            "low_interest_regions": len([r for r in regions if r['interest_score'] < 25])
        },
        "insights": generate_geo_insights(regions, query)
    }
    
    return analytics


def analyze_related_topics(query: str, results: dict) -> dict:
    """Analyze related topics for content strategy insights."""
    if "related_topics" not in results:
        return {"error": "No related topics data available"}
    
    related_topics = results['related_topics']
    
    analytics = {
        "query": query,
        "data_type": "related_topics",
        "rising_topics": [],
        "top_topics": [],
        "topic_categories": {},
        "insights": []
    }
    
    # Process rising topics
    if 'rising' in related_topics and related_topics['rising']:
        for topic in related_topics['rising']:
            topic_info = topic['topic']
            analytics["rising_topics"].append({
                "title": topic_info['title'],
                "type": topic_info['type'],
                "growth": topic['value']
            })
    
    # Process top topics
    if 'top' in related_topics and related_topics['top']:
        for topic in related_topics['top']:
            topic_info = topic['topic']
            analytics["top_topics"].append({
                "title": topic_info['title'],
                "type": topic_info['type'],
                "popularity": topic['value']
            })
    
    # Categorize topics by type
    all_topics = analytics["rising_topics"] + analytics["top_topics"]
    for topic in all_topics:
        topic_type = topic['type']
        if topic_type not in analytics["topic_categories"]:
            analytics["topic_categories"][topic_type] = 0
        analytics["topic_categories"][topic_type] += 1
    
    analytics["insights"] = generate_topic_insights(analytics, query)
    
    return analytics


def analyze_related_queries(query: str, results: dict) -> dict:
    """Analyze related queries for keyword strategy insights."""
    if "related_queries" not in results:
        return {"error": "No related queries data available"}
    
    related_queries = results['related_queries']
    
    analytics = {
        "query": query,
        "data_type": "related_queries",
        "rising_queries": [],
        "top_queries": [],
        "query_patterns": {},
        "insights": []
    }
    
    # Process rising queries
    if 'rising' in related_queries and related_queries['rising']:
        for query_item in related_queries['rising']:
            analytics["rising_queries"].append({
                "query": query_item['query'],
                "growth": query_item['value'],
                "search_volume": int(query_item['extracted_value'])
            })
    
    # Process top queries
    if 'top' in related_queries and related_queries['top']:
        for query_item in related_queries['top']:
            analytics["top_queries"].append({
                "query": query_item['query'],
                "popularity": query_item['value'],
                "search_volume": int(query_item['extracted_value'])
            })
    
    # Analyze query patterns
    all_queries = [q['query'] for q in analytics["rising_queries"] + analytics["top_queries"]]
    analytics["query_patterns"] = analyze_query_patterns(all_queries)
    analytics["insights"] = generate_query_insights(analytics, query)
    
    return analytics


def analyze_query_patterns(queries: list) -> dict:
    """Analyze patterns in related queries."""
    patterns = {
        "common_words": {},
        "query_lengths": [],
        "question_queries": 0
    }
    
    for query in queries:
        # Count word frequency
        words = query.lower().split()
        for word in words:
            if len(word) > 2:  # Ignore short words
                patterns["common_words"][word] = patterns["common_words"].get(word, 0) + 1
        
        # Track query length
        patterns["query_lengths"].append(len(words))
        
        # Count question queries
        if any(q_word in query.lower() for q_word in ['how', 'what', 'why', 'when', 'where', 'who']):
            patterns["question_queries"] += 1
    
    # Get top common words
    if patterns["common_words"]:
        sorted_words = sorted(patterns["common_words"].items(), key=lambda x: x[1], reverse=True)
        patterns["top_words"] = sorted_words[:10]
    
    return patterns
