from __future__ import annotations

from pathlib import Path
import subprocess

import pytest


def _run_git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    )


@pytest.fixture()
def skill_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "skill-repo"
    repo.mkdir()
    _run_git(repo, "init")
    _run_git(repo, "config", "user.email", "tests@example.com")
    _run_git(repo, "config", "user.name", "Tests")

    (repo / "skills" / "python-alpha").mkdir(parents=True)
    (repo / "skills" / "python-alpha" / "SKILL.md").write_text(
        "alpha\n", encoding="utf-8"
    )
    (repo / "skills" / "js-beta").mkdir(parents=True)
    (repo / "skills" / "js-beta" / "SKILL.md").write_text("beta\n", encoding="utf-8")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-m", "initial")
    _run_git(repo, "tag", "v1.0.0")

    (repo / "skills" / "python-gamma").mkdir(parents=True)
    (repo / "skills" / "python-gamma" / "SKILL.md").write_text(
        "gamma\n", encoding="utf-8"
    )
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-m", "add gamma")
    return repo
