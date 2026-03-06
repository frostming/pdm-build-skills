from __future__ import annotations

from pathlib import Path

from pdm_build_bub.config import SkillSource
from pdm_build_bub.fetcher import materialize_sources


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
