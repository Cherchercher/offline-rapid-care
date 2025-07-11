"""
AI Prompts Template File
Centralized prompts for various AI tasks in the RapidCare system
"""

# Characteristic Extraction Prompts
CHARACTERISTIC_EXTRACTION_PROMPT = """Analyze this person and provide a structured description in the following JSON format:

{
    "physical_features": {
        "gender": "male/female/unknown",
        "face_shape": "round/oval/square/heart",
        "hair_color": "black/brown/blonde/red/gray/white",
        "hair_length": "short/medium/long",
        "hair_style": "straight/wavy/curly/bald",
        "eye_color": "brown/blue/green/hazel/gray",
        "skin_tone": "light/medium/dark",
        "height": "estimated height in feet and inches",
        "build": "slim/average/stocky/athletic"
    },
    "clothing": {
        "top": "color and type of shirt/jacket",
        "bottom": "color and type of pants/skirt",
        "accessories": "glasses, jewelry, hat, etc."
    },
    "distinctive_features": [
        "any scars, birthmarks, tattoos, piercings, or unique characteristics"
    ],
    "age_range": "estimated age range (e.g., 25-30, 40-45)"
}

Provide only the JSON response, no additional text."""

# Vitals Extraction Prompts
VITALS_EXTRACTION_PROMPT = """Extract vital signs from this medical transcription and return ONLY a JSON object with the following structure:

{
    "heart_rate": <number or null>,
    "bp_sys": <number or null>,
    "bp_dia": <number or null>,
    "resp_rate": <number or null>,
    "o2_sat": <number or null>,
    "temperature": <number or null>,
    "pain_score": <number 0-10 or null>
}

Rules:
- Return ONLY the JSON object, no other text
- Use null for missing values
- Heart rate should be BPM (beats per minute)
- Blood pressure should be systolic/diastolic in mmHg
- Respiratory rate should be breaths per minute
- O2 saturation should be percentage (0-100)
- Temperature should be in Fahrenheit
- Pain score should be 0-10 scale
- If no vitals are mentioned, return all null values"""

# Medical Triage Prompts
MEDICAL_TRIAGE_PROMPT = """MANDATORY OUTPUT FORMAT - You MUST respond in exactly this structure, no exceptions:

**TRIAGE LEVEL:** [RED/YELLOW/GREEN/BLACK]
**REASONING:** [Clear explanation of triage decision based on observed conditions]

**PATIENT INFORMATION:**
- **Approximate Age:** [Estimate age range]
- **Gender:** [Male/Female/Unknown]
- **Mechanism of Injury:** [How the injury occurred - trauma, medical emergency, etc.]
- **Brief Assessment Findings:** [Key observations from the video frames]

**TRIAGE CATEGORY DETAILS:**
- **RED (Immediate):** Life-threatening injuries requiring immediate attention
- **YELLOW (Delayed):** Serious injuries that can wait for treatment  
- **GREEN (Minor):** Minor injuries that can wait or self-treat
- **BLACK (Deceased/Expectant):** Deceased or injuries incompatible with life

**IMMEDIATE ACTIONS:** [Specific steps to take based on triage level]

CRITICAL: You must use the exact format above with the exact section headers. Do not provide additional medical assessment sections or deviate from this structure. Focus on visible injuries, level of consciousness, breathing patterns, bleeding, and overall patient condition."""

# Reunification Search Prompts
REUNIFICATION_SEARCH_PROMPT = """You are a reunification coordinator searching for missing persons. Analyze the provided description and search the database for potential matches.

Focus on:
1. Physical characteristics (age, height, hair color, eye color, distinctive features)
2. Clothing descriptions
3. Location and timing information
4. Family relationships mentioned
5. Medical conditions or special needs

Provide a structured analysis of potential matches with confidence scores and reasoning."""

