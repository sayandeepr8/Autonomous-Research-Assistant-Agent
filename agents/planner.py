"""
Planner Agent — decomposes a broad research topic into structured sub-questions
and search queries for arXiv.
"""
from .base import BaseAgent


PLANNER_SYSTEM = """You are a Research Planning Agent. Your role is to take a broad
research topic and decompose it into a structured research plan.

You must output valid JSON with the following schema:
{
  "main_topic": "string — the refined main topic",
  "research_questions": [
    {
      "id": "Q1",
      "question": "string — a specific research question",
      "category": "string — e.g. 'foundational', 'methodology', 'application', 'limitation', 'future_direction'",
      "priority": "high | medium | low"
    }
  ],
  "search_queries": [
    {
      "id": "S1",
      "query": "string — an arXiv search query (use arXiv query syntax)",
      "targets_questions": ["Q1", "Q2"],
      "rationale": "string — why this query is needed"
    }
  ],
  "scope_notes": "string — any scope boundaries or clarifications"
}

Generate 4-6 research questions and 3-5 search queries. Be specific and academic.
Use proper arXiv query syntax (e.g., ti:\"transformer\" AND abs:\"attention\").
"""


class PlannerAgent(BaseAgent):
    """Decomposes a research topic into sub-questions and search queries."""

    def plan(self, topic: str) -> dict:
        """Generate a structured research plan for the given topic."""
        prompt = f"Create a comprehensive research plan for the following topic:\n\n{topic}"
        raw = self._call_llm(prompt, system_instruction=PLANNER_SYSTEM)
        parsed = self._parse_json_response(raw)
        if parsed is None:
            return {
                "main_topic": topic,
                "research_questions": [],
                "search_queries": [],
                "scope_notes": "Failed to generate structured plan.",
                "_raw": raw,
            }
        return parsed

    def refine_plan(self, original_plan: dict, gaps: list[str]) -> dict:
        """Refine the research plan based on identified knowledge gaps."""
        prompt = (
            "You previously generated the following research plan:\n"
            f"```json\n{__import__('json').dumps(original_plan, indent=2)}\n```\n\n"
            "The Critic Agent identified the following knowledge gaps:\n"
            + "\n".join(f"- {g}" for g in gaps)
            + "\n\nGenerate additional search queries to fill these gaps. "
            "Return the COMPLETE updated plan (with new queries appended)."
        )
        raw = self._call_llm(prompt, system_instruction=PLANNER_SYSTEM)
        parsed = self._parse_json_response(raw)
        return parsed if parsed else original_plan
