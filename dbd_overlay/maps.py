from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from typing import Iterable


SUPPORTED_EXTENSIONS = {".png", ".webp", ".gif"}


@dataclass
class MapAsset:
    name: str
    path: Path
    aliases: list[str] = field(default_factory=list)
    template_region: list[int] | None = None


@dataclass
class MapEntry:
    name: str
    variants: list[MapAsset] = field(default_factory=list)

    @property
    def primary(self) -> MapAsset | None:
        return self.variants[0] if self.variants else None


def normalize_map_name(value: str) -> str:
    value = Path(value).stem
    value = re.sub(r"\s+-\s+.*$", "", value)
    value = re.sub(r"[_-]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


class MapLibrary:
    def __init__(self, root: Path, maps_dir: str) -> None:
        self.root = root
        self.maps_path = (root / maps_dir).resolve()
        self.maps_path.mkdir(parents=True, exist_ok=True)
        self.entries: dict[str, MapEntry] = {}

    def reload(self) -> None:
        entries: dict[str, MapEntry] = {}
        for path in sorted(self.maps_path.rglob("*"), key=lambda p: str(p).lower()):
            if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            base_name = normalize_map_name(path.name)
            metadata = self._load_metadata(path)
            aliases = metadata.get("aliases", [])
            display_name = metadata.get("name", base_name)
            asset = MapAsset(
                name=display_name,
                path=path,
                aliases=list(dict.fromkeys([display_name, base_name, *aliases])),
                template_region=metadata.get("template_region"),
            )
            entries.setdefault(display_name, MapEntry(display_name)).variants.append(asset)
        self.entries = entries

    def names(self) -> list[str]:
        return sorted(self.entries)

    def all_assets(self) -> Iterable[MapAsset]:
        for entry in self.entries.values():
            yield from entry.variants

    def get(self, name: str) -> MapEntry | None:
        return self.entries.get(name)

    def _load_metadata(self, image_path: Path) -> dict:
        metadata_path = image_path.with_name(f"{image_path.name}.json")
        if not metadata_path.exists():
            return {}
        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
