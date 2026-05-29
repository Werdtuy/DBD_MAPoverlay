from __future__ import annotations

from collections.abc import Callable
import logging

from .config import AppConfig
from .focus import FocusGate

try:
    import keyboard
except Exception:  # pragma: no cover - optional dependency
    keyboard = None


class HotkeyManager:
    def __init__(self, config: AppConfig, focus_gate: FocusGate, logger: logging.Logger) -> None:
        self.config = config
        self.focus_gate = focus_gate
        self.logger = logger
        self._handles: list = []

    def register(self, actions: dict[str, Callable[[], None]]) -> None:
        self.unregister()
        if not keyboard:
            self.logger.warning("keyboard is not installed; global hotkeys disabled")
            return

        guarded_mapping = {
            self.config.hotkeys.toggle_overlay: actions.get("toggle_overlay"),
            self.config.hotkeys.reload_maps: actions.get("reload_maps"),
            self.config.hotkeys.cycle_variant: actions.get("cycle_variant"),
            self.config.hotkeys.force_select: actions.get("force_select"),
        }
        unguarded_mapping = {
            self.config.hotkeys.force_update_map: actions.get("force_update_map"),
        }
        for combo, callback in guarded_mapping.items():
            if not combo or not callback:
                continue
            try:
                handle = keyboard.add_hotkey(combo, self._guarded(callback), suppress=False)
                self._handles.append(handle)
                self.logger.info("Registered hotkey %s", combo)
            except Exception as exc:
                self.logger.warning("Could not register hotkey %s: %s", combo, exc)
        for combo, callback in unguarded_mapping.items():
            if not combo or not callback:
                continue
            try:
                handle = keyboard.add_hotkey(combo, callback, suppress=False)
                self._handles.append(handle)
                self.logger.info("Registered hotkey %s", combo)
            except Exception as exc:
                self.logger.warning("Could not register hotkey %s: %s", combo, exc)

    def unregister(self) -> None:
        if not keyboard:
            return
        for handle in self._handles:
            try:
                keyboard.remove_hotkey(handle)
            except Exception:
                pass
        self._handles.clear()

    def _guarded(self, callback: Callable[[], None]) -> Callable[[], None]:
        def wrapper() -> None:
            if self.focus_gate.is_game_focused():
                callback()

        return wrapper
