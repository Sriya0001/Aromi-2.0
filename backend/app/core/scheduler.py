"""
Background scheduler for AroMi 2.0.
Uses APScheduler to run periodic background jobs.

Jobs:
  1. Memory decay (weekly): Apply confidence decay to all user memories.
     Prune memories with confidence < 0.2 (too stale to be reliable).
     WHY: Without decay, a preference from 6 months ago poisons recommendations.

  2. Behavioral memory extraction (weekly): Re-analyze workout history for
     all active users and update memory entries.
     WHY: New behavioral patterns emerge over time.

  3. Evaluation metrics snapshot (daily): Compute and store all evaluation
     metrics for active users. Enables trend analysis and A/B experiment monitoring.

Trade-off: APScheduler is in-process (no external queue). For production at
Amazon scale, replace with AWS EventBridge + Lambda or SQS + worker.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)


def run_memory_decay():
    """Weekly job: Apply confidence decay and prune stale memories."""
    from app.core.database import SessionLocal
    from app.services.memory_service import MemoryService

    db = SessionLocal()
    try:
        pruned = MemoryService.decay_all_memories(db)
        logger.info(f"Memory decay complete. Pruned {pruned} stale memories.")
    except Exception as e:
        logger.error(f"Memory decay job failed: {e}")
    finally:
        db.close()


def run_behavioral_extraction():
    """Weekly job: Extract behavioral patterns from workout history for all users."""
    from app.core.database import SessionLocal
    from app.models.user import User
    from app.services.memory_service import MemoryService

    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        total_extracted = 0
        for user in users:
            try:
                count = MemoryService.extract_memories_from_behavior(db, user.id)
                total_extracted += count
            except Exception as e:
                logger.warning(f"Memory extraction failed for user {user.id}: {e}")
        logger.info(f"Behavioral extraction complete. {total_extracted} memories updated across {len(users)} users.")
    except Exception as e:
        logger.error(f"Behavioral extraction job failed: {e}")
    finally:
        db.close()


def run_evaluation_snapshot():
    """Daily job: Compute and log evaluation metrics for active users."""
    from app.core.database import SessionLocal
    from app.models.user import User
    from app.services.evaluation_service import EvaluationService

    db = SessionLocal()
    try:
        # Only process users who have at least some workout history
        from app.models.workout import WorkoutSession
        active_user_ids = [
            r[0] for r in db.query(WorkoutSession.user_id).distinct().all()
        ]
        for user_id in active_user_ids:
            try:
                EvaluationService.compute_full_evaluation_report(db, user_id)
            except Exception as e:
                logger.warning(f"Evaluation snapshot failed for user {user_id}: {e}")
        logger.info(f"Evaluation snapshot complete for {len(active_user_ids)} users.")
    except Exception as e:
        logger.error(f"Evaluation snapshot job failed: {e}")
    finally:
        db.close()


def create_scheduler() -> BackgroundScheduler:
    """Create and configure the APScheduler background scheduler."""
    scheduler = BackgroundScheduler(
        job_defaults={
            "coalesce": True,      # Don't run missed jobs multiple times
            "max_instances": 1,    # Prevent concurrent runs of same job
        },
        timezone="UTC"
    )

    # Memory decay — runs every Sunday at 2am UTC
    scheduler.add_job(
        run_memory_decay,
        trigger=CronTrigger(day_of_week="sun", hour=2, minute=0),
        id="memory_decay",
        name="Weekly Memory Confidence Decay"
    )

    # Behavioral extraction — runs every Monday at 3am UTC (after weekly plan generation)
    scheduler.add_job(
        run_behavioral_extraction,
        trigger=CronTrigger(day_of_week="mon", hour=3, minute=0),
        id="behavioral_extraction",
        name="Weekly Behavioral Memory Extraction"
    )

    # Evaluation snapshot — runs daily at 1am UTC
    scheduler.add_job(
        run_evaluation_snapshot,
        trigger=CronTrigger(hour=1, minute=0),
        id="evaluation_snapshot",
        name="Daily Evaluation Metrics Snapshot"
    )

    return scheduler


# Singleton scheduler instance
_scheduler: BackgroundScheduler = None


def get_scheduler() -> BackgroundScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = create_scheduler()
    return _scheduler


def start_scheduler():
    """Start the background scheduler. Called from FastAPI startup."""
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("AroMi background scheduler started.")


def stop_scheduler():
    """Stop the background scheduler. Called from FastAPI shutdown."""
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("AroMi background scheduler stopped.")
