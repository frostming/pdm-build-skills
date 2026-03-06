from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_GITHUB_SHORTHAND_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?$")


@dataclass(frozen=True)
class SkillSource:
    git: str
    ref: str | None = None
    include: tuple[str, ...] = ()

    @property
    def normalized_git(self) -> str:
        return normalize_git_url(self.git)


def normalize_git_url(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise ValueError("Git source cannot be empty")

    if Path(candidate).exists():
        return candidate
    if "://" in candidate or candidate.startswith("git@"):
        return candidate.rstrip("/")
    if _GITHUB_SHORTHAND_RE.match(candidate):
        return f"https://github.com/{candidate.rstrip('/')}.git"
    return candidate


def load_skill_sources(pyproject_path: Path) -> list[SkillSource]:
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    return parse_skill_sources(data)


def parse_skill_sources(data: dict[str, Any]) -> list[SkillSource]:
    raw_sources = data.get("tool", {}).get("bub", {}).get("skills", [])
    if not isinstance(raw_sources, list):
        raise ValueError("[tool.bub].skills must be a list")

    parsed: list[SkillSource] = []
    for index, item in enumerate(raw_sources):
        if isinstance(item, str):
            parsed.append(SkillSource(git=item))
            continue
        if isinstance(item, dict):
            git = item.get("git")
            if not isinstance(git, str) or not git.strip():
                raise ValueError(f"skills[{index}].git must be a non-empty string")
            ref = item.get("ref")
            if ref is not None and not isinstance(ref, str):
                raise ValueError(f"skills[{index}].ref must be a string")
            include = item.get("include", [])
            if include is None:
                include = []
            if not isinstance(include, list) or not all(
                isinstance(pattern, str) for pattern in include
            ):
                raise ValueError(f"skills[{index}].include must be a list of strings")
            parsed.append(SkillSource(git=git, ref=ref, include=tuple(include)))
            continue
        raise ValueError(f"skills[{index}] must be a string or table")
    return parsed
