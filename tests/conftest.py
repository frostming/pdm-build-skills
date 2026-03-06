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


@pytest.fixture()
def discovered_skill_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "discovered-skill-repo"
    repo.mkdir()
    _run_git(repo, "init")
    _run_git(repo, "config", "user.email", "tests@example.com")
    _run_git(repo, "config", "user.name", "Tests")

    (repo / ".codex" / "skills" / "codex-review").mkdir(parents=True)
    (repo / ".codex" / "skills" / "codex-review" / "SKILL.md").write_text(
        "codex-review\n", encoding="utf-8"
    )

    (repo / "plugins" / "docs" / "skills" / "docs-lint").mkdir(parents=True)
    (repo / "plugins" / "docs" / "skills" / "docs-lint" / "SKILL.md").write_text(
        "docs-lint\n", encoding="utf-8"
    )
    (repo / ".claude-plugin").mkdir()
    (repo / ".claude-plugin" / "marketplace.json").write_text(
        (
            "{"
            '"metadata": {"pluginRoot": "./plugins"},'
            '"plugins": ['
            '{"name": "docs", "source": "./docs", "skills": ["./skills/docs-lint"]}'
            "]"
            "}"
        ),
        encoding="utf-8",
    )

    (repo / "misc" / "deep" / "fallback-skill").mkdir(parents=True)
    (repo / "misc" / "deep" / "fallback-skill" / "SKILL.md").write_text(
        "fallback\n", encoding="utf-8"
    )

    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-m", "initial")
    return repo
