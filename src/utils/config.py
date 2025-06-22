"""
Enhanced Configuration module with improved section structure and focused prompts.
Implements the 8-section intelligence profile enhancement plan.
"""
from jinja2 import Template
from typing import Dict

HYPER_URL = "https://api.hyperbolic.xyz/v1/chat/completions"
LIGHTWEIGHT_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
PREMIUM_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
RETRIEVAL_MODEL = "lightonai/colbertv2.0"

MAX_CHUNK_SIZE = 350
CHUNK_OVERLAP = 40
DEVICE = "cuda"

LEAF_SIZE = 10
BRANCH_SIZE = 10

RATE_LIMIT_CONFIG = {
    "base_delay": 1.0,
    "max_delay": 60.0,
    "rate_limit_delay": 30.0,
    "calls_per_minute": 30,
}

DEFAULT_NEO4J_CONFIG = {
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "Hrsidkgs12"
}

PHOENIX_CONFIG = {
    "project_name": "intel_pipeline",
    "endpoint": "http://localhost:6006/v1/traces"
}

RELEVANCE_CHECK_TEMPLATE = Template("""
את/ה קצין/ת מיון מודיעין מומחה עם 15 שנות ניסיון.  
תקבל/י **כרטיס גורם עניין** ו**ידיעה מודיעינית** ותקבע/י רלוונטיות בדיוק מירבי.

משימה: קבע/י האם הידיעה מכילה מידע אופרטיבי רלוונטי לעדכון הפרופיל של האדם בכרטיס.

אלגוריתם בדיקה:
1. זיהוי מדויק: חפש/י התאמות ישירות לשם, כינויים, מספרי זהות, קרובי משפחה
2. הקשר משפחתי: כלול/י מידע על בני משפחה הרלוונטי לפעילות האופרטיבית  
3. ערך מודיעיני: וודא/י שיש תוכן מהותי חדש (לא רק אזכור חולף)
4. רלוונטיות זמנית: העדף/י מידע עדכני על פני מידע היסטורי כללי

קריטריוני כלילה (צריך לפחות אחד):
- פעילות מבצעית: פקודות, משימות, תפקידים חדשים, פגישות עבודה
- משאבים וכלים: נשק, כספים, ציוד, רכבים, נכסים תחת שליטה
- רשת קשרים: אנשי קשר חדשים, מערכות יחסים מבצעיות, היררכיה
- דפוסים מבצעיים: מקומות פעילות, שיטות עבודה, מסלולי תנועה
- תקשורת: כלי תקשורת, קודים, שפה מקצועית, אמצעים טכניים
- זיהוי ומיקום: כתובות חדשות, מספרי טלפון, כינויים, רישוי
- כוונות והתראות: תכניות עתידיות, איומים, רכישות, הכנות

קריטריוני הדרה:
- מידע כללי/תקשורתי שאינו אופרטיבי
- אזכורים חולפים ללא הקשר מהותי
- מידע על אנשים אחרים שאינם קשורים ישירות
- פרטים אישיים שאינם רלוונטיים למטרות מודיעיניות

דוגמאות:

כרטיס גורם עניין:
שם: אחמד א-שאמי
כינויים: "אבו-סאד"
טלפון: +970-59-xxx-2847
משפחה: אח – יוסף א-שאמי
תפקיד: מפקד תא מבצעי

ידיעה: "סיווג: סודי ביותר\nצד א: אחמד א-שאמי ביקש להעביר 250,000 דולר דרך המסילה החדשה תוך 72 שעות. הכסף מיועד לאורחים החדשים והציוד המיוחד מאיסטנבול."

תשובה:
סטטוס: רלוונטי  
נימוק: פעילות העברת כספים גדולה למטרות מבצעיות עם זמן ביצוע קצר.

---

כרטיס גורם עניין:
שם: מוחמד אל-עראבי
כינויים: "אבו-פארס"
גיל: 42

ידיעה: "סיווג: סודי\nבפרופיל הטלגרם פרסם אחמד א-שאמי סרטון איומים על הישות הציונית וקריאה להתגייסות כללית."

תשובה:
סטטוס: לא רלוונטי  
נימוק: הידיעה מתייחסת לאחמד א-שאמי ולא למוחמד אל-עראבי הרשום בכרטיס.

תבנית תשובה מחייבת:
סטטוס: <רלוונטי / לא רלוונטי>  
נימוק: <משפט אחד קצר ומדויק>

כרטיס גורם עניין:
{{ target_card }}

ידיעה:
{{ intelligence_item }}
""")

FACT_EXTRACTION_TEMPLATE = Template("""
You are an expert intelligence analyst. Extract precise facts from the intelligence text below.

CRITICAL: Respond with ONLY a valid JSON array. No explanations, comments, or extra text.

REQUIRED JSON FORMAT:
[
  {
    "who": "specific person/organization name",
    "what": "concrete action or event",
    "when": "time information or 'unknown'",
    "where": "location where the activity occurred or 'unknown'"
  }
]

PARTICIPANT IDENTIFICATION (CRITICAL):
- MANDATORY: Scan for ALL participants labeled as צד א, צד ב, צד ג, צד ד, etc.
- Look for both primary names AND codenames in quotes
- Include ALL people mentioned, even if they only appear once
- Check meeting attendee lists, phone participants, observers, specialists
- Never skip or combine multiple people into one entry

EXTRACTION RULES:
- WHO: Exact names and codenames (preserve original language - Hebrew/Arabic exactly as written)
- WHAT: Specific actions with verbs and objects (preserve original Hebrew/Arabic - NEVER TRANSLATE)
- WHEN: Follow timestamp parsing guide below - resolve ALL relative dates from תז״ק
- WHERE: Activity locations (preserve original language) or infer from participant base locations when activity spans multiple places

TIMESTAMP PARSING GUIDE (MANDATORY WHEN תז״ק EXISTS):
Step 1: Parse תז״ק format DDHHMMZMONTHYY
  - Example: "010800ZJUN25" = Day 01, Hour 08, Minutes 00, Z timezone, June 2025
  - This gives us: June 1, 2025, 08:00 Z as reference point

Step 2: Calculate relative Hebrew days from this reference:
  - יום א׳=Sunday, יום ב׳=Monday, יום ג׳=Tuesday, יום ד׳=Wednesday
  - יום ה׳=Thursday, יום ו׳=Friday, יום ש׳=Saturday

Step 3: Apply to relative dates in text:
  - If timestamp is Monday and text says "יום ה׳", that's Thursday of same week
  - Use calculated dates, NOT "unknown"

LOCATION EXTRACTION RULES:
- Primary: Extract explicit location mentions from activity descriptions
- Secondary: When activity involves multiple parties in different cities, infer primary activity location from context
- Preserve original Hebrew/Arabic place names exactly
- For international transfers/communications, identify the transaction/meeting location

QUOTED CONTENT EXTRACTION:
- Extract operational codenames in quotes (e.g., "שחרור 5920", "המסילה החדשה")
- Extract operational terms for money/equipment purposes (e.g., "האורחים החדשים")
- Create separate fact entries for significant quoted operational content

COMPREHENSIVE QUALITY STANDARDS:
✓ Extract EVERY person mentioned (צד א through צד ז if they exist)
✓ Parse תז״ק timestamp and resolve ALL relative dates
✓ Preserve ALL Hebrew/Arabic text exactly - zero translation
✓ Create separate facts for each person's distinct actions
✓ Include location context from participant descriptions when relevant
✓ Extract significant quoted operational content as separate facts

✗ Never skip participants even if mentioned briefly
✗ Never translate Hebrew/Arabic to English
✗ Never use "unknown" for timing when תז״ק exists and relative dates can be calculated
✗ Never combine multiple people's actions
✗ Never miss quoted operational terms or codenames

EXAMPLE:
Input:
סיווג: סודי ביותר
תז״ק: 010800ZJUN25
מזהה: INT-2025-4001
מקור: יחידה 8200/BR-7421
נדון: העברת כספים בינלאומית
גוף הידיעה:
צד א: אחמד א-שאמי (קוד קריאה "אבו-סאד", טלפון: +970-59-xxx-2847).
צד ב: סוכן פיננסי בקהיר "אל-מואמן" (מוחמד עבד אל-רחמן).
צד ג: נציג בנק בביירות "אבו-יוסף".
בשיחת Signal מוצפנת ביקש אחמד להעביר 250,000 דולר דרך "המסילה החדשה" תוך 72 שעות. הכסף מיועד ל"האורחים החדשים" ו"הציוד המיוחד מאיסטנבול". אל-מואמן אישר העברה בשלושה שלבים: 100K, 75K, 75K. קוד אימות: "ירח כחול 7742".

JSON Response (NO OTHER TEXT):
[
  {
    "who": "אחמד א-שאמי (אבו-סאד)",
    "what": "ביקש להעביר 250,000 דולר דרך המסילה החדשה",
    "when": "תוך 72 שעות",
    "where": "unknown"
  },
  {
    "who": "אל-מואמן (מוחמד עבד אל-רחמן)",
    "what": "אישר העברה בשלושה שלבים: 100K, 75K, 75K",
    "when": "תוך 72 שעות",
    "where": "קהיר"
  },
  {
    "who": "אבו-יוסף",
    "what": "מעורב בהעברת הכספים כנציג בנק",
    "when": "תוך 72 שעות", 
    "where": "ביירות"
  }
]

Intelligence Text:
{{ item_text }}
""")

