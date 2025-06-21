"""
Stage 3: Hierarchical Neo4j + ColBERT retrieval system with tree navigation.

Stores and queries complete digest tree structure enabling:
- Level-specific retrieval (strategic/pattern/specific queries)
- Hierarchical context enhancement
- Parent-child relationship traversal
- Multi-level semantic + graph-based ranking
"""
import uuid
import logging
from pathlib import Path
from typing import Dict, List, LiteralString, Optional, Any
import torch
import numpy as np
from tqdm import tqdm
from pylate import models
from neo4j import GraphDatabase
from opentelemetry import trace

from src.utils.config import QUERY_CLASSIFICATION_TEMPLATE
from src.core.digest_layer import DigestTree, QueryLevel
from src.utils.utils import chat_completion, format_fact_for_retrieval

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class RetrievalIndex:
    """
    Hierarchical Neo4j + ColBERT retrieval system with tree navigation.

    Stores complete digest tree structure and enables intelligent query routing
    based on query classification and tree level optimization.
    """

    def __init__(
            self,
            db_root: Path,
            neo4j_uri: str = "bolt://localhost:7687",
            neo4j_user: str = "neo4j",
            neo4j_password: str = "password"
    ) -> None:
        """
        Initialize hierarchical Neo4j + ColBERT retrieval system.

        Args:
            db_root: Root directory for ColBERT embeddings cache
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        with tracer.start_as_current_span("init_hierarchical_retrieval") as span:
            self.db_root = db_root
            self.db_root.mkdir(exist_ok=True, parents=True)
            span.set_attribute("db.path", str(db_root))

            self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            self._initialize_hierarchical_schema()

            self.model = models.ColBERT(
                model_name_or_path="lightonai/colbertv2.0"
            )
            span.set_attribute("model.name", "lightonai/colbertv2.0")

            self.documents = []
            self.document_embeddings = []
            self.doc_id_to_neo4j_id = {}
            self.tree_structure: Optional[DigestTree] = None

            span.set_attribute("storage.type", "hierarchical_neo4j+colbert")

    def _initialize_hierarchical_schema(self) -> None:
        """Create Neo4j schema for hierarchical tree storage and querying."""
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE")
            session.run("CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)")
            session.run("CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)")

            session.run("CREATE CONSTRAINT doc_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE")
            session.run("CREATE INDEX doc_level IF NOT EXISTS FOR (d:Document) ON (d.level)")
            session.run("CREATE INDEX doc_confidence IF NOT EXISTS FOR (d:Document) ON (d.confidence)")
            session.run("CREATE INDEX doc_tree_position IF NOT EXISTS FOR (d:Document) ON (d.tree_position)")

    def add_documents(self, digest_tree: DigestTree) -> None:
        """
        Add complete digest tree to hierarchical Neo4j + ColBERT index.

        Args:
            digest_tree: Complete hierarchical digest tree structure
        """
        with tracer.start_as_current_span("add_hierarchical_documents") as span:
            self.documents = []
            self.document_embeddings = []
            self.doc_id_to_neo4j_id = {}
            self.tree_structure = digest_tree

            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")

                self._add_tree_level(session, "root", [digest_tree.root], {0: []})
                self._add_tree_level(session, "branch", digest_tree.branches, digest_tree.branch_leaf_mapping)
                self._add_tree_level(session, "leaf", digest_tree.leafs, digest_tree.leaf_fact_mapping)
                self._add_tree_level(session, "fact", [format_fact_for_retrieval(f) for f in digest_tree.facts],
                                     {i: [i] for i in range(len(digest_tree.facts))})

                self._create_hierarchy_relationships(session)

            span.set_attribute("documents.added", len(self.documents))
            span.set_attribute("tree.levels", 4)
            span.set_attribute("tree.facts", len(digest_tree.facts))
            span.set_attribute("tree.leafs", len(digest_tree.leafs))
            span.set_attribute("tree.branches", len(digest_tree.branches))
            logger.info(f"Added hierarchical tree with {len(self.documents)} documents to Neo4j+ColBERT")

    def _add_tree_level(self, session, level: str, texts: List[str], mapping: Dict[int, List[int]]) -> None:
        """Add documents for a specific tree level."""
        for i, text in enumerate(texts):
            doc_id = f"{level}_{i:04d}"
            neo4j_id = f"neo4j_{level}_{i:04d}_{uuid.uuid4().hex[:8]}"

            self.documents.append({"id": doc_id, "text": text})
            self.doc_id_to_neo4j_id[doc_id] = neo4j_id

            tree_position = mapping.get(i, [])

            session.run("""
                CREATE (d:Document {
                    id: $neo4j_id,
                    doc_id: $doc_id,
                    text: $text,
                    level: $level,
                    tree_position: $tree_position,
                    level_index: $level_index,
                    confidence: $confidence,
                    created: datetime()
                })
            """, {
                "neo4j_id": neo4j_id,
                "doc_id": doc_id,
                "text": text,
                "level": level,
                "tree_position": tree_position,
                "level_index": i,
                "confidence": 1.0 if level == "root" else 0.8
            })

            if level == "fact" and self.tree_structure:
                fact = self.tree_structure.facts[i]
                self._create_entities_and_relationships(session, fact, neo4j_id)

    def _create_hierarchy_relationships(self, session) -> None:
        """Create parent-child relationships in the tree hierarchy."""
        if not self.tree_structure:
            return

        for branch_id, leaf_indices in self.tree_structure.branch_leaf_mapping.items():
            for leaf_id in leaf_indices:
                session.run("""
                    MATCH (branch:Document {level: 'branch', level_index: $branch_id})
                    MATCH (leaf:Document {level: 'leaf', level_index: $leaf_id})
                    CREATE (leaf)-[:SUMMARIZED_BY]->(branch)
                """, {"branch_id": branch_id, "leaf_id": leaf_id})

        for leaf_id, fact_indices in self.tree_structure.leaf_fact_mapping.items():
            for fact_id in fact_indices:
                session.run("""
                    MATCH (leaf:Document {level: 'leaf', level_index: $leaf_id})
                    MATCH (fact:Document {level: 'fact', level_index: $fact_id})
                    CREATE (fact)-[:SUMMARIZED_BY]->(leaf)
                """, {"leaf_id": leaf_id, "fact_id": fact_id})

        if self.tree_structure.branches:
            session.run("""
                MATCH (root:Document {level: 'root'})
                MATCH (branch:Document {level: 'branch'})
                CREATE (branch)-[:SUMMARIZED_BY]->(root)
            """)

    @staticmethod
    def _create_entities_and_relationships(session, fact: Dict[str, Any], doc_neo4j_id: str) -> None:
        """Create entity nodes and relationships from facts."""
        entities = []
        if fact.get('who', '').lower() != 'unknown':
            entities.append(("Person", fact['who']))
        if fact.get('where', '').lower() != 'unknown':
            entities.append(("Location", fact['where']))

        entity_ids = []
        for entity_type, entity_name in entities:
            entity_id = f"{entity_type}_{entity_name}".replace(" ", "_").lower()

            session.run("""
                MERGE (e:Entity {id: $entity_id})
                ON CREATE SET e.name = $name, 
                             e.type = $type, 
                             e.created = datetime(),
                             e.mention_count = 1
                ON MATCH SET e.last_seen = datetime(),
                            e.mention_count = e.mention_count + 1
            """, {
                "entity_id": entity_id,
                "name": entity_name,
                "type": entity_type
            })

            session.run("""
                MATCH (d:Document {id: $doc_id})
                WITH d
                MATCH (e:Entity {id: $entity_id})
                MERGE (d)-[:MENTIONS]->(e)
            """, {"doc_id": doc_neo4j_id, "entity_id": entity_id})

            entity_ids.append(entity_id)

        if len(entity_ids) >= 2:
            for i in range(len(entity_ids)):
                for j in range(i + 1, len(entity_ids)):
                    session.run("""
                        MATCH (e1:Entity {id: $entity1})
                        WITH e1
                        MATCH (e2:Entity {id: $entity2})
                        MERGE (e1)-[r:CO_OCCURS]-(e2)
                        ON CREATE SET r.first_seen = datetime(), r.co_occurrence_count = 1
                        ON MATCH SET r.last_seen = datetime(), 
                                    r.co_occurrence_count = r.co_occurrence_count + 1
                    """, {"entity1": entity_ids[i], "entity2": entity_ids[j]})

    def build_index(self) -> None:
        """Build ColBERT embeddings index for hierarchical late interaction retrieval."""
        with tracer.start_as_current_span("build_hierarchical_index") as span:
            if not self.documents:
                logger.warning("No documents to index")
                span.set_attribute("documents.count", 0)
                return

            corpus = [doc["text"] for doc in self.documents]
            span.set_attribute("documents.count", len(corpus))

            logger.info("Encoding hierarchical tree with ColBERT for late interaction...")

            with tqdm(total=len(corpus), desc="Encoding hierarchical documents") as pbar:
                self.document_embeddings = self.model.encode(
                    corpus,
                    batch_size=16,
                    is_query=False,
                    show_progress_bar=True
                )
                pbar.update(len(corpus))

            span.set_attribute("index.built", True)
            span.set_attribute("embeddings.count", len(self.document_embeddings))
            logger.info("Built hierarchical ColBERT embeddings index")

    def retrieve(self, query: str, k: int = 20) -> List[str]:
        """
        Retrieve relevant documents using hierarchical tree navigation.

        Args:
            query: Query string
            k: Number of documents to retrieve

        Returns:
            List of retrieved document texts with hierarchical context
        """
        with tracer.start_as_current_span("hierarchical_retrieve") as span:
            span.set_attribute("query", query)
            span.set_attribute("k", k)

            try:
                query_level = self.classify_query_level(query)
                span.set_attribute("query.level", query_level.value)

                if query_level == QueryLevel.STRATEGIC:
                    results = self._query_levels(query, ["root", "branch"], k)
                elif query_level == QueryLevel.PATTERN:
                    results = self._query_levels(query, ["branch", "leaf"], k)
                elif query_level == QueryLevel.SPECIFIC:
                    results = self._query_levels(query, ["leaf", "fact"], k)
                else:
                    results = self._query_all_levels(query, k)

                span.set_attribute("documents.retrieved", len(results))
                span.set_attribute("retrieval.success", True)
                logger.info(f"Retrieved {len(results)} documents for {query_level.value} query: {query}")
                return results

            except Exception as e:
                logger.error(f"Hierarchical retrieval failed: {e}")
                span.set_attribute("error", str(e))
                span.set_attribute("retrieval.success", False)

                try:
                    fallback_docs = [doc["text"] for doc in self.documents[:k]]
                    span.set_attribute("fallback.used", True)
                    span.set_attribute("fallback.documents", len(fallback_docs))
                    return fallback_docs
                except Exception as fallback_e:
                    logger.error(f"Fallback retrieval also failed: {fallback_e}")
                    span.set_attribute("fallback.error", str(fallback_e))
                    return []

    @staticmethod
    def classify_query_level(query: str) -> QueryLevel:
        """
        Classify query using LLM to determine optimal tree level for retrieval.

        Args:
            query: Query string to classify

        Returns:
            QueryLevel enum indicating optimal retrieval strategy
        """
        with tracer.start_as_current_span("classify_query_level") as span:
            span.set_attribute("query", query)
            prompt = QUERY_CLASSIFICATION_TEMPLATE.render(query=query)
            messages = [{"role": "user", "content": prompt}]
            response = chat_completion(
                messages,
                max_tokens=10,
                temperature=0.1,
                operation_name="query_classification",
                use_premium=False
            )
            classification = response.strip().upper()
            span.set_attribute("llm_classification", classification)

            if classification == "STRATEGIC":
                return QueryLevel.STRATEGIC
            elif classification == "PATTERN":
                return QueryLevel.PATTERN
            elif classification == "SPECIFIC":
                return QueryLevel.SPECIFIC
            else:
                return QueryLevel.MIXED

    def _query_levels(self, query: str, levels: List[str], k: int) -> List[str]:
        """Query specific tree levels with level-appropriate boosting."""
        colbert_results = self._colbert_retrieve_by_levels(query, levels, k * 2)
        enhanced_results = self._hierarchical_enhance_results(query, colbert_results, k)
        return enhanced_results

    def _query_all_levels(self, query: str, k: int) -> List[str]:
        """Query across all tree levels with hierarchical boosting."""
        colbert_results = self._colbert_retrieve(query, k * 3)
        enhanced_results = self._hierarchical_enhance_results(query, colbert_results, k)
        return enhanced_results

    def _colbert_retrieve_by_levels(self, query: str, levels: List[str], k: int) -> List[Dict[str, Any]]:
        """Retrieve documents using ColBERT filtering by specific tree levels."""
        if not self.document_embeddings or not self.documents:
            return []

        query_embeddings = self.model.encode([query], is_query=True, show_progress_bar=False)
        query_embedding = query_embeddings[0]

        scores = []
        for i, doc_emb in enumerate(self.document_embeddings):
            doc_level = self.documents[i]["id"].split("_")[0]
            if doc_level not in levels:
                continue

            doc_score = self._safe_colbert_similarity(query_embedding, doc_emb)

            scores.append({
                "doc_index": i,
                "score": doc_score,
                "doc_id": self.documents[i]["id"],
                "text": self.documents[i]["text"],
                "level": doc_level
            })

        scores.sort(key=lambda x: x["score"], reverse=True)
        return scores[:k]

    def _colbert_retrieve(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Retrieve documents using ColBERT across all levels."""
        if not self.document_embeddings or not self.documents:
            return []

        query_embeddings = self.model.encode([query], is_query=True, show_progress_bar=False)
        query_embedding = query_embeddings[0]

        scores = []
        for i, doc_emb in enumerate(self.document_embeddings):
            doc_score = self._safe_colbert_similarity(query_embedding, doc_emb)

            doc_level = self.documents[i]["id"].split("_")[0]
            scores.append({
                "doc_index": i,
                "score": doc_score,
                "doc_id": self.documents[i]["id"],
                "text": self.documents[i]["text"],
                "level": doc_level
            })

        scores.sort(key=lambda x: x["score"], reverse=True)
        return scores[:k]

    @staticmethod
    def _safe_colbert_similarity(query_embedding, doc_embedding):
        """Calculate ColBERT late-interaction similarity with fallback."""
        try:
            if isinstance(query_embedding, np.ndarray):
                query_embedding = torch.from_numpy(query_embedding)
            if isinstance(doc_embedding, np.ndarray):
                doc_embedding = torch.from_numpy(doc_embedding)

            if query_embedding.device != doc_embedding.device:
                doc_embedding = doc_embedding.to(query_embedding.device)

            if len(query_embedding.shape) == 1:
                query_embedding = query_embedding.unsqueeze(0)
            if len(doc_embedding.shape) == 1:
                doc_embedding = doc_embedding.unsqueeze(0)

            similarity_matrix = torch.matmul(query_embedding, doc_embedding.transpose(-2, -1))
            max_sim_per_query_token = torch.max(similarity_matrix, dim=-1)[0]
            total_similarity = torch.sum(max_sim_per_query_token)

            return float(total_similarity.item())

        except Exception as e:
            logger.warning(f"ColBERT similarity calculation failed: {e}, using cosine fallback")
            try:
                if isinstance(query_embedding, np.ndarray):
                    query_embedding = torch.from_numpy(query_embedding)
                if isinstance(doc_embedding, np.ndarray):
                    doc_embedding = torch.from_numpy(doc_embedding)

                query_flat = query_embedding.flatten()
                doc_flat = doc_embedding.flatten()

                if query_flat.device != doc_flat.device:
                    doc_flat = doc_flat.to(query_flat.device)

                similarity = torch.nn.functional.cosine_similarity(query_flat.unsqueeze(0), doc_flat.unsqueeze(0))
                return float(similarity.item())
            except Exception:
                return 0.0

    def _hierarchical_enhance_results(self, query: str, colbert_results: List[Dict], k: int) -> List[str]:
        """Enhance ColBERT results using hierarchical tree relationships and context."""
        if not colbert_results:
            return []

        enhanced_results = []

        try:
            with self.driver.session() as session:
                for result in colbert_results:
                    doc_id = result["doc_id"]
                    neo4j_id = self.doc_id_to_neo4j_id.get(doc_id)

                    if neo4j_id:
                        context_query: LiteralString = """
                        MATCH (d:Document {id: $doc_id})
                        OPTIONAL MATCH (d)-[:SUMMARIZED_BY]->(parent:Document)
                        OPTIONAL MATCH (child:Document)-[:SUMMARIZED_BY]->(d)
                        OPTIONAL MATCH (d)-[:MENTIONS]->(e:Entity)
                        OPTIONAL MATCH (e)-[:CO_OCCURS]-(related:Entity)
                        RETURN d.level as level,
                               parent.text as parent_context,
                               collect(DISTINCT child.text)[0..3] as child_contexts,
                               collect(DISTINCT e.name)[0..5] as entities,
                               collect(DISTINCT related.name)[0..3] as related_entities
                        """

                        context = session.run(context_query, {"doc_id": neo4j_id}).single()

                        if context:
                            level = context["level"]
                            boosted_score = result["score"]

                            level_boost = {
                                "root": 1.3,
                                "branch": 1.2,
                                "leaf": 1.1,
                                "fact": 1.0
                            }.get(level, 1.0)

                            query_terms = set(query.lower().split())
                            entities = context.get("entities", []) or []
                            entity_boost = sum(0.1 for entity in entities
                                               if any(term in entity.lower() for term in query_terms))

                            final_score = boosted_score * level_boost + entity_boost

                            enhanced_text = result["text"]
                            if context.get("parent_context") and level in ["leaf", "fact"]:
                                enhanced_text = f"CONTEXT: {context['parent_context'][:200]}...\n\n{enhanced_text}"

                            enhanced_results.append({
                                "text": enhanced_text,
                                "score": final_score,
                                "level": level,
                                "entities": entities,
                                "context": context
                            })
                    else:
                        enhanced_results.append({
                            "text": result["text"],
                            "score": result["score"],
                            "level": result.get("level", "unknown"),
                            "entities": [],
                            "context": {}
                        })

                enhanced_results.sort(key=lambda x: x["score"], reverse=True)

                return [result["text"] for result in enhanced_results[:k]]

        except Exception as e:
            logger.warning(f"Hierarchical enhancement failed, falling back to ColBERT results: {e}")
            return [result["text"] for result in colbert_results[:k]]

    def close(self) -> None:
        """Close Neo4j connection and cleanup resources."""
        if hasattr(self, 'driver'):
            self.driver.close()