import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler(db):
    """Start weekly retraining scheduler."""

    async def weekly_retrain():
        logger.info("[TIMER] Weekly retraining triggered by scheduler")
        from app.ml.retrainer import model_retrainer
        result = await model_retrainer.retrain(db, triggered_by="auto_weekly")
        logger.info(f"Weekly retrain result: {result}")

    # Every Sunday at 2:00 AM
    scheduler.add_job(
        weekly_retrain,
        trigger=CronTrigger(day_of_week="sun", hour=2, minute=0),
        id="weekly_retrain",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("[OK] Scheduler started - weekly retraining every Sunday 02:00")



def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()