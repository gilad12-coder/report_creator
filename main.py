"""
Intelligence Pipeline with Hyperbolic API, PyLate ColBERT, and Arize Phoenix.

A comprehensive 5-stage intelligence processing pipeline that transforms raw intelligence
items into structured reports using hierarchical tree processing and intelligent retrieval.
"""

import time
import uuid
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
import phoenix as px
from phoenix.otel import register
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry import trace
from dotenv import load_dotenv

from src.utils.config import DEFAULT_NEO4J_CONFIG, LIGHTWEIGHT_MODEL, PREMIUM_MODEL
from src.utils.utils import load_jsonl, get_utc_timestamp
from src.core.fact_extractor import FactExtractor
from src.core.digest_layer import DigestLayer
from src.core.retrieval_index import RetrievalIndex
from src.core.report_generator import SectionedReportGenerator

load_dotenv()

logger = logging.getLogger(__name__)


def initialize_phoenix() -> tuple[px.Session, trace.TracerProvider]:
    """
    Initialize Phoenix observability session with immediate tracing setup.

    Returns:
        Tuple of (Phoenix session object, tracer provider)
    """
    phoenix_session = px.launch_app()
    print(f"Phoenix UI available at: {phoenix_session.url}")

    tracer_provider = register(
        project_name="intel_pipeline",
        auto_instrument=True,
        endpoint="http://localhost:6006/v1/traces"
    )

    RequestsInstrumentor().instrument()

    return phoenix_session, tracer_provider


def get_neo4j_config() -> Dict[str, str]:
    """
    Get Neo4j configuration from environment variables with defaults.

    Returns:
        Dictionary containing Neo4j connection parameters
    """
    return {
        "uri": os.getenv('NEO4J_URI', DEFAULT_NEO4J_CONFIG["uri"]),
        "user": os.getenv('NEO4J_USER', DEFAULT_NEO4J_CONFIG["user"]),
        "password": os.getenv('NEO4J_PASSWORD', DEFAULT_NEO4J_CONFIG["password"])
    }


def validate_environment() -> None:
    """
    Validate required environment variables and dependencies.

    Raises:
        ValueError: If required environment variables are missing
    """
    api_key = os.getenv('HYPERBOLIC_API_KEY')
    if not api_key:
        raise ValueError("HYPERBOLIC_API_KEY environment variable not set")

    logger.info("Environment validation passed")


def generate_intel_report(
        dossier_path: str,
        target: str,
        output_path: str,
        neo4j_config: Optional[Dict[str, str]] = None,
        target_info: Optional[Dict[str, str]] = None
) -> None:
    """
    Main pipeline function with hierarchical tree processing and intelligent report generation.

    Args:
        dossier_path: Path to JSONL file containing intelligence items
        target: Target name for the intelligence report
        output_path: Path where the final report will be saved
        neo4j_config: Optional Neo4j configuration override
        target_info: Optional detailed target information for relevance filtering
    """
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("hierarchical_intel_pipeline") as span:
        start_time = time.time()
        span.set_attribute("target", target)
        span.set_attribute("dossier_path", dossier_path)
        span.set_attribute("lightweight_model", LIGHTWEIGHT_MODEL)
        span.set_attribute("premium_model", PREMIUM_MODEL)
        span.set_attribute("pipeline.type", "hierarchical_tree")

        if neo4j_config is None:
            neo4j_config = get_neo4j_config()

        span.set_attribute("neo4j.uri", neo4j_config["uri"])
        span.set_attribute("neo4j.user", neo4j_config["user"])

        if target_info is None:
            target_info = {"name": target}

        logger.info(f"Starting hierarchical intelligence pipeline for target: {target}")
        logger.info(f"Neo4j connection: {neo4j_config['uri']}")
        logger.info(f"Using tree processing: {LIGHTWEIGHT_MODEL} for tree construction, {PREMIUM_MODEL} for reports")

        raw_items = load_jsonl(Path(dossier_path))
        span.set_attribute("input.raw_items", len(raw_items))
        logger.info(f"Loaded {len(raw_items)} raw intelligence items")

        logger.info(f"Stage 1: Extracting facts using {LIGHTWEIGHT_MODEL}...")
        extractor = FactExtractor()
        facts, extraction_stats = extractor.extract_facts(raw_items, target_info)

        span.set_attribute("facts.extracted", len(facts))
        span.set_attribute("stats.total_items", extraction_stats["total_items"])
        span.set_attribute("stats.relevant_items", extraction_stats["relevant_items"])
        span.set_attribute("stats.filtered_out", extraction_stats["filtered_out"])

        logger.info(f"Stage 2: Creating hierarchical digest tree using {LIGHTWEIGHT_MODEL}...")
        digest_layer = DigestLayer()
        digest_tree = digest_layer.digest_facts(facts)
        span.set_attribute("tree.leafs", len(digest_tree.leafs))
        span.set_attribute("tree.branches", len(digest_tree.branches))
        span.set_attribute("tree.has_root", bool(digest_tree.root))

        logger.info("Stage 3: Building hierarchical Neo4j + ColBERT index...")
        db_path = Path("colbert_cache") / f"intel_{uuid.uuid4().hex[:8]}"
        retrieval_index = RetrievalIndex(
            db_path,
            neo4j_config["uri"],
            neo4j_config["user"],
            neo4j_config["password"]
        )

        try:
            retrieval_index.add_documents(digest_tree)
            retrieval_index.build_index()

            logger.info(f"Stage 4: Generating hierarchical sectioned report using {PREMIUM_MODEL}...")
            generator = SectionedReportGenerator(target, retrieval_index)
            report = generator.generate_report()

            elapsed = time.time() - start_time
            span.set_attribute("pipeline.duration", elapsed)
            span.set_attribute("pipeline.success", True)

            final_report = _assemble_final_report(
                report, target, elapsed, len(raw_items), len(facts), digest_tree, extraction_stats
            )

            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(final_report, encoding="utf-8")

            logger.info(f"Hierarchical report saved to: {output_path}")
            logger.info(f"Total pipeline time: {elapsed:.1f} seconds")
            logger.info(
                f"Extraction stats: {extraction_stats['relevant_items']}/{extraction_stats['total_items']} items were relevant")
            logger.info(
                f"Tree structure: {len(digest_tree.leafs)} leafs → {len(digest_tree.branches)} branches → 1 root")
            logger.info(f"LLM usage: {LIGHTWEIGHT_MODEL} for tree, {PREMIUM_MODEL} for hierarchical reports")

        finally:
            try:
                retrieval_index.close()
            except Exception as e:
                logger.warning(f"Error closing retrieval index: {e}")


