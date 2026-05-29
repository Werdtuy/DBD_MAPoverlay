from __future__ import annotations

import logging
from queue import Queue
from pathlib import Path


def configure_logging(root: Path) -> tuple[logging.Logger, Queue[str]]:
    log_dir = root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    queue: Queue[str] = Queue()

    class TextQueueHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            queue.put(self.format(record))

    logger = logging.getLogger("dbd_overlay")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    formatter = logging.Formatter("%(asctime)s  %(levelname)-7s  %(message)s", "%H:%M:%S")

    stream_handler = TextQueueHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger, queue
