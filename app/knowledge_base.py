"""
Knowledge Base service — JSON-based biomarker reference + interaction modifiers.
No external dependencies (no ChromaDB, no embeddings).
Loads curated medical data, interaction modifiers, cluster triggers, and priority rules.
Enables keyword search and multi-marker interaction detection.
"""
import json
import os
from app.config import KNOWLEDGE_BASE_DIR


class KnowledgeBaseService:
    def __init__(self):
        self.biomarkers: list[dict] = []
        self.interaction_modifiers: list[dict] = []
        self.cluster_triggers: dict = {}
        self.priority_rules: dict = {}
        self._load_data()
        self._load_interaction_modifiers()

    def _load_data(self):
        """Load biomarker reference data from JSON file."""
        json_path = os.path.join(KNOWLEDGE_BASE_DIR, "biomarker_references.json")
        if not os.path.exists(json_path):
            print(f"[KB] Warning: {json_path} not found. Knowledge base will be empty.")
            return

        with open(json_path, "r", encoding="utf-8") as f:
            self.biomarkers = json.load(f)

        print(f"[KB] Loaded {len(self.biomarkers)} biomarker references from JSON.")

    def _load_interaction_modifiers(self):
        """Load interaction modifiers, cluster triggers, and priority rules."""
        json_path = os.path.join(KNOWLEDGE_BASE_DIR, "interaction_modifiers.json")
        if not os.path.exists(json_path):
            print(f"[KB] Warning: {json_path} not found. Interaction modifiers will be empty.")
            return

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.interaction_modifiers = data.get("interaction_modifiers", [])
        self.cluster_triggers = data.get("cluster_triggers", {})
        self.priority_rules = data.get("priority_rules", {})

        print(
            f"[KB] Loaded {len(self.interaction_modifiers)} interaction modifiers, "
            f"{len(self.cluster_triggers)} cluster trigger groups, "
            f"priority rules: {'yes' if self.priority_rules else 'no'}."
        )

    def detect_interactions(self, classifications: list[dict]) -> list[dict]:
        """
        Detect which interaction modifiers are triggered by the current biomarker data.

        Args:
            classifications: List of classified biomarker results with 'key' and 'status'.

        Returns:
            List of triggered interaction modifier dicts, each with:
              - id, name, description
              - score_modifier (negative number to deduct)
              - affected_cluster
              - priority
              - clinical_significance
              - triggered_recommendations (dict with activity, nutrition, etc.)
        """
        if not self.interaction_modifiers or not classifications:
            return []

        # Build lookup: biomarker_key -> status
        status_map = {}
        for c in classifications:
            key = c.get("key", "")
            status = c.get("status", "normal")
            if key:
                status_map[key] = status

        triggered = []
        for modifier in self.interaction_modifiers:
            conditions = modifier.get("conditions", [])
            operator = modifier.get("operator", "AND")

            if operator == "AND":
                # All conditions must match
                all_match = True
                for cond in conditions:
                    bm_key = cond["biomarker"]
                    required_status = cond["status"]
                    actual_status = status_map.get(bm_key,  "normal")
                    if actual_status != required_status:
                        all_match = False
                        break
                if all_match:
                    triggered.append(modifier)

            elif operator == "OR":
                # At least one condition must match
                for cond in conditions:
                    bm_key = cond["biomarker"]
                    required_status = cond["status"]
                    actual_status = status_map.get(bm_key, "normal")
                    if actual_status == required_status:
                        triggered.append(modifier)
                        break

        # Sort by priority (lower number = higher priority)
        triggered.sort(key=lambda x: x.get("priority", 99))
        return triggered

    def detect_cluster_triggers(self, classifications: list[dict]) -> list[dict]:
        """
        Detect which cluster trigger patterns are active.

        Returns list of dicts with:
          - cluster, pattern, diagnosis, priority
        """
        if not self.cluster_triggers or not classifications:
            return []

        status_map = {}
        for c in classifications:
            key = c.get("key", "")
            status = c.get("status", "normal")
            if key:
                status_map[key] = status

        detected = []
        for cluster_key, cluster_info in self.cluster_triggers.items():
            for tp in cluster_info.get("trigger_patterns", []):
                pattern_text = tp.get("pattern", "")
                # Parse simple pattern: "Low Hb + Low Ferritin"
                if self._pattern_matches(pattern_text, status_map):
                    detected.append({
                        "cluster": cluster_key,
                        "cluster_label": cluster_info.get("description", cluster_key),
                        "pattern": pattern_text,
                        "diagnosis": tp.get("diagnosis", ""),
                        "priority": tp.get("priority", 3),
                    })

        detected.sort(key=lambda x: x.get("priority", 99))
        return detected

    def _pattern_matches(self, pattern_text: str, status_map: dict) -> bool:
        """
        Parse a simple pattern like 'Low Hb + Low Ferritin' or 'High LDL + Low HDL'
        and check if it matches current biomarker statuses.
        """
        # Name to key mapping
        name_to_key = {
            "hb": "hemoglobin",
            "hemoglobin": "hemoglobin",
            "ferritin": "ferritin",
            "b12": "vitamin_b12",
            "d": "vitamin_d",
            "rbc": "rbc_count",
            "glucose": "fasting_glucose",
            "hba1c": "hba1c",
            "tc": "total_cholesterol",
            "ldl": "ldl",
            "hdl": "hdl",
            "tg": "triglycerides",
            "crp": "hs_crp",
            "cpr": "hs_crp",
            "tsh": "tsh",
            "alt": "sgpt_alt",
        }

        # Split on '+'
        parts = [p.strip() for p in pattern_text.split("+")]
        for part in parts:
            part_lower = part.strip().lower()

            # Detect status keyword
            if part_lower.startswith("low "):
                required_status = "low"
                marker_name = part_lower[4:].strip()
            elif part_lower.startswith("high "):
                required_status = "high"
                marker_name = part_lower[5:].strip()
            elif part_lower.startswith("normal "):
                required_status = "normal"
                marker_name = part_lower[7:].strip()
            else:
                # Pattern like "High CRP alone" — check just the keyword
                # Try to extract
                continue

            # Map marker name to key
            bm_key = name_to_key.get(marker_name)
            if not bm_key:
                continue  # Unknown marker in pattern, skip

            actual_status = status_map.get(bm_key, "normal")
            if actual_status != required_status:
                return False

        return True

    def get_interaction_context(self, classifications: list[dict]) -> str:
        """
        Build a context string summarizing all triggered interactions and cluster patterns.
        This is injected into the LLM prompt for better clinical accuracy.
        """
        lines = []

        # Interaction modifiers
        interactions = self.detect_interactions(classifications)
        if interactions:
            lines.append("=== INTERACTION MODIFIERS DETECTED ===")
            for ix in interactions:
                lines.append(
                    f"\n--- {ix['name']} (Priority {ix['priority']}, Score Impact: {ix['score_modifier']} points) ---"
                )
                lines.append(f"Description: {ix['description']}")
                lines.append(f"Clinical Significance: {ix['clinical_significance']}")
                recs = ix.get("triggered_recommendations", {})
                if recs:
                    for cat, items in recs.items():
                        lines.append(f"  {cat.title()}: {'; '.join(items)}")

        # Cluster triggers
        triggers = self.detect_cluster_triggers(classifications)
        if triggers:
            lines.append("\n=== CLUSTER TRIGGER PATTERNS DETECTED ===")
            for t in triggers:
                lines.append(
                    f"  [{t['cluster_label']}] {t['pattern']} → {t['diagnosis']} (Priority {t['priority']})"
                )

        # Priority rules
        if self.priority_rules:
            ordering = self.priority_rules.get("ordering_rules", [])
            if ordering:
                lines.append("\n=== PRIORITY ORDERING RULES ===")
                for rule in ordering:
                    lines.append(f"  • {rule}")

        return "\n".join(lines) if lines else ""

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
        self.interaction_modifiers = []
        self.cluster_triggers = {}
        self.priority_rules = {}
        self._load_data()
        self._load_interaction_modifiers()
        return {
            "status": "reloaded",
            "count": len(self.biomarkers),
            "interactions": len(self.interaction_modifiers),
        }