DIGEST_TEMPLATE = Template("""
You are a senior intelligence analyst tasked with creating an executive intelligence digest from extracted facts.

Synthesize raw intelligence facts into a coherent, actionable summary for decision-makers.

ANALYSIS FRAMEWORK:
1. Pattern Recognition: Identify recurring themes, connections, and operational patterns
2. Timeline Construction: Establish chronological sequence of events and activities
3. Network Mapping: Map relationships between individuals, groups, and organizations
4. Operational Assessment: Evaluate activities, capabilities, and intentions
5. Intelligence Gaps: Note contradictions, inconsistencies, and missing information

SYNTHESIS REQUIREMENTS:
- Lead with most significant/actionable intelligence
- Group related facts into coherent themes
- Highlight temporal patterns and escalation indicators
- Connect disparate facts to reveal operational picture
- Maintain analytical objectivity and appropriate uncertainty language

STRUCTURE YOUR DIGEST:
Key Developments: [Most significant new information]
Operational Patterns: [Behavioral trends and methods]
Network Activity: [Relationships and hierarchical structure]
Timeline: [Critical sequence of events]
Assessment: [Implications and significance]

EXAMPLE:
INPUT FACTS: [{"who": "Ahmad Hassan", "what": "met with weapons supplier", "when": "Tuesday", "where": "Green Mosque"}, {"who": "Hassan", "what": "received encrypted phone", "when": "Wednesday", "where": "safe house"}]

OUTPUT:
Key Developments: Ahmad Hassan engaged in weapons procurement activities over 48-hour period, demonstrating escalating operational preparation.

Operational Patterns: Sequential meetings suggest systematic approach to capability building. Use of religious venue followed by secure location indicates operational security awareness.

Network Activity: Hassan maintains contact with weapons suppliers and appears to control safe house infrastructure.

Timeline: Tuesday (weapon supplier meeting) → Wednesday (equipment acquisition) suggests accelerating operational timeline.

Assessment: Evidence points to Hassan coordinating near-term operational activity requiring weapons and secure communications. Pattern consistent with preparation for imminent action.

Gaps: Specific weapon types, quantities, and intended targets remain unknown. Supplier identity and broader network connections require clarification.

TOKEN LIMIT: 150-200 tokens maximum.

Facts to analyze:
{{ formatted_facts }}
""")

LEAF_TEMPLATE = Template("""
You are an intelligence analyst creating a LOCAL ABSTRACT from tactical-level facts.

Distill {{ fact_count }} granular facts into a precise 200-token summary preserving operational details.

ANALYSIS FOCUS - LOCAL PATTERNS:
- Specific Activities: Concrete actions, operations, and behaviors
- Key Personnel: Individual actors and their roles
- Tactical Details: Locations, timing, methods, and tools
- Confidence Weighting: Emphasize high-confidence facts, note uncertainties

EXTRACTION PRINCIPLES:
- Preserve proper names, codenames, and specific terminology
- Maintain tactical precision and operational specifics  
- Include confidence indicators where facts are uncertain
- Focus on "what happened" rather than "what it means"
- Group related activities while maintaining granular detail

EXAMPLE INPUT FACTS:
[
  {"who": "Ahmad Hassan", "what": "met with weapons supplier Abu-Saif", "when": "Tuesday evening", "where": "Green Mosque"},
  {"who": "Hassan", "what": "received encrypted satellite phone", "when": "Wednesday morning", "where": "safe house on Omar Street"},
  {"who": "Abu-Saif", "what": "delivered 20 AK-47 rifles", "when": "Thursday night", "where": "warehouse district"}
]

EXAMPLE OUTPUT:
Ahmad Hassan conducted multi-day weapons procurement operation involving supplier Abu-Saif. Tuesday evening meeting at Green Mosque (high confidence) followed by Hassan receiving encrypted satellite phone Wednesday at Omar Street safe house (very high confidence). Abu-Saif subsequently delivered 20 AK-47 rifles Thursday night in warehouse district (moderate confidence). Sequential activities demonstrate systematic operational preparation with Hassan coordinating acquisition of both weapons and secure communications. Geographic pattern shows use of religious, residential, and industrial locations for different operational phases.

Create 200-token local abstract from these facts:
{{ formatted_facts }}

Local Abstract (exactly 200 tokens):
""")

