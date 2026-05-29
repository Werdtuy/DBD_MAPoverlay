from __future__ import annotations

import os
from pathlib import Path
import shutil


def tesseract_search_paths() -> list[Path]:
    paths: list[Path] = []

    found = shutil.which("tesseract")
    if found:
        paths.append(Path(found))

    candidates: list[Path] = []
    for env_name in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        value = os.environ.get(env_name)
        if value:
            candidates.append(Path(value))

    common_paths = [
        Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
        Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
    ]
    paths.extend(common_paths)

    for root in candidates:
        paths.extend(
            [
                root / "Tesseract-OCR/tesseract.exe",
                root / "Programs/Tesseract-OCR/tesseract.exe",
            ]
        )

    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path).lower()
        if key not in seen:
            unique.append(path)
            seen.add(key)
    return unique


def find_tesseract() -> Path | None:
    for path in tesseract_search_paths():
        if path.exists():
            return path
    return None


def tesseract_search_report() -> tuple[Path | None, list[Path]]:
    paths = tesseract_search_paths()
    for path in paths:
        if path.exists():
            return path, paths
    return None, paths


def is_tesseract_path(path: str) -> bool:
    if not path:
        return False
    target = Path(path)
    return target.exists() and target.name.lower() == "tesseract.exe"
