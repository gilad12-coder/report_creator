"""
Core utilities module providing LLM interface, rate limiting, and text processing functions.
"""
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Any
import requests
import os
from opentelemetry import trace

from src.utils.config import HYPER_URL, LIGHTWEIGHT_MODEL, PREMIUM_MODEL, RATE_LIMIT_CONFIG, MAX_CHUNK_SIZE, CHUNK_OVERLAP

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# Global rate limiting state
_last_call_time = 0
_call_count = 0
_minute_start = time.time()


def get_utc_timestamp() -> str:
    """Return current UTC timestamp in ISO format."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def apply_rate_limit() -> None:
    """Apply intelligent rate limiting to prevent 429 errors."""
    global _last_call_time, _call_count, _minute_start

    current_time = time.time()
    if current_time - _minute_start > 60:
        _call_count = 0
        _minute_start = current_time

    if _call_count >= RATE_LIMIT_CONFIG["calls_per_minute"]:
        sleep_time = 60 - (current_time - _minute_start) + 1
        logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
        time.sleep(sleep_time)
        _call_count = 0
        _minute_start = time.time()

    time_since_last = current_time - _last_call_time
    if time_since_last < RATE_LIMIT_CONFIG["base_delay"]:
        sleep_time = RATE_LIMIT_CONFIG["base_delay"] - time_since_last
        time.sleep(sleep_time)

    _last_call_time = time.time()
    _call_count += 1


def chat_completion(
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float = 0.3,
        operation_name: str = "llm_call",
        use_premium: bool = False
) -> str:
    """
    Call Hyperbolic API with intelligent rate limiting, error handling, retries, and Phoenix tracing.

    Args:
        messages: List of message dictionaries for the chat API
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature for generation
        operation_name: Name for the operation span in Phoenix
        use_premium: Whether to use premium model or lightweight model

    Returns:
        Generated text response from the API

    Raises:
        ValueError: If API key is not set
        requests.exceptions.HTTPError: For HTTP errors after retries
    """
    with tracer.start_as_current_span(operation_name) as span:
        api_key = os.getenv('HYPERBOLIC_API_KEY')
        if not api_key:
            raise ValueError("HYPERBOLIC_API_KEY environment variable not set")

        model = PREMIUM_MODEL if use_premium else LIGHTWEIGHT_MODEL

        span.set_attribute("llm.model", model)
        span.set_attribute("llm.temperature", temperature)
        span.set_attribute("llm.max_tokens", max_tokens)
        span.set_attribute("llm.operation", operation_name)
        span.set_attribute("llm.use_premium", use_premium)
        span.set_attribute("llm.provider", "hyperbolic")
        span.set_attribute("llm.input.messages", json.dumps(messages))

        for attempt in range(3):
            try:
                apply_rate_limit()

                logger.debug(f"API call attempt {attempt + 1} for {operation_name} using {model}")

                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "top_p": 0.9,
                    "max_tokens": max_tokens,
                }

                span.set_attribute("llm.request.payload", json.dumps(payload))

                response = requests.post(
                    HYPER_URL,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=120,
                )
                response.raise_for_status()

                response_data = response.json()
                content = response_data["choices"][0]["message"]["content"].strip()

                span.set_attribute("llm.output.content", content)
                span.set_attribute("llm.response_length", len(content))
                span.set_attribute("llm.success", True)

                if "usage" in response_data:
                    usage = response_data["usage"]
                    span.set_attribute("llm.usage.prompt_tokens", usage.get("prompt_tokens", 0))
                    span.set_attribute("llm.usage.completion_tokens", usage.get("completion_tokens", 0))
                    span.set_attribute("llm.usage.total_tokens", usage.get("total_tokens", 0))

                logger.debug(f"Successful API call for {operation_name} using {model}")
                return content

            except requests.exceptions.HTTPError as e:
                span.set_attribute("llm.error", str(e))
                span.set_attribute("llm.success", False)
                span.set_attribute("llm.error.type", "http_error")
                span.set_attribute("llm.error.status_code", e.response.status_code)

                if e.response.status_code == 429:
                    retry_after = e.response.headers.get('Retry-After')
                    if retry_after:
                        sleep_time = int(retry_after)
                    else:
                        sleep_time = RATE_LIMIT_CONFIG["rate_limit_delay"] * (attempt + 1)

                    logger.warning(f"Rate limit hit (429) on attempt {attempt + 1} for {operation_name}. "
                                   f"Sleeping for {sleep_time} seconds")
                    time.sleep(sleep_time)

                    if attempt == 2:
                        raise
                    continue

                elif e.response.status_code >= 500:
                    sleep_time = min(2 ** attempt, RATE_LIMIT_CONFIG["max_delay"])
                    logger.warning(
                        f"Server error ({e.response.status_code}) on attempt {attempt + 1} for {operation_name}. "
                        f"Sleeping for {sleep_time} seconds")
                    time.sleep(sleep_time)

                    if attempt == 2:
                        raise
                    continue
                else:
                    logger.error(f"Client error ({e.response.status_code}) for {operation_name}: {e}")
                    raise

            except Exception as e:
                span.set_attribute("llm.error", str(e))
                span.set_attribute("llm.success", False)
                span.set_attribute("llm.error.type", "general_error")
                sleep_time = min(2 ** attempt, RATE_LIMIT_CONFIG["max_delay"])
                logger.warning(f"API call attempt {attempt + 1} failed for {operation_name}: {e}. "
                               f"Sleeping for {sleep_time} seconds")
                if attempt == 2:
                    raise
                time.sleep(sleep_time)


def load_jsonl(path: Path) -> List[str]:
    """
    Load text items from JSONL file with error handling and Phoenix tracing.

    Args:
        path: Path to the JSONL file

    Returns:
        List of text strings extracted from the file

    Raises:
        FileNotFoundError: If the specified file doesn't exist
    """
    with tracer.start_as_current_span("load_jsonl") as span:
        span.set_attribute("file.path", str(path))

        items = []
        try:
            with path.open(encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line.strip())
                        if "text" in data:
                            items.append(data["text"])
                        else:
                            logger.warning(f"Line {line_num}: No 'text' field found")
                    except json.JSONDecodeError:
                        logger.warning(f"Line {line_num}: Invalid JSON, skipping")
        except FileNotFoundError:
            logger.error(f"File not found: {path}")
            span.set_attribute("error", f"File not found: {path}")
            raise

        span.set_attribute("items.loaded", len(items))
        logger.info(f"Loaded {len(items)} items from {path}")
        return items


def chunk_text(text: str, max_size: int = MAX_CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks for processing.

    Args:
        text: Input text to chunk
        max_size: Maximum number of words per chunk
        overlap: Number of words to overlap between chunks

    Returns:
        List of text chunks
    """
    with tracer.start_as_current_span("chunk_text") as span:
        words = text.split()
        span.set_attribute("input.word_count", len(words))
        span.set_attribute("chunk.max_size", max_size)
        span.set_attribute("chunk.overlap", overlap)

        if len(words) <= max_size:
            span.set_attribute("output.chunk_count", 1)
            return [text]

        chunks = []
        start = 0

        while start < len(words):
            end = min(start + max_size, len(words))
            chunk = " ".join(words[start:end])
            chunks.append(chunk)

            if end >= len(words):
                break
            start = end - overlap

        span.set_attribute("output.chunk_count", len(chunks))
        return chunks


