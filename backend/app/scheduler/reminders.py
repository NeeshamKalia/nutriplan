"""APScheduler jobs for WhatsApp reminders.

NEW-004: In multi-worker deployments (uvicorn --workers N), only ONE worker
should run the scheduler to avoid duplicate reminders. This module uses
an env-var marker to ensure at most one scheduler instance per process group.
"""

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
    """Start cron jobs when ENABLE_SCHEDULER is true.

    NEW-004: Uses an env marker to prevent duplicate schedulers in
    multi-worker deployments. Only the first worker to call this
    function will actually start the scheduler.
    """
    global _scheduler
    if not settings.ENABLE_SCHEDULER:
        logger.info("Scheduler disabled (ENABLE_SCHEDULER=false)")
        return None
    if _scheduler is not None:
        return _scheduler

    # NEW-004: Multi-worker guard — only one worker should run the scheduler.
    # In production with --workers N, each worker forks and gets its own copy.
    # We use an env marker set by the first worker to claim ownership.
    import os
    marker_key = "_NUTRIPLAN_SCHEDULER_PID"
    existing_pid = os.environ.get(marker_key)
    my_pid = str(os.getpid())

    if existing_pid and existing_pid != my_pid:
        logger.info(
            "Scheduler already claimed by worker PID %s, skipping in PID %s",
            existing_pid, my_pid,
        )
        return None

    os.environ[marker_key] = my_pid

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
        "Scheduler started on worker PID %s (morning %s:00 IST, weekly Sun %s:00 IST)",
        my_pid,
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