def _assemble_final_report(
        report: str,
        target: str,
        elapsed: float,
        raw_items_count: int,
        facts_count: int,
        digest_tree: Any,
        extraction_stats: Dict[str, int]
) -> str:
    """
    Assemble final report with metadata and performance metrics.

    Args:
        report: Generated report content
        target: Target name
        elapsed: Processing time in seconds
        raw_items_count: Number of raw intelligence items
        facts_count: Number of extracted facts
        digest_tree: Hierarchical digest tree structure
        extraction_stats: Statistics from fact extraction and relevance filtering

    Returns:
        Complete report with metadata
    """
    return f"""# Hierarchical Intelligence Report: {target}

**Generated:** {get_utc_timestamp()}  
**Processing Time:** {elapsed:.1f} seconds  
**Source Items:** {raw_items_count}  
**Relevant Items:** {extraction_stats['relevant_items']} ({100 * extraction_stats['relevant_items'] / raw_items_count:.1f}%)
**Extracted Facts:** {facts_count}  
**Tree Structure:** {len(digest_tree.leafs)} leafs, {len(digest_tree.branches)} branches, 1 root
**LLM Strategy:** Tree Construction: {LIGHTWEIGHT_MODEL}, Hierarchical Reports: {PREMIUM_MODEL}
**Retrieval:** Neo4j Graph + ColBERT Late Interaction + LLM Query Classification

---

{report}

---

## Pipeline Performance Metrics
- **Relevance Filtering:** {extraction_stats['relevant_items']}/{extraction_stats['total_items']} items relevant ({extraction_stats['filtered_out']} filtered out)
- **Fact Extraction:** {facts_count} facts from {extraction_stats['relevant_items']} relevant items
- **Tree Construction:** {len(digest_tree.leafs)} leaf abstracts, {len(digest_tree.branches)} branch summaries
- **Processing Model:** {LIGHTWEIGHT_MODEL} (with relevance filtering)
- **Report Generation Model:** {PREMIUM_MODEL} (hierarchical context-aware)
- **Retrieval Strategy:** Hierarchical tree navigation with intelligent query classification
- **Total Pipeline Time:** {elapsed:.1f} seconds
- **Observability:** Full Phoenix tracing enabled for hierarchical processing
"""


def main() -> None:
    """
    Main entry point that initializes Phoenix tracing immediately and runs the intelligence pipeline.
    """
    print("Starting Phoenix session and tracing...")
    phoenix_session, tracer_provider = initialize_phoenix()

    validate_environment()

    try:
        dossier_path = "enhanced_dossier.jsonl"
        target = "אחמד א-שאמי"
        output_path = "intelligence_report.md"

        target_info = {
            "name": "אחמד א-שאמי",
            "aliases": ["אבו-סאד"],
            "role": "מפקד תא מבצעי"
        }

        generate_intel_report(
            dossier_path=dossier_path,
            target=target,
            output_path=output_path,
            target_info=target_info
        )

        print(f"Intelligence report generated successfully: {output_path}")
        print(f"Phoenix UI available at: {phoenix_session.url}")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise
    finally:
        print("Phoenix tracing session active for analysis")


if __name__ == "__main__":
    main()