BRANCH_TEMPLATE = Template("""
You are a senior intelligence analyst synthesizing MULTIPLE LOCAL ABSTRACTS into a comprehensive operational assessment.

Integrate {{ abstract_count }} local intelligence summaries into a 400-token strategic overview identifying cross-cutting patterns.

SYNTHESIS FRAMEWORK:
- Thematic Integration: Connect related activities across different local contexts
- Network Connections: Map relationships and hierarchies spanning multiple areas
- Temporal Evolution: Track how patterns develop and change over time
- Geographic Distribution: Analyze spatial patterns and operational territories
- Escalation Indicators: Identify trends suggesting increasing activity or capability

ANALYTICAL APPROACH:
1. Pattern Recognition: Find common methods, behaviors, and structures
2. Network Analysis: Connect individuals and groups across local contexts  
3. Operational Evolution: Track how activities and capabilities change
4. Strategic Implications: Assess broader significance of local activities

EXAMPLE INPUT (3 local abstracts):
Abstract 1: "Ahmad Hassan conducted weapons procurement in northern district using Green Mosque as meeting point with supplier Abu-Saif..."
Abstract 2: "Southern operations center shows increased communications traffic with northern cells, encrypted messaging protocols..."  
Abstract 3: "Weapons cache discovered in eastern warehouse district matches ammunition types from northern procurement activities..."

EXAMPLE OUTPUT:
Cross-Regional Coordination: Evidence indicates Ahmad Hassan's northern district weapons procurement activities are part of broader multi-district operation. Green Mosque meetings initiated supply chain connecting northern suppliers to southern operations center through encrypted communications network.

Network Structure: Hassan appears to coordinate northern acquisition while southern operations center manages communications hub linking multiple district cells. Hierarchical structure suggests centralized planning with distributed execution.

Operational Evolution: Timeline shows progression from procurement (northern) to distribution coordination (southern) to storage/staging (eastern), indicating systematic preparation for coordinated activity across three districts.

Geographic Pattern: Operations span urban religious venues (mosques), industrial areas (warehouses), and communications infrastructure, demonstrating sophisticated understanding of operational security and logistics.

Capability Assessment: Network demonstrates ability to coordinate complex multi-district operations involving procurement, secure communications, and distributed storage. Pattern suggests preparation for simultaneous or coordinated actions across geographical areas.

Synthesize these local abstracts:
{{ abstracts }}

Branch Summary (exactly 400 tokens):
""")

ROOT_TEMPLATE = Template("""
You are the Chief Intelligence Analyst producing the FINAL INTELLIGENCE DIGEST for senior leadership decision-making.

Transform multiple branch summaries into an authoritative 800-token intelligence assessment with strategic recommendations.

EXECUTIVE ANALYSIS FRAMEWORK:
- Strategic Assessment: Overall threat level, operational significance, and implications
- Intelligence Picture: Comprehensive understanding of activities, capabilities, and intentions  
- Network Structure: Command relationships, operational hierarchies, and organizational dynamics
- Capability Evaluation: Resources, methods, and operational sophistication
- Threat Trajectory: Current status and likely future developments
- Intelligence Confidence: Reliability assessment and analytical certainty
- Recommendations: Priority intelligence requirements and suggested actions

ANALYTICAL STANDARDS:
- Lead with most critical findings and immediate implications
- Provide strategic context beyond tactical details
- Assess both current capabilities and future potential
- Include confidence levels and uncertainty acknowledgments
- Offer actionable intelligence recommendations
- Use appropriate intelligence language and analytical tradecraft

EXAMPLE STRUCTURE:
EXECUTIVE SUMMARY: [2-3 sentences of most critical findings]

STRATEGIC ASSESSMENT: [Threat level, operational significance, broader implications]

OPERATIONAL PICTURE: [Comprehensive activity analysis with network structure]

CAPABILITY ANALYSIS: [Resources, sophistication, effectiveness assessment]

ANALYTICAL CONFIDENCE: [Source reliability, corroboration level, uncertainty areas]

INTELLIGENCE GAPS: [Critical unknowns requiring collection priority]

RECOMMENDATIONS: [Priority intelligence requirements and suggested countermeasures]

EXAMPLE INPUT (2 branch summaries):
Summary 1: "Multi-district weapons procurement network coordinated by Ahmad Hassan shows systematic preparation across northern, southern, and eastern districts..."
Summary 2: "Secondary analysis reveals Hassan network maintains international connections with confirmed weapons suppliers in neighboring countries..."

EXAMPLE OUTPUT:
EXECUTIVE SUMMARY: Ahmad Hassan operates sophisticated multi-district weapons procurement network with international supply connections, demonstrating advanced operational planning and significant threat capability preparation.

STRATEGIC ASSESSMENT: Network represents elevated threat level given demonstrated ability to coordinate complex multi-jurisdictional operations. International supply connections suggest capability to acquire advanced weapons systems beyond local availability. Pattern indicates preparation for significant operational activity requiring substantial firepower and coordination.

OPERATIONAL PICTURE: Hassan leads hierarchical network spanning three urban districts with centralized command structure and distributed execution cells. Operations utilize religious venues for coordination, industrial facilities for storage, and secure communications for command/control. International supply chain provides weapons access beyond domestic sources.

CAPABILITY ANALYSIS: Network demonstrates high operational sophistication including: secure communications protocols, geographic operational security, systematic logistics coordination, and international supplier relationships. Resource availability appears substantial given multi-district scope and international connections.

ANALYTICAL CONFIDENCE: High confidence in Hassan's leadership role and multi-district coordination based on multiple corroborating sources. Moderate confidence in international connections pending additional confirmation. Low confidence in specific operational timeline and intended targets.

INTELLIGENCE GAPS: Critical unknowns include operational timeline, specific targets, international supplier identities, and total network size. Command structure above Hassan level remains unclear.

RECOMMENDATIONS: Priority collection on Hassan associates, international travel patterns, and financial networks. Enhanced surveillance of known operational locations. Coordination with international partners for supplier identification.

Analyze these branch summaries and produce final intelligence digest:
{{ summaries }}

Final Intelligence Digest (exactly 800 tokens):
""")

