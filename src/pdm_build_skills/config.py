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
    subpath: str | None = None
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


def _sanitize_subpath(subpath: str) -> str:
    normalized = subpath.replace("\\", "/").strip("/")
    if not normalized:
        raise ValueError("Skill source subpath cannot be empty")
    if any(part == ".." for part in normalized.split("/")):
        raise ValueError(f'Unsafe skill source subpath: "{subpath}"')
    return normalized


def parse_git_source(
    value: str,
) -> tuple[str, str | None, str | None]:
    candidate = value.strip()
    if not candidate:
        raise ValueError("Git source cannot be empty")

    if Path(candidate).exists():
        return candidate, None, None

    return normalize_git_url(candidate), None, None


def load_skill_sources(pyproject_path: Path) -> list[SkillSource]:
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    return parse_skill_sources(data)


def parse_skill_sources(data: dict[str, Any]) -> list[SkillSource]:
    raw_sources = data.get("tool", {}).get("pdm", {}).get("build", {}).get("skills", [])
    if not isinstance(raw_sources, list):
        raise ValueError("[tool.pdm.build].skills must be a list")

    parsed: list[SkillSource] = []
    for index, item in enumerate(raw_sources):
        if isinstance(item, str):
            git, ref, subpath = parse_git_source(item)
            parsed.append(SkillSource(git=git, ref=ref, subpath=subpath))
            continue
        if isinstance(item, dict):
            git_val = item.get("git")
            if not isinstance(git_val, str) or not git_val.strip():
                raise ValueError(f"skills[{index}].git must be a non-empty string")
            git = git_val
            normalized_git, parsed_ref, parsed_subpath = parse_git_source(git)
            ref = item.get("ref", parsed_ref)
            if ref is not None and (not isinstance(ref, str) or not ref.strip()):
                raise ValueError(f"skills[{index}].ref must be a string")
            subpath = item.get("subpath", parsed_subpath)
            if subpath is not None and not isinstance(subpath, str):
                raise ValueError(f"skills[{index}].subpath must be a string")
            normalized_subpath = (
                _sanitize_subpath(subpath) if isinstance(subpath, str) else None
            )
            include = item.get("include", [])
            if include is None:
                include = []
            if not isinstance(include, list) or not all(
                isinstance(pattern, str) for pattern in include
            ):
                raise ValueError(f"skills[{index}].include must be a list of strings")
            parsed.append(
                SkillSource(
                    git=normalized_git,
                    ref=ref.strip() if isinstance(ref, str) else None,
                    subpath=normalized_subpath,
                    include=tuple(include),
                )
            )
            continue
        raise ValueError(f"skills[{index}] must be a string or table")
    return parsed
