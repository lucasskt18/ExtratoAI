from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from app.config import settings
from app.db.session import SessionLocal
from app.services.pipeline import DuplicateStatementError, process_pdf

logger = logging.getLogger(__name__)


class PdfInboxHandler(FileSystemEventHandler):
    def __init__(self) -> None:
        self._pending: Dict[str, float] = {}
        self._lock = threading.Lock()

    def on_created(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() != ".pdf":
            return
        with self._lock:
            self._pending[str(path)] = time.time()

    def drain_ready(self, settle_seconds: float = 1.0) -> List[Path]:
        now = time.time()
        ready: List[Path] = []
        with self._lock:
            for key, ts in list(self._pending.items()):
                if now - ts >= settle_seconds:
                    ready.append(Path(key))
                    del self._pending[key]
        return ready


class InboxWatcher:
    def __init__(self) -> None:
        self._handler = PdfInboxHandler()
        self._observer = Observer()
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    def start(self) -> None:
        settings.inbox_dir.mkdir(parents=True, exist_ok=True)
        self._observer.schedule(self._handler, str(settings.inbox_dir), recursive=False)
        self._observer.start()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("Watching inbox at %s", settings.inbox_dir)

    def stop(self) -> None:
        self._stop.set()
        self._observer.stop()
        self._observer.join(timeout=5)

    def _loop(self) -> None:
        while not self._stop.is_set():
            for path in self._handler.drain_ready():
                if not path.exists():
                    continue
                with SessionLocal() as db:
                    try:
                        process_pdf(db, path)
                    except DuplicateStatementError:
                        logger.info("Duplicate skipped: %s", path.name)
                    except Exception:
                        logger.exception("Watcher failed on %s", path)
            self._stop.wait(0.5)


_watcher: Optional[InboxWatcher] = None


def start_watcher() -> InboxWatcher:
    global _watcher
    if _watcher is None:
        _watcher = InboxWatcher()
        _watcher.start()
    return _watcher


def stop_watcher() -> None:
    global _watcher
    if _watcher is not None:
        _watcher.stop()
        _watcher = None
