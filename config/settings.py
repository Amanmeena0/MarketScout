import os
import warnings
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

google_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")
huggingfacehub_api_token: Optional[str] = os.getenv("HUGGINGFACEHUB_API_TOKEN")
groq_api_key: Optional[str] = os.getenv("GROQ_API_KEY")

ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Provider: 'google', 'huggingface', 'groq', 'jan', or 'ollama'
llm_provider: str = os.getenv("LLM_PROVIDER", "").lower()
if not llm_provider:
    if google_api_key:
        llm_provider = "google"
    elif huggingfacehub_api_token:
        llm_provider = "huggingface"
    elif groq_api_key:
        llm_provider = "groq"
    else:
        llm_provider = "google"

google_model: str = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")
multipurpose_model: str = os.getenv("MULTIPURPOSE_MODEL", "jan-v1-4b")

# Component-Specific Models Configuration
planner_model: str = os.getenv("PLANNER_MODEL", "gemini-2.0-flash")
tool_routing_model: str = os.getenv("TOOL_ROUTING_MODEL", "gemini-2.0-flash")
summarization_model: str = os.getenv("SUMMARIZATION_MODEL", "jan-v1-4b")
evidence_analysis_model: str = os.getenv("EVIDENCE_ANALYSIS_MODEL", "gemini-2.0-flash")
report_writing_model: str = os.getenv("REPORT_WRITING_MODEL", "gemini-2.0-flash")
report_review_model: str = os.getenv("REPORT_REVIEW_MODEL", "gemini-2.0-flash")

# Default rate limit for Free Tier is 0.1 rps (1 request per 10 seconds).
# Set GOOGLE_RATE_LIMIT_RPS to 0, none, or empty to disable the rate limiter.
google_rate_limit_rps: Optional[float] = 0.1
raw_rps = os.getenv("GOOGLE_RATE_LIMIT_RPS")
if raw_rps is not None:
    if raw_rps.strip().lower() in ("0", "none", "false", ""):
        google_rate_limit_rps = None
    else:
        try:
            google_rate_limit_rps = float(raw_rps)
        except ValueError:
            warnings.warn(f"Invalid GOOGLE_RATE_LIMIT_RPS: '{raw_rps}'. Defaulting to 0.1.")
            google_rate_limit_rps = 0.1

serp_api_key: Optional[str] = os.getenv("SERP_API_KEY")
serp_dev_api_key: Optional[str] = os.getenv("SERP_DEV_API_KEY")

x_bearer_token: Optional[str] = os.getenv("X_BEARER_TOKEN") or os.getenv("TWITTER_BEARER_TOKEN")
x_api_key: Optional[str] = os.getenv("X_API_KEY") or os.getenv("TWITTER_API_KEY")
x_api_secret: Optional[str] = os.getenv("X_API_SECRET") or os.getenv("X_SECRET_API_KEY") or os.getenv("TWITTER_API_SECRET")
x_access_token: Optional[str] = os.getenv("X_ACCESS_TOKEN") or os.getenv("TWITTER_ACCESS_TOKEN")
x_access_token_secret: Optional[str] = os.getenv("X_ACCESS_TOKEN_SECRET") or os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

mongodb_uri: Optional[str] = os.getenv("MONGO_DB_URI", None)

if llm_provider == "google" and not google_api_key:
    raise ValueError("Warning: Google API Key is not set but LLM_PROVIDER is 'google'.")

if llm_provider == "huggingface" and not huggingfacehub_api_token:
    raise ValueError("Warning: HUGGINGFACEHUB_API_TOKEN is not set but LLM_PROVIDER is 'huggingface'.")

if llm_provider == "groq" and not groq_api_key:
    raise ValueError("Warning: GROQ_API_KEY is not set but LLM_PROVIDER is 'groq'.")

if not serp_dev_api_key:
    raise ValueError("Warning: SERP Dev API Key is not set. Some features may not work.")

if not mongodb_uri:
    raise ValueError("Warning: MongoDB URI is not set. Database operations will not work.")

output_dir: str = os.getenv("OUTPUT_DIR", "reports")