from __future__ import annotations

import fnmatch
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .config import SkillSource

_SKIP_DIR_NAMES = {"node_modules", ".git", "dist", "build", "__pycache__"}
_PRIORITY_SKILL_DIRS = (
    "skills",
    "skills/.curated",
    "skills/.experimental",
    "skills/.system",
    ".agent/skills",
    ".agents/skills",
    ".claude/skills",
    ".cline/skills",
    ".codebuddy/skills",
    ".codex/skills",
    ".commandcode/skills",
    ".continue/skills",
    ".github/skills",
    ".goose/skills",
    ".iflow/skills",
    ".junie/skills",
    ".kilocode/skills",
    ".kiro/skills",
    ".mux/skills",
    ".neovate/skills",
    ".opencode/skills",
    ".openhands/skills",
    ".pi/skills",
    ".qoder/skills",
    ".roo/skills",
    ".trae/skills",
    ".windsurf/skills",
    ".zencoder/skills",
)


@dataclass(frozen=True)
class MaterializedSkill:
    name: str
    source: Path


def materialize_sources(
    sources: list[SkillSource], destination: Path
) -> list[MaterializedSkill]:
    destination.mkdir(parents=True, exist_ok=True)
    materialized: list[MaterializedSkill] = []
    for source in sources:
        with tempfile.TemporaryDirectory(prefix="pdm-build-skills-") as clone_dir:
            repo_dir = _clone_repository(source, Path(clone_dir))
            for skill_dir in _discover_skill_directories(repo_dir, source):
                target_dir = destination / skill_dir.name
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                shutil.copytree(skill_dir, target_dir)
                materialized.append(
                    MaterializedSkill(name=skill_dir.name, source=target_dir)
                )
    return materialized


def _clone_repository(source: SkillSource, destination: Path) -> Path:
    repo_dir = destination / "repo"
    if source.ref:
        _run_git(
            ["clone", "--quiet", "--no-checkout", source.normalized_git, str(repo_dir)]
        )
        _run_git(
            [
                "-C",
                str(repo_dir),
                "fetch",
                "--quiet",
                "--depth",
                "1",
                "origin",
                source.ref,
            ]
        )
        _run_git(["-C", str(repo_dir), "checkout", "--quiet", "FETCH_HEAD"])
    else:
        _run_git(
            ["clone", "--quiet", "--depth", "1", source.normalized_git, str(repo_dir)]
        )
    return repo_dir


def _run_git(args: list[str]) -> None:
    try:
        subprocess.run(["git", *args], check=True, capture_output=True, text=True)
    except FileNotFoundError as exc:  # pragma: no cover
        raise RuntimeError(
            "git executable is required to fetch skill repositories"
        ) from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip()
        message = stderr or "git command failed"
        raise RuntimeError(message) from exc


def _resolve_search_path(repo_dir: Path, subpath: str | None) -> Path:
    if subpath is None:
        return repo_dir
    search_path = (repo_dir / subpath).resolve()
    try:
        search_path.relative_to(repo_dir.resolve())
    except ValueError as exc:  # pragma: no cover
        raise ValueError(
            f'Invalid subpath "{subpath}" escapes repository root'
        ) from exc
    if not search_path.exists():
        raise ValueError(f'Repository {repo_dir} does not contain "{subpath}"')
    if not search_path.is_dir():
        raise ValueError(f'Skill source path "{subpath}" is not a directory')
    return search_path


def _discover_skill_directories(repo_dir: Path, source: SkillSource) -> list[Path]:
    search_path = _resolve_search_path(repo_dir, source.subpath)

    if _has_skill_md(search_path):
        return _filter_skill_directories([search_path], source.include)

    discovered = _priority_search(search_path)
    if discovered:
        return _filter_skill_directories(discovered, source.include)

    fallback = _recursive_search(search_path)
    if fallback:
        return _filter_skill_directories(fallback, source.include)

    raise ValueError(f"Repository {repo_dir} does not contain any discoverable skills")


