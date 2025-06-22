"""
Enhanced Stage 4: Multi-section report generation with improved information flow.

Implements the 8-section intelligence profile enhancement plan with:
- Logical progression from basic identification to complex analysis
- Non-overlapping focused sections
- Enhanced temporal context and chronological understanding
- Improved operational intelligence and gap analysis
- Better geographic intelligence integration
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
    Enhanced intelligence report generator implementing the 8-section improvement plan.

    Generates comprehensive intelligence profiles with:
    - Logical information flow from basic to complex
    - Non-overlapping focused sections
    - Enhanced temporal and geographic context
    - Operational intelligence focus
    - Intelligence gaps identification
    """

    def __init__(self, target: str, retrieval_index: RetrievalIndex) -> None:
        """
        Initialize enhanced report generator with hierarchical retrieval capability.

        Args:
            target: Target name for the intelligence report
            retrieval_index: Hierarchical retrieval index with tree navigation
        """
        self.target = target
        self.retrieval_index = retrieval_index

    def generate_report(self) -> str:
        """
        Generate enhanced intelligence report using the new 8-section structure.

        Returns:
            Generated intelligence report text with improved flow and context
        """
        with tracer.start_as_current_span("generate_enhanced_report") as span:
            span.set_attribute("target", self.target)
            span.set_attribute("report.type", "enhanced_8_section")
            span.set_attribute("improvement_plan", "implemented")
            return self._generate_enhanced_sectioned_report()

    def _generate_enhanced_sectioned_report(self) -> str:
        """
        Generate full report using the enhanced 8-section structure with logical flow.

        Returns:
            Full sectioned Hebrew intelligence report with enhanced content flow
        """
        with tracer.start_as_current_span("generate_enhanced_sectioned_report") as span:
            span.set_attribute("target", self.target)
            span.set_attribute("report.language", "hebrew")
            span.set_attribute("sections.count", 8)

            sections = {}
            total_queries = 0

            logger.info(f"Generating enhanced 8-section intelligence profile for {self.target}")

            # Generate sections in logical order with enhanced context
            for section_name, query_info in self._get_enhanced_section_queries().items():
                with tracer.start_as_current_span(f"generate_section_{section_name}") as section_span:
                    section_span.set_attribute("section.name", section_name)
                    section_span.set_attribute("query.terms", query_info["query"])
                    section_span.set_attribute("section.focus", query_info["focus"])

                    query = f"{self.target} {query_info['query']}"
                    retrieved_docs = self.retrieval_index.retrieve(query, k=25)
                    total_queries += 1

                    section_span.set_attribute("docs.retrieved", len(retrieved_docs))

                    if not retrieved_docs:
                        logger.warning(f"No documents retrieved for section {section_name}")
                        sections[section_name] = f"לא נמצא מידע מספיק עבור {SECTION_TITLES[section_name]}"
                        continue

                    # Enhanced query classification with section-specific optimization
                    classification = self.retrieval_index.classify_query_level(query)

                    # Generate section-specific context instructions
                    context_instruction = self._get_enhanced_context_instruction(
                        section_name, classification
                    )

                    section_content = self._generate_enhanced_section_content(
                        section_name,
                        retrieved_docs,
                        context_instruction,
                        query_info
                    )

                    sections[section_name] = section_content
                    section_span.set_attribute("section.length", len(section_content))
                    section_span.set_attribute("classification", classification.value)
                    logger.info(f"Generated enhanced section: {section_name} ({classification.value})")

            span.set_attribute("total.queries", total_queries)
            span.set_attribute("sections.generated", len(sections))

            # Enhanced source tracking with metadata
            source_metadata = self._get_enhanced_source_metadata()
            final_report = self._assemble_enhanced_final_report(sections, source_metadata)

            span.set_attribute("report.length", len(final_report))
            span.set_attribute("sources.tracked", len(source_metadata))
            return final_report

    @staticmethod
    def _get_enhanced_section_queries() -> Dict[str, Dict[str, str]]:
        """
        Get enhanced section queries with focus areas and optimization hints.

        Returns:
            Dictionary mapping section names to enhanced query information
        """
        return {
            "target_overview": {
                "query": SECTION_QUERIES["target_overview"],
                "focus": "basic_identification",
                "template_type": "overview_analysis",
                "priority": "strategic_context"
            },
            "network_analysis": {
                "query": SECTION_QUERIES["network_analysis"],
                "focus": "relationship_mapping",
                "template_type": "network_assessment",
                "priority": "hierarchy_structure"
            },
            "operational_profile": {
                "query": SECTION_QUERIES["operational_profile"],
                "focus": "capabilities_command",
                "template_type": "operational_analysis",
                "priority": "tactical_assessment"
            },
            "communication_intelligence": {
                "query": SECTION_QUERIES["communication_intelligence"],
                "focus": "sigint_patterns",
                "template_type": "communication_analysis",
                "priority": "behavioral_patterns"
            },
            "geographic_footprint": {
                "query": SECTION_QUERIES["geographic_footprint"],
                "focus": "location_patterns",
                "template_type": "geographic_analysis",
                "priority": "spatial_intelligence"
            },
            "timeline": {
                "query": SECTION_QUERIES["timeline"],
                "focus": "chronological_development",
                "template_type": "temporal_analysis",
                "priority": "historical_context"
            },
            "resources": {
                "query": SECTION_QUERIES["resources"],
                "focus": "material_capabilities",
                "template_type": "resource_assessment",
                "priority": "logistical_analysis"
            },
            "intelligence_gaps": {
                "query": SECTION_QUERIES["intelligence_gaps"],
                "focus": "collection_requirements",
                "template_type": "gap_analysis",
                "priority": "future_intelligence"
            }
        }

    @staticmethod
    def _get_enhanced_context_instruction(
      section_name: str,
      classification: QueryLevel
    ) -> str:
        """
        Generate enhanced context instructions based on section focus and query classification.

        Args:
            section_name: Name of the section being generated
            classification: Query level classification (strategic/pattern/specific/mixed)

        Returns:
            Enhanced context instruction string
        """
        base_instructions = {
            "target_overview": """
            התמקד בבניית תמונה ראשונית ובסיסית:
            - זיהוי ברור ומדויק של היעד
            - מעמד נוכחי והקשר ארגוני
            - נקודות מפתח להבנת האיום
            - ייחודיות וחתימה מבצעית
            """,
            "network_analysis": """
            התמקד במיפוי יחסים ומבנה ארגוני:
            - היררכיה ומערכות יחסי כוח
            - קשרים פעילים לעומת רדומים
            - נקודות השפעה ותלות
            - רשתות תמיכה ופגיעות
            """,
            "operational_profile": """
            התמקד ביכולות ושיטות מבצעיות:
            - יכולת פיקוד ושליטה
            - התמחות וכישורים ייחודיים
            - דפוסי פעולה וטקטיקות
            - מדדי ביצועים והצלחה
            """,
            "communication_intelligence": """
            התמקד בדפוסי תקשורת ו-SIGINT:
            - פלטפורמות ושיטות תקשורת
            - קודים ושפה מוסווית
            - דפוסי זמן ותדירות
            - אבטחת תקשורת ופגיעויות
            """,
            "geographic_footprint": """
            התמקד בדפוסים גיאוגרפיים ומקומיים:
            - אזורי פעילות ושליטה
            - דפוסי תנועה ולוגיסטיקה
            - תשתיות ומתקנים קריטיים
            - נתיבי מילוט ובטיחות
            """,
            "timeline": """
            התמקד בהתפתחות כרונולוגית ומגמות:
            - אירועי מפתח והתפתחות היסטורית
            - מעורבות מבצעית לאורך זמן
            - מגמות אחרונות ושינויים
            - אינדיקטורים לפעילות עתידית
            """,
            "resources": """
            התמקד במשאבים ויכולות לוגיסטיות:
            - משאבים כספיים ומקורות מימון
            - נשק וציוד מבצעי
            - כוח אדם ומומחיות
            - תשתיות ונכסים פיזיים
            """,
            "intelligence_gaps": """
            התמקד בזיהוי חוסרי מידע וצרכי איסוף:
            - פערים קריטיים לקבלת החלטות
            - מידע סותר או לא מאומת
            - צרכי איסוף לפי עדיפות
            - המלצות למעקב עתידי
            """
        }

        classification_additions = {
            QueryLevel.STRATEGIC: """
            הוסף דגש אסטרטגי:
            - השלכות ומשמעות רחבה
            - הערכת איום כללית
            - השפעה על יציבות אזורית
            - המלצות לקבלת החלטות
            """,
            QueryLevel.PATTERN: """
            הוסף דגש על דפוסים וקשרים:
            - זיהוי מגמות ושינויים
            - קורלציות וקשרים סמויים
            - התפתחות לאורך זמן
            - חזיה והערכת כיוונים עתידיים
            """,
            QueryLevel.SPECIFIC: """
            הוסף דגש על פרטים קונקרטיים:
            - עובדות מדויקות ומאומתות
            - אירועים ספציפיים
            - מיקומים וזמנים מדויקים
            - ראיות ותיעוד מפורט
            """,
            QueryLevel.MIXED: """
            הוסף דגש מאוזן:
            - שילוב עובדות וניתוח
            - הקשר רחב ופרטים ספציפיים
            - תמונה מקיפה ומאוזנת
            - מענה לצרכים מגוונים
            """
        }

        base_instruction = base_instructions.get(section_name, "")
        classification_addition = classification_additions.get(classification, "")

        return base_instruction + classification_addition

    def _generate_enhanced_section_content(self,
                                           section_name: str,
                                           retrieved_docs: List[str],
                                           context_instruction: str,
                                           query_info: Dict[str, str]) -> str:
        """
        Generate enhanced section content using focused templates and improved context.

        Args:
            section_name: Name of the section being generated
            retrieved_docs: Retrieved documents from hierarchical search
            context_instruction: Enhanced context prompt based on section and classification
            query_info: Section query information with focus areas

        Returns:
            Generated section content in Hebrew with enhanced quality
        """
        # Enhanced prompt with section-specific guidance and metadata
        prompt = f"""
        אתה מנתח מודיעין מומחה מהדרג הבכיר. כתב סעיף מקצועי ומפורט עבור דוח מודיעיני מתקדם.

        **מטלה**: {SECTION_TITLES[section_name]} של {self.target}
        **מיקוד ניתוח**: {query_info['focus']}
        **רמת עדיפות**: {query_info['priority']}

        {context_instruction}

        **הנחיות כתיבה מתקדמות**:
        - כתב בעברית מודיעינית מקצועית ברמה בכירה
        - השתמש במונחולוגיה מקצועית מדויקת
        - ציין רמות ביטחון עבור טענות קריטיות
        - הדגש קשרים לסעיפים אחרים כשרלוונטי
        - השתמש בפורמט ויזואלי ברור (כותרות משנה, רשימות)
        - הימנע מחזרה על מידע מסעיפים אחרים
        - התמקד בתוספת ערך ייחודית לסעיף זה

        **מבנה מומלץ**:
        - פתיחה: ממצא מרכזי או הערכה עיקרית
        - פיתוח: פרטים מקצועיים ודוגמאות
        - סיכום: משמעות והשלכות

        **רמות ביטחון**:
        🔴 ביטחון גבוה - מאומת ממקורות מרובים
        🟡 ביטחון בינוני - מאומת חלקית  
        🟢 ביטחון נמוך - לא מאומת אך סביר
        ❓ לא ידוע - חוסר מידע

        **מסמכי מקור עם הקשר היררכי**:
        {chr(10).join(f"מסמך {i + 1}: {doc}" for i, doc in enumerate(retrieved_docs))}

        **סעיף: {SECTION_TITLES[section_name]} של {self.target}**:
        """

        messages = [{"role": "user", "content": prompt}]

        section_content = chat_completion(
            messages,
            max_tokens=3000,  # Increased for more detailed content
            temperature=0.01,
            operation_name=f"enhanced_section_{section_name}",
            use_premium=True
        )

        return section_content

    def _get_enhanced_source_metadata(self) -> Dict[str, any]:
        """
        Get enhanced source metadata with hierarchical context and quality indicators.

        Returns:
            Dictionary containing source metadata and quality indicators
        """
        try:
            with self.retrieval_index.driver.session() as session:
                metadata_query: LiteralString = """
                MATCH (d:Document)
                WHERE d.level IN ['fact', 'leaf', 'branch', 'root']
                OPTIONAL MATCH (d)-[:MENTIONS]->(e:Entity)
                RETURN 
                    d.doc_id AS source_id, 
                    d.level AS level,
                    d.confidence AS confidence,
                    d.created AS created_date,
                    count(e) AS entity_mentions,
                    d.tree_position AS tree_position
                ORDER BY 
                    CASE d.level 
                        WHEN 'root' THEN 1 
                        WHEN 'branch' THEN 2 
                        WHEN 'leaf' THEN 3 
                        WHEN 'fact' THEN 4 
                    END,
                    d.confidence DESC,
                    d.level_index
                LIMIT 25
                """

                results = session.run(metadata_query)
                sources = []
                level_counts = {"fact": 0, "leaf": 0, "branch": 0, "root": 0}
                total_entities = 0

                for record in results:
                    source_info = {
                        "id": record["source_id"],
                        "level": record["level"],
                        "confidence": record["confidence"] or 1.0,
                        "created": str(record["created_date"]) if record["created_date"] else "unknown",
                        "entities": record["entity_mentions"] or 0,
                        "position": record["tree_position"] or []
                    }
                    sources.append(source_info)
                    level_counts[record["level"]] += 1
                    total_entities += record["entity_mentions"] or 0

                return {
                    "sources": sources,
                    "level_distribution": level_counts,
                    "total_entities": total_entities,
                    "quality_score": self._calculate_quality_score(sources),
                    "coverage_assessment": self._assess_coverage(level_counts)
                }

        except Exception as e:
            logger.error(f"Failed to get enhanced source metadata: {e}")
            return {
                "sources": [],
                "level_distribution": {"fact": 0, "leaf": 0, "branch": 0, "root": 0},
                "total_entities": 0,
                "quality_score": 0.0,
                "coverage_assessment": "לא זמין בשל שגיאה במסד הנתונים"
            }

    @staticmethod
    def _calculate_quality_score(sources: List[Dict]) -> float:
        """Calculate overall quality score based on source distribution and confidence."""
        if not sources:
            return 0.0

        # Weight by level importance and confidence
        level_weights = {"root": 4, "branch": 3, "leaf": 2, "fact": 1}
        total_weight = 0
        weighted_confidence = 0

        for source in sources:
            weight = level_weights.get(source["level"], 1)
            confidence = source["confidence"]
            total_weight += weight
            weighted_confidence += weight * confidence

        return round(weighted_confidence / total_weight if total_weight > 0 else 0.0, 2)

    @staticmethod
    def _assess_coverage(level_counts: Dict[str, int]) -> str:
        """Assess information coverage based on level distribution."""
        total = sum(level_counts.values())
        if total == 0:
            return "אין כיסוי מידע"

        fact_ratio = level_counts["fact"] / total
        strategic_ratio = (level_counts["root"] + level_counts["branch"]) / total

        if fact_ratio > 0.6:
            return "כיסוי טקטי מעמיק"
        elif strategic_ratio > 0.5:
            return "כיסוי אסטרטגי מקיף"
        else:
            return "כיסוי מאוזן"

    def _assemble_enhanced_final_report(self,
                                        sections: Dict[str, str],
                                        source_metadata: Dict) -> str:
        """
        Assemble enhanced final Hebrew intelligence report with improved structure and metadata.

        Args:
            sections: Dictionary of section names to content
            source_metadata: Enhanced source metadata with quality indicators

        Returns:
            Complete assembled report with enhanced formatting and metadata
        """
        # Enhanced header with metadata
        report_parts = [
            f"# פרופיל מודיעיני מתקדם – {self.target}\n",
            "## מטא-נתונים",
            f"**שיטת עיבוד:** ניתוח היררכי רב-שכבתי מתקדם",
            f"**מבנה מידע:** {source_metadata['level_distribution']['fact']} עובדות → {source_metadata['level_distribution']['leaf']} תקצירים → {source_metadata['level_distribution']['branch']} ענפים → {source_metadata['level_distribution']['root']} הערכה כוללת",
            f"**איכות מידע:** {source_metadata['quality_score']}/4.0 ({source_metadata['coverage_assessment']})",
            f"**ישויות מזוהות:** {source_metadata['total_entities']} ישויות רלוונטיות",
            f"**טכנולוגיה:** Neo4j Graph + ColBERT Retrieval + LLM Classification\n"
        ]

        # Enhanced sections with improved formatting
        for section_name in NUMBERED_SECTION_TITLES.keys():
            if section_name in sections:
                report_parts.append(f"\n## {NUMBERED_SECTION_TITLES[section_name]}")
                report_parts.append(sections[section_name])

        # Enhanced source section with metadata
        report_parts.append(f"\n## 9. מקורות ואמינות")
        report_parts.append("### התפלגות מקורות לפי רמה:")

        level_names = {
            "root": "הערכה כוללת",
            "branch": "סיכומי ענפים",
            "leaf": "תקצירים מקומיים",
            "fact": "עובדות גולמיות"
        }

        for level, count in source_metadata['level_distribution'].items():
            if count > 0:
                report_parts.append(f"• {level_names[level]}: {count} מסמכים")

        report_parts.append(f"\n### מדדי איכות:")
        report_parts.append(f"• **ציון איכות כללי**: {source_metadata['quality_score']}/4.0")
        report_parts.append(f"• **סוג כיסוי**: {source_metadata['coverage_assessment']}")
        report_parts.append(f"• **עושר ישויות**: {source_metadata['total_entities']} ישויות מזוהות")

        if source_metadata['sources']:
            report_parts.append(f"\n### מזהי מקור מייצגים:")
            for i, source in enumerate(source_metadata['sources'][:10], 1):
                confidence_indicator = "🔴" if source['confidence'] > 0.8 else "🟡" if source[
                                                                                         'confidence'] > 0.5 else "🟢"
                report_parts.append(f"• {source['id']} ({source['level']}) {confidence_indicator}")

        # Enhanced disclaimer
        report_parts.append(f"\n---")
        report_parts.append(f"**הערה**: דוח זה נוצר באמצעות ניתוח אוטומטי מתקדם. יש לאמת מידע קריטי ממקורות עצמאיים.")
        report_parts.append(f"**תאריך יצירה**: {source_metadata.get('generated_date', 'לא זמין')}")

        return "\n".join(report_parts)