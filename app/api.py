import os
from functools import lru_cache
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field, HttpUrl
from app.schemas import StrictModel
from app.orchestration import ConsensusEngine, ConsensusRequest
from app.orchestration.schemas import configured_models
from app.knowledge.store import Store, StaleVersion
from app.validation import ReviewService, ReviewRequest
from app.retrieval import RetrievalService

router = APIRouter(prefix="/api/consensus", tags=["Mahthildis"])


@lru_cache(maxsize=1)
def get_store():
    local = os.getenv("DATABASE_URL", "sqlite:///data/mahthildis.db").startswith("sqlite")
    return Store(initialize=local)


@router.get("/config")
def configuration():
    return {"models": [m.model_dump() for m in configured_models()],
            "development_mode": os.getenv("DEV_MODE", "false").lower() == "true",
            "embedding_backend": os.getenv("EMBEDDING_BACKEND", "hash"),
            "nli_backend": os.getenv("NLI_BACKEND", "structured"),
            "database": "sqlite-development" if os.getenv("DATABASE_URL", "sqlite:").startswith("sqlite") else "postgresql",
            "vector_store": "qdrant" if os.getenv("QDRANT_URL") else "memory-development"}


@router.post("/executions")
async def execute(request: ConsensusRequest, store=Depends(get_store)):
    return await ConsensusEngine(store).run(request)


@router.get("/executions/{request_id}")
def execution(request_id: str, store=Depends(get_store)):
    result = store.execution(request_id)
    if result is None:
        raise HTTPException(404, "Execution not found")
    return result


@router.get("/knowledge")
def knowledge(status: str | None = None, store=Depends(get_store)):
    return store.list_knowledge(status)


@router.get("/knowledge/{knowledge_id}/history")
def history(knowledge_id: str, store=Depends(get_store)):
    rows = store.history(knowledge_id)
    if not rows:
        raise HTTPException(404, "Knowledge not found")
    return rows


@router.post("/knowledge/{knowledge_id}/review")
def review(knowledge_id: str, request: ReviewRequest, store=Depends(get_store)):
    try:
        return ReviewService(store).review(knowledge_id, request)
    except KeyError:
        raise HTTPException(404, "Knowledge not found") from None
    except StaleVersion as exc:
        raise HTTPException(409, str(exc)) from None


class DocumentRequest(StrictModel):
    text: str = Field(min_length=1, max_length=200000)
    source: str = Field(min_length=1, max_length=500)
    source_type: str = Field(default="document", pattern="^(document|dataset|web)$")
    quality: float = Field(default=.5, ge=0, le=1)
    url: HttpUrl | None = None


@router.post("/documents")
def ingest(request: DocumentRequest, store=Depends(get_store)):
    if not request.text.strip():
        raise HTTPException(422, "Document is empty")
    items = RetrievalService(store).ingest(request.text, request.source, request.source_type,
                                           request.quality, request.url)
    return {"evidence": [e.model_dump(mode="json") for e in items], "chunks": len(items)}
