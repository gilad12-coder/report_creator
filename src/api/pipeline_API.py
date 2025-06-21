"""
Intelligence Pipeline API

FastAPI service for storing and querying intelligence data using Neo4j + ColBERT embeddings.
"""
import asyncio
import uuid
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.core.fact_extractor import FactExtractor
from src.core.digest_layer import DigestLayer
from src.core.retrieval_index import RetrievalIndex
from src.core.report_generator import SectionedReportGenerator
from src.utils.utils import get_utc_timestamp, setup_logging
from dotenv import load_dotenv

load_dotenv()

setup_logging()
logger = logging.getLogger(__name__)

active_indices: Dict[str, Dict[str, Any]] = {}
cleanup_tasks: Dict[str, asyncio.Task] = {}

INDEX_TIMEOUT = 3600
MAX_ACTIVE_INDICES = 10


class DossierRequest(BaseModel):
    """Request model for creating a new intelligence index."""
    items: List[str] = Field(..., description="List of intelligence text items")
    target_name: str = Field(..., description="Target name for the intelligence")
    target_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional target information (aliases, role, etc.)"
    )
    index_id: Optional[str] = Field(
        default=None,
        description="Optional custom index ID, will generate UUID if not provided"
    )
    neo4j_config: Optional[Dict[str, str]] = Field(
        default=None,
        description="Custom Neo4j configuration (uri, user, password)"
    )


class QueryRequest(BaseModel):
    """Request model for querying an intelligence index."""
    index_id: str = Field(..., description="Index ID to query")
    query: str = Field(..., description="Search query text")
    k: int = Field(default=20, ge=1, le=100, description="Number of documents to retrieve")
    query_level: Optional[str] = Field(
        default=None,
        description="Optional query level override: strategic, pattern, specific, mixed"
    )
    include_context: bool = Field(
        default=True,
        description="Whether to include hierarchical context enhancement"
    )


class ReportRequest(BaseModel):
    """Request model for generating intelligence reports."""
    index_id: str = Field(..., description="Index ID to generate report from")
    sections: Optional[List[str]] = Field(
        default=None,
        description="Optional list of specific sections to include"
    )
    custom_queries: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional custom queries for specific sections"
    )


class IndexResponse(BaseModel):
    """Response model for index creation."""
    index_id: str
    target_name: str
    status: str
    message: str
    facts_extracted: int
    tree_structure: Dict[str, int]
    created_at: str
    expires_at: str


class QueryResponse(BaseModel):
    """Response model for document queries."""
    index_id: str
    query: str
    query_level: str
    documents: List[str]
    total_retrieved: int
    processing_time_ms: float


class ReportResponse(BaseModel):
    """Response model for report generation."""
    index_id: str
    target_name: str
    report: str
    sections_included: List[str]
    processing_time_ms: float
    generated_at: str


class IndexInfo(BaseModel):
    """Model for index information."""
    index_id: str
    target_name: str
    status: str
    facts_count: int
    tree_structure: Dict[str, int]
    created_at: str
    last_accessed: str
    expires_at: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    logger.info("Starting Intelligence Pipeline API")
    yield
    logger.info("Shutting down, cleaning up active indices")
    for index_id in list(active_indices.keys()):
        await cleanup_index(index_id)