def _has_skill_md(path: Path) -> bool:
    return (path / "SKILL.md").is_file()


def _priority_search(search_path: Path) -> list[Path]:
    discovered: list[Path] = []
    seen = set[Path]()
    candidate_roots = [search_path / relative for relative in _PRIORITY_SKILL_DIRS]
    candidate_roots.extend(_plugin_skill_roots(search_path))

    for skill_root in candidate_roots:
        if not skill_root.is_dir():
            continue
        for path in sorted(skill_root.iterdir()):
            if not path.is_dir() or not _has_skill_md(path) or path in seen:
                continue
            seen.add(path)
            discovered.append(path)
    return discovered


def _recursive_search(
    search_path: Path, depth: int = 0, max_depth: int = 5
) -> list[Path]:
    if depth > max_depth or not search_path.is_dir():
        return []

    discovered: list[Path] = []
    if _has_skill_md(search_path):
        discovered.append(search_path)

    for entry in sorted(search_path.iterdir()):
        if not entry.is_dir() or entry.name in _SKIP_DIR_NAMES:
            continue
        discovered.extend(_recursive_search(entry, depth + 1, max_depth))
    return discovered


def _filter_skill_directories(
    skill_dirs: Iterable[Path], include: tuple[str, ...]
) -> list[Path]:
    paths = sorted(dict.fromkeys(skill_dirs))
    if not include:
        return paths
    return [
        path
        for path in paths
        if any(fnmatch.fnmatch(path.name, pattern) for pattern in include)
    ]


def _plugin_skill_roots(search_path: Path) -> list[Path]:
    return _marketplace_skill_roots(search_path) + _plugin_json_skill_roots(search_path)


def _marketplace_skill_roots(search_path: Path) -> list[Path]:
    manifest_path = search_path / ".claude-plugin" / "marketplace.json"
    if not manifest_path.is_file():
        return []

    data = _load_json(manifest_path)
    if not isinstance(data, dict):
        return []

    metadata = data.get("metadata")
    plugin_root = (
        metadata.get("pluginRoot")
        if isinstance(metadata, dict) and isinstance(metadata.get("pluginRoot"), str)
        else ""
    )
    plugin_root_path = (
        _safe_relative_dir(search_path, plugin_root) if plugin_root else search_path
    )
    if plugin_root and plugin_root_path is None:
        return []

    roots: list[Path] = []
    for plugin in data.get("plugins", []):
        if not isinstance(plugin, dict):
            continue
        source = plugin.get("source", "")
        if source and not isinstance(source, str):
            continue
        plugin_base = (
            _safe_relative_dir(plugin_root_path, source) if source else plugin_root_path
        )
        if plugin_base is None:
            continue
        roots.append(plugin_base / "skills")
        roots.extend(_manifest_declared_skill_roots(plugin_base, plugin.get("skills")))
    return roots


def _plugin_json_skill_roots(search_path: Path) -> list[Path]:
    manifest_path = search_path / ".claude-plugin" / "plugin.json"
    if not manifest_path.is_file():
        return []

    data = _load_json(manifest_path)
    if not isinstance(data, dict):
        return []
    return _manifest_declared_skill_roots(search_path, data.get("skills"))


def _manifest_declared_skill_roots(base_path: Path, skills: object) -> list[Path]:
    if not isinstance(skills, list):
        return []

    roots: list[Path] = []
    for skill_path in skills:
        if not isinstance(skill_path, str):
            continue
        resolved = _safe_relative_dir(base_path, skill_path)
        if resolved is not None:
            roots.append(resolved.parent)
    return roots


def _safe_relative_dir(base_path: Path | None, relative: str) -> Path | None:
    if base_path is None or not relative.startswith("./"):
        return None
    resolved = (base_path / relative).resolve()
    try:
        resolved.relative_to(base_path.resolve())
    except ValueError:
        return None
    return resolved


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
