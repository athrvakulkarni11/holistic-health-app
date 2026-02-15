"""
Web Search service using SerpAPI (Google Search) for real-time medical information retrieval.
Provides up-to-date research, guidelines, and health information to augment
the static knowledge base. Uses Google Search via SerpAPI for highly accurate results.
"""
import os
import json
from app.config import SERPAPI_KEY


class WebSearchService:
    def __init__(self):
        self.api_key = SERPAPI_KEY
        if not self.api_key:
            print("[WebSearch] Warning: SERPAPI_KEY not set. Web search will be unavailable.")

    def _serpapi_search(self, query: str, num: int = 5) -> list[dict]:
        """Execute a search query using SerpAPI Google Search."""
        if not self.api_key:
            print("[WebSearch] Skipping search — no API key.")
            return []

        try:
            import requests
            params = {
                "engine": "google",
                "q": query,
                "api_key": self.api_key,
                "num": num,
                "hl": "en",
                "gl": "us",
            }
            response = requests.get("https://serpapi.com/search", params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            results = []
            # Parse organic results
            for r in data.get("organic_results", [])[:num]:
                results.append({
                    "title": r.get("title", ""),
                    "body": r.get("snippet", ""),
                    "url": r.get("link", ""),
                    "source": r.get("source", ""),
                    "position": r.get("position", 0),
                })

            # Also include knowledge graph if available (often has medical summaries)
            kg = data.get("knowledge_graph", {})
            if kg and kg.get("description"):
                results.insert(0, {
                    "title": kg.get("title", "Knowledge Graph"),
                    "body": kg.get("description", ""),
                    "url": kg.get("source", {}).get("link", "") if isinstance(kg.get("source"), dict) else "",
                    "source": "Google Knowledge Graph",
                    "position": 0,
                })

            # Include answer box if available
            answer_box = data.get("answer_box", {})
            if answer_box and answer_box.get("snippet"):
                results.insert(0, {
                    "title": answer_box.get("title", "Featured Snippet"),
                    "body": answer_box.get("snippet", ""),
                    "url": answer_box.get("link", ""),
                    "source": "Google Featured Snippet",
                    "position": 0,
                })

            return results

        except Exception as e:
            print(f"[WebSearch] SerpAPI error: {e}")
            return []

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """
        Search the web for health-related information.
        Automatically appends medical context to improve result quality.
        """
        medical_query = f"{query} medical health research peer reviewed"
        return self._serpapi_search(medical_query, num=max_results)

    def search_biomarker(self, biomarker: str, context: str = "") -> list[dict]:
        """
        Targeted search for a specific biomarker with optional context
        (e.g., 'high', 'low', 'treatment').
        """
        query = f"{biomarker} biomarker {context} latest research guidelines 2025 site:ncbi.nlm.nih.gov OR site:mayoclinic.org OR site:who.int"
        return self._serpapi_search(query, num=5)

    def search_health_condition(self, condition: str) -> list[dict]:
        """Search for a health condition and its management."""
        query = f"{condition} causes symptoms treatment management site:mayoclinic.org OR site:ncbi.nlm.nih.gov OR site:webmd.com"
        return self._serpapi_search(query, num=5)

    def search_supplement_interaction(self, supplements: list[str]) -> list[dict]:
        """Search for interactions between supplements or medications."""
        query = f"{' '.join(supplements)} supplement interaction safety evidence-based"
        return self._serpapi_search(query, num=5)

    def search_general(self, query: str) -> list[dict]:
        """General health search for chat-based queries."""
        query = f"{query} health medical evidence-based"
        return self._serpapi_search(query, num=5)
