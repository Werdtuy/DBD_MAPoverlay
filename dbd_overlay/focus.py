from __future__ import annotations

from dataclasses import dataclass
import logging

try:
    import win32gui
    import win32process
    import win32api
    import win32con
    import psutil
except Exception:  # pragma: no cover - optional Windows-only dependencies
    win32gui = None
    win32process = None
    win32api = None
    win32con = None
    psutil = None


@dataclass(frozen=True)
class Monitor:
    x: int
    y: int
    width: int
    height: int
    name: str


@dataclass(frozen=True)
class GameWindowState:
    focused: bool
    visible: bool
    running: bool
    title: str = ""
    process_name: str = ""


def _normalize_process_name(value: str) -> str:
    value = value.lower().strip()
    return value[:-4] if value.endswith(".exe") else value


DEFAULT_GAME_TITLES = {"dead by daylight"}
DEFAULT_GAME_PROCESSES = {"deadbydaylight", "deadbydaylight-win64-shipping"}


class FocusGate:
    def __init__(self, config, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger

    def is_game_focused(self) -> bool:
        if not self.config.game.require_focus:
            return True
        if not win32gui:
            return False
        return self.game_window_state().focused

    def is_game_visible(self) -> bool:
        return self.game_window_state().visible

    def can_show_overlay(self) -> bool:
        state = self.game_window_state()
        return (
            state.focused
            or (self.config.game.allow_overlay_when_visible and state.visible)
            or (self.config.game.allow_overlay_when_running and state.running)
        )

    def game_window_state(self) -> GameWindowState:
        if not win32gui:
            process_name = self._find_running_game_process()
            return GameWindowState(False, False, bool(process_name), process_name=process_name)
        try:
            foreground = win32gui.GetForegroundWindow()
            focused = self._matches_window(foreground)
            if focused:
                title, process_name = self._window_identity(foreground)
                return GameWindowState(True, True, True, title, process_name)

            visible_hwnd = self._find_visible_game_window()
            if visible_hwnd:
                title, process_name = self._window_identity(visible_hwnd)
                return GameWindowState(False, True, True, title, process_name)

            process_name = self._find_running_game_process()
            if process_name:
                return GameWindowState(False, False, True, process_name=process_name)
        except Exception as exc:
            self.logger.debug("Game window state check failed: %s", exc)
        return GameWindowState(False, False, False)

    def _find_visible_game_window(self):
        matches = []

        def callback(hwnd, _extra):
            try:
                if not win32gui.IsWindowVisible(hwnd) or win32gui.IsIconic(hwnd):
                    return True
                left, top, right, bottom = win32gui.GetWindowRect(hwnd)
                if right - left <= 0 or bottom - top <= 0:
                    return True
                if self._matches_window(hwnd):
                    matches.append(hwnd)
                    return False
            except Exception:
                return True
            return True

        win32gui.EnumWindows(callback, None)
        return matches[0] if matches else None

    def _matches_window(self, hwnd) -> bool:
        if not hwnd:
            return False
        title, process_name = self._window_identity(hwnd)
        title_keywords = {key.lower() for key in self.config.game.window_title_keywords} | DEFAULT_GAME_TITLES
        if any(key in title.lower() for key in title_keywords):
            return True
        wanted = {_normalize_process_name(item) for item in self.config.game.process_names} | DEFAULT_GAME_PROCESSES
        return _normalize_process_name(process_name) in wanted

    def _window_identity(self, hwnd) -> tuple[str, str]:
        title = win32gui.GetWindowText(hwnd) or ""
        process_name = ""
        if psutil and win32process:
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process_name = psutil.Process(pid).name()
            except Exception:
                process_name = ""
        return title, process_name

    def _find_running_game_process(self) -> str:
        if not psutil:
            return ""
        wanted = {_normalize_process_name(item) for item in self.config.game.process_names} | DEFAULT_GAME_PROCESSES
        try:
            for proc in psutil.process_iter(["name"]):
                name = proc.info.get("name") or ""
                if _normalize_process_name(name) in wanted:
                    return name
        except Exception as exc:
            self.logger.debug("Process scan failed: %s", exc)
        return ""


def get_monitors() -> list[Monitor]:
    monitors: list[Monitor] = []
    if win32api:
        try:
            for index, (handle, _, rect) in enumerate(win32api.EnumDisplayMonitors()):
                info = win32api.GetMonitorInfo(handle)
                left, top, right, bottom = info["Monitor"]
                monitors.append(Monitor(left, top, right - left, bottom - top, info.get("Device", f"Monitor {index + 1}")))
        except Exception:
            monitors.clear()
    if monitors:
        return monitors
    try:
        import mss

        with mss.mss() as sct:
            for index, mon in enumerate(sct.monitors[1:]):
                monitors.append(Monitor(mon["left"], mon["top"], mon["width"], mon["height"], f"Monitor {index + 1}"))
    except Exception:
        pass
    return monitors or [Monitor(0, 0, 1920, 1080, "Primary")]