def format_facts_for_display(facts: List[Dict[str, Any]]) -> str:
    """
    Format facts for digest processing and display.

    Args:
        facts: List of fact dictionaries

    Returns:
        Formatted facts string
    """
    formatted = []
    for i, fact in enumerate(facts):
        conf = fact.get('confidence', 0)
        formatted.append(
            f"{i + 1}. WHO: {fact.get('who', 'unknown')} | "
            f"WHAT: {fact.get('what', 'unknown')} | "
            f"WHEN: {fact.get('when', 'unknown')} | "
            f"WHERE: {fact.get('where', 'unknown')} | "
            f"CONFIDENCE: {conf:.2f}"
        )
    return "\n".join(formatted)


def format_fact_for_retrieval(fact: Dict[str, Any]) -> str:
    """
    Format fact for retrieval indexing.

    Args:
        fact: Fact dictionary

    Returns:
        Formatted fact string for retrieval
    """
    return (
        f"Individual: {fact.get('who', 'unknown')} "
        f"Action: {fact.get('what', 'unknown')} "
        f"Time: {fact.get('when', 'unknown')} "
        f"Location: {fact.get('where', 'unknown')} "
        f"Confidence: {fact.get('confidence', 0):.2f}"
    )


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('../../intel_pipeline.log'),
            logging.StreamHandler()
        ]
    )