"""
Biomarker Analytics Engine -- The core intelligence layer.
Combines Groq LLM, ChromaDB knowledge base, and web search to provide
comprehensive, doctor-grade health analytics and personalized suggestions.

v3 Improvements:
- Inverted score direction: higher = healthier (100 = perfect, 0 = critical)
- Category health scores semantically consistent (100 = all normal, 0 = all abnormal/severe)
- Report-aware dosages: clinical treatment doses, not RDA
- Conservative thyroid language (monitor vs treat)
- Web sources returned for citation display
- Normal categories shown as green/healthy, not inflated
- Accurate marker counts per category
"""
import json
from groq import Groq
from app.config import GROQ_API_KEY, GROQ_MODEL
from app.knowledge_base import KnowledgeBaseService
from app.web_search import WebSearchService


# Biomarker reference ranges for quick classification
BIOMARKER_RANGES = {
    "hemoglobin": {"unit": "g/dL", "male": (13.5, 17.5), "female": (12.0, 15.5), "category": "blood_health"},
    "rbc_count": {"unit": "million cells/mcL", "male": (4.5, 5.5), "female": (4.0, 5.0), "category": "blood_health"},
    "ferritin": {"unit": "ng/mL", "male": (20, 250), "female": (10, 120), "category": "deficiencies"},
    "vitamin_b12": {"unit": "pg/mL", "male": (200, 900), "female": (200, 900), "category": "deficiencies"},
    "vitamin_d": {"unit": "ng/mL", "male": (30, 100), "female": (30, 100), "category": "deficiencies"},
    "fasting_glucose": {"unit": "mg/dL", "male": (70, 100), "female": (70, 100), "category": "metabolic"},
    "hba1c": {"unit": "%", "male": (4.0, 5.6), "female": (4.0, 5.6), "category": "metabolic"},
    "total_cholesterol": {"unit": "mg/dL", "male": (125, 200), "female": (125, 200), "category": "lipids"},
    "ldl": {"unit": "mg/dL", "male": (0, 100), "female": (0, 100), "category": "lipids"},
    "hdl": {"unit": "mg/dL", "male": (40, 100), "female": (50, 100), "category": "lipids"},
    "triglycerides": {"unit": "mg/dL", "male": (0, 150), "female": (0, 150), "category": "lipids"},
    "hs_crp": {"unit": "mg/L", "male": (0, 1.0), "female": (0, 1.0), "category": "inflammation"},
    "tsh": {"unit": "mIU/L", "male": (0.4, 4.0), "female": (0.4, 4.0), "category": "hormonal"},
    "sgpt_alt": {"unit": "U/L", "male": (7, 56), "female": (7, 45), "category": "liver"},
}

# Maps form field keys to biomarker friendly names
BIOMARKER_DISPLAY_NAMES = {
    "hemoglobin": "Hemoglobin",
    "rbc_count": "RBC Count",
    "ferritin": "Ferritin",
    "vitamin_b12": "Vitamin B12",
    "vitamin_d": "Vitamin D (25-OH)",
    "fasting_glucose": "Fasting Glucose",
    "hba1c": "HbA1c",
    "total_cholesterol": "Total Cholesterol",
    "ldl": "LDL",
    "hdl": "HDL",
    "triglycerides": "Triglycerides",
    "hs_crp": "hs-CRP",
    "tsh": "TSH",
    "sgpt_alt": "SGPT / ALT",
}

# Human-readable category names and their risk weights
RISK_CATEGORIES = {
    "metabolic": {"label": "Metabolic / Diabetes Risk", "weight": 1.3, "icon": "fire"},
    "lipids": {"label": "Cardiovascular / Lipids", "weight": 1.2, "icon": "heart-pulse"},
    "deficiencies": {"label": "Nutritional Deficiencies", "weight": 1.0, "icon": "capsules"},
    "inflammation": {"label": "Inflammation", "weight": 1.15, "icon": "shield-virus"},
    "hormonal": {"label": "Hormonal / Thyroid", "weight": 1.1, "icon": "dna"},
    "blood_health": {"label": "Blood Health / Anemia", "weight": 1.0, "icon": "droplet"},
    "liver": {"label": "Liver Function", "weight": 1.0, "icon": "hand-holding-medical"},
}


