from __future__ import annotations

from pathlib import Path

from pdm_build_skills.config import SkillSource
from pdm_build_skills.fetcher import materialize_sources


def test_materialize_sources_honors_ref_and_include(
    skill_repo: Path, tmp_path: Path
) -> None:
    destination = tmp_path / "out"
    sources = [SkillSource(git=str(skill_repo), ref="v1.0.0", include=("python*",))]

    materialize_sources(sources, destination)

    assert (destination / "python-alpha" / "SKILL.md").read_text(
        encoding="utf-8"
    ) == "alpha\n"
    assert not (destination / "python-gamma").exists()
    assert not (destination / "js-beta").exists()


def test_later_sources_override_existing_skill(
    skill_repo: Path, tmp_path: Path
) -> None:
    destination = tmp_path / "out"
    sources = [
        SkillSource(git=str(skill_repo), ref="v1.0.0", include=("python-alpha",)),
        SkillSource(git=str(skill_repo), include=("python-alpha",)),
    ]

    materialize_sources(sources, destination)

    assert (destination / "python-alpha" / "SKILL.md").read_text(
        encoding="utf-8"
    ) == "alpha\n"


def test_materialize_sources_discovers_priority_skill_locations(
    discovered_skill_repo: Path, tmp_path: Path
) -> None:
    destination = tmp_path / "out"

    materialize_sources([SkillSource(git=str(discovered_skill_repo))], destination)

    assert (destination / "codex-review" / "SKILL.md").read_text(encoding="utf-8") == (
        "codex-review\n"
    )
    assert (destination / "docs-lint" / "SKILL.md").read_text(encoding="utf-8") == (
        "docs-lint\n"
    )
    assert not (destination / "fallback-skill").exists()


def test_materialize_sources_supports_subpath_selection(
    discovered_skill_repo: Path, tmp_path: Path
) -> None:
    destination = tmp_path / "out"
    source = SkillSource(git=str(discovered_skill_repo), subpath="misc/deep")

    materialize_sources([source], destination)

    assert (destination / "fallback-skill" / "SKILL.md").read_text(
        encoding="utf-8"
    ) == ("fallback\n")
    assert not (destination / "codex-review").exists()
