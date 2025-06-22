"""
Configuration module containing constants, templates, and system settings for the intelligence pipeline.
"""
from jinja2 import Template
from typing import Dict


HYPER_URL = "https://api.hyperbolic.xyz/v1/chat/completions"
LIGHTWEIGHT_MODEL = "meta-llama/Llama-3.3-70B-Instruct"
PREMIUM_MODEL = "meta-llama/Llama-3.3-70B-Instruct"

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
Gaps: [Contradictions and missing elements]

EXAMPLE:
INPUT FACTS: [{"who": "Ahmad Hassan", "what": "met with weapons supplier", "when": "Tuesday", "where": "Green Mosque", "confidence": 0.8}, {"who": "Hassan", "what": "received encrypted phone", "when": "Wednesday", "where": "safe house", "confidence": 0.9}]

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
  {"who": "Ahmad Hassan", "what": "met with weapons supplier Abu-Saif", "when": "Tuesday evening", "where": "Green Mosque", "confidence": 0.8},
  {"who": "Hassan", "what": "received encrypted satellite phone", "when": "Wednesday morning", "where": "safe house on Omar Street", "confidence": 0.9},
  {"who": "Abu-Saif", "what": "delivered 20 AK-47 rifles", "when": "Thursday night", "where": "warehouse district", "confidence": 0.7}
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
    "role_activities": Template("""
אתה מנתח מודיעין מומחה עם התמחות בניתוח ארגוני ופעילות מבצעית.

נתח את המסמכים וכתב סעיף מפורט ומקצועי על "תפקיד ופעילות עיקרית" של {{ target }}.

מתודולוגיית ניתוח:

תפקיד ארגוני:
- דרגה ומעמד בארגון
- תחומי אחריות ופיקוד
- יחסי כפיפות והיררכיה
- סמכויות מבצעיות

פעילות מבצעית:
- משימות עיקריות ואופיין
- שיטות פעולה אופייניות
- תכניות ופרויקטים בניהולו
- דפוסי פיקוד ובקרה

דוגמת ניתוח מצוין:
"אחמד חסן מכהן כמפקד מרחב צפוני בארגון, כפוף ישירות למפקד הכללי. באחריותו 3 יחידות מבצעיות הכוללות כ-50 פעילים. פעילותו העיקרית מתמקדת בתיאום פעולות חבלה ברמה האזורית, כולל תכנון מסלולי חדירה ואישור יעדים. נהג לקיים ישיבות פיקוד שבועיות בבטיפן המבצעי ולתאם פעילות עם מפקדי מרחבים סמוכים. בתקופה האחרונה הוביל פרויקט הקמת מערך רקטות ארוך טווח והיה אחראי על רכישת ציוד צבאי מתקדם."

הנחיות כתיבה:
- השתמש במידע מדויק בלבד מהמסמכים
- כתב בעברית מקצועית וברורה
- ספק פרטים ספציפיים ותאריכים כשאפשר
- הדגש היבטים מבצעיים ואסטרטגיים
- שמור על אובייקטיביות אנליטית
- אל תמציא מידע שאינו במסמכים
- המנע מהערכות לא מבוססות

מסמכי מקור לניתוח:
{% for doc in documents %}
---
{{ doc }}
---
{% endfor %}

סעיף: תפקיד ופעילות עיקרית של {{ target }}
"""),

    "capabilities_resources": Template("""
אתה מנתח מודיעין מומחה בהערכת יכולות וכוח לוחם של גורמי טרור וארגונים עוינים.

### משימה
נתח את המסמכים וכתב הערכה מפורטת על "יכולות ומשאבים" של {{ target }}.

### מסגרת ניתוח יכולות
**אמצעי לחימה:**
- נשק אישי וקל (סוג, כמות, מקור)
- נשק כבד ומערכות (רקטות, נ"ט, מרגמות)
- חומרי נפץ וכלי חבלה
- ציוד מתקדם (תקשורת, ראיית לילה, וכו')

**משאבים כספיים:**
- מקורות מימון ותקציבים
- מעורבות בפעילות כלכלית
- קשרים למקורות חיצוניים
- יכולת רכש ותשלום

**משאב אנושי:**
- כוח אדם תחת פיקוד/השפעה
- מומחיות וכישורים מיוחדים
- רמת הכשרה ומקצועיות
- יכולת גיוס והכשרה

**תשתיות ומתקנים:**
- בסיסים ומחסנים
- מעבדות ומתקני ייצור
- אמצעי תחבורה ותקשורת
- מקומות מפלט ומסתור

### דוגמת ניתוח מצוין
"חסן שולט במחסן נשק מרכזי הכולל כ-200 רובי קלאשניקוב, 50 רקטות RPG, וכמויות גדולות של חומרי נפץ מתוצרת איראן. הוא מנהל תקציב חודשי של כ-100,000 דולר המתקבל ממקורות באיראן ולבנון. תחת פיקודו המישיר 85 פעילים מאומנים כולל 12 מומחי חבלה. בבעלותו 5 מתקני ייצור רקטות סמויים ברצועה ומערך תקשורת מוצפן המבוסס על ציוד סיני מתקדם."

### קטגוריות הערכה
🔴 **יכולת גבוהה**: משאבים משמעותיים עם נגישות קבועה
🟡 **יכולת בינונית**: משאבים מוגבלים או נגישות חלקית  
🟢 **יכולת נמוכה**: משאבים מועטים או נגישות מוגבלת
❓ **לא ידוע**: מידע חסר או לא מאומת

**מסמכי מקור לניתוח:**
{% for doc in documents %}
---
{{ doc }}
---
{% endfor %}

**סעיף: יכולות ומשאבים של {{ target }}**
"""),

    "communication_patterns": Template("""
אתה מנתח SIGINT מומחה עם התמחות בדפוסי תקשורת של גורמי טרור וארגונים עוינים.

נתח את המסמכים וכתב פרופיל מפורט של "דפוסי תקשורת ושפה" של {{ target }}.

מסגרת ניתוח תקשורת:

אמצעי תקשורת:
- טלפונים (סלולריים, קוויים, לוויין)
- אפליקציות מוצפנות (Signal, Telegram, WhatsApp)
- רדיו ואמצעי ותיק
- שליחים ותקשורת פיזית

דפוסי שפה וסגנון:
- ביטויים אופייניים וחזרתיים
- מבטא ודיאלקט אזורי
- רמת השכלה ואוצר מילים
- שגיאות כתיב אופייניות

קודים ומונחי מפתח:
- מילות קוד לפעילות מבצעית
- כינויים לאנשים ומקומות
- מונחי רמז לציוד ונשק
- ביטויי זמן מוסווים

דפוסי שימוש:
- שעות פעילות אופייניות
- תדירות ואורך שיחות
- מעגלי קשר עיקריים
- פרוטוקולי אבטחת תקשורת

דוגמת ניתוח מצוין:
"חסן משתמש בעיקר ב-Signal עם מספר מזויף +972-59-xxx-7890, פעיל בין השעות 18:00-23:00. שפתו מאופיינת בביטויים כמו 'האורחים מגיעים' (= פיגוע מתוכנן), 'פיקניק במינהרה' (= העברת נשק), ו'האח הגדול מתקשר' (= הוראה מהמפקדה). מבטאו עזתי ברור עם השפעות מצריות. נוהג לחסוך במילים - הודעות קצרות של 1-3 מילים. טעויות כתיב קבועות: כותב 'אמש' במקום 'אתמול', 'אראך' במקום 'אכנע'. משתמש ברדיו ב-FM 94.3 לתקשורת חירום עם קודים מספריים."

רמות דיוק ניתוח:
דיוק גבוה: מבוסס על הקלטות וחומר מאומת
דיוק בינוני: מבוסס על עדויות וצולבות
דיוק נמוך: מבוסס על מקורות בודדים לא מאומתים

מסמכי מקור לניתוח:
{% for doc in documents %}
---
{{ doc }}
---
{% endfor %}

סעיף: דפוסי תקשורת ושפה של {{ target }}
"""),

    "activity_patterns": Template("""
אתה מנתח מודיעין מומחה במעקב והתנהגות מבצעית של יעדי מעקב.

נתח את המסמכים וכתב פרופיל מפורט של "דפוסי פעילות" של {{ target }}.

מסגרת ניתוח דפוסים:

דפוסי זמן:
- שעות פעילות יומיות
- ימי שבוע מועדפים
- עונתיות ומחזוריות
- שינויים בתזמון לפי פעילות

דפוסי מקום:
- מקומות מפגש קבועים
- נתיבי תנועה אופייניים
- אזורי פעילות מרכזיים
- מקומות מפלט ובטיחות

דפוסי התנהגות:
- שיטות פעולה חוזרות
- אמצעי זהירות ובטיחות
- התנהגות בפני לחץ
- אינטראקציה עם אחרים

דפוסי לוגיסטיים:
- אמצעי תחבורה מועדפים
- ציוד נייד אופייני
- הרגלי אכילה ולינה
- תמיכה לוגיסטית

דוגמת ניתוח מצוין:
"חסן פעיל בעיקר בין השעות 15:00-20:00, נמנע מפעילות בימי שישי (יום תפילה). נוהג להגיע לפגישות ברכב הונדה אזרחית דרך רחוב א-שהדא, תמיד 15 דקות מוקדם. מתבונן במקום מ-3 כיוונים לפני כניסה. בפגישות ממנע לשבת עם הגב לכניסה ושומר על מרחק 2 מטר מאחרים. נושא תמיד תרמיל קטן עם ציוד תקשורת ובקבוק מים. במצבי לחץ נוטה לעזוב בכיוון מזרח דרך שכונות צפופות. מקומות מפגש אהובים: בית קפה 'אל-בהג'ה' (ימי ב'-ד'), מסגד אל-ח'אלידי (ימי שישי אחר הצהריים)."

סיווג דפוסים:
דפוס קבוע: מתרחש בעקביות גבוהה (80%+ מהמקרים)
דפוס משתנה: מתרחש בעקביות בינונית (50-80% מהמקרים)
דפוס חריג: מתרחש לעיתים נדירות (פחות מ-50% מהמקרים)

מסמכי מקור לניתוח:
{% for doc in documents %}
---
{{ doc }}
---
{% endfor %}

סעיף: דפוסי פעילות של {{ target }}
"""),

    "network_analysis": Template("""
אתה מנתח מודיעין מומחה ברשתות טרור וארגונים עוינים עם התמחות בניתוח קשרים.

נתח את המסמכים וכתב מפת קשרים מפורטת של "רשת קשרים" של {{ target }}.

מסגרת ניתוח רשתות:

היררכיה ארגונית:
- ממונים ובכירים
- כפופים ומפקדים עליהם
- עמיתים באותה דרגה
- קשרי פיקוד ובקרה

קשרים מבצעיים:
- שותפים למשימות
- מקורות מידע ומשאבים
- אנשי קשר טקטיים
- רשתות תמיכה

קשרים אישיים:
- קרובי משפחה מעורבים
- חברים אישיים מהארגון
- קשרים רומנטיים
- שכנים וקהילה

קשרים חיצוניים:
- נציגי ארגונים אחרים
- מקורות מימון חיצוניים
- ספקי נשק וציוד
- תמיכה בינלאומית

דוגמת ניתוח מצוין:
"חסן כפוף ישירות לאבו-סעיד (מפקד מרחב צפון) ובעל סמכות פיקוד על 8 לוחמים כולל המפקדים אחמד נסר ומוחמד קסם. מקיים קשר הדוק עם אבו-עלי (מפקד מרחב דרום) לתיאום פעילות בין-מרחבית. אחיו יוסף חסן משמש כקשר למפקדה הכללית. מקבל מימון מהאח החמוס (איראן) דרך אבו-כארם (לבנון). קשור רומנטית לפאטמה אל-שאמי שאביה בכיר בחמאס. שותף קבוע בפעילות עם התאום מוסטפא זהרן. מקומות מגורים בשכונת א-שג'אעיה מקנים לו קשרים נרחבים עם משפחות מקומיות תומכות."

מפתח סוגי קשרים:
פיקוד עליון: ממונה ישיר או בכיר מעליו
פיקוד תחתון: כפוף ישיר או מקבל הוראות
שותפות מבצעית: עמית לפעילות וביצוע
מקור משאבים: ספק כספים/נשק/ציוד
קשר משפחתי: בן משפחה מעורב בארגון
קשר אישי: חבר/רומנטי ללא תפקיד מבצעי

רמות עוצמת קשר:
קשר חזק: יומי/שבועי, חיוני לפעילות
קשר בינוני: חודשי/מזדמן, חשוב לפעילות
קשר חלש: נדיר/עקיף, תמיכה כללית

מסמכי מקור לניתוח:
{% for doc in documents %}
---
{{ doc }}
---
{% endfor %}

סעיף: רשת קשרים של {{ target }}
"""),

    "key_topics": Template("""
אתה מנתח מודיעין מומחה בתוכן שיחות ותקשורת של גורמי טרור וארגונים עוינים.

נתח את המסמכים וכתב סקירה מפורטת של "נושאי שיחה מרכזיים" של {{ target }}.

מסגרת ניתוח תוכן:

נושאים מבצעיים:
- תכניות פיגועים ומשימות
- הכשרות ואימונים
- רכש נשק וציוד
- תיאום עם יחידות אחרות

נושאים ארגוניים:
- מינויים ושינויי תפקידים
- משמעת ובעיות פנימיות
- תקציבים ומשאבים
- מדיניות והחלטות

נושאים אישיים רלוונטיים:
- בעיות משפחתיות המשפיעות על הפעילות
- בריאות ומגבלות פיזיות
- שאיפות אישיות בארגון
- יחסים עם דמויות מפתח

נושאים חיצוניים:
- מצב הסביבה הביטחונית
- פעילות כוחות הביטחון
- מצב פוליטי ותקשורתי
- קשרים בינלאומיים

דוגמת ניתוח מצוין:
"חסן דן בעיקר בתכנון פיגועי מרגמות (60% מהשיחות), כולל בחירת עמדות ירי ותזמון. מתעניין רבות בציוד חדיש איראני ומבקש להוסיף רקטות ארוכות טווח למחסן. דואג למצב אמו החולה אשר דורשת טיפול רפואי יקר, מה שמקשה על התרכזותו במשימות. מבקר תדיר את מדיניות המפקדה בנושא הפצת שכר ומאיים לפנות למפקד הכללי. דן הרבה במצב הביטחוני אחרי מבצע 'שומר החומות' ובדרכים להתמודד עם מעקב מוגבר. מתכנן לנסוע ללבנון להכשרה מתקדמת במטעני דרך."

קטגוריות עדיפות:
עדיפות מבצעית: נושאים הקשורים ישירות לפעילות טרור
עדיפות ארגונית: נושאים לניהול והפעלת הארגון
עדיפות אישית: נושאים אישיים המשפיעים על הפעילות
עדיפות סביבתית: נושאים חיצוניים המשפיעים על התכנון

רמות שכיחות:
דיון תכוף: מופיע ברוב השיחות (70%+)
דיון בינוני: מופיע חלק מהשיחות (30-70%)
דיון נדיר: מופיע לעיתים רחוקות (פחות מ-30%)

מסמכי מקור לניתוח:
{% for doc in documents %}
---
{{ doc }}
---
{% endfor %}

סעיף: נושאי שיחה מרכזיים של {{ target }}
"""),

    "code_words": Template("""
אתה מנתח SIGINT מומחה עם התמחות בפיענוח קודים ושפה מוסווית של ארגוני טרור.

נתח את המסמכים וכתב מילון מפורט של "מילות מפתח וביטויי קוד" של {{ target }}.

מסגרת ניתוח קודים:

קודים מבצעיים:
- שמות קוד לפעילות חבלה
- ביטויים למשלוח נשק
- רמזים לתזמון פעילות
- כינויים ליעדים

קודים לוגיסטיים:
- ביטויים לכספים ותשלומים
- רמזים לציוד ואמצעים
- כינויים למקומות ומתקנים
- ביטויי תחבורה והעברה

קודים אישיים:
- כינויים לאנשי קשר
- ביטויים למצבי רוח
- רמזים למצב בריאות
- כינויים לקרובי משפחה

קודים ביטחוניים:
- אזהרות מפני מעקב
- ביטויים לשינוי תכניות
- רמזים לסכנה
- כינויים לכוחות ביטחון

דוגמת ניתוח מצוין:

קודים מבצעיים:
- "פיקניק" = פיגוע מתוכנן
- "אורחים מגיעים" = התקפה תוך 24 שעות
- "חתונה בגן" = פיגוע בשטח פתוח
- "ארוחת ערב" = פיגוע ברי"ר

קודים לוגיסטיים:
- "אורז" = רקטות וטילים
- "סוכר" = חומרי נפץ
- "התה מוכן" = הנשק הגיע למעון
- "המחסן מלא" = יש מספיק אמצעים

קודים אישיים:
- "הדוד" = מפקד הכללי
- "האח הגדול" = אבו-סעיד (מפקד)
- "הילדים בסדר" = הלוחמים מוכנים
- "אמא חולה" = יש בעיה במשימה

דיוק פיענוח:
דיוק גבוה: מאומת בכמה מקורות עצמאיים
דיוק בינוני: נסמך על הקשר חוזר
דיוק נמוך: אומדן ראשוני הדורש אימות

תדירות שימוש:
שימוש קבוע: מופיע בכל התקשורת
שימוש מזדמן: מופיע בנושאים מסוימים
שימוש חירום: מופיע במצבי לחץ בלבד

מסמכי מקור לניתוח:
{% for doc in documents %}
---
{{ doc }}
---
{% endfor %}

סעיף: מילות מפתח וביטויי קוד של {{ target }}
"""),

    "threat_assessment": Template("""
אתה מנתח איומים בכיר עם מומחיות בהערכת סיכונים ביטחוניים של גורמי טרור.

נתח את המסמכים וכתב הערכה מקיפה של "הערכת סיכון ומשמעות מבצעית" של {{ target }}.

מסגרת הערכת איום:

רמת סיכון נוכחית:
- איום מידי ומשמעותי
- יכולת פגיעה ונזק
- כוונה והזדמנות
- מידת דחיפות התמודדות

יכולות מבצעיות:
- נשק ואמצעי תקיפה
- כוח אדם ומומחיות
- תמיכה לוגיסטית
- גישה למטרות

ניתוח כוונות:
- מטרות מוצהרות
- דפוסי פעילות עברית
- אידיאולוגיה ומניעים
- לחצים והזדמנויות

השפעה אסטרטגית:
- השפעה על יציבות אזורית
- השפעה על ארגונים אחרים
- השפעה על מדיניות ביטחון
- משמעות בינלאומית

דוגמת הערכה מצוינת:

רמת סיכון: גבוהה מאוד (דרגה 4/5)

חסן מהווה איום מידי משמעותי בשל שליטתו במחסן נשק משמעותי ויכולת לבצע פיגועי רקטות ארוכי טווח. בעל ניסיון מוכח בביצוע 12 פיגועים בשנתיים האחרונות עם שיעור הצלחה של 85%. רשת הקשרים שלו מספקת מודיעין איכותי על מטרות ותמיכה לוגיסטית מתקדמת.

יכולת פגיעה: יכול לפגוע במטרות עד 40 ק"מ מרצועת עזה באמצעות רקטות גראד. בעל נגישות לחומרי נפץ איכותיים ומומחיות בהכנת מטעני דרך מתקדמים.

כוונות: מתכנן פיגוע משמעותי לציון יום השנה למבצע הקודם. דגש על מטרות אזרחיות לזעזוע הציבור הישראלי ושיפור מעמדו בארגון.

משמעות אסטרטגית: פיגוע מוצלח עלול לגרום להסלמה אזורית ולהשפיע על מוכנות ארגונים נוספים לפעולה דומה.

מטריצת סיכון:
רמה 5 - איום קיצוני: פיגוע מתוכנן ליום הקרוב
רמה 4 - איום גבוה: יכולת וכוונה מוכחת לפעילות
רמה 3 - איום בינוני: יכולת עם כוונה לא ברורה
רמה 2 - איום נמוך: יכולת מוגבלת או כוונה חלשה
רמה 1 - איום מינימלי: איום עקיף או עתידי

דחיפות פעולה:
מידי: פעולה נדרשת תוך 24-48 שעות
דחוף: פעולה נדרשת תוך שבוע
רגיל: פעולה נדרשת תוך חודש
מעקב: דורש מעקב מתמשך בלבד

מסמכי מקור לניתוח:
{% for doc in documents %}
---
{{ doc }}
---
{% endfor %}

סעיף: הערכת סיכון ומשמעות מבצעית של {{ target }}
"""),

    "recommendations": Template("""
אתה קצין איסוף מודיעין בכיר עם מומחיות בתכנון משימות SIGINT, HUMINT ו-OSINT.

נתח את המסמכים וכתב המלצות מפורטות ומקצועיות ל"מעקב עתידי" של {{ target }}.

מסגרת המלצות איסוף:

איסוף SIGINT (מודיעין אלקטרוני):
- יירוט תקשורת סלולרית ואינטרנט
- מעקב אחר רשתות חברתיות
- פיענוח הודעות מוצפנות
- מעקב אחר פעילות דיגיטלית

איסוף HUMINT (מודיעין אנושי):
- גיוס מקורות בסביבה הקרובה
- חדירה לארגון או לרשת
- מעקב פיזי ותצפית
- איסוף מקורות פתוחים

איסוף OSINT (מקורות פתוחים):
- מעקב תקשורתי ורשתות חברתיות
- ניתוח פרסומים ומסמכים
- מעקב פעילות כלכלית
- ניתוח תמונות ווידאו

נקודות מעקב קריטיות:
- אירועים ומועדים משמעותיים
- שינויים בדפוסי התנהגות
- קשרים חדשים או חריגים
- רכישות או פעילות חריגה

דוגמת המלצות מצוינות:

המלצות SIGINT בעדיפות גבוהה:
1. יירוט תקשורת: הפעלת מעקב 24/7 על המספר +972-59-xxx-7890 עם דגש על השעות 18:00-23:00
2. פיענוח קודים: תגבור המאמץ לפיענוח ביטויים: "פיקניק", "אורחים מגיעים", "המחסן מלא"
3. מעקב דיגיטלי: חדירה לחשבון Signal הפעיל ומעקב אחר קבוצות Telegram רלוונטיות

המלצות HUMINT בעדיפות גבוהה:
1. גיוס מקור: תפעול מקור בסביבת בית קפה "אל-בהג'ה" לאיסוף מידע על פגישות
2. מעקב פיזי: הצבת צוות מעקב בנקודות המעבר העיקריות ברח' א-שהדא
3. חדירה משפחתית: ניסיון גיוס דרך קשרי משפחה - יוסף חסן (אח) או פאטמה אל-שאמי (בת זוג)

המלצות OSINT בעדיפות בינונית:
1. מעקב כלכלי: ניתוח תנועות כספיות חריגות ורכישות גדולות
2. ניתוח תמונות: איסוף תמונות מהאזור לזיהוי שינויים בתשתיות
3. מעקב תקשורתי: סריקת פרסומים בעיתונות המקומית לאזכורים עקיפים

מטריצת עדיפויות:
עדיפות מקסימלית: איום מידי - תגובה תוך שעות
עדיפות גבוהה: חשיבות מבצעית - תגובה תוך ימים
עדיפות בינונית: השלמת תמונה - תגובה תוך שבועות
עדיפות נמוכה: ידע כללי - תגובה לפי זמינות

לוחות זמנים מומלצים:
מעקב מידי: 24/7 במצבי איום מוגבר
מעקב יומי: בשעות הפעילות העיקריות
מעקב שבועי: לבדיקת דפוסים ארוכי טווח
סקירה חודשית: להערכה מחדש של האיום

מסמכי מקור לניתוח:
{% for doc in documents %}
---
{{ doc }}
---
{% endfor %}

סעיף: המלצות למעקב עתידי של {{ target }}
""")
}

