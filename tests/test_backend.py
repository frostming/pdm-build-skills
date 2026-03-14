from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from pdm.backend.hooks.base import Context

from pdm_build_skills.backend import SkillsBuildHook


def _make_context(project_root: Path, tmp_path: Path, target: str) -> Context:
    builder = SimpleNamespace(
        location=project_root,
        target=target,
        config_settings={},
        config=SimpleNamespace(),
    )
    return Context(
        build_dir=tmp_path / "build",
        dist_dir=tmp_path / "dist",
        kwargs={},
        builder=builder,
    )


def _make_project(project_root: Path, skill_repo: Path) -> None:
    project_root.mkdir()
    (project_root / "pyproject.toml").write_text(
        "\n".join(
            [
                "[tool.pdm.build]",
                "skills = [",
                f'  {{ git = "{skill_repo}", include = ["python*"] }},',
                "]",
            ]
        ),
        encoding="utf-8",
    )


def test_build_hook_enabled_for_wheel_and_editable(
    skill_repo: Path, tmp_path: Path
) -> None:
    project_root = tmp_path / "project"
    _make_project(project_root, skill_repo)

    hook = SkillsBuildHook()

    assert hook.pdm_build_hook_enabled(_make_context(project_root, tmp_path, "wheel"))
    assert hook.pdm_build_hook_enabled(
        _make_context(project_root, tmp_path, "editable")
    )
    assert not hook.pdm_build_hook_enabled(
        _make_context(project_root, tmp_path, "sdist")
    )


def test_build_hook_updates_wheel_files(skill_repo: Path, tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _make_project(project_root, skill_repo)

    context = _make_context(project_root, tmp_path, "wheel")
    files = {"skills/python-alpha/SKILL.md": project_root / "old.txt"}

    hook = SkillsBuildHook()
    hook.pdm_build_update_files(context, files)

    assert sorted(files) == [
        "skills/python-alpha/SKILL.md",
        "skills/python-gamma/SKILL.md",
    ]
    assert (
        files["skills/python-alpha/SKILL.md"].read_text(encoding="utf-8") == "alpha\n"
    )


def test_build_hook_updates_editable_files(skill_repo: Path, tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _make_project(project_root, skill_repo)

    context = _make_context(project_root, tmp_path, "editable")
    files = {"skills/python-alpha/SKILL.md": project_root / "old.txt"}

    hook = SkillsBuildHook()
    hook.pdm_build_update_files(context, files)

    assert sorted(files) == [
        "skills/python-alpha/SKILL.md",
        "skills/python-gamma/SKILL.md",
    ]
    assert (
        files["skills/python-alpha/SKILL.md"].read_text(encoding="utf-8") == "alpha\n"
    )
