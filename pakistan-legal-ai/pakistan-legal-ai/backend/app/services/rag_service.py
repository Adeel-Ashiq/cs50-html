import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.models.schemas import (
    ConstitutionResult, ActResult, JudgmentResult, 
    LegalArgument, QueryResponse
)


class LegalRAGService:
    def __init__(self):
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self.documents_meta: Dict[str, Dict] = {}
        self.is_ready = False

    def initialize(self):
        """Load models and build vector store from sample data."""
        print("🔄 Loading embedding model...")
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        
        print("🔄 Initializing ChromaDB (in-memory for demo)...")
        self.chroma_client = chromadb.Client()  # In-memory for reliability
        
        sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=settings.EMBEDDING_MODEL
        )
        
        self.collection = self.chroma_client.create_collection(
            name="pakistan_legal",
            embedding_function=sentence_transformer_ef,
            metadata={"hnsw:space": "cosine"}
        )
        print("🆕 Created new in-memory collection")
        self._load_and_index_data()
        
        # Always load metadata for response building
        self._load_metadata()
        self.is_ready = True
        print(f"✅ RAG Service ready. Documents in collection: {self.collection.count()}")

    def _load_metadata(self):
        """Load all JSON data into memory for rich responses."""
        data_dir = settings.SAMPLE_DATA_DIR
        
        for filename in ["constitution.json", "acts.json", "judgments.json"]:
            filepath = data_dir / filename
            if filepath.exists():
                with open(filepath, "r", encoding="utf-8") as f:
                    items = json.load(f)
                    for item in items:
                        self.documents_meta[item["id"]] = item

    def _load_and_index_data(self):
        """Index all sample documents into ChromaDB."""
        data_dir = settings.SAMPLE_DATA_DIR
        ids, documents, metadatas = [], [], []

        # Constitution
        with open(data_dir / "constitution.json", "r", encoding="utf-8") as f:
            for item in json.load(f):
                ids.append(item["id"])
                text = f"{item['title']}. {item['text']}"
                documents.append(text)
                metadatas.append({
                    "type": "constitution",
                    "title": item["title"],
                    "source": item.get("source", "")
                })

        # Acts
        with open(data_dir / "acts.json", "r", encoding="utf-8") as f:
            for item in json.load(f):
                ids.append(item["id"])
                text = f"{item['act_name']} {item['section']}: {item['title']}. {item['text']}"
                documents.append(text)
                metadatas.append({
                    "type": "act",
                    "act_name": item["act_name"],
                    "section": item["section"],
                    "title": item["title"],
                    "source": item.get("source", "")
                })

        # Judgments
        with open(data_dir / "judgments.json", "r", encoding="utf-8") as f:
            for item in json.load(f):
                ids.append(item["id"])
                holdings = " ".join(item.get("key_holdings", []))
                text = (
                    f"Case: {item['case_name']} ({item['citation']}). "
                    f"Court: {item['court']} ({item['year']}). "
                    f"Summary: {item['summary']} "
                    f"Key Holdings: {holdings}"
                )
                documents.append(text)
                metadatas.append({
                    "type": "judgment",
                    "case_name": item["case_name"],
                    "citation": item["citation"],
                    "court": item["court"],
                    "year": str(item["year"]),
                    "source": item.get("source", "")
                })

        if ids:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            print(f"✅ Indexed {len(ids)} documents")

    def search(self, query: str, top_k: int = 6) -> QueryResponse:
        """Main search + structured response generation."""
        if not self.is_ready:
            raise RuntimeError("RAG Service not initialized")

        # Query expansion for better Urdu/English mixed queries
        expanded_query = self._expand_query(query)

        results = self.collection.query(
            query_texts=[expanded_query],
            n_results=min(top_k * 2, 20),  # get more then filter
            include=["documents", "metadatas", "distances"]
        )

        constitution_articles = []
        relevant_acts = []
        similar_judgments = []

        if results and results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                meta = results["metadatas"][0][i]
                distance = results["distances"][0][i]
                score = round(1 - distance, 4)  # convert distance to similarity
                full_meta = self.documents_meta.get(doc_id, {})

                if meta["type"] == "constitution" and len(constitution_articles) < 3:
                    constitution_articles.append(ConstitutionResult(
                        id=doc_id,
                        title=full_meta.get("title", meta.get("title", "")),
                        text=full_meta.get("text", ""),
                        source=full_meta.get("source", ""),
                        score=score
                    ))
                elif meta["type"] == "act" and len(relevant_acts) < 5:
                    relevant_acts.append(ActResult(
                        id=doc_id,
                        act_name=full_meta.get("act_name", meta.get("act_name", "")),
                        section=full_meta.get("section", meta.get("section", "")),
                        title=full_meta.get("title", meta.get("title", "")),
                        text=full_meta.get("text", ""),
                        source=full_meta.get("source", ""),
                        score=score
                    ))
                elif meta["type"] == "judgment" and len(similar_judgments) < 4:
                    similar_judgments.append(JudgmentResult(
                        id=doc_id,
                        case_name=full_meta.get("case_name", ""),
                        citation=full_meta.get("citation", ""),
                        court=full_meta.get("court", ""),
                        year=full_meta.get("year", 0),
                        judges=full_meta.get("judges", []),
                        summary=full_meta.get("summary", ""),
                        key_holdings=full_meta.get("key_holdings", []),
                        relevant_acts=full_meta.get("relevant_acts", []),
                        source=full_meta.get("source", ""),
                        score=score
                    ))

        # Generate suggested legal arguments (rule-based + template for demo)
        suggested_arguments = self._generate_arguments(query, constitution_articles, relevant_acts, similar_judgments)

        return QueryResponse(
            query=query,
            constitution_articles=constitution_articles,
            relevant_acts=relevant_acts,
            similar_judgments=similar_judgments,
            suggested_arguments=suggested_arguments
        )

    def _expand_query(self, query: str) -> str:
        """Simple keyword expansion for better retrieval on common Pakistani legal topics."""
        q = query.lower()
        expansions = []

        if any(w in q for w in ["warasat", "inheritance", "virasat", "tarka", "hissa", "share"]):
            expansions.append("inheritance succession Muslim Family Laws Ordinance Section 4 legal heirs")
        if any(w in q for w in ["zameen", "land", "property", "jaidad", "immovable"]):
            expansions.append("land property Transfer of Property Act Land Revenue Act mutation ownership")
        if any(w in q for w in ["bhai", "brother", "behn", "sister", "family"]):
            expansions.append("co-sharer joint owners partition family dispute")
        if any(w in q for w in ["gift", "hiba", "hiba", "donation"]):
            expansions.append("oral gift hiba declaration acceptance delivery of possession")
        if any(w in q for w in ["mutation", "intiqal", "fard"]):
            expansions.append("revenue record mutation presumption of truth Section 42 Land Revenue Act")

        if expansions:
            return query + " " + " ".join(expansions)
        return query

    def _generate_arguments(
        self, 
        query: str, 
        articles: List[ConstitutionResult], 
        acts: List[ActResult], 
        judgments: List[JudgmentResult]
    ) -> List[LegalArgument]:
        """Generate possible legal arguments based on retrieved context (template-based for reliability)."""
        arguments = []
        q_lower = query.lower()

        # Argument 1: Inheritance / Warasat
        if any(w in q_lower for w in ["warasat", "inheritance", "virasat", "hissa", "share", "tarka"]):
            refs = []
            for a in acts:
                if "Muslim Family" in a.act_name or "Section 4" in a.section:
                    refs.append(f"{a.act_name} {a.section}")
            for j in judgments:
                if j.citation:
                    refs.append(j.citation)
            arguments.append(LegalArgument(
                title="Claim of Legal Share under Islamic Law of Inheritance",
                description=(
                    "All legal heirs (including sisters/daughters) are entitled to their Quranic shares "
                    "from the date of death of the propositus. Any alleged oral gift, family settlement "
                    "or relinquishment must be strictly proved. Children of a predeceased son/daughter "
                    "are protected under Section 4 of the Muslim Family Laws Ordinance, 1961."
                ),
                supporting_references=refs[:5] or ["Muslim Family Laws Ordinance, 1961 Section 4"]
            ))

        # Argument 2: Property / Land Rights
        if any(w in q_lower for w in ["zameen", "land", "property", "jaidad", "mutation", "intiqal"]):
            refs = []
            for a in acts:
                if "Land Revenue" in a.act_name or "Transfer of Property" in a.act_name:
                    refs.append(f"{a.act_name} {a.section}")
            for art in articles:
                if "23" in art.title or "24" in art.title:
                    refs.append(art.title)
            arguments.append(LegalArgument(
                title="Protection of Property Rights & Challenge to Mutation",
                description=(
                    "Right to acquire, hold and dispose of property is a fundamental right under "
                    "Article 23 of the Constitution. No person can be deprived of property except "
                    "in accordance with law (Article 24). Entries in revenue record have presumption "
                    "of truth under Section 42 of the Land Revenue Act but the presumption is rebuttable. "
                    "Mutation is not a document of title."
                ),
                supporting_references=refs[:5] or ["Article 23 & 24 Constitution", "Land Revenue Act Section 42"]
            ))

        # Argument 3: Co-sharer / Partition
        if any(w in q_lower for w in ["bhai", "brother", "joint", "co-sharer", "hissa", "partition"]):
            refs = [j.citation for j in judgments if j.citation][:3]
            arguments.append(LegalArgument(
                title="Rights of Co-sharers and Remedy of Partition",
                description=(
                    "One co-sharer cannot claim exclusive ownership against other co-sharers without "
                    "partition. Exclusive possession by one co-sharer does not automatically amount to "
                    "ouster. The proper remedy is a suit for partition and separate possession. "
                    "A co-sharer in possession is not a trespasser vis-à-vis other co-sharers."
                ),
                supporting_references=refs or ["2012 SCMR 987", "Transfer of Property Act principles"]
            ))

        # Argument 4: Burden of Proof
        arguments.append(LegalArgument(
            title="Burden of Proof & Evidentiary Standards",
            description=(
                "Under Article 117 of the Qanun-e-Shahadat Order, 1984, the burden of proof lies on "
                "the person who asserts a fact. In case of alleged gift (hiba), the beneficiary must "
                "prove declaration, acceptance and delivery of possession. Long-standing entries in "
                "revenue record shift the burden to the person challenging them."
            ),
            supporting_references=["Qanun-e-Shahadat Order, 1984 Article 117", "Land Revenue Act Section 42"]
        ))

        # Argument 5: Constitutional Remedy
        if articles:
            arguments.append(LegalArgument(
                title="Constitutional Jurisdiction under Article 199",
                description=(
                    "If no other adequate remedy is available, the High Court under Article 199 of the "
                    "Constitution can issue directions to revenue authorities or declare actions taken "
                    "without lawful authority as illegal. This is particularly useful against arbitrary "
                    "mutation cancellations or refusal to enter inheritance mutation."
                ),
                supporting_references=["Article 199 Constitution of Pakistan"]
            ))

        return arguments[:5]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "ready": self.is_ready,
            "total_documents": self.collection.count() if self.collection else 0,
            "metadata_loaded": len(self.documents_meta)
        }


# Singleton
rag_service = LegalRAGService()
