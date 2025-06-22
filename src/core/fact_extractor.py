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
    Returns facts with WHO/WHAT/WHEN/WHERE structure.
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
        Extract facts from a single text chunk with enhanced retry logic and robust JSON parsing.

        Args:
            chunk: Text chunk to process

        Returns:
            List of extracted fact dictionaries
        """
        with tracer.start_as_current_span("extract_from_chunk") as span:
            span.set_attribute("chunk.length", len(chunk))

            prompt = FACT_EXTRACTION_TEMPLATE.render(item_text=chunk)
            messages = [{"role": "user", "content": prompt}]

            for attempt in range(4):
                try:
                    response = chat_completion(
                        messages,
                        max_tokens=800,
                        temperature=0.1,
                        operation_name="fact_extraction",
                        use_premium=False
                    )

                    if not response or not response.strip():
                        logger.warning(f"Empty response on attempt {attempt + 1}")
                        if attempt < 3:
                            messages.append({
                                "role": "user",
                                "content": "Please provide a valid JSON array response. Example: [{\"who\": \"person\", \"what\": \"action\", \"when\": \"time\", \"where\": \"location\"}]"
                            })
                            continue
                        else:
                            span.set_attribute("extraction.result", "empty_response")
                            return []

                    facts = self._extract_json_with_fallbacks(response, attempt)

                    if facts is not None:
                        valid_facts = self._validate_and_clean_facts(facts)
                        span.set_attribute("extraction.result", "success")
                        span.set_attribute("facts.extracted", len(valid_facts))
                        logger.debug(f"Successfully extracted {len(valid_facts)} facts on attempt {attempt + 1}")
                        return valid_facts
                    else:
                        logger.warning(f"Failed to extract valid JSON on attempt {attempt + 1}")
                        if attempt < 3:
                            error_msg = FactExtractor._generate_retry_message(response, attempt)
                            messages.extend([
                                {"role": "assistant", "content": response},
                                {"role": "user", "content": error_msg}
                            ])
                            continue

                except Exception as e:
                    logger.warning(f"Unexpected error on attempt {attempt + 1}: {e}")
                    span.set_attribute("extraction.error", f"unexpected_error: {e}")
                    if attempt < 3:
                        messages.append({
                            "role": "user",
                            "content": f"Error occurred: {e}. Please provide a clean JSON array format with no extra text."
                        })

            span.set_attribute("extraction.result", "failed_all_attempts")
            logger.warning(f"Failed to extract facts from chunk after all attempts")
            return []

    @staticmethod
    def _extract_json_with_fallbacks(response: str, attempt: int) -> Optional[List[Dict[str, Any]]]:
        """
        Try multiple strategies to extract valid JSON from the response.

        Args:
            response: Raw LLM response
            attempt: Current attempt number (for logging)

        Returns:
            List of fact dictionaries if successful, None if failed
        """
        strategies = [
            FactExtractor._extract_clean_json,
            FactExtractor._extract_json_from_code_block,
            FactExtractor._extract_json_with_regex,
            FactExtractor._extract_json_lenient_parsing,
            FactExtractor._fix_common_json_issues
        ]

        for i, strategy in enumerate(strategies):
            try:
                result = strategy(response)
                if result is not None:
                    logger.debug(f"JSON extraction successful with strategy {i + 1} on attempt {attempt + 1}")
                    return result
            except Exception as e:
                logger.debug(f"Strategy {i + 1} failed: {e}")
                continue

        return None

    @staticmethod
    def _extract_clean_json(response: str) -> Optional[List[Dict[str, Any]]]:
        """Try to parse response as direct JSON."""
        response = response.strip()
        if response.startswith('[') and response.endswith(']'):
            return json.loads(response)
        return None

    @staticmethod
    def _extract_json_from_code_block(response: str) -> Optional[List[Dict[str, Any]]]:
        """Extract JSON from markdown code blocks."""
        if "```json" in response:
            start = response.find("```json") + 7
            end = response.find("```", start)
            if end != -1:
                json_str = response[start:end].strip()
                return json.loads(json_str)
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            if end != -1:
                json_str = response[start:end].strip()
                if json_str.startswith('['):
                    return json.loads(json_str)
        return None

    @staticmethod
    def _extract_json_with_regex(response: str) -> Optional[List[Dict[str, Any]]]:
        """Use regex to find JSON array in response."""
        pattern = r'\[(?:[^[\]]|(?:\[[^\]]*\]))*\]'
        matches = re.findall(pattern, response, re.DOTALL)

        for match in matches:
            try:
                cleaned = match.strip()
                if cleaned.startswith('[') and cleaned.endswith(']'):
                    return json.loads(cleaned)
            except json.JSONDecodeError:
                continue
        return None

    @staticmethod
    def _extract_json_lenient_parsing(response: str) -> Optional[List[Dict[str, Any]]]:
        """Try to find and parse JSON with more lenient approach."""
        start_idx = response.find('[')
        end_idx = response.rfind(']')

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            potential_json = response[start_idx:end_idx + 1]
            try:
                return json.loads(potential_json)
            except json.JSONDecodeError:
                pass
        return None

    @staticmethod
    def _fix_common_json_issues(response: str) -> Optional[List[Dict[str, Any]]]:
        """Try to fix common JSON formatting issues."""
        start_idx = response.find('[')
        end_idx = response.rfind(']')

        if start_idx == -1 or end_idx == -1:
            return None

        json_str = response[start_idx:end_idx + 1]

        fixes = [
            (r',\s*}', '}'),
            (r',\s*]', ']'),
            (r'([{,]\s*)(\w+):', r'\1"\2":'),
            (r"'([^']*)'", r'"\1"'),
        ]

        for pattern, replacement in fixes:
            json_str = re.sub(pattern, replacement, json_str)

        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _validate_and_clean_facts(facts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and clean extracted facts.

        Args:
            facts: Raw list of fact dictionaries

        Returns:
            List of validated and cleaned fact dictionaries
        """
        if not isinstance(facts, list):
            logger.warning(f"Facts is not a list: {type(facts)}")
            return []

        valid_facts = []
        required_keys = {"who", "what", "when", "where"}

        for i, fact in enumerate(facts):
            if not isinstance(fact, dict):
                logger.warning(f"Fact {i} is not a dictionary: {type(fact)}")
                continue

            if not required_keys.issubset(fact.keys()):
                missing_keys = required_keys - set(fact.keys())
                logger.warning(f"Fact {i} missing required keys: {missing_keys}")
                continue

            cleaned_fact = FactExtractor._clean_individual_fact(fact)
            if cleaned_fact:
                valid_facts.append(cleaned_fact)
            else:
                logger.warning(f"Fact {i} failed validation after cleaning")

        return valid_facts

    @staticmethod
    def _clean_individual_fact(fact: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Clean and validate individual fact.

        Args:
            fact: Single fact dictionary

        Returns:
            Cleaned fact dictionary or None if invalid
        """
        try:
            cleaned = {
                "who": str(fact.get("who", "unknown")).strip(),
                "what": str(fact.get("what", "unknown")).strip(),
                "when": str(fact.get("when", "unknown")).strip(),
                "where": str(fact.get("where", "unknown")).strip()
            }

            if all(v in ["unknown", "", "Unknown", "UNKNOWN"] for v in
                   [cleaned["who"], cleaned["what"], cleaned["when"], cleaned["where"]]):
                logger.warning("Fact has all unknown values, skipping")
                return None

            return cleaned

        except (ValueError, TypeError) as e:
            logger.warning(f"Error cleaning fact: {e}")
            return None

    @staticmethod
    def _generate_retry_message(response: str, attempt: int) -> str:
        """
        Generate specific retry message based on the response and attempt.

        Args:
            response: Failed response
            attempt: Current attempt number

        Returns:
            Specific error message for retry
        """
        if not response.strip():
            return "Response was empty. Please provide a JSON array with fact objects."

        if '[' not in response or ']' not in response:
            return "Response must be a JSON array starting with '[' and ending with ']'. Example: [{\"who\": \"person\", \"what\": \"action\", \"when\": \"time\", \"where\": \"location\"}]"

        if '"who"' not in response or '"what"' not in response:
            return "Each fact object must contain all required fields: 'who', 'what', 'when', 'where'. Please ensure proper JSON formatting."

        if attempt == 0:
            return "JSON parsing failed. Please ensure proper JSON syntax with double quotes around strings and proper comma separation."
        elif attempt == 1:
            return "Still having JSON issues. Please return ONLY a clean JSON array with no extra text, comments, or formatting."
        else:
            return "Final attempt: Provide exactly this format: [{\"who\": \"value\", \"what\": \"value\", \"when\": \"value\", \"where\": \"value\"}]"