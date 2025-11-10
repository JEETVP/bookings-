import os
import logging
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from notifications.worker import process_pending

log = logging.getLogger("scheduler")

# ------------------ Config vía ENV ------------------
# Cada cuántos segundos corre el worker
INTERVAL_SECONDS = int(os.getenv("NOTIF_SCHEDULER_EVERY_SECONDS", "30"))
# Tamaño de lote por corrida
BATCH_LIMIT = int(os.getenv("NOTIF_WORKER_BATCH", "100"))
# Gracia para misfires (segundos)
MISFIRE_GRACE = int(os.getenv("NOTIF_MISFIRE_GRACE", "60"))

def _run_worker():
    try:
        log.debug(f"[scheduler] Running process_pending(limit={BATCH_LIMIT})")
        process_pending(limit=BATCH_LIMIT)
    except Exception as e:
        # No tirar el scheduler por errores del job
        log.exception(f"[scheduler] Error in process_pending: {e}")

def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    trigger = IntervalTrigger(seconds=INTERVAL_SECONDS)

    scheduler.add_job(
        _run_worker,
        trigger=trigger,
        id="notifications_worker",
        max_instances=1,          # evita solapamientos
        coalesce=True,            # junta ejecuciones perdidas
        misfire_grace_time=MISFIRE_GRACE,
        replace_existing=True,
    )

    scheduler.start()
    log.info(
        f"[scheduler] Started: interval={INTERVAL_SECONDS}s, "
        f"batch={BATCH_LIMIT}, misfire_grace={MISFIRE_GRACE}s, tz=UTC"
    )
    return scheduler

def stop_scheduler(scheduler: Optional[BackgroundScheduler]):
    if scheduler:
        try:
            scheduler.shutdown(wait=False)
            log.info("[scheduler] Stopped")
        except Exception as e:
            log.warning(f"[scheduler] Stop error: {e}")