# Description Parsing Prompts
DESCRIPTION_PARSING_PROMPT = """Parse this missing person description and extract structured characteristics in JSON format:

{
    "physical_features": {
        "gender": "male/female/unknown if mentioned",
        "age_range": "estimated age range",
        "height": "estimated height",
        "hair_color": "hair color if mentioned",
        "eye_color": "eye color if mentioned",
        "build": "body type if mentioned"
    },
    "clothing": {
        "top": "shirt/jacket description",
        "bottom": "pants/skirt description", 
        "accessories": "glasses, jewelry, etc."
    },
    "distinctive_features": [
        "scars, birthmarks, tattoos, piercings, unique characteristics"
    ],
    "location_info": "last seen location if mentioned",
    "family_relationships": "mentioned family members"
}

Extract only what is explicitly mentioned in the description. Use null for missing information."""

# Audio Transcription Prompts
AUDIO_TRANSCRIPTION_PROMPT = "Transcribe this audio accurately, preserving medical terminology and patient information."

MEDICAL_TRANSCRIPTION_PROMPT = "Transcribe this medical audio with high accuracy, preserving all medical terminology, vital signs, and patient assessment details."

# SOAP Notes Prompts
SOAP_SUBJECTIVE_PROMPT = "Transcribe this audio into a structured SOAP subjective note, including patient's chief complaint, history of present illness, and relevant medical history."

SOAP_OBJECTIVE_PROMPT = "Transcribe this audio into a structured SOAP objective note, including vital signs, physical examination findings, and any diagnostic test results."

SOAP_ASSESSMENT_PROMPT = "Transcribe this audio into a structured SOAP assessment note, including differential diagnoses, working diagnosis, and clinical reasoning."

SOAP_PLAN_PROMPT = "Transcribe this audio into a structured SOAP plan note, including treatment plan, medications, follow-up instructions, and disposition."

# General Medical Analysis Prompts
GENERAL_MEDICAL_ANALYSIS_PROMPT = """Analyze this medical content and provide a structured response focusing on:

1. Key medical findings
2. Patient assessment
3. Recommended actions
4. Urgency level
5. Special considerations

Provide clear, actionable medical information suitable for emergency response personnel."""

# Error Handling Prompts
FALLBACK_CHARACTERISTIC_PROMPT = """Extract any identifiable characteristics from this text response. Look for:
- Age mentions
- Physical descriptions
- Clothing details
- Distinctive features
- Any structured information about the person

Return in a simple format with available information."""

# AI Query System Prompts
AI_QUERY_SYSTEM_PROMPT_TEMPLATE = """You are a {role} in an emergency response system with access to a reunification database.

Your task is to analyze the user's query and determine the best search strategy. You can:

1. Search for missing persons
2. Search patients for reunification
3. Find potential matches
4. Get reunification protocols
5. Look up medical notes for context

Respond with a JSON object containing:
{{
    "search_type": "missing_persons|patients|matches|reunification_protocols|medical_notes",
    "search_query": "optimized search query",
    "filters": {{"status": "missing", "type": "missing_person"}},
    "explanation": "why this search type was chosen"
}}

Query: {query}"""

# Transcribe Text System Prompts
TRANSCRIBE_TEXT_SYSTEM_PROMPT_TEMPLATE = """You are a {role} in an emergency response system. 

CRITICAL REQUIREMENTS:
1. ALWAYS provide a triage category (RED, YELLOW, GREEN, BLACK) at the beginning of your response
2. ALWAYS provide clear reasoning for your triage decision
3. ALWAYS provide specific actionable steps for the situation
4. Use medical triage protocols and emergency response procedures

TRIAGE CATEGORIES:
- RED (Immediate): Life-threatening injuries requiring immediate attention
- YELLOW (Delayed): Serious injuries that can wait for treatment
- GREEN (Minor): Minor injuries that can wait or self-treat
- BLACK (Deceased/Expectant): Deceased or injuries incompatible with life

Process this audio transcription and provide medical insights with triage categorization.
If the transcription is unclear, ask for clarification.
Focus on medical terminology, patient information, and emergency details.

Format your response as:
**Triage: [CATEGORY]** **Reasoning:** [Clear explanation] **Action:** [Specific steps]""" 

# Audio Transcription Enhancement Prompt
AUDIO_ENHANCEMENT_PROMPT_TEMPLATE = """You are a {role} in an emergency response system. 
Process this audio transcription and provide medical insights. If the transcription is unclear,
ask for clarification. Focus on medical terminology, patient information, and emergency details.""" 