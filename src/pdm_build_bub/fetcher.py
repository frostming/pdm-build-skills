from __future__ import annotations

import fnmatch
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .config import SkillSource


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
        with tempfile.TemporaryDirectory(prefix="pdm-build-bub-") as clone_dir:
            repo_dir = _clone_repository(source, Path(clone_dir))
            for skill_dir in _iter_skill_directories(repo_dir, source.include):
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


def _iter_skill_directories(repo_dir: Path, include: tuple[str, ...]) -> list[Path]:
    skills_root = repo_dir / "skills"
    if not skills_root.is_dir():
        raise ValueError(f"Repository {repo_dir} does not contain a skills/ directory")

    skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir())
    if not include:
        return skill_dirs
    return [
        path
        for path in skill_dirs
        if any(fnmatch.fnmatch(path.name, pattern) for pattern in include)
    ]
