import re
import datetime
import logging
from typing import List, Optional, Any
from database.storage import get_storage
from database.schema import SearchEvidenceItem

logger = logging.getLogger("market_scout.memory")

URL_REGEX = re.compile(r'https?://[^\s)\]"\'<>]+')


def extract_urls(text: str) -> List[str]:
    """Extract unique HTTP/HTTPS URLs from any tool output or string."""
    if not text:
        return []
    matches = URL_REGEX.findall(str(text))
    # Deduplicate while preserving order
    seen = set()
    unique_urls = []
    for u in matches:
        clean = u.rstrip(".,;:")
        if clean not in seen:
            seen.add(clean)
            unique_urls.append(clean)
    return unique_urls


def record_tool_evidence(
    analysis_id: str,
    stage: str,
    tool_name: str,
    tool_args: Any,
    tool_result: str,
) -> None:
    """
    Persists a tool's search result and extracted URLs immediately to disk/storage.
    This guarantees no search calls are lost if downstream steps crash or fail.
    """
    if not analysis_id:
        return

    try:
        storage = get_storage()
        urls = extract_urls(tool_result)
        
        # Build human-readable query string from args
        query_str = ""
        if isinstance(tool_args, dict):
            query_str = str(tool_args.get("query") or tool_args.get("url") or tool_args)
        elif tool_args:
            query_str = str(tool_args)

        # Truncate content snippet for clean preview
        snippet = str(tool_result)[:1000]

        evidence_item = SearchEvidenceItem(
            timestamp=datetime.datetime.now().ctime(),
            stage=stage,
            tool_name=tool_name,
            query_or_url=query_str,
            content_snippet=snippet,
            extracted_urls=urls,
        )

        storage.push_evidence(analysis_id, evidence_item.model_dump())
        logger.info(
            "[%s] Persisted search evidence from tool '%s' (%d URLs found)",
            analysis_id,
            tool_name,
            len(urls),
        )

        # Also cache search result for query deduplication
        if query_str and len(tool_result) > 50:
            cache_key = f"{tool_name}:{query_str.strip().lower()}"
            storage.save_search_cache(cache_key, tool_result)

    except Exception as e:
        logger.warning("[%s] Failed to persist tool evidence: %s", analysis_id, e)


def record_draft_report(analysis_id: str, draft_markdown: str) -> None:
    """
    Saves an intermediate draft report to disk/storage before entering reflection loops.
    """
    if not analysis_id or not draft_markdown:
        return

    try:
        storage = get_storage()
        storage.update_analysis(
            analysis_id,
            {"draft_report": str(draft_markdown)}
        )
        logger.info("[%s] Persisted intermediate draft report to disk/storage", analysis_id)
    except Exception as e:
        logger.warning("[%s] Failed to persist draft report: %s", analysis_id, e)


def get_cached_search(tool_name: str, query: str) -> Optional[str]:
    """Retrieve cached search result if previously executed."""
    try:
        storage = get_storage()
        cache_key = f"{tool_name}:{query.strip().lower()}"
        return storage.get_search_cache(cache_key)
    except Exception:
        return None
