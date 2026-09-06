import sys
import json
import asyncio
import argparse
import requests

try:
    import websockets
except ImportError:
    websockets = None

SERVER_HTTP_URL = "http://localhost:8000"
SERVER_WS_URL = "ws://localhost:8000"

async def stream_logs(analysis_id: str):
    if websockets is None:
        print("[!] Note: 'websockets' python library is not installed. You can install it with: pip install websockets")
        print(f"[*] Analysis {analysis_id} is running in the background. Check logs via server terminal or data/ folder.")
        return

    ws_endpoint = f"{SERVER_WS_URL}/ws/research/{analysis_id}"
    print(f"[*] Connecting to live log stream: {ws_endpoint} ...\n")
    try:
        async with websockets.connect(ws_endpoint) as ws:
            while True:
                try:
                    msg = await ws.recv()
                    if msg.startswith("__OUTPUT_FILE__"):
                        report_path = msg.replace("__OUTPUT_FILE__", "").strip()
                        print(f"\n[✓] Research Completed Successfully!")
                        print(f"[✓] PDF Report Generated at: {report_path}")
                        break
                    elif msg.startswith("__ERROR__"):
                        err_msg = msg.replace("__ERROR__", "").strip()
                        print(f"\n[✗] Pipeline Error Encountered: {err_msg}")
                        break
                    else:
                        print(msg, end="", flush=True)
                except websockets.exceptions.ConnectionClosed:
                    print("\n[*] WebSocket connection closed.")
                    break
    except Exception as e:
        print(f"\n[!] WebSocket stream connection ended: {e}")

def run_analysis(topic: str, analysis_type: str = "sales_forecasting", depth: str = "quick"):
    payload = {
        "market_topic": topic,
        "analysis_type": analysis_type,
        "geography": "Global",
        "research_depth": depth,
        "objective": {
            "type": "estimate_future_demand",
            "description": "Estimate future demand and market trends"
        },
        "decision_question": f"What is the market outlook and demand forecast for {topic}?",
        "context": {
            "forecast_period": "3 Years",
            "business_stage": "exploring"
        }
    }

    print(f"[*] Submitting research request to {SERVER_HTTP_URL}/analysis ...")
    print(f"    - Topic: {topic}")
    print(f"    - Analysis Type: {analysis_type}")
    print(f"    - Research Depth: {depth}")
    
    try:
        response = requests.post(f"{SERVER_HTTP_URL}/analysis", json=payload, timeout=10)
        if response.status_code != 200:
            print(f"[✗] Error submitting request ({response.status_code}): {response.text}")
            return
        
        data = response.json()
        analysis_id = data.get("id")
        print(f"[✓] Analysis created successfully! ID: {analysis_id}\n")
        
        asyncio.run(stream_logs(analysis_id))
    except requests.exceptions.ConnectionError:
        print(f"[✗] Error: Could not connect to MarketScout server at {SERVER_HTTP_URL}.")
        print("    Please ensure `python server.py` is running.")
    except Exception as e:
        print(f"[✗] Unexpected error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MarketScout research analysis via Terminal")
    parser.add_argument("--topic", type=str, default="B2B Remote Collaboration Software", help="Market topic / query")
    parser.add_argument("--type", type=str, default="sales_forecasting", 
                        choices=["sales_forecasting", "industry_analysis", "competitor_analysis", "market_gap_analysis", "target_market_analysis", "barrier_analysis"],
                        help="Analysis type")
    parser.add_argument("--depth", type=str, default="quick", choices=["quick", "comprehensive", "deep_research"], help="Depth/iterations")

    args = parser.parse_args()
    run_analysis(topic=args.topic, analysis_type=args.type, depth=args.depth)
