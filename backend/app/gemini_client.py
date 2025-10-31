import os
import json
from typing import Any, Dict
import google.generativeai as genai

# Placeholder for actual Gemini API client integration. Keeping separate module allows swapping SDKs.


def call_gemini(prompt: str, response_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call Gemini with structured output (JSON mode) enforcing the provided schema.
    Returns parsed JSON response.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set")
    
    genai.configure(api_key=api_key)
    
    # Try with response_schema first (newer API), fallback if not supported
    # Use gemini-2.5-flash (stable version supporting generateContent)
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": response_schema,
            }
        )
        response = model.generate_content(prompt)
    except Exception as e:
        # Fallback: Try without response_schema and just ask for JSON in prompt
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={
                "temperature": 0.1,  # Low temperature for consistent JSON
            }
        )
        enhanced_prompt = f"{prompt}\n\nYou MUST respond with ONLY valid JSON (no markdown, no explanation) matching this schema:\n{json.dumps(response_schema, indent=2)}"
        response = model.generate_content(enhanced_prompt)
    
    # Parse JSON response
    try:
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini returned invalid JSON: {e}\nResponse: {response.text[:500]}") from e

