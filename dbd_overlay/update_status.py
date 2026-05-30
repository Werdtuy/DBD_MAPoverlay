from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen


DEFAULT_CONFIG = {
    "repository": "Werdtuy/DBD_MAPoverlay",
    "release_tag": "latest-beta",
    "manifest_asset": "update_manifest.json",
    "github_token": "",
}


@dataclass(frozen=True)
class AppUpdateStatus:
    current_version: str
    latest_version: str

    @property
    def update_available(self) -> bool:
        return self.latest_version != self.current_version


def load_updater_config(app_dir: Path) -> dict[str, str]:
    config = dict(DEFAULT_CONFIG)
    path = app_dir / "updater_config.json"
    if path.exists():
        try:
            saved = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                config.update({key: str(value) for key, value in saved.items() if key in config})
        except Exception:
            pass
    token = os.environ.get("DBD_OVERLAY_GITHUB_TOKEN", "").strip()
    if token:
        config["github_token"] = token
    return config


def _request_json(url: str, token: str = "", accept: str = "application/vnd.github+json") -> dict:
    headers = {
        "Accept": accept,
        "User-Agent": "DBDCompanionOverlay",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(Request(url, headers=headers), timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def check_for_app_update(app_dir: Path, current_version: str) -> AppUpdateStatus:
    config = load_updater_config(app_dir)
    repository = config["repository"].strip()
    tag = config["release_tag"].strip()
    token = config["github_token"].strip()
    if not repository or not tag:
        raise RuntimeError("Updater repository settings are missing")

    release = _request_json(f"https://api.github.com/repos/{repository}/releases/tags/{tag}", token)
    manifest_name = config["manifest_asset"]
    manifest_asset = next(
        (asset for asset in release.get("assets", []) if asset.get("name") == manifest_name),
        None,
    )
    if not manifest_asset or not manifest_asset.get("url"):
        raise RuntimeError(f"GitHub release asset is missing: {manifest_name}")
    manifest = _request_json(manifest_asset["url"], token, "application/octet-stream")
    latest_version = str(manifest.get("version", "")).strip()
    if not latest_version:
        raise RuntimeError("Update manifest does not contain a version")
    return AppUpdateStatus(current_version=current_version, latest_version=latest_version)
