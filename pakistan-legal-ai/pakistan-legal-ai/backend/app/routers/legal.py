from fastapi import APIRouter, HTTPException
from app.models.schemas import QueryRequest, QueryResponse, HealthResponse
from app.services.rag_service import rag_service
from app.core.config import settings

router = APIRouter(prefix="/api", tags=["Legal Research"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    stats = rag_service.get_stats()
    return HealthResponse(
        status="ok" if stats["ready"] else "initializing",
        version=settings.APP_VERSION,
        documents_loaded=stats["total_documents"]
    )


@router.post("/search", response_model=QueryResponse)
async def search_legal(request: QueryRequest):
    """
    Main endpoint: Submit a legal query in Urdu or English.
    Returns relevant Constitution articles, Acts/Sections, 
    similar judgments with summaries, and suggested legal arguments.
    """
    if not rag_service.is_ready:
        raise HTTPException(status_code=503, detail="System is still initializing. Please try again in a few seconds.")
    
    try:
        result = rag_service.search(query=request.query, top_k=request.top_k or 6)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/examples")
async def get_examples():
    """Sample queries for demo."""
    return {
        "examples": [
            "Do bhaiyon ke darmiyan zameen ki warasat ka dispute hai",
            "Sister ko inheritance se exclude karne ki koshish ki gai hai oral gift ke zariye",
            "Mutation mein ghalat entry hai, kaise challenge karein?",
            "Co-sharer ne exclusive possession le liya hai, partition ka suit maintainable hai?",
            "Predeceased son ke children ka hissa kya hoga under MFLO Section 4?"
        ]
    }
