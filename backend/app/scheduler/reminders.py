"""APScheduler jobs for WhatsApp reminders."""

from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.core.logger import get_logger
from app.services import reminder_service

logger = get_logger(__name__)

IST = ZoneInfo("Asia/Kolkata")
_scheduler: AsyncIOScheduler | None = None


def get_scheduler() -> AsyncIOScheduler | None:
    return _scheduler


def start_scheduler() -> AsyncIOScheduler | None:
    """Start cron jobs when ENABLE_SCHEDULER is true."""
    global _scheduler
    if not settings.ENABLE_SCHEDULER:
        logger.info("Scheduler disabled (ENABLE_SCHEDULER=false)")
        return None
    if _scheduler is not None:
        return _scheduler

    _scheduler = AsyncIOScheduler(timezone=IST)
    _scheduler.add_job(
        reminder_service.send_morning_reminders,
        CronTrigger(
            hour=settings.REMINDER_MORNING_HOUR,
            minute=0,
            timezone=IST,
        ),
        id="morning_reminders",
        replace_existing=True,
    )
    _scheduler.add_job(
        reminder_service.send_weekly_summaries,
        CronTrigger(
            day_of_week="sun",
            hour=settings.REMINDER_WEEKLY_HOUR,
            minute=0,
            timezone=IST,
        ),
        id="weekly_summaries",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        "Scheduler started (morning %s:00 IST, weekly Sun %s:00 IST)",
        settings.REMINDER_MORNING_HOUR,
        settings.REMINDER_WEEKLY_HOUR,
    )
    return _scheduler


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")
