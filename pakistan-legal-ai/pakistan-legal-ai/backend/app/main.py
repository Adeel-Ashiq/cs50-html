from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.routers import legal
from app.services.rag_service import rag_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Pakistan Legal AI System...")
    rag_service.initialize()
    yield
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Legal Research and Case Recommendation System for Pakistan (FYP Demo)",
    lifespan=lifespan
)

# CORS - allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(legal.router)


@app.get("/")
async def root():
    return {
        "message": "Pakistan Legal AI Research System is running",
        "docs": "/docs",
        "health": "/api/health"
    }