app = FastAPI(
    title="Intelligence Pipeline API",
    description="API for storing and querying intelligence data using Neo4j + ColBERT embeddings",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def cleanup_index(index_id: str) -> None:
    """Clean up an index and its resources."""
    if index_id in active_indices:
        try:
            index_info = active_indices[index_id]
            retrieval_index = index_info["retrieval_index"]
            retrieval_index.close()

            cache_path = index_info["cache_path"]
            if cache_path.exists():
                shutil.rmtree(cache_path)

            if index_id in cleanup_tasks:
                cleanup_tasks[index_id].cancel()
                del cleanup_tasks[index_id]

            del active_indices[index_id]
            logger.info(f"Cleaned up index {index_id}")

        except Exception as e:
            logger.error(f"Error cleaning up index {index_id}: {e}")


async def schedule_cleanup(index_id: str, delay: int = INDEX_TIMEOUT) -> None:
    """Schedule cleanup of an index after specified delay."""
    try:
        await asyncio.sleep(delay)
        await cleanup_index(index_id)
        logger.info(f"Auto-cleaned up expired index {index_id}")
    except asyncio.CancelledError:
        logger.debug(f"Cleanup task for {index_id} was cancelled")


def get_neo4j_config(custom_config: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Get Neo4j configuration with fallbacks."""
    if custom_config:
        return custom_config

    return {
        "uri": os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        "user": os.getenv('NEO4J_USER', 'neo4j'),
        "password": os.getenv('NEO4J_PASSWORD', 'password')
    }


def validate_index_exists(index_id: str) -> Dict[str, Any]:
    """Validate that an index exists and update its last accessed time."""
    if index_id not in active_indices:
        raise HTTPException(
            status_code=404,
            detail=f"Index {index_id} not found or has expired"
        )

    active_indices[index_id]["last_accessed"] = get_utc_timestamp()

    if index_id in cleanup_tasks:
        cleanup_tasks[index_id].cancel()

    cleanup_tasks[index_id] = asyncio.create_task(schedule_cleanup(index_id))

    return active_indices[index_id]


@app.post("/api/v1/indices", response_model=IndexResponse)
async def create_index(request: DossierRequest) -> IndexResponse:
    """
    Create a new intelligence index from a dossier of intelligence items.

    Processes intelligence items through the full pipeline:
    1. Relevance filtering and fact extraction
    2. Hierarchical digest tree creation
    3. Neo4j + ColBERT index building

    Returns index metadata including processing statistics and expiration time.
    """
    import time
    start_time = time.time()

    index_id = request.index_id or f"intel_{uuid.uuid4().hex[:8]}"

    if index_id in active_indices:
        raise HTTPException(
            status_code=409,
            detail=f"Index {index_id} already exists"
        )

    if len(active_indices) >= MAX_ACTIVE_INDICES:
        oldest_id = min(
            active_indices.keys(),
            key=lambda x: active_indices[x]["created_at"]
        )
        await cleanup_index(oldest_id)

    try:
        logger.info(f"Creating index {index_id} for target: {request.target_name}")

        extractor = FactExtractor()
        facts, extraction_stats = extractor.extract_facts(
            request.items,
            request.target_info
        )

        if not facts:
            raise HTTPException(
                status_code=400,
                detail="No relevant facts could be extracted from the provided items"
            )

        digest_layer = DigestLayer()
        digest_tree = digest_layer.digest_facts(facts)

        cache_path = Path("../../colbert_cache") / index_id
        neo4j_config = get_neo4j_config(request.neo4j_config)

        retrieval_index = RetrievalIndex(
            cache_path,
            neo4j_config["uri"],
            neo4j_config["user"],
            neo4j_config["password"]
        )

        retrieval_index.add_documents(digest_tree)
        retrieval_index.build_index()

        created_at = get_utc_timestamp()
        expires_at = datetime.now(timezone.utc).timestamp() + INDEX_TIMEOUT

        active_indices[index_id] = {
            "index_id": index_id,
            "target_name": request.target_name,
            "target_info": request.target_info or {},
            "retrieval_index": retrieval_index,
            "digest_tree": digest_tree,
            "cache_path": cache_path,
            "facts_count": len(facts),
            "extraction_stats": extraction_stats,
            "created_at": created_at,
            "last_accessed": created_at,
            "expires_at": datetime.fromtimestamp(expires_at, timezone.utc).isoformat()
        }

        cleanup_tasks[index_id] = asyncio.create_task(schedule_cleanup(index_id))

        processing_time = time.time() - start_time

        logger.info(f"Successfully created index {index_id} in {processing_time:.2f}s")

        return IndexResponse(
            index_id=index_id,
            target_name=request.target_name,
            status="created",
            message=f"Index created successfully in {processing_time:.2f} seconds",
            facts_extracted=len(facts),
            tree_structure={
                "facts": len(digest_tree.facts),
                "leafs": len(digest_tree.leafs),
                "branches": len(digest_tree.branches),
                "root": 1 if digest_tree.root else 0
            },
            created_at=created_at,
            expires_at=active_indices[index_id]["expires_at"]
        )

    except Exception as e:
        if index_id in active_indices:
            await cleanup_index(index_id)

        logger.error(f"Failed to create index {index_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create index: {str(e)}"
        )


@app.post("/api/v1/query", response_model=QueryResponse)
async def query_index(request: QueryRequest) -> QueryResponse:
    """
    Query an intelligence index for relevant documents.

    Uses hierarchical tree navigation with intelligent query classification
    to retrieve the most relevant documents. Query level is automatically
    determined but can be overridden via request parameters.

    Returns documents ranked by relevance with hierarchical context enhancement.
    """
    import time
    start_time = time.time()

    index_info = validate_index_exists(request.index_id)
    retrieval_index = index_info["retrieval_index"]

    try:
        documents = retrieval_index.retrieve(request.query, k=request.k)
        query_level = retrieval_index.classify_query_level(request.query)

        processing_time = (time.time() - start_time) * 1000

        logger.info(f"Query '{request.query}' on index {request.index_id} returned {len(documents)} documents")

        return QueryResponse(
            index_id=request.index_id,
            query=request.query,
            query_level=query_level.value,
            documents=documents,
            total_retrieved=len(documents),
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error(f"Failed to query index {request.index_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )


@app.post("/api/v1/report", response_model=ReportResponse)
async def generate_report(request: ReportRequest) -> ReportResponse:
    """
    Generate a comprehensive intelligence report from an indexed dossier.

    Creates a structured Hebrew intelligence report with multiple sections
    using hierarchical context-aware generation. Report includes strategic
    analysis, behavioral patterns, network relationships, and operational details.

    Returns complete formatted report with metadata and processing statistics.
    """
    import time
    start_time = time.time()

    index_info = validate_index_exists(request.index_id)
    retrieval_index = index_info["retrieval_index"]
    target_name = index_info["target_name"]

    try:
        generator = SectionedReportGenerator(target_name, retrieval_index)
        report = generator.generate_report()

        processing_time = (time.time() - start_time) * 1000

        sections_included = [
            "role_activities", "capabilities_resources", "communication_patterns",
            "activity_patterns", "network_analysis", "key_topics", "code_words"
        ]

        logger.info(f"Generated report for index {request.index_id} in {processing_time:.0f}ms")

        return ReportResponse(
            index_id=request.index_id,
            target_name=target_name,
            report=report,
            sections_included=sections_included,
            processing_time_ms=processing_time,
            generated_at=get_utc_timestamp()
        )

    except Exception as e:
        logger.error(f"Failed to generate report for index {request.index_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Report generation failed: {str(e)}"
        )


@app.get("/api/v1/indices", response_model=List[IndexInfo])
async def list_indices() -> List[IndexInfo]:
    """
    List all active intelligence indices.

    Returns metadata for all currently active indices including
    target information, processing statistics, and expiration times.
    """
    indices = []

    for index_id, info in active_indices.items():
        indices.append(IndexInfo(
            index_id=index_id,
            target_name=info["target_name"],
            status="active",
            facts_count=info["facts_count"],
            tree_structure={
                "facts": len(info["digest_tree"].facts),
                "leafs": len(info["digest_tree"].leafs),
                "branches": len(info["digest_tree"].branches),
                "root": 1 if info["digest_tree"].root else 0
            },
            created_at=info["created_at"],
            last_accessed=info["last_accessed"],
            expires_at=info["expires_at"]
        ))

    return indices


@app.get("/api/v1/indices/{index_id}", response_model=IndexInfo)
async def get_index_info(index_id: str) -> IndexInfo:
    """
    Get detailed information about a specific intelligence index.

    Returns comprehensive metadata including target details, processing
    statistics, tree structure, and access timestamps.
    """
    index_info = validate_index_exists(index_id)

    return IndexInfo(
        index_id=index_id,
        target_name=index_info["target_name"],
        status="active",
        facts_count=index_info["facts_count"],
        tree_structure={
            "facts": len(index_info["digest_tree"].facts),
            "leafs": len(index_info["digest_tree"].leafs),
            "branches": len(index_info["digest_tree"].branches),
            "root": 1 if index_info["digest_tree"].root else 0
        },
        created_at=index_info["created_at"],
        last_accessed=index_info["last_accessed"],
        expires_at=index_info["expires_at"]
    )


@app.delete("/api/v1/indices/{index_id}")
async def delete_index(index_id: str) -> Dict[str, str]:
    """
    Manually delete an intelligence index and clean up its resources.

    Immediately removes the index from memory, closes Neo4j connections,
    and deletes associated ColBERT cache files.
    """
    if index_id not in active_indices:
        raise HTTPException(
            status_code=404,
            detail=f"Index {index_id} not found"
        )

    await cleanup_index(index_id)

    return {
        "message": f"Index {index_id} deleted successfully",
        "deleted_at": get_utc_timestamp()
    }


@app.get("/api/v1/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for API monitoring.

    Returns current system status including active index count,
    configuration limits, and timestamp information.
    """
    return {
        "status": "healthy",
        "active_indices": len(active_indices),
        "max_indices": MAX_ACTIVE_INDICES,
        "index_timeout": INDEX_TIMEOUT,
        "timestamp": get_utc_timestamp()
    }