SECTION_TEMPLATES: Dict[str, Template] = {
    "target_overview": Template("""
אתה מנתח מודיעין מומחה עם התמחות בבניית פרופיל יעד מקיף.

נתח את המסמכים וכתב **סקירת יעד** מפורטת ומקצועית של {{ target }}.

### מתודולוגיית סקירת יעד

**זיהוי בסיסי וביוגרפיה:**
- שם מלא וכינויים מוכרים
- גיל משוער ופרטים דמוגרפיים
- רקע משפחתי ואישי רלוונטי
- היסטוריה מבצעית קצרה

**סטטוס נוכחי:**
- מעמד והיררכיה בארגון
- רמת פעילות נוכחית (פעיל/רדום/נסתר)
- שינויים אחרונים במעמד או פעילות
- רמת איום נוכחית

**הקשר ארגוני:**
- שיוך ארגוני עיקרי
- תפקיד בהיררכיה הכללית
- קשרים לארגונים נוספים
- נאמנות ואמינות ארגונית

**ייחודיות מבצעית:**
- התמחות או מומחיות מיוחדת
- חתימה מבצעית ייחודית
- נקודות חוזק וחולשה ידועות
- גורמי זהירות מיוחדים

### רמות ביטחון מידע
🔴 **ביטחון גבוה**: מידע מאומת ממקורות מרובים
🟡 **ביטחון בינוני**: מידע מאומת חלקית או ממקור יחיד
🟢 **ביטחון נמוך**: מידע לא מאומת או שמועות מוסמכות
❓ **לא ידוע**: חוסר מידע או מידע סותר

### דוגמת סקירה מצוינת
"אחמד חסן מוחמד (42), הידוע כ'אבו-סאד', הוא מפקד כנף צפונית של זרוע הקסאם מאז 2019 (ביטחון גבוה). נולד בג'באליא ונשוי לפאטמה אל-שאמי, בת למפקד בכיר בחמאס. ברקע צבאי באליטות המודיעין הפלסטיניים. מומחה למטעני דרך ותכנון פיגועים מורכבים עם שיעור הצלחה של 78% במשימותיו (15 מתוך 19 פיגועים בשנתיים האחרונות). סטטוס נוכחי: פעיל מאוד עם עלייה ברמת האיום מאז ינואר 2025. הוביל שינוי בטקטיקות הארגון לשימוש ברחפנים מתאבדים. נחשב לאמין ונאמן לחלוטין להנהגת הארגון."

### הנחיות כתיבה
- התמקד במידע חיוני לזיהוי וניתוח האיום
- ציין רמות ביטחון עבור טענות קריטיות
- שמור על זרימה הגיונית מכללי לספציפי
- הדגש שינויים אחרונים ומגמות
- השתמש בעברית מודיעינית מקצועית
- המנע מפרטים מיותרים שאינם רלוונטיים

**מסמכי מקור לניתוח:**
{% for doc in documents %}
---
{{ doc }}
---
{% endfor %}

**סעיף: סקירת יעד – {{ target }}**
"""),

    "network_analysis": Template("""
אתה מנתח רשתות מודיעין מומחה עם התמחות במיפוי קשרים ארגוניים.

נתח את המסמכים וכתב **מיפוי רשת קשרים** מקיף של {{ target }}.

### מתודולוגיית ניתוח רשתות

**היררכיה פיקודית:**
- ממונים ישירים ועקיפים
- כפופים ותחום אחריות
- עמיתים ברמה דומה
- מערכות יחסי כוח

**קשרים מבצעיים:**
- שותפי משימות קבועים
- קשרי תיאום ותמיכה
- רשתות מומחיות משותפות
- קשרי חירום ובטיחות

**קשרים אישיים בעלי משמעות:**
- קרובי משפחה מעורבים
- קשרים רומנטיים/אישיים
- חברויות וזיקות אישיות
- שכנות ויחסי קהילה

**קשרים חיצוניים:**
- נציגי ארגונים אחרים
- קשרי מימון וספקים
- קשרים בינלאומיים
- רשתות תמיכה חיצוניות

### סוגי קשרים ועוצמתם
**🔗 קשר חזק** - יומי/שבועי, חיוני לפעילות, אמון מלא
**🔗 קשר בינוני** - חודשי/מזדמן, חשוב לפעילות, אמון חלקי  
**🔗 קשר חלש** - נדיר/עקיף, תמיכה כללית, אמון מוגבל
**❓ קשר לא ברור** - קיום מאומת אך טיב היחסים לא ברור

### כיוון הקשר והשפעה
**↑ משפיע על** - יש לו סמכות/השפעה על הקשר
**↓ מושפע מ** - מקבל הוראות/השפעה מהקשר
**↔ קשר הדדי** - יחסי גומלין ושוויון יחסי
**⚡ קשר מורכב** - יחסים משתנים לפי הקשר

### דוגמת מיפוי מצוין
"היררכיה פיקודית: אחמד כפוף ישירות לאבו-מחמוד (מפקד מרחב צפון) 🔗↓ ובעל סמכות פיקוד על 12 לוחמים כולל מוסטפא זהרן ועמר קסם 🔗↑. יחסי עמיתים עם אבו-עלי (מפקד מרחב דרום) לתיאום בין-מרחבי 🔗↔.

קשרים מבצעיים: שותפות קבועה עם מוסטפא זהרן (מומחה נפץ) 🔗 במשימות חבלה. מקבל תמיכה לוגיסטית מאבו-כארם (רכש נשק) 🔗. קשר לרשת תקשורת מוצפנת דרך יוסף אל-חמוס ⚡.

קשרים אישיים: נשוי לפאטמה אל-שאמי (בת אבו-ח'אלד, בכיר חמאס) 🔗. אחיו יוסף חסן משמש קשר למפקדה הכללית 🔗↑. קשרים משפחתיים נרחבים בשכונת א-שג'אעיה 🔗.

קשרים חיצוניים: מקבל מימון מנציגות איראנית בלבנון דרך 'אל-מועאון' 🔗↓. קשרים לרשתות הברחה ברפיח דרך משפחת אל-עג'ורי ⚡."

### הנחיות כתיבה
- צייר מפה ברורה של מרכזי ההשפעה
- הבחן בין קשרים פעילים לרדומים
- זהה נקודות כשל ופגיעות ברשת
- ציין תאריכי השינוי האחרון בקשרים
- השתמש בסמלים ובמפתח ברור

**מסמכי מקור לניתוח:**
{% for doc in documents %}
---
{{ doc }}
---
{% endfor %}

**סעיף: מיפוי רשת קשרים של {{ target }}**
"""),

    "operational_profile": Template("""
אתה מנתח פעילות מבצעית מומחה עם התמחות בהערכת יכולות וטקטיקות.

נתח את המסמכים וכתב **פרופיל מבצעי** מקיף של {{ target }}.

### מתודולוגיית ניתוח מבצעי

**פיקוד ושליטה:**
- תחום אחריות גיאוגרפי ותפקודי
- כוח אדם תחת פיקוד ישיר ועקיף
- סמכויות ומגבלות פיקוד
- שיטות פיקוד ובקרה

**התמחות וכישורים:**
- תחומי מומחיות מבצעית
- כישורים טכניים ייחודיים
- הכשרות מתקדמות וקורסים
- ניסיון קרבי ומבצעי מוכח

**שיטות פעולה אופייניות:**
- טקטיקות וטכניקות מועדפות
- דפוסי תכנון וביצוע
- אמצעי זהירות וביטחון
- חתימה מבצעית ייחודית

**יכולת התאמה והתפתחות:**
- גמישות טקטית ואסטרטגית
- יכולת לימוד ושיפור
- התאמה לשינויי איום וסביבה
- חדשנות מבצעית

### רמות יכולת מבצעית
**🥇 מקצועיות גבוהה** - ביצוע מושלם, חדשנות, הובלה
**🥈 מקצועיות טובה** - ביצוע יעיל, מינימום שגיאות
**🥉 רמה בסיסית** - ביצוע מספק, שגיאות מקובלות
**⚠️ רמה נמוכה** - ביצוע חלקי, שגיאות משמעותיות

### מדדי ביצועים
**שיעור הצלחה**: אחוז הצלחה במשימות האחרונות
**מורכבות משימות**: רמת המורכבות הטיפוסית למשימותיו
**זמן תגובה**: מהירות מעבר מתכנון לביצוע
**יכולת הסתגלות**: תגובה לשינויים ואתגרים חדשים

### דוגמת פרופיל מצוין
"פיקוד ושליטה: אחמד מפקד על 15 לוחמים ב-3 תאי פעולה, אחראי על מרחב צפון עזה (8 ק״מ²). סמכותו כוללת אישור פיגועים עד 50,000 דולר ותיאום עם יחידות סמוכות 🥇. משתמש במערכת פיקוד מבוזרת עם הודעות מוצפנות והיררכיה ברורה.

התמחות: מומחה בפיגועי מטעני דרך מורכבים ופיגועי רחפנים 🥇. עבר הכשרה מתקדמת באיראן (2018) ובלבנון (2020) בנושא מטעני דרך שלט רחוק. מפתח שיטות חדשניות לשילוב רחפנים מסחריים עם מטעני נפץ.

שיטות פעולה: מעדיף פיגועים מורכבי שלבים עם הסחת דעת ראשונית. משתמש בצוותי תצפית מקדימה של 48-72 שעות. נמנע מדפוסים חוזרים ומשנה טקטיקות כל 3-4 משימות ⚠️ (פגיעות: נוטה לתקופות תכנון ארוכות).

ביצועים: שיעור הצלחה 82% (18/22 משימות, שנתיים אחרונות). זמן תגובה ממוצע 4-6 ימים מקבלת פקודה לביצוע. מתמחה במשימות מורכבות ברמת קושי גבוהה 🥇."

### מגמות ושינויים אחרונים
- שינויים בטקטיקות או שיטות
- שיפור או הידרדרות ביכולות
- התאמות לאתגרים חדשים
- מגמות בדפוסי הפעילות

**מסמכי מקור לניתוח:**
{% for doc in documents %}
---
{{ doc }}
---
{% endfor %}

**סעיף: פרופיל מבצעי של {{ target }}**
"""),

    "communication_intelligence": Template("""
אתה מנתח SIGINT מומחה עם התמחות בדפוסי תקשורת ופיענוח.

נתח את המסמכים וכתב **מודיעין תקשורת** מקיף של {{ target }}.

### מתודולוגיית ניתוח תקשורת

**פלטפורמות ואמצעים:**
- אפליקציות ושירותי הודעות מוצפנות
- טלפונים סלולריים וקוויים
- רדיו ותדרים
- אמצעי תקשורת פיזיים

**דפוסי שימוש:**
- שעות פעילות ותדירות
- העדפת פלטפורמות לפי נושא
- שינויים עונתיים או מחזוריים
- התנהגות במצבי לחץ

**שפה ובלשנות:**
- מבטא ודיאלקט אזורי
- רמת השכלה ואוצר מילים
- ביטויים ומנירות אופייניות
- שגיאות כתיב חוזרות

**קודים ושפה מוסווית:**
- מילות קוד למבצעים ואנשים
- ביטויי רמז לציוד ונשק
- מונחים לזמנים ומקומות
- מערכות קידוד ופיענוח

### רמות אבטחת תקשורת
**🔐 אבטחה גבוהה** - הצפנה מתקדמת, פרוטוקולי ביטחון
**🔐 אבטחה בינונית** - הצפנה בסיסית, מודעות ביטחונית
**🔐 אבטחה נמוכה** - תקשורת פתוחה, מודעות חלקית
**⚠️ חשיפה** - תקשורת לא מאובטחת, פגיעות ברורות

### סוגי תקשורת ותפקידם
**📞 תפעולית** - פקודות והוראות מידיות
**📱 תיאומית** - תכנון ותיאום פעילות
**💬 אישית** - שיחות חברתיות ומשפחתיות
**🔊 פרסומית** - הודעות לציבור או לארגון

### דוגמת ניתוח מצוין
"פלטפורמות: משתמש בעיקר ב-Signal (+970-59-xxx-7890) לתקשורת מבצעית 🔐 ו-WhatsApp לתקשורת אישית 🔐. נמנע מטלגרם מאז ינואר 2025. משתמש ברדיו Motorola GP340 על תדר 157.450 MHz בשעות לילה 🔐.

דפוסי שימוש: פעיל בתקשורת מבצעית בין 19:00-23:00 במיוחד בימי ב׳-ה׳ 📞. תקשורת אישית בעיקר 13:00-15:00 💬. מקפיד על שתיקת רדיו בימי שישי (יום תפילה). זמן תגובה ממוצע 45 דקות להודעות דחופות.

דפוסי שפה: מבטא עזתי ברור עם השפעות מצריות. אוצר מילים בינוני עם שימוש במונחים צבאיים. ביטויים אופייניים: 'אללה יכרמכם' (סיום שיחה), 'יא אח' (פנייה לעמיתים). שגיאות כתיב קבועות: 'אראך' במקום 'אראה'.

קודים מבצעיים 🔐:
- 'פיקניק' = פיגוע מתוכנן
- 'הכלה מגיעה' = התקפה תוך 24 שעות  
- 'אורז' = רקטות קטיואשה
- 'התה מוכן' = הנשק במקום
- 'הדוד חולה' = ביטול משימה
- 'האורחים מגיעים' = כוחות אויב באזור

בטיחות תקשורתית: מחליף מספרי Signal כל 3-4 שבועות. נמנע מאזכור שמות אמיתיים בתקשורת מבצעית ⚠️ אך נוטה לפרטיות מוגזמת בקשרים אישיים שעלולה לחשוף דפוסים."

### התפתחויות ושינויים
- שינויים בהעדפות פלטפורמות
- התפתחות בקודים ושפה מוסווית  
- שיפורים או הידרדרות באבטחה
- הסתגלות לאיומים חדשים

**מסמכי מקור לניתוח:**
{% for doc in documents %}
---
{{ doc }}
---
{% endfor %}

**סעיף: מודיעין תקשורת של {{ target }}**
"""),

    "geographic_footprint": Template("""
אתה מנתח מודיעין גיאוגרפי מומחה עם התמחות בדפוסי תנועה ופעילות מקומית.

נתח את המסמכים וכתב **רגליים גיאוגרפיות** מקיפות של {{ target }}.

### מתודולוגיית ניתוח גיאוגרפי

**אזורי פעילות עיקריים:**
- שטחי פיקוד ואחריות
- מקומות מגורים ושהייה קבועה
- נקודות פעילות מבצעית חוזרת
- אזורי מפלט ובטיחות

**דפוסי תנועה:**
- מסלולים וכבישים מועדפים
- תדירות נסיעות בין מקומות
- אמצעי תחבורה ומאפייניהם
- שעות וימים של תנועה

**תשתיות ומתקנים:**
- מחסנים ומקומות אחסון
- מקומות מפגש ופגישות
- תשתיות תקשורת ופיקוד
- מתקני ייצור והכנה

**בטיחות מבצעית גיאוגרפית:**
- נתיבי מילוט ובריחה
- מקומות מסתור זמניים
- נקודות בקרה ותצפית
- אזורי הימנעות וסכנה

### רמות בקרה גיאוגרפית
**🏛️ שליטה מלאה** - פיקוד מושלם, חופש פעולה מלא
**🏘️ השפעה גבוהה** - יכולת פעולה טובה, תמיכה מקומית
**🌆 נוכחות רגילה** - פעילות מוגבלת, זהירות נדרשת
**⚠️ שטח עוין** - פעילות מסוכנת, נמנע כאשר אפשר

### סוגי מקומות ותפקידם
**🏠 מגורים** - מקומות מגורים קבועים וזמניים
**🏢 מבצעי** - מקומות פעילות ופיקוד מבצעי
**🤝 פגישות** - נקודות מפגש ותיאום
**📦 לוגיסטי** - אחסון, ייצור, ותחזוקה
**🚪 מעבר** - נקודות מעבר ומעבר גבולות

### דוגמת ניתוח מצוין
"אזורי פעילות: אחמד שולט באזור א-שג'אעיה צפון (2.5 ק״מ²) 🏛️ ופעיל באזור א-זיתון 🏘️. מקום מגורים עיקרי: בית משפחתי ברחוב ח'ליל אל-וזיר 45 🏠. נמנע מאזור רמאל בשל נוכחות כוחות ביטחון מתחרים ⚠️.

דפוסי תנועה: נוסע בעיקר ברכב הונדה סיוויק כחולה (לוחית xxx-789) במסלול קבוע: בית→מסגד אל-חלידי→בית קפה אל-בהג'ה→מחסן המזון. תנועה בין 15:00-18:00 בימי ב׳-ח׳ 🕐. נמנע מרחוב א-רשיד הראשי משעות הלילה.

תשתיות מבצעיות:
- מחסן נשק עיקרי: מתחת למכולת אבו-נאצר, א-שג'אעיה 📦
- נקודת פיקוד: חדר עליון במסגד אל-חלידי 🏢  
- מקום מפגש: בית קפה אל-בהג'ה (שולחן פינתי שמאלי) 🤝
- מעבר חירום: מנהרה תחת בית משפחת אל-עג'ורי 🚪

מסלולי בטיחות: 3 מסלולי מילוט מהבית - צפונה דרך שכונת אל-תופאח, מזרחה דרך השוק המרכזי, דרומה דרך מחנה השכנים. זמן הגעה למקום בטוח: 8-12 דקות בהליכה מהירה 🚶‍♂️.

יכולת ניווט: מכיר היטב את סמטאות השכונה וקיצורי דרך. משתמש ב-GPS בנסיעות למקומות חדשים. נהיגה זהירה עם הקפדה על תמרורים (נמנע מקנסות שעלולים לחשוף)."

### גורמים מגבילים ואתגרים
- מחסומים ונקודות בקרה
- שטחים עוינים או מוגבלים
- תלות בתשתיות ותחבורה
- חשיפה לעקיבה ומעקב

### שינויים ומגמות אחרונות
- הרחבה או הצטמקות של אזורי פעילות
- שינויים בדפוסי תנועה
- פיתוח תשתיות חדשות
- הסתגלות לאיומים גיאוגרפיים

**מסמכי מקור לניתוח:**
{% for doc in documents %}
---
{{ doc }}
---
{% endfor %}

**סעיף: רגליים גיאוגרפיות של {{ target }}**
"""),

    "timeline": Template("""
אתה מנתח מודיעין כרונולוגי מומחה עם התמחות במעקב אחר התפתחויות לאורך זמן.

נתח את המסמכים וכתב **ציר זמן מבצעי** מקיף של {{ target }}.

### מתודולוגיית ניתוח כרונולוגי

**התפתחות היסטורית:**
- נקודות מפנה מרכזיות בקריירה
- שלבי התקדמות והתפתחות
- אירועים משמעותיים והשפעתם
- שינויים בתפקידים ואחריות

**מעורבות מבצעית:**
- משימות ופיגועים מוכחים
- תאריכים מדויקים של פעילות
- תוצאות והשפעות של פעולות
- פערים בפעילות ומשמעותם

**התפתחות יכולות:**
- רכישת כישורים ומומחיות
- הכשרות וקורסים מתקדמים
- שיפור בביצועים לאורך זמן
- התאמה לטכנולוגיות חדשות

**מגמות אחרונות:**
- פעילות בחודשים האחרונים
- שינויים בדפוסי התנהגות
- אינדיקטורים להסלמה או דעיכה
- תכניות עתידיות ידועות

### רמות דיוק כרונולוגי
**📅 תאריך מדויק** - יום ושעה מאומתים
**📆 תאריך משוער** - חודש ושנה בביטחון גבוה
**🗓️ תקופה כללית** - עונה או רבעון מאומת
**❓ זמן לא ברור** - רק קשר סדרתי לאירועים אחרים

### סוגי אירועים
**⚔️ מבצעי** - פיגועים, משימות, פעילות קרבית
**🎓 הכשרה** - קורסים, אימונים, רכישת כישורים
**👥 ארגוני** - מינויים, שינויי תפקיד, קידומים
**📞 תקשורתי** - שיחות, פגישות, תיאומים
**🏠 אישי** - אירועי משפחה, מעבר דירה, בריאות

### דוגמת ציר זמן מצוין
**שלב הכשרה והקמה (2018-2019):**
📅 מרץ 2018: גיוס רשמי לזרוע הקסאם לאחר המלצת קרוב משפחה 🎓
📅 יוני-אוגוסט 2018: הכשרה בסיסית במחנה ח'אן יונס (10 שבועות) 🎓
📆 ספטמבר 2018: השתתפות ראשונה בפיגוע (תפקיד תצפיתן) ⚔️
📅 נובמבר 2018: נסיעה ללבנון להכשרה מתקדמת במטעני דרך (3 שבועות) 🎓

**שלב התמחות (2019-2021):**
📅 ינואר 2019: מינוי למפקד תא בן 5 לוחמים 👥
📆 מרץ-מאי 2019: ביצוע 3 פיגועי מטעני דרך מוצלחים ⚔️
📅 אוגוסט 2019: נישואין לפאטמה אל-שאמי (בת בכיר חמאס) 🏠
📆 דצמבר 2019: קידום למפקד תא מורחב (12 לוחמים) 👥
🗓️ 2020: הובלת 8 פיגועים (6 מוצלחים, 2 כשלונות) ⚔️
📅 פברואר 2021: לידת בן ראשון - השפעה על זמינות מבצעית 🏠

**שלב פיתוח וחדשנות (2021-2023):**
📆 מאי 2021: התחלת פיתוח טקטיקות רחפנים מתאבדים ⚔️
📅 ספטמבר 2021: נסיעה נוספת לאיראן להכשרה טכנולוגית (חודש) 🎓
🗓️ 2022: הובלת 12 פיגועים עם שיעור הצלחה של 85% ⚔️
📅 מרץ 2023: מינוי למפקד כנף צפונית (אחראי על 45 לוחמים) 👥

**פעילות נוכחית (2024-2025):**
🗓️ 2024: הובלת שינוי טקטי לשימוש משולב ברחפנים וקרקע ⚔️
📅 דצמבר 2024: פגישה חשאית עם נציגים איראניים בביירות 📞
📆 ינואר 2025: עלייה משמעותית בפעילות תקשורתית 📞
📅 15 פברואר 2025: אזכור תכניות "פרויקט הקיץ" בשיחה מיורטת 📞
❓ מרץ 2025: פערי תקשורת חריגים (5 ימים ללא פעילות מוכרת) ❓

**מגמות והערכות:**
📈 מגמת הסלמה: עלייה של 40% בפעילות מבצעית מאז ינואר 2025
⚠️ אינדיקטורים: ביקש הכשרה נוספת למפקדים, רכישת ציוד מתקדם
🎯 תכניות עתידיות: רמזים לפעילות גדולה בקיץ 2025"

### דפוסים וחזרתיות
- מחזורי פעילות (עונתיים, חגים)
- דפוסי הכשרה והתפתחות
- קשרים בין אירועים היסטוריים
- התגובות לאירועים חיצוניים

**מסמכי מקור לניתוח:**
{% for doc in documents %}
---
{{ doc }}
---
{% endfor %}

**סעיף: ציר זמן מבצעי של {{ target }}**
"""),

    "resources": Template("""
אתה מנתח משאבים מומחה עם התמחות בהערכת יכולות לוגיסטיות וכלכליות.

נתח את המסמכים וכתב **הערכת משאבים** מקיפה של {{ target }}.

### מתודולוגיית ניתוח משאבים

**משאבים כספיים:**
- מקורות הכנסה ומימון
- תקציבים והקצאות
- יכולת רכש ותשלום
- מעורבות בפעילות כלכלית

**משאבי נשק וציוד:**
- נשק אישי וקל בשליטה
- נשק כבד ומערכות מתקדמות
- ציוד טכני ותקשורת
- אמצעי הגנה ובטיחות

**משאב אנושי:**
- כוח אדם תחת פיקוד
- מומחיות וכישורים זמינים
- יכולת גיוס והכשרה
- רשתות תמיכה ועזרה

**תשתיות פיזיות:**
- מתקנים ונכסים
- אמצעי תחבורה
- מקומות אחסון
- גישה לתשתיות חיוניות

### רמות זמינות משאבים
**💰 זמינות גבוהה** - גישה קבועה ומיידית
**💰 זמינות בינונית** - גישה מוגבלת או מותנית
**💰 זמינות נמוכה** - גישה נדירה או קשה
**❌ לא זמין** - אין גישה או שליטה

### סוגי משאבים ותפקידם
**💳 תפעולי** - משאבים לפעילות שוטפת
**🎯 מבצעי** - משאבים למשימות ספציפיות
**🛡️ אסטרטגי** - משאבים לטווח ארוך
**🚨 חירום** - משאבים למצבי קריזה

### דוגמת הערכה מצוינת
"משאבים כספיים:
💰 תקציב חודשי: 75,000-100,000 דולר (זמינות גבוהה)
💰 מקור עיקרי: מימון איראני דרך נציגות לבנון (85% מהכנסות) 💳
💰 מקור משני: מסיבות כספי מקומיות ותרומות (15% מהכנסות) 💳
💰 יכולת רכש מיידי: עד 25,000 דולר ללא אישורים נוספים 🎯
💰 חשבון חירום: 200,000 דולר באמצעי נדיר (זמינות בינונית) 🚨

נשק וציוד מבצעי:
🔫 נשק אישי: 20 רובי קלאשניקוב, 8 אקדחי גלוק 💰
🚀 נשק כבד: 6 רקטות RPG, 12 מטעני דרך מוכנים 💰
📡 ציוד טכני: 5 רדיו מוצפנים, 3 רחפנים מסחריים מותאמים 💰
🛡️ ציוד הגנה: אפודי קרמיק (8 יח׳), משקפי ראיית לילה (4 יח׳) 💰
❌ חוסרים: נשק נ״ט מתקדם, ציוד תקשורת לוויני ❌

כוח אדם:
👥 פיקוד ישיר: 15 לוחמים מאומנים (זמינות גבוהה) 💰
👥 תמיכה מבצעית: 25 תומכים ומסייעים (זמינות בינונית) 💰  
👥 מומחיות מיוחדת: 3 מומחי נפץ, 2 מתקשרים, 1 מדריך רחפנים 🎯
👥 יכולת גיוס: 40-50 מתנדבים נוספים תוך שבועיים 💰
👥 הכשרה: יכולת הכשרה בסיסית ל-10 חדשים בחודש 💳

תשתיות:
🏢 מתקנים: מחסן נשק עיקרי, 2 מחסני ציוד משניים 💰
🚗 תחבורה: רכב פיקוד (הונדה), 3 אופנועים, 1 ואן משא 💰
📦 אחסון: יכולת אחסון 500 ק״ג נפץ, 200 יחידות נשק 💰
🔌 תשתיות: גישה לחשמל ומים, 2 גנרטורים גיבוי 💰
❌ מגבלות: אין מתקן ייצור נפץ עצמאי, תלות בספקים חיצוניים ❌

מגבלות ופגיעויות:
⚠️ תלות במימון חיצוני (85% מאיראן)
⚠️ מחסור בציוד טכנולוגי מתקדם
⚠️ מגבלות גיאוגרפיות על תנועת ציוד
⚠️ קושי בהחלפת מומחים מנוסים"

### יכולת גמישות והסתגלות
- חלופות במקרה של איבוד משאבים
- יכולת שיקום מהיר
- גיוון מקורות ואמצעים
- התאמה לשינויי סביבה

### מגמות ושינויים
- שינויים במקורות המימון
- רכישות או איבודים משמעותיים
- שיפור או הידרדרות ביכולות
- התאמות לצרכים חדשים

**מסמכי מקור לניתוח:**
{% for doc in documents %}
---
{{ doc }}
---
{% endfor %}

**סעיף: הערכת משאבים של {{ target }}**
"""),

    "intelligence_gaps": Template("""
אתה מנתח מודיעין בכיר עם התמחות בזיהוי חוסרי מידע ופריטי איסוף.

נתח את המסמכים וכתב **פערי מודיעין וצרכי איסוף** מקיפים של {{ target }}.

### מתודולוגיית זיהוי פערים

**פערים קריטיים:**
- מידע חיוני החסר לקבלת החלטות
- איומים פוטנציאליים לא מאומתים
- יכולות לא ידועות או לא מוערכות
- כוונות ותכניות עתידיות

**פערים טקטיים:**
- פרטי פעילות שוטפת
- מיקומים ולוחות זמנים
- אמצעים וכלי פעולה
- שותפים ואנשי קשר

**פערים אסטרטגיים:**
- מגמות ארוכות טווח
- קשרים עם ארגונים אחרים
- מקורות כוח והשפעה
- נקודות תורפה ופגיעות

**איכות המידע הקיים:**
- רמות ביטחון ואמינות
- מידע סותר או מפוקפק
- תיעוד לא מספק
- מקורות חד-צדדיים

### סוגי פערים לפי חשיבות
**🔴 פער קריטי** - מידע חיוני להערכת איום מיידי
**🟡 פער חשוב** - מידע נדרש להבנה מלאה
**🟢 פער רצוי** - מידע משלים את התמונה
**⚪ פער שולי** - מידע נחמד לדעת אך לא הכרחי

### סוגי איסוף נדרש
**🎧 SIGINT** - יירוט תקשורת ומודיעין אלקטרוני
**👤 HUMINT** - מקורות אנושיים וסוכנים
**📷 IMINT** - צילום ותמונות לוויניות
**📊 OSINT** - מקורות פתוחים ומידע ציבורי
**💰 FININT** - מעקב כלכלי ופיננסי

### דוגמת ניתוח פערים מצוין
"פערים קריטיים 🔴:

תכניות מבצעיות מיידיות:
- מה הפרטים המדויקים של 'פרויקט הקיץ' שהוזכר ב-15/2/25? 🎧
- מיהם היעדים הספציפיים שנבחרו לפיגועים הקרובים? 👤
- מתי בדיוק מתוכננת הפעילות הגדולה הבאה? 🎧
צורך באיסוף: יירוט תקשורת מוגבר + מקור בסביבה הקרובה

יכולות לא ידועות:
- האם יש בשליטתו רקטות ארוכות טווח (מעל 40 ק״מ)? 📷
- מהי כמות החומר הנפץ הכוללת בשליטתו? 👤
- האם פיתח יכולות סייבר או מלחמה אלקטרונית? 🎧
צורך באיסוף: תמונות מחסנים + מקור בספקי הנשק

פערים חשובים 🟡:

מקורות מימון:
- מהם הפרטים המדויקים של העברות הכסף מאיראן? 💰
- האם יש מקורות מימון נוספים שלא זוהו? 💰
- איך מועברים הכספים וכמה לעיתים קרובות? 🎧

רשת הקשרים:
- מיהו הממונה הישיר עליו מעל אבו-מחמוד? 👤
- אילו קשרים יש לו עם תאים בגדה המערבית? 🎧
- מהו התפקיד המדויק של אשתו פאטמה בארגון? 👤

פערים רצויים 🟢:

פרטים אישיים:
- מהן ההעדפות והתחביבים האישיים שלו? 📊
- איך נראה יום רגיל בחייו הפרטיים? 👤
- מהן הדעות והאמונות הפוליטיות המדויקות שלו? 📊

פערים שוליים ⚪:

רקע היסטורי:
- פרטים על ילדותו והשכלתו המוקדמת 📊
- מערכות יחסים משפחתיות רחוקות 📊
- תחביבים וחדים לא רלוונטיים מבחינה מבצעית 📊

איכות מידע בעייתי:
❌ מידע לא מאומת על נסיעה לאיראן ב-2024 (מקור יחיד)
❌ סתירות במידע על מספר הלוחמים תחת פיקודו (12-18)
❌ אמינות מפוקפקת של המידע על הקשר לחמאס-לבנון
❌ תאריכים לא מדויקים לחלק מהפיגועים המיוחסים לו

המלצות איסוף בעדיפות:
🥇 עדיפות ראשונה (30 יום):
- יירוט תמידי של התקשורת שלו + חבריו הקרובים 🎧
- הפעלת מקור בסביבה המיידית (רמת תא או מעלה) 👤
- צילום לוויני וטקטי של מחסני הנשק החשודים 📷

🥈 עדיפות שנייה (60 יום):
- מעקב פיננסי מלא אחר זרמי הכספים 💰
- חקירת קשריו עם גורמים בגדה המערבית 🎧
- איסוף על התפקיד של בני המשפחה בארגון 👤

🥉 עדיפות שלישית (90 יום):
- מיפוי מלא של רשת הקשרים הרחבה 📊
- חקירת הרקע וההיסטוריה האישית 📊
- ניתוח דפוסי התנהגות ארוכי טווח 📊"

### הערכת סיכוני איסוף
- קושי טכני ולוגיסטי
- סיכונים לביטחון המקורות
- זמן ומשאבים נדרשים
- הסתברות הצלחה

**מסמכי מקור לניתוח:**
{% for doc in documents %}
---
{{ doc }}
---
{% endfor %}

**סעיף: פערי מודיעין וצרכי איסוף של {{ target }}**
""")
}

