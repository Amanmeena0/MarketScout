import statistics


def calculate_trend(values: list) -> dict:
    """Calculate trend direction and strength."""
    if len(values) < 2:
        return {"direction": "insufficient_data", "strength": 0}
    
    # Simple linear trend calculation
    n = len(values)
    x = list(range(n))
    
    # Calculate slope using least squares
    x_mean = sum(x) / n
    y_mean = sum(values) / n
    
    numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        slope = 0
    else:
        slope = numerator / denominator
    
    # Determine trend direction and strength
    if abs(slope) < 0.1:
        direction = "stable"
    elif slope > 0:
        direction = "increasing"
    else:
        direction = "decreasing"
    
    strength = min(abs(slope) * 10, 100)  # Normalize to 0-100 scale
    
    return {
        "direction": direction,
        "strength": round(strength, 2),
        "slope": round(slope, 4)
    }


def calculate_volatility(values: list) -> dict:
    """Calculate volatility metrics."""
    if len(values) < 2:
        return {"level": "insufficient_data", "coefficient": 0}
    
    mean_val = statistics.mean(values)
    std_dev = statistics.stdev(values)
    
    # Coefficient of variation
    cv = (std_dev / mean_val * 100) if mean_val != 0 else 0
    
    # Categorize volatility
    if cv < 10:
        level = "low"
    elif cv < 25:
        level = "moderate"
    else:
        level = "high"
    
    return {
        "level": level,
        "coefficient": round(cv, 2),
        "standard_deviation": round(std_dev, 2)
    }


def detect_patterns(values: list, dates: list) -> dict:
    """Detect seasonal or cyclical patterns."""
    patterns = {
        "seasonal_detected": False,
        "peak_months": [],
        "low_months": [],
        "cyclical_pattern": "unknown"
    }
    
    # Basic month-based analysis
    month_values = {}
    for i, date in enumerate(dates):
        try:
            # Extract month from date string (assuming format like "Jul 21 – 27, 2024")
            month = date.split()[0]
            if month not in month_values:
                month_values[month] = []
            month_values[month].append(values[i])
        except:
            continue
    
    if month_values:
        month_averages = {month: statistics.mean(vals) for month, vals in month_values.items()}
        overall_avg = statistics.mean(values)
        
        # Find peak and low months
        peak_months = [month for month, avg in month_averages.items() if avg > overall_avg * 1.1]
        low_months = [month for month, avg in month_averages.items() if avg < overall_avg * 0.9]
        
        patterns.update({
            "seasonal_detected": len(peak_months) > 0 or len(low_months) > 0,
            "peak_months": peak_months,
            "low_months": low_months
        })
    
    return patterns


def identify_performance_periods(values: list, dates: list) -> dict:
    """Identify high and low performance periods."""
    if not values:
        return {}
    
    avg_value = statistics.mean(values)
    
    high_periods = []
    low_periods = []
    
    for i, (value, date) in enumerate(zip(values, dates)):
        if value >= avg_value * 1.2:  # 20% above average
            high_periods.append({"date": date, "value": value})
        elif value <= avg_value * 0.8:  # 20% below average
            low_periods.append({"date": date, "value": value})
    
    return {
        "high_performance_periods": high_periods[:5],  # Top 5
        "low_performance_periods": low_periods[:5],   # Bottom 5
        "average_baseline": round(avg_value, 2)
    }

