"""
Critic Agent — evaluates the research coverage completeness, identifies
knowledge gaps, and determines whether another iteration is needed.
"""
from .base import BaseAgent


CRITIC_SYSTEM = """You are a Research Critic Agent. You evaluate the quality and
completeness of a literature review analysis.

Given the research plan (questions) and the analysis results, you must assess
how well the research covers the topic. Output valid JSON:
{
  "overall_coverage_score": 8,
  "dimension_scores": {
    "breadth": 7,
    "depth": 8,
    "recency": 9,
    "methodology_diversity": 6,
    "question_coverage": 8
  },
  "covered_well": ["string — aspect that is well covered"],
  "knowledge_gaps": [
    {
      "gap": "string — description of what is missing",
      "severity": "critical | moderate | minor",
      "suggested_query": "string — arXiv query to fill this gap"
    }
  ],
  "quality_issues": ["string — any quality concerns with the analysis"],
  "recommendation": "accept | iterate",
  "reasoning": "string — explain your assessment"
}

Score each dimension from 1-10. Set recommendation to 'iterate' if
overall_coverage_score < 7 or there are critical gaps.
Be rigorous but fair. A good literature review should cover foundational work,
recent advances, methodologies, applications, and limitations.
"""


class CriticAgent(BaseAgent):
    """Evaluates research coverage and identifies gaps."""

    def evaluate(self, plan: dict, analysis: dict, iteration: int) -> dict:
        """Evaluate the current research analysis against the plan."""
        prompt = (
            f"## Research Plan\n"
            f"Main Topic: {plan.get('main_topic', 'Unknown')}\n"
            f"Research Questions:\n"
            + "\n".join(
                f"- [{q['id']}] {q['question']}"
                for q in plan.get("research_questions", [])
            )
            + f"\n\n## Analysis Results (Iteration {iteration})\n"
            f"Thematic Clusters: {len(analysis.get('thematic_clusters', []))}\n"
            f"Question Coverage:\n"
            + "\n".join(
                f"- [{c.get('question_id', '?')}] {c.get('coverage_level', 'unknown')}: {c.get('summary', 'N/A')[:200]}"
                for c in analysis.get("question_coverage", [])
            )
            + f"\nMethodology Landscape: {analysis.get('methodology_landscape', {})}"
            + f"\nCross-cutting Insights: {len(analysis.get('cross_cutting_insights', []))}"
            + f"\n\nIteration: {iteration}"
            + "\n\nEvaluate the coverage and identify gaps."
        )

        raw = self._call_llm(prompt, system_instruction=CRITIC_SYSTEM)
        parsed = self._parse_json_response(raw)

        if parsed is None:
            return {
                "overall_coverage_score": 5,
                "dimension_scores": {},
                "covered_well": [],
                "knowledge_gaps": [],
                "quality_issues": ["Could not parse critic evaluation."],
                "recommendation": "accept",
                "reasoning": raw,
            }
        return parsed