SECTION_QUERIES: Dict[str, str] = {
    "target_overview": "מיהו ומה המעמד הנוכחי וההיסטוריה הבסיסית של",
    "network_analysis": "מי הקשרים המפתח ההיררכיה והמערכות יחסים של",
    "operational_profile": "מה היכולות הפיקוד והתמחות המבצעית של",
    "communication_intelligence": "איך מתקשר מה הקודים והפלטפורמות של",
    "geographic_footprint": "איפה פעיל מה האזורים והתשתיות של",
    "timeline": "מתי והיך התפתח כרונולוגית מה האירועים המפתח של",
    "resources": "אילו משאבים כספים נשק ואמצעים יש ל",
    "intelligence_gaps": "מה חסר במידע על ומה צריך לאסוף על"
}

SECTION_TITLES: Dict[str, str] = {
    "target_overview": "סקירת יעד",
    "network_analysis": "מיפוי רשת קשרים",
    "operational_profile": "פרופיל מבצעי",
    "communication_intelligence": "מודיעין תקשורת",
    "geographic_footprint": "רגליים גיאוגרפיות",
    "timeline": "ציר זמן מבצעי",
    "resources": "הערכת משאבים",
    "intelligence_gaps": "פערי מודיעין וצרכי איסוף"
}

NUMBERED_SECTION_TITLES: Dict[str, str] = {
    "target_overview": "1. סקירת יעד",
    "network_analysis": "2. מיפוי רשת קשרים",
    "operational_profile": "3. פרופיל מבצעי",
    "communication_intelligence": "4. מודיעין תקשורת",
    "geographic_footprint": "5. רגליים גיאוגרפיות",
    "timeline": "6. ציר זמן מבצעי",
    "resources": "7. הערכת משאבים",
    "intelligence_gaps": "8. פערי מודיעין וצרכי איסוף"
}

