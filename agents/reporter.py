"""
Reporter Agent — generates a polished, structured literature review report
from the analysis results.
"""
from .base import BaseAgent


REPORTER_SYSTEM = """You are a Research Report Generator Agent. You take the
complete research analysis and produce a structured, publication-quality
literature review in Markdown.

The report MUST follow this structure:

# Literature Review: {topic}

## Executive Summary
(3-4 sentence overview of the research landscape)

## 1. Introduction
(Context, motivation, scope of the review)

## 2. Methodology
(How papers were retrieved, how many, from which sources)

## 3. Thematic Analysis
### 3.1 Theme Name
(For each thematic cluster, discuss the papers and findings)

## 4. Research Question Coverage
(Map findings to each research question)

## 5. Methodological Landscape
(Dominant and emerging methods in the field)

## 6. Timeline & Trends
(How the field has evolved)

## 7. Knowledge Gaps & Future Directions
(What is missing, what should be studied next)

## 8. Conclusion
(Summary of key takeaways)

## References
(List all cited papers with full metadata)

Write in an academic but accessible style. Be specific and reference papers
by their titles and authors. Make the report comprehensive and insightful.
"""


class ReporterAgent(BaseAgent):
    """Generates structured literature review reports."""

    def generate_report(
        self,
        plan: dict,
        analysis: dict,
        critic_eval: dict,
        papers: dict,
        metadata: dict,
    ) -> str:
        """Generate a comprehensive literature review report."""
        # Flatten and deduplicate papers
        all_papers = []
        seen = set()
        for qid, paper_list in papers.items():
            for p in paper_list:
                if "error" not in p and p["arxiv_id"] not in seen:
                    seen.add(p["arxiv_id"])
                    all_papers.append(p)

        papers_ref = "\n".join(
            f"- [{p['arxiv_id']}] {', '.join(p['authors'][:3])}. "
            f"\"{p['title']}\". arXiv:{p['arxiv_id']}, {p['published'][:10]}."
            for p in all_papers
        )

        import json

        prompt = (
            f"## Topic: {plan.get('main_topic', 'Research Topic')}\n\n"
            f"## Research Plan\n```json\n{json.dumps(plan, indent=2)}\n```\n\n"
            f"## Analysis\n```json\n{json.dumps(analysis, indent=2)}\n```\n\n"
            f"## Critic Evaluation\n```json\n{json.dumps(critic_eval, indent=2)}\n```\n\n"
            f"## Papers Retrieved ({len(all_papers)} total)\n{papers_ref}\n\n"
            f"## Metadata\n"
            f"- Total iterations: {metadata.get('iterations', 1)}\n"
            f"- Total papers found: {metadata.get('total_papers', len(all_papers))}\n"
            f"- Final coverage score: {critic_eval.get('overall_coverage_score', 'N/A')}/10\n\n"
            "Generate the full literature review report in Markdown."
        )

        return self._call_llm(prompt, system_instruction=REPORTER_SYSTEM)
