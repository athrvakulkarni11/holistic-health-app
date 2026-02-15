"""
Knowledge Base service — simple JSON-based biomarker reference lookup.
No external dependencies (no ChromaDB, no embeddings).
Loads curated medical data and enables keyword search for relevant information.
"""
import json
import os
from app.config import KNOWLEDGE_BASE_DIR


class KnowledgeBaseService:
    def __init__(self):
        self.biomarkers: list[dict] = []
        self._load_data()

    def _load_data(self):
        """Load biomarker reference data from JSON file."""
        json_path = os.path.join(KNOWLEDGE_BASE_DIR, "biomarker_references.json")
        if not os.path.exists(json_path):
            print(f"[KB] Warning: {json_path} not found. Knowledge base will be empty.")
            return

        with open(json_path, "r", encoding="utf-8") as f:
            self.biomarkers = json.load(f)

        print(f"[KB] Loaded {len(self.biomarkers)} biomarker references from JSON.")

    def _biomarker_to_document(self, bm: dict) -> str:
        """Convert a biomarker dict into a readable text document."""
        sections = [
            f"Biomarker: {bm['biomarker']}",
            f"Category: {bm['category']}",
            f"Unit: {bm['unit']}",
            f"Description: {bm['description']}",
            f"Normal Range (Male): {bm['normal_range_male']['low']} - {bm['normal_range_male']['high']} {bm['unit']}",
            f"Normal Range (Female): {bm['normal_range_female']['low']} - {bm['normal_range_female']['high']} {bm['unit']}",
            f"Critical Low: {bm['critical_low']} {bm['unit']}",
            f"Critical High: {bm['critical_high']} {bm['unit']}",
            f"Causes of Low Values: {', '.join(bm['low_causes'])}",
            f"Causes of High Values: {', '.join(bm['high_causes'])}",
            f"Symptoms of Low Values: {', '.join(bm['low_symptoms'])}",
            f"Symptoms of High Values: {', '.join(bm['high_symptoms'])}",
            f"Dietary Recommendations (Low): {', '.join(bm['dietary_recommendations_low'])}",
            f"Dietary Recommendations (High): {', '.join(bm['dietary_recommendations_high'])}",
            f"Lifestyle Recommendations: {', '.join(bm['lifestyle_recommendations'])}",
            f"Related Biomarkers: {', '.join(bm['related_biomarkers'])}",
        ]
        return "\n".join(sections)

    def _relevance_score(self, query: str, bm: dict) -> float:
        """Simple keyword-based relevance scoring."""
        query_lower = query.lower()
        query_words = query_lower.split()
        score = 0.0

        # Direct biomarker name match (highest weight)
        bm_name = bm["biomarker"].lower()
        if bm_name in query_lower or query_lower in bm_name:
            score += 10.0

        # Category match
        if bm["category"].lower() in query_lower:
            score += 5.0

        # Word overlap with biomarker name, description, causes, symptoms
        searchable_text = " ".join([
            bm["biomarker"],
            bm["category"],
            bm.get("description", ""),
            " ".join(bm.get("low_causes", [])),
            " ".join(bm.get("high_causes", [])),
            " ".join(bm.get("low_symptoms", [])),
            " ".join(bm.get("high_symptoms", [])),
            " ".join(bm.get("related_biomarkers", [])),
        ]).lower()

        for word in query_words:
            if len(word) > 2 and word in searchable_text:
                score += 1.0

        return score

    def search(self, query: str, n_results: int = 5) -> list[dict]:
        """Keyword-based search of the knowledge base."""
        if not self.biomarkers:
            return []

        scored = []
        for bm in self.biomarkers:
            score = self._relevance_score(query, bm)
            if score > 0:
                scored.append((score, bm))

        # Sort by relevance, return top N
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, bm in scored[:n_results]:
            results.append({
                "content": self._biomarker_to_document(bm),
                "metadata": {
                    "biomarker": bm["biomarker"],
                    "category": bm["category"],
                    "unit": bm["unit"],
                },
                "relevance_score": round(min(score / 10.0, 1.0), 4),
            })
        return results

    def get_biomarker_info(self, biomarker_name: str) -> dict | None:
        """Get specific biomarker reference data by name."""
        for bm in self.biomarkers:
            if bm["biomarker"].lower() == biomarker_name.lower():
                return {
                    "content": self._biomarker_to_document(bm),
                    "metadata": {
                        "biomarker": bm["biomarker"],
                        "category": bm["category"],
                        "unit": bm["unit"],
                    },
                }
        # Fallback: partial match
        for bm in self.biomarkers:
            if biomarker_name.lower() in bm["biomarker"].lower():
                return {
                    "content": self._biomarker_to_document(bm),
                    "metadata": {
                        "biomarker": bm["biomarker"],
                        "category": bm["category"],
                        "unit": bm["unit"],
                    },
                }
        return None

    def get_all_biomarkers(self) -> list[str]:
        """Return all biomarker names in the knowledge base."""
        return [bm["biomarker"] for bm in self.biomarkers]

    def reload(self):
        """Force reload the knowledge base from JSON."""
        self.biomarkers = []
        self._load_data()
        return {"status": "reloaded", "count": len(self.biomarkers)}
