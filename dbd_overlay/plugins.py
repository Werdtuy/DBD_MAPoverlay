from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class OverlayPlugin(Protocol):
    name: str

    def on_map_changed(self, map_name: str) -> None:
        ...


@dataclass
class PluginManager:
    root: Path

    def __post_init__(self) -> None:
        self.plugins_dir = self.root / "plugins"
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.plugins: list[OverlayPlugin] = []

    def load(self) -> None:
        # Placeholder extension point. Future plugins can be discovered here
        # without changing the app's overlay, OCR, or hotkey modules.
        self.plugins.clear()

    def emit_map_changed(self, map_name: str) -> None:
        for plugin in self.plugins:
            plugin.on_map_changed(map_name)

