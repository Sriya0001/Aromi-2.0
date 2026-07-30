"""
AroMi 2.0 FastAPI Application Entry Point.

Architecture: Multi-agent personalized wellness planning system.
- 4 specialized agents: Recovery, Workout, Nutrition, Planner
- 15-table PostgreSQL schema with biometric time-series data
- Long-term memory with confidence decay
- Automated evaluation framework (10 metrics)
- APScheduler background jobs for memory decay and metric snapshots
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import Base, engine
from app.core.config import settings

# Import all models so SQLAlchemy creates tables
import app.models  # noqa: F401

# Routers
from app.routers import auth, users, workout, nutrition, progress, ai, calendar, reviews, favourites
from app.routers import health, memory, evaluation


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: startup and shutdown logic."""
    # Create all DB tables
    Base.metadata.create_all(bind=engine)

    # Start background scheduler (memory decay, evaluation snapshots)
    try:
        from app.core.scheduler import start_scheduler
        start_scheduler()
    except Exception as e:
        print(f"Scheduler start warning (non-fatal): {e}")

    yield

    # Shutdown scheduler
    try:
        from app.core.scheduler import stop_scheduler
        stop_scheduler()
    except Exception:
        pass


app = FastAPI(
    title="AroMi 2.0 API",
    description=(
        "Intelligent Personalized Wellness Planning System. "
        "Multi-agent AI with long-term memory, adaptive planning, "
        "explainability, and automated evaluation framework."
    ),
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Existing Routers (backward compatible) ───────────────────────────────────
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(workout.router)
app.include_router(nutrition.router)
app.include_router(progress.router)
app.include_router(ai.router)
app.include_router(calendar.router)
app.include_router(reviews.router)
app.include_router(favourites.router)

# ─── AroMi 2.0 New Routers ───────────────────────────────────────────────────
app.include_router(health.router)       # Sleep, hydration, progress, feedback
app.include_router(memory.router)       # Long-term memory viewer
app.include_router(evaluation.router)   # 10 metrics + experiment assignment


@app.get("/")
def root():
    return {
        "message": "AroMi 2.0 API 🧠",
        "docs": "/docs",
        "version": "2.0.0",
        "architecture": "multi-agent (Recovery + Workout + Nutrition + Planner)",
        "features": [
            "Personalized multi-agent planning",
            "Long-term memory with confidence decay",
            "Medical safety constraints",
            "Explainability on every recommendation",
            "Automated evaluation framework (10 metrics)",
            "A/B experiment infrastructure"
        ]
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "2.0.0"}
