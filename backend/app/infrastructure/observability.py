import json
import logging
import math
from collections import deque
from datetime import datetime, timezone
from threading import Lock


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        payload.update(getattr(record, "fields", {}))

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def configure_structured_logger():
    logger = logging.getLogger("drift")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False

    return logger


def log_event(logger, event, **fields):
    logger.info(event, extra={"fields": fields})


class SearchMetrics:
    def __init__(self, max_samples=100):
        self._durations_ms = deque(maxlen=max_samples)
        self._lock = Lock()

    def record_search(self, duration_ms):
        with self._lock:
            self._durations_ms.append(duration_ms)

    def snapshot(self):
        with self._lock:
            samples = list(self._durations_ms)

        if not samples:
            return {
                "metric": "drift_search_latency_ms",
                "sample_count": 0,
                "average_ms": None,
                "p95_ms": None,
                "window": "latest 100 searches in current process",
                "resets_on_restart": True,
            }

        ordered_samples = sorted(samples)
        p95_index = max(0, math.ceil(len(ordered_samples) * 0.95) - 1)

        return {
            "metric": "drift_search_latency_ms",
            "sample_count": len(samples),
            "average_ms": round(sum(samples) / len(samples), 2),
            "p95_ms": round(ordered_samples[p95_index], 2),
            "window": "latest 100 searches in current process",
            "resets_on_restart": True,
        }