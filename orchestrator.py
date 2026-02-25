"""
Orchestrator — coordinates the multi-agent research workflow.
Implements the iterative Plan → Retrieve → Analyze → Critique loop.
"""
import json
import time
from datetime import datetime, timezone

from agents import PlannerAgent, RetrieverAgent, AnalyzerAgent, CriticAgent, ReporterAgent
from config import Config


class ResearchOrchestrator:
    """Coordinates the autonomous research pipeline."""

    def __init__(self):
        self.planner = PlannerAgent()
        self.retriever = RetrieverAgent()
        self.analyzer = AnalyzerAgent()
        self.critic = CriticAgent()
        self.reporter = ReporterAgent()
        self.log: list[dict] = []

    def _log_event(self, agent: str, action: str, detail: str = "", data: dict | None = None):
        """Record an event in the research log."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": agent,
            "action": action,
            "detail": detail,
        }
        if data:
            event["data"] = data
        self.log.append(event)

    def run(self, topic: str, progress_callback=None) -> dict:
        """
        Execute the full autonomous research workflow.
        
        Args:
            topic: The research topic to investigate.
            progress_callback: Optional callable(stage, message, data) for live updates.
        
        Returns:
            dict with the full research session results.
        """
        def notify(stage: str, message: str, data: dict | None = None):
            if progress_callback:
                progress_callback(stage, message, data)

        session = {
            "topic": topic,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "iterations": [],
            "final_report": "",
            "status": "running",
        }

        try:
            # ── Phase 1: Planning ─────────────────────────────────────
            notify("planning", "🧠 Planner Agent is decomposing the research topic...")
            self._log_event("Planner", "start", f"Topic: {topic}")

            plan = self.planner.plan(topic)
            self._log_event("Planner", "complete", f"Generated {len(plan.get('research_questions', []))} questions, {len(plan.get('search_queries', []))} queries")
            notify("planning_done", "✅ Research plan created", plan)

            all_papers: dict = {}
            analysis: dict = {}
            critic_eval: dict = {}
            iteration = 0

            while iteration < Config.MAX_ITERATIONS:
                iteration += 1
                iter_data = {"iteration": iteration}
                notify("iteration_start", f"🔄 Starting iteration {iteration}/{Config.MAX_ITERATIONS}")

                # ── Phase 2: Retrieval ────────────────────────────────
                notify("retrieving", f"📚 Retriever Agent is searching arXiv ({len(plan.get('search_queries', []))} queries)...")
                self._log_event("Retriever", "start", f"Iteration {iteration}")

                new_papers = self.retriever.search(plan.get("search_queries", []))
                # Merge new papers with existing ones
                for qid, papers in new_papers.items():
                    if qid in all_papers:
                        existing_ids = {p["arxiv_id"] for p in all_papers[qid]}
                        for p in papers:
                            if p.get("arxiv_id") and p["arxiv_id"] not in existing_ids:
                                all_papers[qid].append(p)
                    else:
                        all_papers[qid] = papers

                total = self.retriever.get_total_paper_count(all_papers)
                self._log_event("Retriever", "complete", f"Total unique papers: {total}")
                notify("retrieving_done", f"✅ Retrieved {total} unique papers", {"total_papers": total})

                # ── Phase 3: Analysis ─────────────────────────────────
                notify("analyzing", "🔬 Analyzer Agent is synthesizing findings...")
                self._log_event("Analyzer", "start", f"Iteration {iteration}")

                analysis = self.analyzer.analyze(all_papers, plan.get("research_questions", []))
                clusters = len(analysis.get("thematic_clusters", []))
                self._log_event("Analyzer", "complete", f"Found {clusters} thematic clusters")
                notify("analyzing_done", f"✅ Identified {clusters} thematic clusters", analysis)

                # ── Phase 4: Critique ─────────────────────────────────
                notify("critiquing", "🧐 Critic Agent is evaluating coverage...")
                self._log_event("Critic", "start", f"Iteration {iteration}")

                critic_eval = self.critic.evaluate(plan, analysis, iteration)
                score = critic_eval.get("overall_coverage_score", 0)
                recommendation = critic_eval.get("recommendation", "accept")
                gaps = critic_eval.get("knowledge_gaps", [])
                self._log_event("Critic", "complete", f"Score: {score}/10, Recommendation: {recommendation}, Gaps: {len(gaps)}")
                notify("critiquing_done", f"✅ Coverage score: {score}/10 — {recommendation.upper()}", critic_eval)

                iter_data.update({
                    "papers_found": total,
                    "clusters": clusters,
                    "coverage_score": score,
                    "recommendation": recommendation,
                    "gaps_found": len(gaps),
                })
                session["iterations"].append(iter_data)

                # ── Check if we should stop ───────────────────────────
                if recommendation == "accept" or score >= Config.MIN_COVERAGE_SCORE:
                    self._log_event("Orchestrator", "stop", f"Accepted at iteration {iteration} with score {score}")
                    notify("iteration_accepted", f"🎯 Research accepted at iteration {iteration}")
                    break

                if iteration < Config.MAX_ITERATIONS:
                    # Refine the plan with gap information
                    notify("refining", "🔄 Planner Agent is refining the search strategy...")
                    gap_descriptions = [g.get("gap", "") for g in gaps if g.get("severity") in ("critical", "moderate")]
                    plan = self.planner.refine_plan(plan, gap_descriptions)
                    notify("refining_done", "✅ Research plan refined with new queries")

            # ── Phase 5: Report Generation ────────────────────────────
            notify("reporting", "📝 Reporter Agent is generating the literature review...")
            self._log_event("Reporter", "start", "Generating final report")

            metadata = {
                "iterations": iteration,
                "total_papers": self.retriever.get_total_paper_count(all_papers),
            }
            report = self.reporter.generate_report(plan, analysis, critic_eval, all_papers, metadata)
            session["final_report"] = report
            self._log_event("Reporter", "complete", f"Report generated ({len(report)} chars)")
            notify("reporting_done", "✅ Literature review generated!")

            # ── Finalize ──────────────────────────────────────────────
            session["status"] = "completed"
            session["completed_at"] = datetime.now(timezone.utc).isoformat()
            session["plan"] = plan
            session["analysis"] = analysis
            session["critic_evaluation"] = critic_eval
            session["papers"] = all_papers
            session["agent_log"] = self.log

            notify("complete", "🎉 Research complete!", {
                "total_papers": metadata["total_papers"],
                "iterations": iteration,
                "coverage_score": critic_eval.get("overall_coverage_score", "N/A"),
            })

        except Exception as exc:
            session["status"] = "error"
            session["error"] = str(exc)
            self._log_event("Orchestrator", "error", str(exc))
            notify("error", f"❌ Error: {str(exc)}")

        return session
