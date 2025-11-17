# adjuster_brief_agent.py

import google.generativeai as genai
import json
import os

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-pro")

ADJUSTER_BRIEF_PROMPT = """
You are an Insurance Adjuster Assistant. 
Your task is to convert structured claim intelligence into a clear, factual, and concise adjuster brief. 
Do not fabricate any information. Use only the data provided in the JSON input.

Follow these rules:
1. No hallucinations. If information is missing, write “Not provided.”
2. Maintain a professional, objective tone.
3. Keep paragraphs short and factual.
4. Do not include chain-of-thought; only final conclusions.
5. Do not reference the JSON directly; rewrite it as narrative.
6. The output MUST follow the exact 5-section structure below.

Required Structure:

1. Incident Summary  
2. Evidence Review  
3. Policy & Coverage Assessment  
4. Benchmark & Decision Rationale  
5. Recommended Next Steps  

Input JSON:
{claim_json}

Output:
A professionally written adjuster brief in the 5-section structured format.
"""

def generate_adjuster_brief(claim_json: dict) -> str:
    """Generate an adjuster brief using Gemini given structured claim data."""

    prompt = ADJUSTER_BRIEF_PROMPT.replace("{claim_json}", json.dumps(claim_json, indent=2))

    response = model.generate_content(prompt)

    return response.text
