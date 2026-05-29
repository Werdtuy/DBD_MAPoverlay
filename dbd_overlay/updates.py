from __future__ import annotations

import logging
from pathlib import Path
import threading

from .config import AppConfig
from .maps import MapLibrary

try:
    import requests
except Exception:  # pragma: no cover - optional dependency
    requests = None


class MapUpdateChecker:
    def __init__(self, config: AppConfig, library: MapLibrary, logger: logging.Logger) -> None:
        self.config = config
        self.library = library
        self.logger = logger

    def check_async(self) -> None:
        if not self.config.updates.check_for_map_updates or not self.config.updates.update_manifest_url:
            return
        threading.Thread(target=self._check, name="MapUpdateChecker", daemon=True).start()

    def _check(self) -> None:
        if not requests:
            self.logger.warning("requests is not installed; map update checks unavailable")
            return
        try:
            response = requests.get(self.config.updates.update_manifest_url, timeout=8)
            response.raise_for_status()
            manifest = response.json()
        except Exception as exc:
            self.logger.warning("Map update check failed: %s", exc)
            return

        remote_maps = manifest.get("maps", []) if isinstance(manifest, dict) else []
        local_names = set(self.library.names())
        missing = [item.get("name") for item in remote_maps if isinstance(item, dict) and item.get("name") not in local_names]
        if missing:
            self.logger.info("Map updates available: %s", ", ".join(missing))
        else:
            self.logger.info("Map library is up to date")

