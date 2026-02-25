"""
Base Agent class providing shared Gemini integration for all agents.
"""
import json
import re
from google import genai
from config import Config


class BaseAgent:
    """Base class for all research agents with shared AI capabilities."""

    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.model = Config.GEMINI_MODEL

    def _call_llm(self, prompt: str, system_instruction: str = "") -> str:
        """Call Gemini LLM with the given prompt and optional system instruction."""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_instruction or None,
                    temperature=0.4,
                ),
            )
            return response.text.strip()
        except Exception as e:
            return f"[LLM Error]: {str(e)}"

    def _parse_json_response(self, text: str) -> dict | list | None:
        """Extract and parse JSON from an LLM response that may contain markdown fences."""
        # Try to find JSON inside ```json ... ``` blocks first
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
        candidate = match.group(1).strip() if match else text.strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Last resort: find the first { or [ and try from there
            for i, ch in enumerate(candidate):
                if ch in "{[":
                    try:
                        return json.loads(candidate[i:])
                    except json.JSONDecodeError:
                        continue
            return None