class BiomarkerAnalyticsEngine:
    def __init__(self):
        try:
            if not GROQ_API_KEY:
                print("[Engine] Warning: GROQ_API_KEY not set. LLM analysis will be unavailable.")
                self.groq_client = None
            else:
                self.groq_client = Groq(api_key=GROQ_API_KEY)
        except Exception as e:
            print(f"[Engine] Error initializing Groq client: {e}")
            self.groq_client = None

        self.kb = KnowledgeBaseService()
        self.web_search = WebSearchService()

    def classify_biomarker(self, key: str, value: float, gender: str) -> dict:
        """Classify a single biomarker value as low, normal, or high."""
        ref = BIOMARKER_RANGES.get(key)
        if not ref:
            return {"status": "unknown", "message": f"No reference for {key}"}

        gender_key = "male" if gender.lower() in ("male", "m") else "female"
        low, high = ref[gender_key]

        if value < low:
            status = "low"
            deviation = round(((low - value) / low) * 100, 1)
        elif value > high:
            status = "high"
            deviation = round(((value - high) / high) * 100, 1)
        else:
            status = "normal"
            deviation = 0.0

        return {
            "biomarker": BIOMARKER_DISPLAY_NAMES.get(key, key),
            "key": key,
            "value": value,
            "unit": ref["unit"],
            "status": status,
            "normal_range": f"{low} - {high}",
            "deviation_percent": deviation,
            "category": ref.get("category", "other"),
        }

    def classify_all(self, biomarkers: dict, gender: str) -> list[dict]:
        """Classify all provided biomarkers."""
        results = []
        for key, value in biomarkers.items():
            if value is not None and value != "":
                try:
                    val = float(value)
                    results.append(self.classify_biomarker(key, val, gender))
                except (ValueError, TypeError):
                    pass
        return results

    def _get_risk_score(self, classifications: list[dict]) -> dict:
        """
        Calculate health score with per-category breakdown.
        
        Scoring direction: HIGHER = HEALTHIER
        - 100/100 = perfect, all markers normal
        - 0/100 = critical, all markers severely abnormal
        
        Category scores follow same convention:
        - 100 = all normal in this category
        - 0 = all severely abnormal
        
        Interaction modifiers are applied when multi-marker patterns are detected.
        """
        if not classifications:
            return {"score": 0, "level": "unknown", "summary": "No data", "category_scores": {}, "triggered_interactions": []}

        total = len(classifications)
        abnormal = [c for c in classifications if c["status"] != "normal"]
        high_deviation = [c for c in abnormal if c["deviation_percent"] > 30]

        # --- Detect interaction modifiers ---
        triggered_interactions = self.kb.detect_interactions(classifications)
        # Build a map: cluster -> total penalty from interactions
        interaction_penalties_by_cluster = {}
        total_interaction_penalty = 0
        for ix in triggered_interactions:
            cluster = ix.get("affected_cluster", "")
            penalty = abs(ix.get("score_modifier", 0))
            interaction_penalties_by_cluster[cluster] = (
                interaction_penalties_by_cluster.get(cluster, 0) + penalty
            )
            total_interaction_penalty += penalty

        # --- Category-level breakdown ---
        category_scores = {}
        total_weighted_penalty = 0
        total_weight = 0

        for cat_key, cat_info in RISK_CATEGORIES.items():
            cat_markers = [c for c in classifications if c.get("category") == cat_key]
            cat_abnormal = [c for c in cat_markers if c["status"] != "normal"]

            if not cat_markers:
                continue

            # Calculate risk score (0-100, higher = worse)
            ratio = len(cat_abnormal) / len(cat_markers)
            avg_deviation = (
                sum(c["deviation_percent"] for c in cat_abnormal) / len(cat_abnormal)
                if cat_abnormal else 0
            )
            severity_factor = min(avg_deviation / 50, 1.0)  # Cap at 1.0

            risk_raw = (ratio * 60 + severity_factor * 40) * cat_info["weight"]
            risk_score = min(100, round(risk_raw))

            # Apply interaction modifier penalties for this cluster
            cluster_interaction_penalty = interaction_penalties_by_cluster.get(cat_key, 0)
            risk_score = min(100, risk_score + cluster_interaction_penalty)

            # INVERT: Health score = 100 - risk (higher = healthier)
            health_score = max(0, 100 - risk_score)

            # Weight contribution to overall score
            cat_weight = cat_info["weight"] * len(cat_markers)
            penalty_contribution = risk_score * cat_weight
            total_weighted_penalty += penalty_contribution
            total_weight += cat_weight

            # Status label for display
            if health_score >= 90:
                status_label = "Healthy"
            elif health_score >= 70:
                status_label = "Mild Concern"
            elif health_score >= 40:
                status_label = "Needs Attention"
            else:
                status_label = "High Risk"

            # Note interaction modifiers that affected this cluster
            cluster_interactions = [
                {"name": ix["name"], "modifier": ix["score_modifier"]}
                for ix in triggered_interactions
                if ix.get("affected_cluster") == cat_key
            ]

            category_scores[cat_key] = {
                "label": cat_info["label"],
                "icon": cat_info["icon"],
                "health_score": health_score,  # 100 = healthy, 0 = critical
                "status_label": status_label,
                "total_markers": len(cat_markers),
                "abnormal_markers": len(cat_abnormal),
                "markers": [
                    {"name": c["biomarker"], "status": c["status"], "deviation": c["deviation_percent"]}
                    for c in cat_markers
                ],
                "interaction_modifiers": cluster_interactions,
            }

        # Overall health score (weighted average of inverted category scores)
        if total_weight > 0:
            overall_risk = total_weighted_penalty / total_weight
            severity_penalty = len(high_deviation) * 2  # Extra penalty for severe deviations
            overall_risk = min(100, overall_risk + severity_penalty)
        else:
            overall_risk = 0

        health_score = max(0, round(100 - overall_risk))

        if health_score >= 85:
            level = "excellent"
        elif health_score >= 70:
            level = "good"
        elif health_score >= 50:
            level = "moderate"
        elif health_score >= 30:
            level = "needs_attention"
        else:
            level = "high_risk"

        return {
            "score": health_score,          # 0-100, higher = healthier
            "risk_score": round(overall_risk),  # 0-100, higher = worse (internal use)
            "level": level,
            "total_markers": total,
            "abnormal_markers": len(abnormal),
            "high_deviation_markers": len(high_deviation),
            "category_scores": category_scores,
            "triggered_interactions": [
                {
                    "id": ix.get("id", ""),
                    "name": ix["name"],
                    "description": ix["description"],
                    "score_modifier": ix["score_modifier"],
                    "affected_cluster": ix.get("affected_cluster", ""),
                    "priority": ix.get("priority", 3),
                    "clinical_significance": ix.get("clinical_significance", ""),
                    "triggered_recommendations": ix.get("triggered_recommendations", {}),
                }
                for ix in triggered_interactions
            ],
        }

    def _gather_kb_context(self, classifications: list[dict]) -> str:
        """Gather relevant knowledge base information for abnormal biomarkers."""
        abnormal = [c for c in classifications if c["status"] != "normal"]
        if not abnormal:
            return "All biomarkers are within normal range."

        context_parts = []
        for c in abnormal:
            biomarker_name = c["biomarker"]
            kb_result = self.kb.get_biomarker_info(biomarker_name)
            if kb_result:
                context_parts.append(
                    f"--- {biomarker_name} (Status: {c['status']}, Value: {c['value']} {c['unit']}, "
                    f"Deviation: {c['deviation_percent']}%) ---\n{kb_result['content']}"
                )
        return "\n\n".join(context_parts) if context_parts else "No knowledge base data available."

    def _gather_web_context(self, classifications: list[dict]) -> tuple:
        """
        Search the web for additional context on abnormal biomarkers.
        Returns (context_text, web_sources_list) for both LLM context and UI display.
        """
        abnormal = [c for c in classifications if c["status"] != "normal"]
        if not abnormal:
            return "", []

        # Search for the top 3 most deviated biomarkers
        sorted_abnormal = sorted(abnormal, key=lambda x: x["deviation_percent"], reverse=True)[:3]

        web_parts = []
        web_sources = []  # For UI display

        for c in sorted_abnormal:
            direction = "high" if c["status"] == "high" else "low"
            results = self.web_search.search_biomarker(c["biomarker"], f"{direction} levels treatment")
            if results:
                snippets = [f"- {r['title']}: {r['body']}" for r in results[:2]]
                web_parts.append(
                    f"--- Web Research: {c['biomarker']} ({direction}) ---\n" + "\n".join(snippets)
                )
                # Collect sources for UI
                for r in results[:2]:
                    web_sources.append({
                        "title": r.get("title", ""),
                        "url": r.get("link", r.get("url", "")),
                        "snippet": r.get("body", ""),
                        "biomarker": c["biomarker"],
                        "direction": direction,
                    })

        context_text = "\n\n".join(web_parts) if web_parts else ""
        return context_text, web_sources

    def analyze(self, user_profile: dict, biomarkers: dict) -> dict:
        """
        Full analysis pipeline:
        1. Classify all biomarkers
        2. Calculate health score with category breakdown + interaction modifiers
        3. Gather knowledge base context + interaction context
        4. Gather web search context + sources
        5. Generate LLM-powered analysis with Groq
        """
        gender = user_profile.get("gender", "male")
        age = user_profile.get("age", 40)
        height = user_profile.get("height", "")
        weight = user_profile.get("weight", "")

        # Step 1 & 2: Classify and score (interaction modifiers applied inside)
        classifications = self.classify_all(biomarkers, gender)
        risk_score = self._get_risk_score(classifications)

        # Step 3: Gather context (KB + interaction modifiers)
        kb_context = self._gather_kb_context(classifications)
        interaction_context = self.kb.get_interaction_context(classifications)
        if interaction_context:
            kb_context = kb_context + "\n\n" + interaction_context

        # Step 4: Web search context
        web_context, web_sources = self._gather_web_context(classifications)

        # Step 5: LLM Analysis
        llm_analysis = self._generate_llm_analysis(
            user_profile, classifications, risk_score, kb_context, web_context
        )

        return {
            "user_profile": {
                "age": age,
                "gender": gender,
                "height": height,
                "weight": weight,
            },
            "classifications": classifications,
            "risk_score": risk_score,
            "analysis": llm_analysis,
            "web_sources": web_sources,
        }

    def _generate_llm_analysis(
        self,
        user_profile: dict,
        classifications: list[dict],
        risk_score: dict,
        kb_context: str,
        web_context: str,
    ) -> dict:
        """Generate comprehensive health analysis using Groq LLM."""

        # Build the biomarker summary grouped by category
        category_summaries = {}
        for c in classifications:
            cat = c.get("category", "other")
            if cat not in category_summaries:
                category_summaries[cat] = []
            category_summaries[cat].append(
                f"  - {c['biomarker']}: {c['value']} {c['unit']} (Status: {c['status'].upper()}, "
                f"Normal: {c['normal_range']}, Deviation: {c['deviation_percent']}%)"
            )

        biomarker_summary = ""
        for cat, markers in category_summaries.items():
            cat_label = RISK_CATEGORIES.get(cat, {}).get("label", cat)
            biomarker_summary += f"\n[{cat_label}]\n" + "\n".join(markers) + "\n"

        # Build category health score breakdown for the LLM
        cat_breakdown = ""
        for cat_key, cs in risk_score.get("category_scores", {}).items():
            cat_breakdown += (
                f"  - {cs['label']}: {cs['health_score']}/100 health "
                f"({cs['abnormal_markers']}/{cs['total_markers']} abnormal) - {cs['status_label']}\n"
            )

        # Count abnormals accurately per category for the summary
        abnormal_by_cat = {}
        for c in classifications:
            if c["status"] != "normal":
                cat = RISK_CATEGORIES.get(c.get("category"), {}).get("label", c.get("category", "Other"))
                if cat not in abnormal_by_cat:
                    abnormal_by_cat[cat] = []
                abnormal_by_cat[cat].append(c["biomarker"])
        abnormal_summary = "; ".join(
            f"{cat}: {', '.join(names)}" for cat, names in abnormal_by_cat.items()
        )

        system_prompt = """You are a clinical-grade health analytics AI. You analyze biomarker reports with the precision of an experienced physician.

CRITICAL RULES FOR MEDICAL ACCURACY:
1. Use PRECISE medical terminology:
   - Fasting glucose 100-125 mg/dL AND/OR HbA1c 5.7-6.4% = "Prediabetes" (NOT "diabetes")
   - Fasting glucose >= 126 mg/dL AND/OR HbA1c >= 6.5% = "Type 2 Diabetes"
   - TSH 4.0-10.0 with normal Free T4 = "Subclinical hypothyroidism" (NOT "hypothyroidism")
   - TSH > 10.0 or low Free T4 = "Overt hypothyroidism"
   - hs-CRP 1.0-3.0 mg/L = "Moderate cardiovascular risk", > 3.0 = "High cardiovascular risk"
2. NEVER miss any abnormal biomarker. Every HIGH or LOW value MUST appear in key_findings.
3. Include ALL organ systems: thyroid, liver, blood, metabolic, lipids, inflammation.
4. When values suggest a condition, NAME the condition explicitly.

SUPPLEMENT DOSAGE RULES:
- DO NOT suggest direct medicine or supplement quantities or dosages to the user.
- Recommend the name of the supplement or treatment needed based on the deficiency, but explicitly advise the user to consult a healthcare provider for the appropriate dosage.

THYROID LANGUAGE RULES:
- For subclinical hypothyroidism (TSH 4-10, normal FT4): Recommend "monitoring and evaluation" NOT "starting thyroid replacement therapy"
- Say: "Consult healthcare provider to evaluate whether continued monitoring or treatment initiation is appropriate"
- Many mild TSH elevations are observed first, not immediately treated

HEALTH SCORE CONVENTION:
- Health Score uses 0-100 where HIGHER = HEALTHIER
- 100 = perfect health, all markers normal
- 0 = critical, all markers severely abnormal
- Category health scores follow the same convention


DISCLAIMER AND SAFETY RULES:
- Include a clear disclaimer field stating that this is an AI analysis and not a substitute for professional medical advice.
- If any values are Critical/Panic values (e.g., Glucose < 50 or > 400, Hemoglobin < 7, Troponin high), add an IMMEDIATE action to "Seek emergency medical attention".
- Maintain a supportive, professional, and objective tone. Avoid alarmist language unless there is an immediate life-threatening risk.

Respond ONLY with valid JSON in this EXACT structure:
{
  "summary": "A 3-4 sentence clinical summary. Mention the health score (X/100) and what it means. List the affected systems by name (e.g., 'Abnormalities were detected across blood health, nutritional, metabolic, cardiovascular, inflammatory, and hormonal systems'). Be specific about conditions. Example: 'Findings are consistent with iron-deficiency anemia, prediabetes (per ADA criteria), mixed dyslipidemia, and subclinical hypothyroidism.'",
  "key_findings": [
    {
      "biomarker": "name",
      "status": "low/high/normal",
      "severity": "mild/moderate/severe",
      "explanation": "Precise clinical interpretation with exact value vs reference range. Name the condition.",
      "concern_level": 1-5
    }
  ],
  "health_risks": [
    {
      "risk": "Named clinical risk",
      "likelihood": "low/moderate/high",
      "explanation": "Which specific biomarkers contribute and why. Cross-reference related markers.",
      "preventive_actions": ["specific action 1", "specific action 2"]
    }
  ],
  "priority_actions": [
    {
      "priority": 1,
      "action": "Clear, specific action (DO NOT provide exact dosages)",
      "category": "deficiency/metabolic/cardiovascular/hormonal/inflammation/monitoring",
      "urgency": "immediate/within_2_weeks/within_1_month/within_3_months",
      "rationale": "Why this is prioritized at this level"
    }
  ],
  "activity_recommendations": [
    {
      "recommendation": "Specific exercise or physical activity advice",
      "intensity": "light/moderate/vigorous",
      "frequency": "How often (e.g., '30 mins daily', '3x/week')",
      "reason": "Why this activity is recommended, linking to biomarker findings",
      "precaution": "Any safety considerations based on current health status"
    }
  ],
  "dietary_recommendations": [
    {
      "category": "Foods to Include/Avoid",
      "items": ["item1", "item2"],
      "reason": "Why, linking to specific biomarker findings"
    }
  ],
  "supplement_suggestions": [
    {
      "supplement": "Name",
      "dosage": "State 'Consult provider for dosage' (Do NOT suggest direct quantity)",
      "reason": "Why suggested, referencing the specific abnormal value",
      "duration": "How long to take it before retest",
      "caution": "Any warnings or interactions"
    }
  ],
  "lifestyle_recommendations": [
    {
      "recommendation": "Specific actionable advice",
      "priority": "high/medium/low",
      "expected_impact": "What improvement to expect and in what timeframe"
    }
  ],
  "alternate_healing_recommendations": [
    {
      "system": "Ayurveda/Yoga/Traditional Chinese Medicine/Naturopathy",
      "recommendation": "Specific practice or remedy name",
      "description": "Brief explanation of how this practice helps",
      "target_condition": "Which biomarker issue this addresses",
      "caution": "Important safety considerations or contraindications"
    }
  ],
  "follow_up_tests": [
    {
      "test": "Test name",
      "reason": "Why recommended based on findings",
      "urgency": "routine/soon/urgent",
      "timeframe": "When to get tested (e.g., '6 weeks', '3 months')"
    }
  ],
  "score_explanation": {
    "health_score": "N/100 (where higher = healthier)",
    "interpretation": "What this score means. E.g., 'A score of 8/100 indicates significant health concerns across multiple systems requiring medical attention. The score is primarily driven down by...'",
    "interaction_modifiers_applied": ["List any multi-marker interaction patterns detected and their score impact"],
    "top_contributors": [
      {"category": "category name", "impact": "-N points", "reason": "why this category reduces the score"}
    ]
  },
  "positive_findings": ["Positive aspects - mention specific normal biomarkers by name"],
  "disclaimer": "Medical disclaimer text"
}"""

        health_score = risk_score.get("score", 0)

        user_prompt = f"""Analyze the following health profile and biomarker data with clinical precision.

**Patient Profile:**
- Age: {user_profile.get('age', 'Not provided')} years
- Gender: {user_profile.get('gender', 'Not provided')}
- Diet Preference: {user_profile.get('diet_preference', 'Not provided')}
- Height: {user_profile.get('height', 'Not provided')} cm
- Weight: {user_profile.get('weight', 'Not provided')} kg

**Biomarker Results (grouped by category):**
{biomarker_summary}

**Health Score:** {health_score}/100 (higher = healthier)
Level: {risk_score['level']}
Abnormal markers: {risk_score['abnormal_markers']} out of {risk_score['total_markers']} tested

**Category Health Scores (higher = healthier):**
{cat_breakdown if cat_breakdown else 'No category breakdown available.'}

**Abnormal Markers by System:**
{abnormal_summary if abnormal_summary else 'None'}

**Medical Knowledge Base Context:**
{kb_context}

**Latest Web/Clinical Research:**
{web_context if web_context else 'No additional web research available.'}

IMPORTANT INSTRUCTIONS:
1. Do NOT skip any abnormal biomarker. Every HIGH or LOW marker MUST be addressed in key_findings.
2. Use PRECISE medical terminology (prediabetes vs diabetes, subclinical vs overt hypothyroidism).
3. For supplement_suggestions and priority_actions: DO NOT suggest direct medicine quantities or dosages. Tell the user to consult their healthcare provider for appropriate dosage. Also, tailor dietary_recommendations strictly according to the Patient Profile's Diet Preference (e.g., if veg, give vegetarian food sources only; if non-veg, include meat/fish options).
4. For thyroid: if TSH is mildly elevated with normal T4/T3, recommend "monitoring and evaluation" not "starting replacement therapy."
5. In priority_actions, order from most urgent to least. Number them 1, 2, 3, etc.
6. In score_explanation, explain what the health score of {health_score}/100 means and which categories contribute most to reducing it. If interaction modifiers were detected, mention them.
7. Cross-reference related markers (e.g., low hemoglobin + low ferritin = iron-deficiency anemia pattern). The knowledge base may already provide detected patterns — use them.
8. In the summary, mention the specific systems affected and the health score.
9. For activity_recommendations: Suggest specific exercises appropriate for the patient's conditions. Consider limitations from deficiencies (e.g., avoid high-intensity if anemic).
10. For alternate_healing_recommendations: Include Ayurvedic herbs/remedies, Yoga asanas/pranayama, and other traditional healing practices. Each must link to a specific biomarker finding. Include safety cautions.
11. If the knowledge base provides INTERACTION MODIFIERS or CLUSTER TRIGGERS, prioritize those findings and incorporate their recommendations into your response."""


        if not self.groq_client:
            return {
                "summary": "LLM Analysis unavailable (Missing API Key). However, basic biomarker classification is provided.",
                "key_findings": [],
                "health_risks": [],
                "priority_actions": [],
                "score_explanation": {},
                "error": "GROQ_API_KEY environment variable is missing."
            }

        try:
            response = self.groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,  # Lower for more clinical precision
                max_tokens=6000,  # More tokens for comprehensive analysis
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except json.JSONDecodeError:
            return {
                "summary": content if content else "Analysis could not be parsed.",
                "error": "Response was not valid JSON",
            }
        except Exception as e:
            return {
                "summary": f"Analysis failed: {str(e)}",
                "error": str(e),
            }
