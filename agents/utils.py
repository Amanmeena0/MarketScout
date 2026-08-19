import random
import time
from typing import List, Optional
from google.api_core.exceptions import ServiceUnavailable, ResourceExhausted
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.tools import BaseTool
import os
from config import (
    google_api_key,
    huggingfacehub_api_token,
    groq_api_key,
    llm_provider,
    google_model,
    multipurpose_model,
    google_rate_limit_rps,
    planner_model,
    tool_routing_model,
    summarization_model,
    evidence_analysis_model,
    report_writing_model,
    report_review_model,
)

def _is_transient_error(e: Exception) -> bool:
    """Helper to check if an exception is transient (rate limit/overload)."""
    err_name = type(e).__name__
    if err_name in ("ServiceUnavailable", "ResourceExhausted", "HfHubHTTPError"):
        return True
    
    # Check error message/class for common keywords
    err_str = str(e).lower()
    if "429" in err_str or "503" in err_str or "rate limit" in err_str or "overloaded" in err_str:
        return True
        
    return False

def call_llm_with_backoff(llm, messages, max_retries=7, base_delay=4):
    """Call LLM with exponential backoff retry logic, catching service overloads and rate limits."""
    for attempt in range(max_retries):
        try:
            return llm.invoke(messages)
        except Exception as e:
            if _is_transient_error(e) and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"Transient error ({type(e).__name__}) hit. Retrying in {delay:.2f} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                raise e

def call_tool_llm_with_backoff(tool_llm, messages, max_retries=7, base_delay=4):
    """Call tool-bound LLM with exponential backoff retry logic, catching rate limits."""
    for attempt in range(max_retries):
        try:
            return tool_llm.invoke(messages)
        except Exception as e:
            if _is_transient_error(e) and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"Transient error ({type(e).__name__}) hit. Retrying in {delay:.2f} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
            else:
                raise e


# Setup a shared global rate limiter for Google Generative AI to prevent ResourceExhausted errors across concurrent requests.
_google_rate_limiter = None
if google_rate_limit_rps is not None and google_rate_limit_rps > 0:
    _google_rate_limiter = InMemoryRateLimiter(
        requests_per_second=google_rate_limit_rps,
        check_every_n_seconds=0.1,
        max_bucket_size=1,
    )


def get_llm(model_name: Optional[str] = None, provider: Optional[str] = None):
    # Determine provider based on parameter, model name prefix, or system default
    resolved_model = model_name or google_model
    resolved_provider = provider or llm_provider
    if model_name and not provider:
        m_lower = model_name.lower()
        if "gemini" in m_lower:
            resolved_provider = "google"
        elif "jan" in m_lower:
            resolved_provider = "jan"
        elif "groq" in m_lower or "llama" in m_lower or "mixtral" in m_lower or "gemma" in m_lower:
            resolved_provider = "groq"
        elif "/" in model_name:
            resolved_provider = "huggingface"

    if resolved_provider == "jan":
        jan_base = os.getenv("JAN_API_BASE", "http://localhost:1337/v1")
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model=resolved_model,
                api_key="jan",
                base_url=jan_base,
            )
        except Exception:
            from langchain_community.chat_models import ChatOpenAI
            return ChatOpenAI(
                model=resolved_model,
                openai_api_key="jan",
                openai_api_base=jan_base,
            )

    if resolved_provider == "huggingface":
        if not resolved_model:
            raise ValueError("model_name must be specified for huggingface provider")
        from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
        llm = HuggingFaceEndpoint(
            repo_id=resolved_model,
            task="text-generation",
            max_new_tokens=2048,
            huggingfacehub_api_token=huggingfacehub_api_token,
        )
        chat_model = ChatHuggingFace(llm=llm)
        return chat_model

    if resolved_provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model_name=resolved_model,
            groq_api_key=groq_api_key,
            max_retries=10
        )

    # Default to Google Generative AI
    return ChatGoogleGenerativeAI(
        model=resolved_model,
        rate_limiter=_google_rate_limiter,
        google_api_key=google_api_key,
        max_retries=10
    )


def summarize_text(text: str, max_chars: int = 1500) -> str:
    """Summarize long text using the configured summarization model if it exceeds length limits."""
    if not text or len(text) <= max_chars:
        return text or ""
        
    try:
        llm = get_llm(model_name=summarization_model)
        from langchain_core.messages import HumanMessage
        prompt = (
            f"You are an expert text summarizer. Meticulously analyze the following text and synthesize a highly detailed, "
            f"factual summary preserving all key statistics, numbers, dates, URLs, and insights. Keep it concise but information-dense.\n\n"
            f"Text to summarize:\n{text}"
        )
        summary_response = call_llm_with_backoff(llm, [HumanMessage(content=prompt)])
        return str(summary_response.content) if summary_response else text
    except Exception as e:
        print(f"Failed to summarize text: {e}")
        return text[:max_chars] + "... [Truncated due to summarization failure]"


class SummarizedTool(BaseTool):
    original_tool: BaseTool

    def _run(self, *args, **kwargs) -> str:
        tool_input = kwargs if kwargs else (args[0] if args else {})
        res = self.original_tool.invoke(tool_input)
        res_str = str(res)
        if len(res_str) > 2000:
            res_str = summarize_text(res_str)
        return res_str
        
    async def _arun(self, *args, **kwargs) -> str:
        tool_input = kwargs if kwargs else (args[0] if args else {})
        res = await self.original_tool.ainvoke(tool_input)
        res_str = str(res)
        if len(res_str) > 2000:
            res_str = summarize_text(res_str)
        return res_str


def wrap_tools_with_summarizer(tools: List[BaseTool]) -> List[BaseTool]:
    """Wraps tools so that large results are summarized using the configured summarization model."""
    wrapped = []
    for tool in tools:
        wrapped.append(
            SummarizedTool(
                name=tool.name,
                description=tool.description,
                args_schema=tool.args_schema,
                original_tool=tool,
            )
        )
    return wrapped