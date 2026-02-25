"""
Retriever Agent — searches the arXiv API and retrieves academic papers
matching the research plan's queries.
"""
import time
import urllib.parse
import feedparser
import requests
from .base import BaseAgent
from config import Config


class RetrieverAgent(BaseAgent):
    """Retrieves academic papers from arXiv based on search queries."""

    def search(self, queries: list[dict]) -> dict:
        """
        Execute each search query against the arXiv API.
        Returns a dict mapping query IDs to lists of paper metadata.
        """
        results: dict[str, list[dict]] = {}
        seen_ids: set[str] = set()

        for q in queries:
            qid = q.get("id", "unknown")
            query_text = q.get("query", "")
            papers = self._search_arxiv(query_text)
            unique_papers = []
            for p in papers:
                if p["arxiv_id"] not in seen_ids:
                    seen_ids.add(p["arxiv_id"])
                    unique_papers.append(p)
            results[qid] = unique_papers
            # Respect arXiv rate-limit (3 seconds between requests)
            time.sleep(3)

        return results

    def _search_arxiv(self, query: str) -> list[dict]:
        """Search arXiv and return parsed paper metadata."""
        # Clean the query — feedparser handles Atom XML from arXiv
        params = {
            "search_query": query,
            "start": 0,
            "max_results": Config.ARXIV_MAX_RESULTS,
            "sortBy": Config.ARXIV_SORT_BY,
            "sortOrder": "descending",
        }
        url = f"{Config.ARXIV_API_URL}?{urllib.parse.urlencode(params)}"

        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as exc:
            return [{"error": str(exc), "query": query}]

        feed = feedparser.parse(resp.text)
        papers = []
        for entry in feed.entries:
            arxiv_id = entry.get("id", "").split("/abs/")[-1]
            # Extract categories
            categories = [t.get("term", "") for t in entry.get("tags", [])]

            papers.append(
                {
                    "arxiv_id": arxiv_id,
                    "title": entry.get("title", "").replace("\n", " ").strip(),
                    "authors": [a.get("name", "") for a in entry.get("authors", [])],
                    "abstract": entry.get("summary", "").replace("\n", " ").strip(),
                    "published": entry.get("published", ""),
                    "updated": entry.get("updated", ""),
                    "pdf_url": next(
                        (
                            l["href"]
                            for l in entry.get("links", [])
                            if l.get("type") == "application/pdf"
                        ),
                        "",
                    ),
                    "categories": categories,
                    "primary_category": entry.get("arxiv_primary_category", {}).get(
                        "term", ""
                    ),
                }
            )
        return papers

    def get_total_paper_count(self, results: dict) -> int:
        """Count total unique papers across all queries."""
        return sum(len(papers) for papers in results.values())
