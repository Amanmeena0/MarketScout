import sys
import os
from dotenv import load_dotenv

# Add the server directory to python path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from agents.utils import get_llm
from langchain_core.messages import HumanMessage

def test_model(model_name: str):
    print(f"\n{'='*50}")
    print(f"Testing Model: {model_name}")
    print(f"{'='*50}")
    try:
        # We don't strictly need to pass provider since we built auto-detection
        llm = get_llm(model_name=model_name)
        
        print(f"Successfully instantiated LLM object: {type(llm).__name__}")
        
        prompt = "Hello, reply with exactly one short sentence confirming you are working."
        print(f"Prompt: '{prompt}'")
        print("Waiting for response...")
        
        response = llm.invoke([HumanMessage(content=prompt)])
        print(f"-> Response: {response.content}")
        
    except Exception as e:
        print(f"-> Error testing {model_name}: {e}")

if __name__ == "__main__":
    models_to_test = [
        "llama3.2:3b",
        "phi3:mini",
        "gemma3:4b",
        "jan-v1-4b:latest"
    ]
    
    print("Starting Multi-Model Local Tests...")
    print("Note: Ensure your Ollama and Jan servers are running locally.")
    
    for model in models_to_test:
        test_model(model)
