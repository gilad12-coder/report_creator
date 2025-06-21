"""
Stage 1: Item-level fact extraction using structured prompts with lightweight LLM.

Extracts structured WHO/WHAT/WHEN/WHERE/CONFIDENCE facts from intelligence items
using chunked processing and retry logic for robust JSON parsing.
Now includes relevance filtering to only process items related to the target.
"""
import json
import re
import logging
from typing import Dict, List, Any, Tuple, Optional
from tqdm import tqdm
from opentelemetry import trace
from src.utils.config import FACT_EXTRACTION_TEMPLATE, RELEVANCE_CHECK_TEMPLATE
from src.utils.utils import chunk_text, chat_completion

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class FactExtractor:
    """
    Extracts structured facts from intelligence items using lightweight LLM.

    First filters items for relevance to target, then processes relevant items in chunks
    and applies retry logic for robust JSON parsing.
    Returns facts with WHO/WHAT/WHEN/WHERE/CONFIDENCE structure.
    """

    def extract_facts(self, items: List[str], target_info: Optional[Dict[str, str]] = None) -> Tuple[
        List[Dict[str, Any]], Dict[str, int]]:
        """
        Extract structured facts from intelligence items relevant to target using lightweight model.

        Args:
            items: List of intelligence text items
            target_info: Optional dictionary containing target information (name, aliases, age, etc.)

        Returns:
            Tuple of (list of fact dictionaries, statistics dictionary)
        """
        with tracer.start_as_current_span("fact_extraction_stage") as span:
            span.set_attribute("input.item_count", len(items))

            if target_info:
                span.set_attribute("target.name", target_info.get("name", "unknown"))
                logger.info(
                    f"Starting relevance filtering and fact extraction from {len(items)} items for target: {target_info.get('name', 'unknown')}")

                relevant_items = []
                for i, item in enumerate(tqdm(items, desc="Filtering for relevance")):
                    with tracer.start_as_current_span(f"relevance_check_{i}") as relevance_span:
                        relevance_span.set_attribute("item.index", i)
                        relevance_span.set_attribute("item.length", len(item))

                        is_relevant = self._check_relevance(item, target_info)
                        relevance_span.set_attribute("item.relevant", is_relevant)

                        if is_relevant:
                            relevant_items.append(item)

                span.set_attribute("filtered.relevant_count", len(relevant_items))
                logger.info(f"Filtered {len(relevant_items)} relevant items out of {len(items)} total items")
            else:
                logger.info(f"No target info provided, processing all {len(items)} items")
                relevant_items = items

            all_facts = []
            for i, item in enumerate(tqdm(relevant_items, desc="Extracting facts")):
                with tracer.start_as_current_span(f"extract_item_{i}") as item_span:
                    item_span.set_attribute("item.index", i)
                    item_span.set_attribute("item.length", len(item))

                    chunks = chunk_text(item)
                    item_span.set_attribute("chunks.count", len(chunks))

                    item_facts = []
                    for j, chunk in enumerate(chunks):
                        with tracer.start_as_current_span(f"extract_chunk_{j}") as chunk_span:
                            chunk_span.set_attribute("chunk.index", j)
                            chunk_span.set_attribute("chunk.length", len(chunk))

                            facts = self._extract_from_chunk(chunk)
                            chunk_span.set_attribute("facts.extracted", len(facts))
                            item_facts.extend(facts)

                    item_span.set_attribute("item.facts_extracted", len(item_facts))
                    all_facts.extend(item_facts)

            stats = {
                "total_items": len(items),
                "relevant_items": len(relevant_items),
                "filtered_out": len(items) - len(relevant_items),
                "facts_extracted": len(all_facts)
            }

            span.set_attribute("output.fact_count", len(all_facts))
            logger.info(f"Extracted {len(all_facts)} total facts from {len(relevant_items)} relevant items")

            return all_facts, stats

    def _check_relevance(self, item: str, target_info: Dict[str, str]) -> bool:
        """
        Check if an intelligence item is relevant to the target person.

        Args:
            item: Intelligence text item to check
            target_info: Target person information

        Returns:
            True if item is relevant to target, False otherwise
        """
        with tracer.start_as_current_span("relevance_check") as span:
            span.set_attribute("item.length", len(item))
            span.set_attribute("target.name", target_info.get("name", "unknown"))

            target_card = self._format_target_card(target_info)

            prompt = RELEVANCE_CHECK_TEMPLATE.render(
                target_card=target_card,
                intelligence_item=item
            )

            messages = [{"role": "user", "content": prompt}]

            for attempt in range(3):
                try:
                    response = chat_completion(
                        messages,
                        max_tokens=100,
                        temperature=0.1,
                        operation_name="relevance_check",
                        use_premium=False
                    )

                    if not response or not response.strip():
                        logger.warning(f"Empty response on relevance check attempt {attempt + 1}")
                        if attempt < 2:
                            messages.append(
                                {"role": "user", "content": "אנא השב בפורמט: סטטוס: <רלוונטי / לא רלוונטי>"})
                            continue
                        else:
                            span.set_attribute("relevance.result", "default_not_relevant")
                            return False

                    is_relevant = self._parse_relevance_response(response)
                    span.set_attribute("relevance.result", "relevant" if is_relevant else "not_relevant")
                    return is_relevant

                except Exception as e:
                    logger.warning(f"Error in relevance check attempt {attempt + 1}: {e}")
                    span.set_attribute("relevance.error", f"error: {e}")
                    if attempt < 2:
                        messages.append({"role": "user", "content": "אנא נסה שוב עם תשובה בפורמט הנדרש."})
                    else:
                        logger.warning(
                            f"Failed relevance check after {attempt + 1} attempts, defaulting to not relevant")

            span.set_attribute("relevance.result", "failed_default_not_relevant")
            return False

    @staticmethod
    def _format_target_card(target_info: Dict[str, str]) -> str:
        """
        Format target information into Hebrew card format.

        Args:
            target_info: Dictionary with target details

        Returns:
            Formatted Hebrew target card string
        """
        card_lines = []

        if target_info.get("name"):
            card_lines.append(f"שם: {target_info['name']}")

        if target_info.get("aliases"):
            if isinstance(target_info["aliases"], list):
                aliases_str = ", ".join([f'"{alias}"' for alias in target_info["aliases"]])
            else:
                aliases_str = f'"{target_info["aliases"]}"'
            card_lines.append(f"כינויים: {aliases_str}")

        if target_info.get("age"):
            card_lines.append(f"גיל: {target_info['age']}")

        if target_info.get("address"):
            card_lines.append(f"כתובת: {target_info['address']}")

        if target_info.get("family"):
            card_lines.append(f"משפחה: {target_info['family']}")

        if target_info.get("role"):
            card_lines.append(f"תפקיד: {target_info['role']}")

        if target_info.get("id_number"):
            card_lines.append(f"ת״ז: {target_info['id_number']}")

        return "\n".join(card_lines)

    @staticmethod
    def _parse_relevance_response(response: str) -> bool:
        """
        Parse the Hebrew relevance response to determine if item is relevant.

        Args:
            response: Raw response from relevance check

        Returns:
            True if relevant, False if not relevant
        """
        response = response.strip()

        if "סטטוס:" in response:
            status_line = response.split("סטטוס:")[1].split("\n")[0].strip()
            if "לא רלוונטי" in status_line:
                return False
            elif "רלוונטי" in status_line:
                return True

        if "לא רלוונטי" in response:
            return False
        elif "רלוונטי" in response:
            return True

        logger.warning(f"Unclear relevance response: {response}")
        return False

    def _extract_from_chunk(self, chunk: str) -> List[Dict[str, Any]]:
        """
        Extract facts from a single text chunk with retry logic using lightweight model.

        Args:
            chunk: Text chunk to process

        Returns:
            List of extracted fact dictionaries
        """
        with tracer.start_as_current_span("extract_from_chunk") as span:
            span.set_attribute("chunk.length", len(chunk))

            prompt = FACT_EXTRACTION_TEMPLATE.render(item_text=chunk)
            messages = [{"role": "user", "content": prompt}]

            for attempt in range(3):
                try:
                    response = chat_completion(
                        messages,
                        max_tokens=500,
                        temperature=0.1,
                        operation_name="fact_extraction",
                        use_premium=False
                    )

                    if not response or not response.strip():
                        logger.warning(f"Empty response on attempt {attempt + 1}")
                        if attempt < 2:
                            messages.append({"role": "user", "content": "Please provide a valid JSON response."})
                            continue
                        else:
                            span.set_attribute("extraction.result", "empty_response")
                            return []

                    cleaned_response = self._clean_json_response(response)

                    if not cleaned_response:
                        logger.warning(f"No valid JSON found in response on attempt {attempt + 1}")
                        if attempt < 2:
                            messages.extend([
                                {"role": "assistant", "content": response},
                                {"role": "user", "content": "Please provide ONLY a valid JSON array, no other text."}
                            ])
                            continue
                        else:
                            span.set_attribute("extraction.result", "no_valid_json")
                            return []

                    facts = json.loads(cleaned_response)

                    if isinstance(facts, list):
                        valid_facts = []
                        for fact in facts:
                            if isinstance(fact, dict) and all(
                                    key in fact for key in ["who", "what", "when", "where", "confidence"]):
                                valid_facts.append(fact)

                        span.set_attribute("extraction.result", "success")
                        span.set_attribute("facts.extracted", len(valid_facts))
                        return valid_facts
                    else:
                        logger.warning(f"Response is not a list on attempt {attempt + 1}")
                        if attempt < 2:
                            messages.extend([
                                {"role": "assistant", "content": response},
                                {"role": "user", "content": "Please provide a JSON array (list) format."}
                            ])
                            continue

                except json.JSONDecodeError as e:
                    logger.warning(f"JSON decode error on attempt {attempt + 1}: {e}")
                    logger.debug(f"Problematic response: {repr(response)}")
                    span.set_attribute("extraction.error", f"json_decode_error: {e}")
                    if attempt < 2:
                        messages.extend([
                            {"role": "assistant", "content": response},
                            {"role": "user",
                             "content": f"JSON parsing failed: {e}. Please provide valid JSON format only."}
                        ])
                    else:
                        logger.warning(f"Failed to extract facts from chunk after {attempt + 1} attempts")
                except Exception as e:
                    logger.warning(f"Unexpected error on attempt {attempt + 1}: {e}")
                    span.set_attribute("extraction.error", f"unexpected_error: {e}")
                    if attempt < 2:
                        messages.append({"role": "user", "content": "Please try again with valid JSON format."})

            span.set_attribute("extraction.result", "failed_all_attempts")
            return []

    @staticmethod
    def _clean_json_response(response: str) -> str:
        """
        Clean the response to extract valid JSON.

        Args:
            response: Raw response from LLM

        Returns:
            Cleaned JSON string or empty string if no valid JSON found
        """
        if not response:
            return ""

        response = response.strip()

        if response.startswith("```json"):
            response = response[7:]
        elif response.startswith("```"):
            response = response[3:]

        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        json_pattern = r'\[.*?\]'
        matches = re.findall(json_pattern, response, re.DOTALL)

        if matches:
            return matches[0]

        if response.startswith('[') and response.endswith(']'):
            return response

        return ""