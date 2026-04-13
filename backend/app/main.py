import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.logging_config import setup_logging
from app.workers.background_worker import start_worker
from app.services.reminder_service import check_and_fire_reminders

# ── Routers ───────────────────────────────────────────────────────────────────
from app.routes.auth import router as auth_router
from app.routes.query import router as query_router
from app.routes.record import router as record_router
from app.routes.advanced import router as advanced_router
from app.routes.speaker import router as speaker_router
from app.routes.privacy import router as privacy_router
from app.routes.pipeline_routes import router as pipeline_router
from app.routes.reminders import router as reminders_router   # new

setup_logging()
logger = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler(timezone="UTC")


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SecondBrain starting up...")

    # 1. Start background worker queue
    start_worker()

    # 2. Start reminder scheduler — runs check_and_fire_reminders every 15 min
    _scheduler.add_job(
        check_and_fire_reminders,
        trigger="interval",
        minutes=15,
        id="reminder_check",
        replace_existing=True,
        misfire_grace_time=60,   # allow 60s late start before skipping
    )
    _scheduler.start()
    logger.info("Reminder scheduler started (interval: 15 min)")

    yield

    # Shutdown
    _scheduler.shutdown(wait=False)
    logger.info("SecondBrain shut down cleanly")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="SecondBrain API",
    version="3.0.0",
    description="AI-powered personal memory system",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_cors.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Route registration ────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(query_router)
app.include_router(record_router)
app.include_router(advanced_router)
app.include_router(speaker_router)
app.include_router(privacy_router)
app.include_router(pipeline_router)
app.include_router(reminders_router)    # new


@app.get("/status")
async def status():
    # Get total memory count from MongoDB directly for efficiency
    from app.services.memory_store import _memories_collection
    try:
        col = _memories_collection()
        total_nodes = await col.count_documents({})
    except Exception:
        total_nodes = 0

    return {
        "status": "running",
        "version": "3.0.0",
        "nodes": total_nodes,
        "scheduler": "running" if _scheduler.running else "stopped",
    }


@app.get("/")
async def root():
    return {"message": "SecondBrain API v3.0.0"}
