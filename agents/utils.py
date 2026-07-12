import random
import time
from google.api_core.exceptions import ServiceUnavailable
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.rate_limiters import InMemoryRateLimiter
from config import google_api_key

def call_llm_with_backoff(llm, messages, max_retries=5, base_delay=1):
    """Call LLM with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            return llm.invoke(messages)
        except ServiceUnavailable as e:
            if attempt == max_retries - 1:
                raise e
            
            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"Model overloaded. Retrying in {delay:.2f} seconds... (attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
        except Exception as e:
            # For other exceptions, don't retry
            raise e

def call_tool_llm_with_backoff(tool_llm, messages, max_retries=5, base_delay=1):
    """Call tool-bound LLM with exponential backoff retry logic."""
    for attempt in range(max_retries):
        try:
            return tool_llm.invoke(messages)
        except ServiceUnavailable as e:
            if attempt == max_retries - 1:
                raise e
            
            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"Model overloaded. Retrying in {delay:.2f} seconds... (attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)
        except Exception as e:
            # For other exceptions, don't retry
            raise e


def get_llm():
    rate_limiter = InMemoryRateLimiter(
        requests_per_second=0.25,
        check_every_n_seconds=0.1,
        max_bucket_size=10,
    )
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        rate_limiter=rate_limiter,
        google_api_key=google_api_key
    )