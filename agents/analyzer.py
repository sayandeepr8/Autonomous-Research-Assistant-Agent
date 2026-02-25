"""
Analyzer Agent — synthesizes retrieved papers into thematic clusters,
extracts key findings, and maps papers to research questions.
"""
import json
from .base import BaseAgent


ANALYZER_SYSTEM = """You are a Research Analysis Agent. You receive a set of academic
papers (title + abstract) and a list of research questions.

Your job is to analyze the papers and produce a structured analysis. Output valid JSON:
{
  "thematic_clusters": [
    {
      "theme": "string — cluster theme name",
      "description": "string — what this theme covers",
      "paper_ids": ["arxiv_id_1", "arxiv_id_2"],
      "key_findings": ["string — finding 1", "string — finding 2"]
    }
  ],
  "question_coverage": [
    {
      "question_id": "Q1",
      "question_text": "string",
      "coverage_level": "well_covered | partially_covered | not_covered",
      "supporting_papers": ["arxiv_id_1"],
      "summary": "string — how the papers address this question"
    }
  ],
  "methodology_landscape": {
    "dominant_methods": ["string"],
    "emerging_methods": ["string"],
    "comparison_notes": "string"
  },
  "timeline_trends": "string — how the field has evolved based on publication dates",
  "cross_cutting_insights": ["string — insight that spans multiple clusters"]
}

Be thorough, academic, and evidence-based. Reference specific papers by their arxiv_id.
"""


class AnalyzerAgent(BaseAgent):
    """Analyzes and synthesizes retrieved papers."""

    def analyze(self, papers: dict, research_questions: list[dict]) -> dict:
        """Perform thematic analysis of papers against research questions."""
        # Flatten papers for the prompt
        all_papers = []
        for qid, paper_list in papers.items():
            for p in paper_list:
                if "error" not in p:
                    all_papers.append(p)

        # Deduplicate by arxiv_id
        seen = set()
        unique = []
        for p in all_papers:
            if p["arxiv_id"] not in seen:
                seen.add(p["arxiv_id"])
                unique.append(p)

        papers_text = "\n\n".join(
            f"[{p['arxiv_id']}] \"{p['title']}\"\n"
            f"Authors: {', '.join(p['authors'][:3])}{'...' if len(p['authors']) > 3 else ''}\n"
            f"Published: {p['published'][:10]}\n"
            f"Categories: {', '.join(p['categories'][:3])}\n"
            f"Abstract: {p['abstract'][:500]}"
            for p in unique
        )

        questions_text = "\n".join(
            f"- [{q['id']}] {q['question']} (category: {q.get('category', 'general')}, priority: {q.get('priority', 'medium')})"
            for q in research_questions
        )

        prompt = (
            f"## Papers Retrieved ({len(unique)} total)\n\n{papers_text}\n\n"
            f"## Research Questions\n\n{questions_text}\n\n"
            "Analyze these papers and produce the structured analysis."
        )

        raw = self._call_llm(prompt, system_instruction=ANALYZER_SYSTEM)
        parsed = self._parse_json_response(raw)

        if parsed is None:
            return {
                "thematic_clusters": [],
                "question_coverage": [],
                "methodology_landscape": {},
                "timeline_trends": "Analysis could not be parsed.",
                "cross_cutting_insights": [],
                "_raw": raw,
            }
        return parsed
