
def format_timeseries_summary(data: dict) -> str:
    """Format timeseries analytics data into a readable summary."""
    summary = f"Query: {data['query']}\n"
    summary += f"Analysis Period: {data['date_range']['start']} to {data['date_range']['end']}\n"
    summary += f"Data Points: {data['period_count']} periods\n\n"
    
    # Statistical Overview
    stats = data['statistics']
    summary += "STATISTICAL OVERVIEW:\n"
    summary += f"• Average Interest Score: {stats['mean']}\n"
    summary += f"• Peak Interest: {stats['max']} (highest point)\n"
    summary += f"• Lowest Interest: {stats['min']} (lowest point)\n"
    summary += f"• Interest Range: {stats['range']} points\n"
    summary += f"• Volatility: {stats['std_dev']} standard deviation\n\n"
    
    # Trend Analysis
    trend = data['trend_analysis']
    summary += "TREND ANALYSIS:\n"
    summary += f"• Direction: {trend['direction'].upper()}\n"
    summary += f"• Trend Strength: {trend['strength']}/100\n"
    if trend['direction'] != 'stable':
        summary += f"• Rate of Change: {trend['slope']} points per period\n"
    summary += "\n"
    
    # Volatility Assessment
    volatility = data['volatility']
    summary += "VOLATILITY ASSESSMENT:\n"
    summary += f"• Volatility Level: {volatility['level'].upper()}\n"
    summary += f"• Coefficient of Variation: {volatility['coefficient']}%\n"
    summary += f"• Standard Deviation: {volatility['standard_deviation']}\n\n"
    
    # Seasonal Patterns
    patterns = data['seasonal_patterns']
    summary += "SEASONAL PATTERNS:\n"
    if patterns['seasonal_detected']:
        summary += "• Seasonal patterns detected\n"
        if patterns['peak_months']:
            summary += f"• Peak months: {', '.join(patterns['peak_months'])}\n"
        if patterns['low_months']:
            summary += f"• Low months: {', '.join(patterns['low_months'])}\n"
    else:
        summary += "• No clear seasonal patterns detected\n"
    summary += "\n"
    
    # Performance Periods
    if 'performance_periods' in data and data['performance_periods']:
        perf = data['performance_periods']
        summary += "PERFORMANCE HIGHLIGHTS:\n"
        summary += f"• Baseline Average: {perf['average_baseline']}\n"
        
        if perf['high_performance_periods']:
            summary += "• High Performance Periods:\n"
            for period in perf['high_performance_periods']:
                summary += f"  - {period['date']}: {period['value']}\n"
        
        if perf['low_performance_periods']:
            summary += "• Low Performance Periods:\n"
            for period in perf['low_performance_periods']:
                summary += f"  - {period['date']}: {period['value']}\n"
        summary += "\n"
    
    # Key Insights
    summary += "KEY INSIGHTS:\n"
    for insight in data['insights']:
        summary += f"• {insight}\n"
    
    return summary


def format_geographic_summary(data: dict) -> str:
    """Format geographic analytics data into a readable summary."""
    summary = f""
    summary += f"Query: {data['query']}\n"
    summary += f"Total Regions Analyzed: {data['total_regions']}\n\n"
    
    # Statistics
    stats = data['statistics']
    summary += "REGIONAL STATISTICS:\n"
    summary += f"• Average Interest: {stats['mean_interest']}\n"
    summary += f"• Median Interest: {stats['median_interest']}\n"
    summary += f"• Highest Interest: {stats['max_interest']}\n"
    summary += f"• Lowest Interest: {stats['min_interest']}\n\n"
    
    # Distribution
    dist = data['distribution']
    summary += "INTEREST DISTRIBUTION:\n"
    summary += f"• High Interest Regions (75+): {dist['high_interest_regions']}\n"
    summary += f"• Medium Interest Regions (25-74): {dist['medium_interest_regions']}\n"
    summary += f"• Low Interest Regions (<25): {dist['low_interest_regions']}\n\n"
    
    # Top Regions
    summary += "TOP PERFORMING REGIONS:\n"
    for i, region in enumerate(data['top_regions'][:5], 1):
        summary += f"{i}. {region['location']}: {region['interest_score']}\n"
    summary += "\n"
    
    # Key Insights
    summary += "KEY INSIGHTS:\n"
    for insight in data['insights']:
        summary += f"• {insight}\n"
    
    return summary


def format_topics_summary(data: dict) -> str:
    """Format related topics analytics data into a readable summary."""
    summary = f""
    summary += f"Query: {data['query']}\n\n"
    
    # Rising Topics
    if data['rising_topics']:
        summary += f"RISING TOPICS ({len(data['rising_topics'])}):\n"
        for topic in data['rising_topics'][:5]:
            summary += f"• {topic['title']} ({topic['type']}): {topic['growth']}\n"
        summary += "\n"
    
    # Top Topics
    if data['top_topics']:
        summary += f"TOP TOPICS ({len(data['top_topics'])}):\n"
        for topic in data['top_topics'][:5]:
            summary += f"• {topic['title']} ({topic['type']}): {topic['popularity']}\n"
        summary += "\n"
    
    # Topic Categories
    if data['topic_categories']:
        summary += "TOPIC CATEGORIES:\n"
        for category, count in sorted(data['topic_categories'].items(), key=lambda x: x[1], reverse=True):
            summary += f"• {category}: {count} topics\n"
        summary += "\n"
    
    # Key Insights
    summary += "KEY INSIGHTS:\n"
    for insight in data['insights']:
        summary += f"• {insight}\n"
    
    return summary


def format_queries_summary(data: dict) -> str:
    """Format related queries analytics data into a readable summary."""
    summary = f""
    summary += f"Query: {data['query']}\n\n"
    
    # Rising Queries
    if data['rising_queries']:
        summary += f"RISING QUERIES ({len(data['rising_queries'])}):\n"
        for query in data['rising_queries'][:5]:
            summary += f"• {query['query']}: {query['growth']} (vol: {query['search_volume']})\n"
        summary += "\n"
    
    # Top Queries
    if data['top_queries']:
        summary += f"TOP QUERIES ({len(data['top_queries'])}):\n"
        for query in data['top_queries'][:5]:
            summary += f"• {query['query']}: {query['popularity']} (vol: {query['search_volume']})\n"
        summary += "\n"
    
    # Query Patterns
    if 'query_patterns' in data and data['query_patterns']:
        patterns = data['query_patterns']
        summary += "QUERY PATTERNS:\n"
        
        if 'top_words' in patterns and patterns['top_words']:
            summary += "• Most Common Words:\n"
            for word, count in patterns['top_words'][:5]:
                summary += f"  - {word}: {count} occurrences\n"
        
        if patterns['question_queries'] > 0:
            summary += f"• Question-based Queries: {patterns['question_queries']}\n"
        
        if patterns['query_lengths']:
            avg_length = sum(patterns['query_lengths']) / len(patterns['query_lengths'])
            summary += f"• Average Query Length: {avg_length:.1f} words\n"
        summary += "\n"
    
    # Key Insights
    summary += "KEY INSIGHTS:\n"
    for insight in data['insights']:
        summary += f"• {insight}\n"
    
    return summary
