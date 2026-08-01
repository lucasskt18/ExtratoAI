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
from app.services.pdf import InvalidPdfError, find_pdf_offset
from app.services.pipeline import DuplicateStatementError, process_pdf

logger = logging.getLogger(__name__)


class PdfInboxHandler(FileSystemEventHandler):
    def __init__(self) -> None:
        self._pending: Dict[str, float] = {}
        self._sizes: Dict[str, int] = {}
        self._lock = threading.Lock()

    def on_created(self, event) -> None:  # type: ignore[no-untyped-def]
        self._track(event)

    def on_modified(self, event) -> None:  # type: ignore[no-untyped-def]
        self._track(event)

    def _track(self, event) -> None:  # type: ignore[no-untyped-def]
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() != ".pdf" or path.name.startswith("."):
            return
        with self._lock:
            self._pending[str(path)] = time.time()

    def drain_ready(self, settle_seconds: float = 1.5) -> List[Path]:
        now = time.time()
        ready: List[Path] = []
        with self._lock:
            for key, ts in list(self._pending.items()):
                path = Path(key)
                if now - ts < settle_seconds:
                    continue
                if not path.exists():
                    self._pending.pop(key, None)
                    self._sizes.pop(key, None)
                    continue
                try:
                    size = path.stat().st_size
                except OSError:
                    continue

                previous = self._sizes.get(key)
                self._sizes[key] = size
                # Size still changing — copy/download in progress
                if previous is None or previous != size or size < 8:
                    self._pending[key] = now
                    continue

                data = path.read_bytes()
                if find_pdf_offset(data) < 0:
                    logger.warning("Skipping non-PDF in inbox: %s", path.name)
                    self._pending.pop(key, None)
                    self._sizes.pop(key, None)
                    continue

                ready.append(path)
                self._pending.pop(key, None)
                self._sizes.pop(key, None)
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
                    except InvalidPdfError as exc:
                        logger.warning("Invalid PDF in inbox: %s", exc)
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
