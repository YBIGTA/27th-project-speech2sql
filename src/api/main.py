"""
FastAPI main application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from config.settings import settings
from config.database import create_tables, close_connections

# Import routes
from src.api.routes import audio, query, summary, search, analysis

# Create FastAPI app
app = FastAPI(
    title="Speech2SQL API",
    description="강의·회의록 생성 및 검색 시스템 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(audio.router, prefix="/api/v1/audio", tags=["audio"])
app.include_router(query.router, prefix="/api/v1/query", tags=["query"])
app.include_router(summary.router, prefix="/api/v1/summary", tags=["summary"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["analysis"])

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    print("🚀 Starting Speech2SQL API...")
    create_tables()
    print("✅ Database tables created")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    print("🛑 Shutting down Speech2SQL API...")
    close_connections()
    print("✅ Database connections closed")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Speech2SQL API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "timestamp": "2024-01-01T00:00:00Z"
    }


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    ) 