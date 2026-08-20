import sys
import os
import json
from bson import json_util
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from database.db import client

try:
    db = client['market_analysis']
    analyses = list(db.analyses.find().sort("created_at", -1).limit(10))
    
    print(f"\nTotal analyses found: {len(analyses)}")
    print("=" * 50)
    for index, analysis in enumerate(analyses, start=1):
        # Convert ObjectId and other BSON types to string for clean printing
        print(f"Record #{index}:")
        print(json.dumps(analysis, default=json_util.default, indent=4))
        print("-" * 50)
        
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
