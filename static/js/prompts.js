// Centralized prompts for the frontend
// These should match the prompts in prompts.py

const PROMPTS = {
    VITALS_EXTRACTION: `Extract vital signs from this medical transcription and return ONLY a JSON object with the following structure:

{
  "heart_rate": <number or null>,
  "bp_sys": <number or null>,
  "bp_dia": <number or null>,
  "resp_rate": <number or null>,
  "o2_sat": <number or null>,
  "temperature": <number or null>,
  "pain_score": <number or null>
}

Extract values from the text. If a vital sign is not mentioned, use null. Return ONLY the JSON object, no additional text.`,

    AUDIO_TRANSCRIPTION: "Transcribe this audio accurately, preserving medical terminology and patient information.",

    MEDICAL_TRIAGE: `MANDATORY OUTPUT FORMAT - You MUST respond in exactly this structure, no exceptions:

**Triage: [CATEGORY]** **Reasoning:** [Clear explanation] **Action:** [Specific steps]

Categories:
- Red: Immediate life-threatening conditions requiring immediate intervention
- Yellow: Serious conditions requiring urgent care within 10-60 minutes
- Green: Minor conditions that can wait for care
- Black: Deceased or unsalvageable

Format your response as:
**Triage: [CATEGORY]** **Reasoning:** [Clear explanation] **Action:** [Specific steps]`,
CHARACTERISTIC_EXTRACTION_PROMPT : `Analyze this person and provide a structured description in the following JSON format:

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

Provide only the JSON response, no additional text.`,
    REUNIFICATION_SEARCH: `You are a reunification coordinator searching for missing persons. Analyze the provided description and search the database for potential matches.

Focus on:
1. Physical characteristics (height, build, hair, eyes, distinctive features)
2. Clothing descriptions
3. Age and gender
4. Location and timing
5. Medical conditions or special needs

Provide structured search results with confidence scores.`,

    DESCRIPTION_PARSING: `Parse this missing person description and extract structured characteristics in JSON format:

{
  "physical_features": {
    "height": "estimated height",
    "build": "slim/average/stocky",
    "hair_color": "color",
    "hair_length": "length",
    "eye_color": "color",
    "skin_tone": "light/medium/dark"
  },
  "clothing": {
    "top": "description",
    "bottom": "description",
    "accessories": "description"
  },
  "distinctive_features": "unique characteristics",
  "age_range": "estimated age",
  "gender": "male/female/unknown"
}

Extract what you can from the description. Use "unknown" for missing information.`
};

// Export for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PROMPTS;
} 