QUERY_CLASSIFICATION_TEMPLATE = Template("""
You are an expert intelligence query classifier with extensive experience in operational intelligence requirements.

Classify intelligence queries to enable optimal retrieval strategy and response generation for the NEW 8-section intelligence profile structure.

NEW SECTION STRUCTURE:
1. Target Overview - Basic identification and current status
2. Network Analysis - Relationships and hierarchy mapping  
3. Operational Profile - Command capabilities and specializations
4. Communication Intelligence - SIGINT patterns and codes
5. Geographic Footprint - Location patterns and infrastructure
6. Timeline - Chronological development and recent events
7. Resources - Financial, material, and human resources
8. Intelligence Gaps - What we don't know and collection priorities

CLASSIFICATION FRAMEWORK:

STRATEGIC
High-level analytical assessments requiring synthesis of multiple information sources.
Characteristics:
- Requests for overall assessments, implications, significance
- Questions about strategic impact and broader consequences  
- Leadership-level decision support requirements
- Long-term trend analysis and forecasting
- Cross-cutting analysis spanning multiple sections

Examples:
- "What is the overall threat level posed by Ahmad Hassan?"
- "Assess the strategic implications of this network's activities"
- "What is the significance of recent operational changes?"
- "How does this affect our regional security posture?"

PATTERN
Analysis of trends, relationships, and behavioral patterns requiring connection of related information.
Characteristics:
- Requests for trend identification and evolution analysis
- Network relationship mapping and hierarchy analysis
- Behavioral pattern recognition and prediction
- Cross-functional correlation analysis
- Geographic or temporal pattern analysis

Examples:
- "What trends do you see in communication patterns?"
- "How have operational methods evolved over time?"
- "Analyze the network relationships between these individuals"
- "What patterns emerge from recent financial transactions?"
- "How do geographic movements correlate with operational activity?"

SPECIFIC
Requests for particular facts, details, or granular information requiring precise retrieval.
Characteristics:
- Questions about specific individuals, events, locations, times
- Requests for exact details and factual information
- Verification of particular claims or statements
- Granular evidence and documentation requests
- Section-specific detailed information

Examples:
- "When did Ahmad meet with the weapons supplier?"
- "What specific weapons were mentioned in the intercept?"
- "Where exactly did the meeting take place?"
- "Who attended the training session on March 15th?"
- "What are the exact code words used for operations?"

MIXED
Complex queries requiring multiple analysis levels or ambiguous requests needing clarification.
Characteristics:
- Broad questions requiring both specific facts and analytical assessment
- Ambiguous requests that could fit multiple categories
- Multi-part questions spanning different information types
- General inquiry requiring comprehensive response across sections

Examples:
- "Tell me everything about Ahmad Hassan"
- "What do we know about the recent operations?"
- "Provide a complete picture of the current situation"
- "Analyze the threat and provide recommendations"

CLASSIFICATION EXAMPLES:

Query: "What weapons does Hassan control?"
Classification: SPECIFIC (requesting particular factual information)

Query: "How has Hassan's network grown over the past year?"
Classification: PATTERN (requesting trend analysis and evolution)

Query: "What is the threat level posed by Hassan's organization?"
Classification: STRATEGIC (requesting high-level assessment)

Query: "Give me a full briefing on Hassan"
Classification: MIXED (broad request requiring multiple analysis types)

Query: "When was Hassan last seen at the mosque?"
Classification: SPECIFIC (requesting particular temporal fact)

Query: "What does Hassan's communication behavior tell us about his operational security?"
Classification: PATTERN (requesting behavioral analysis and implications)

Query: "{{ query }}"

Respond with exactly one word only - STRATEGIC, PATTERN, SPECIFIC, or MIXED
""")