QUERY_CLASSIFICATION_TEMPLATE = Template("""
You are an expert intelligence query classifier with extensive experience in operational intelligence requirements.

Classify intelligence queries to enable optimal retrieval strategy and response generation.

CLASSIFICATION FRAMEWORK:

STRATEGIC
High-level analytical assessments requiring synthesis of multiple information sources.
Characteristics:
- Requests for overall assessments, implications, significance
- Questions about strategic impact and broader consequences
- Leadership-level decision support requirements
- Long-term trend analysis and forecasting

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

Examples:
- "What trends do you see in communication patterns?"
- "How have operational methods evolved over time?"
- "Analyze the network relationships between these individuals"
- "What patterns emerge from recent financial transactions?"

SPECIFIC
Requests for particular facts, details, or granular information requiring precise retrieval.
Characteristics:
- Questions about specific individuals, events, locations, times
- Requests for exact details and factual information
- Verification of particular claims or statements
- Granular evidence and documentation requests

Examples:
- "When did Ahmad meet with the weapons supplier?"
- "What specific weapons were mentioned in the intercept?"
- "Where exactly did the meeting take place?"
- "Who attended the training session on March 15th?"

MIXED
Complex queries requiring multiple analysis levels or ambiguous requests needing clarification.
Characteristics:
- Broad questions requiring both specific facts and analytical assessment
- Ambiguous requests that could fit multiple categories
- Multi-part questions spanning different information types
- General inquiry requiring comprehensive response

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

SECTION_QUERIES: Dict[str, str] = {
    "role_activities": "מה התפקיד הבכיר והאחריות המבצעית של",
    "capabilities_resources": "אילו נשקים כספים ויכולות טכניות יש ל",
    "communication_patterns": "איך מתקשר ומה דפוסי התקשורת של",
    "activity_patterns": "איפה ומתי פעיל ומה דפוסי הפעילות של",
    "network_analysis": "מי הקשרים החשובים ברשת של",
    "key_topics": "מה הנושאים העיקריים והתכניות של",
    "code_words": "אילו קודים ומונחים מוסווים משתמש"
}

SECTION_TITLES: Dict[str, str] = {
    "role_activities": "תפקיד ופעילות עיקרית",
    "capabilities_resources": "יכולות ומשאבים",
    "communication_patterns": "דפוסי תקשורת ושפה",
    "activity_patterns": "דפוסי פעילות",
    "network_analysis": "רשת קשרים",
    "key_topics": "נושאי שיחה מרכזיים",
    "code_words": "מילות מפתח וביטויי קוד"
}

NUMBERED_SECTION_TITLES: Dict[str, str] = {
    "role_activities": "1. תפקיד ופעילות עיקרית",
    "capabilities_resources": "2. יכולות ומשאבים",
    "communication_patterns": "3. דפוסי תקשורת ושפה",
    "activity_patterns": "4. דפוסי פעילות",
    "network_analysis": "5. רשת קשרים",
    "key_topics": "6. נושאי שיחה מרכזיים",
    "code_words": "7. מילות מפתח וביטויי קוד"
}