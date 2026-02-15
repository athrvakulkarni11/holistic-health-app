"""
Knowledge Base service using ChromaDB for biomarker medical reference data.
Loads curated medical data and enables semantic search for relevant information.
"""
import json
import os
import chromadb
from app.config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME, KNOWLEDGE_BASE_DIR


class KnowledgeBaseService:
    def __init__(self):
        self.client = None
        self.collection = None
        self._init_client()
        self._initialize()

    def _init_client(self):
        """Initialize ChromaDB client with fallback to in-memory if persistent fails."""
        try:
            self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
            print("[KB] Using PersistentClient (disk-backed).")
        except Exception as e:
            print(f"[KB] PersistentClient failed ({e}), falling back to in-memory client.")
            # Clean up corrupted DB directory if it exists
            import shutil
            if os.path.exists(CHROMA_PERSIST_DIR):
                try:
                    shutil.rmtree(CHROMA_PERSIST_DIR)
                    print("[KB] Removed corrupted chroma_db directory.")
                except Exception:
                    pass
            # Try PersistentClient again with a fresh directory
            try:
                os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
                self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
                print("[KB] Using PersistentClient (fresh directory).")
            except Exception as e2:
                print(f"[KB] PersistentClient retry failed ({e2}), using EphemeralClient.")
                self.client = chromadb.EphemeralClient()
                print("[KB] Using EphemeralClient (in-memory).")

    def _initialize(self):
        """Load biomarker reference data into ChromaDB."""
        self.collection = self.client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        # Only load if collection is empty
        if self.collection.count() == 0:
            self._load_biomarker_data()

    def _load_biomarker_data(self):
        """Parse and load biomarker JSON into ChromaDB as searchable documents."""
        json_path = os.path.join(KNOWLEDGE_BASE_DIR, "biomarker_references.json")
        if not os.path.exists(json_path):
            print(f"[KB] Warning: {json_path} not found. Knowledge base will be empty.")
            return

        with open(json_path, "r", encoding="utf-8") as f:
            biomarkers = json.load(f)

        documents = []
        metadatas = []
        ids = []

        for i, bm in enumerate(biomarkers):
            # Create a rich text document for each biomarker
            doc_text = self._biomarker_to_document(bm)
            documents.append(doc_text)
            metadatas.append({
                "biomarker": bm["biomarker"],
                "category": bm["category"],
                "unit": bm["unit"],
                "normal_low_male": str(bm["normal_range_male"]["low"]),
                "normal_high_male": str(bm["normal_range_male"]["high"]),
                "normal_low_female": str(bm["normal_range_female"]["low"]),
                "normal_high_female": str(bm["normal_range_female"]["high"]),
            })
            ids.append(f"biomarker_{i}_{bm['biomarker'].lower().replace(' ', '_')}")

        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
        print(f"[KB] Loaded {len(documents)} biomarker references into knowledge base.")

    def _biomarker_to_document(self, bm: dict) -> str:
        """Convert a biomarker dict into a searchable text document."""
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

    def search(self, query: str, n_results: int = 5) -> list[dict]:
        """Semantic search the knowledge base."""
        results = self.collection.query(
            query_texts=[query],
            n_results=min(n_results, self.collection.count()),
        )

        output = []
        if results and results["documents"]:
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            ):
                output.append({
                    "content": doc,
                    "metadata": meta,
                    "relevance_score": round(1 - dist, 4),
                })
        return output

    def get_biomarker_info(self, biomarker_name: str) -> dict | None:
        """Get specific biomarker reference data."""
        results = self.collection.query(
            query_texts=[biomarker_name],
            n_results=1,
            where={"biomarker": {"$eq": biomarker_name}} if biomarker_name else None,
        )
        if results and results["documents"] and results["documents"][0]:
            return {
                "content": results["documents"][0][0],
                "metadata": results["metadatas"][0][0],
            }
        return None

    def get_all_biomarkers(self) -> list[str]:
        """Return all biomarker names in the knowledge base."""
        all_data = self.collection.get()
        if all_data and all_data["metadatas"]:
            return [m["biomarker"] for m in all_data["metadatas"]]
        return []

    def reload(self):
        """Force reload the knowledge base."""
        self.client.delete_collection(CHROMA_COLLECTION_NAME)
        self._initialize()
        return {"status": "reloaded", "count": self.collection.count()}
