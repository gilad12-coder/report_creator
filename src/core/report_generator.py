"""
Stage 4: Multi-section report generation leveraging hierarchical tree structure.

Uses intelligent query classification and tree-aware retrieval to generate
targeted intelligence reports with appropriate context from different tree levels.
"""
import logging
from typing import Dict, List, LiteralString
from opentelemetry import trace
from src.utils.config import SECTION_QUERIES, SECTION_TITLES, NUMBERED_SECTION_TITLES
from src.core.digest_layer import QueryLevel
from src.core.retrieval_index import RetrievalIndex
from src.utils.utils import chat_completion

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class SectionedReportGenerator:
    """
    Generates intelligence reports using hierarchical tree-aware approach.

    Uses query classification to determine optimal tree levels for each section
    and generates contextually appropriate Hebrew intelligence reports.
    """

    def __init__(self, target: str, retrieval_index: RetrievalIndex) -> None:
        """
        Initialize sectioned report generator with hierarchical retrieval capability.

        Args:
            target: Target name for the intelligence report
            retrieval_index: Hierarchical retrieval index with tree navigation
        """
        self.target = target
        self.retrieval_index = retrieval_index

    def generate_report(self) -> str:
        """
        Generate intelligence report using hierarchical tree-aware approach.

        Returns:
            Generated intelligence report text with multi-level context
        """
        with tracer.start_as_current_span("generate_hierarchical_report") as span:
            span.set_attribute("target", self.target)
            span.set_attribute("report.type", "hierarchical_sectioned")
            return self._generate_full_sectioned_report()

    def _generate_full_sectioned_report(self) -> str:
        """
        Generate full report by creating each section with hierarchical context.

        Returns:
            Full sectioned Hebrew intelligence report with tree-aware content
        """
        with tracer.start_as_current_span("generate_full_sectioned_report") as span:
            span.set_attribute("target", self.target)
            span.set_attribute("report.language", "hebrew")

            sections = {}
            total_queries = 0

            logger.info(f"Generating hierarchical sectioned report")

            for section_name, query_info in self._get_section_queries().items():
                with tracer.start_as_current_span(f"generate_section_{section_name}") as section_span:
                    section_span.set_attribute("section.name", section_name)
                    section_span.set_attribute("query.terms", query_info["query"])

                    query = f"{self.target} {query_info['query']}"
                    retrieved_docs = self.retrieval_index.retrieve(query, k=20)
                    total_queries += 1

                    section_span.set_attribute("docs.retrieved", len(retrieved_docs))

                    if not retrieved_docs:
                        logger.warning(f"No documents retrieved for section {section_name}")
                        sections[section_name] = f"לא נמצא מידע מספיק עבור {section_name}"
                        continue

                    classification = self.retrieval_index.classify_query_level(query)

                    if classification == QueryLevel.STRATEGIC:
                        context_instruction = """
                        התמקד בניתוח אסטרטגי ברמה גבוהה:
                        - משמעות מבצעית ואסטרטגית
                        - השלכות רחבות ומגמות כלליות
                        - הערכות מקצועיות ומסקנות
                        """
                    elif classification == QueryLevel.PATTERN:
                        context_instruction = """
                        התמקד בזיהוי דפוסים וקשרים:
                        - מגמות התנהגותיות וחזרתיות
                        - קשרים ברשת ויחסי גומלין
                        - התפתחות לאורך זמן
                        """
                    else:
                        context_instruction = """
                        התמקד בפרטים קונקרטיים ועובדות:
                        - מידע ספציפי ומדויק
                        - אירועים מסוימים ופעילויות מפורטות
                        - ראיות ונתונים עובדתיים
                        """

                    section_content = self._generate_section_content(
                        section_name,
                        retrieved_docs,
                        context_instruction
                    )

                    sections[section_name] = section_content
                    section_span.set_attribute("section.length", len(section_content))
                    logger.info(f"Generated hierarchical section: {section_name}")

            span.set_attribute("total.queries", total_queries)
            span.set_attribute("sections.generated", len(sections))

            source_items = self._get_hierarchical_source_items()
            final_report = self._assemble_final_report(sections, source_items)

            span.set_attribute("report.length", len(final_report))
            return final_report

    @staticmethod
    def _get_section_queries() -> Dict[str, Dict[str, str]]:
        """
        Get section queries optimized for hierarchical tree retrieval.

        Returns:
            Dictionary mapping section names to query information
        """
        return {
            "role_activities": {
                "query": SECTION_QUERIES["role_activities"],
                "template_type": "operational_analysis"
            },
            "capabilities_resources": {
                "query": SECTION_QUERIES["capabilities_resources"],
                "template_type": "capabilities_assessment"
            },
            "communication_patterns": {
                "query": SECTION_QUERIES["communication_patterns"],
                "template_type": "behavioral_analysis"
            },
            "activity_patterns": {
                "query": SECTION_QUERIES["activity_patterns"],
                "template_type": "behavioral_analysis"
            },
            "network_analysis": {
                "query": SECTION_QUERIES["network_analysis"],
                "template_type": "network_assessment"
            },
            "key_topics": {
                "query": SECTION_QUERIES["key_topics"],
                "template_type": "thematic_analysis"
            },
            "code_words": {
                "query": SECTION_QUERIES["code_words"],
                "template_type": "linguistic_analysis"
            }
        }

    def _generate_section_content(self,
                                  section_name: str,
                                  retrieved_docs: List[str],
                                  context_instruction: str) -> str:
        """
        Generate section content using hierarchical context-aware prompts.

        Args:
            section_name: Name of the section being generated
            retrieved_docs: Retrieved documents from hierarchical search
            context_instruction: Context prompt based on query classification

        Returns:
            Generated section content in Hebrew
        """
        prompt = f"""
        אתה מנתח מודיעין מומחה. נתח את המסמכים המסופקים וכתב סעיף מפורט על "{SECTION_TITLES[section_name]}" של {self.target}.

        {context_instruction}

        הנחיות כתיבה:
        - כתב בעברית מקצועית ברמה מודיעינית גבוהה
        - השתמש רק במידע מהמסמכים המסופקים
        - ציין רמות ביטחון כאשר רלוונטי
        - הבנה קונטקסטואלית והיררכית של המידע

        מסמכי מקור (כולל הקשר היררכי):
        {chr(10).join(f"מסמך {i + 1}: {doc}" for i, doc in enumerate(retrieved_docs))}

        סעיף: {SECTION_TITLES[section_name]} של {self.target}:
        """

        messages = [{"role": "user", "content": prompt}]

        section_content = chat_completion(
            messages,
            max_tokens=2500,
            temperature=0.01,
            operation_name=f"hierarchical_section_{section_name}",
            use_premium=True
        )

        return section_content

    def _get_hierarchical_source_items(self) -> List[str]:
        """
        Get source item identifiers from hierarchical Neo4j structure.

        Returns:
            List of source identifiers across tree levels
        """
        try:
            with self.retrieval_index.driver.session() as session:
                source_query: LiteralString = """
                MATCH (d:Document)
                WHERE d.level IN ['fact', 'leaf', 'branch', 'root']
                RETURN d.doc_id AS source_id, d.level AS level
                ORDER BY 
                    CASE d.level 
                        WHEN 'fact' THEN 1 
                        WHEN 'leaf' THEN 2 
                        WHEN 'branch' THEN 3 
                        WHEN 'root' THEN 4 
                    END,
                    d.level_index
                LIMIT 20
                """

                results = session.run(source_query)
                source_items = []

                for record in results:
                    source_id = record["source_id"]
                    level = record["level"]
                    source_items.append(f"{source_id} ({level})")

                return source_items if source_items else ["מזהי מקור לא זמינים"]

        except Exception as e:
            logger.error(f"Failed to get hierarchical source items: {e}")
            return ["מזהי מקור לא זמינים - שגיאה בגישה למסד הנתונים"]

    def _assemble_final_report(self, sections: Dict[str, str], source_items: List[str]) -> str:
        """
        Assemble all sections into final Hebrew intelligence report with hierarchical context.

        Args:
            sections: Dictionary of section names to content
            source_items: List of hierarchical source item identifiers

        Returns:
            Complete assembled report with tree structure information
        """
        report_parts = [
            f"# סקירת גורם עניין – {self.target}\n",
            "**שיטת עיבוד:** ניתוח היררכי רב-שכבתי",
            "**מבנה עץ:** עובדות ← תקצירים מקומיים ← סיכומי ענפים ← הערכה כוללת",
            "**טכנולוגיה:** Neo4j + ColBERT + סיווג חכם של שאלות\n"
        ]

        for section_name in NUMBERED_SECTION_TITLES.keys():
            if section_name in sections:
                report_parts.append(f"\n## {NUMBERED_SECTION_TITLES[section_name]}")
                report_parts.append(sections[section_name])

        report_parts.append(f"\n## 8. מקורות (מזהי ידיעה היררכיים)")
        report_parts.append("מקורות מודיעין לפי רמות עץ:")
        for i, source_id in enumerate(source_items[:15], 1):
            report_parts.append(f"• {source_id}")

        return "\n".join(report_parts)