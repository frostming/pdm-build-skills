from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from pdm.backend.hooks.base import Context

from pdm_build_bub.backend import BubBuildHook


def test_build_hook_updates_wheel_files(skill_repo: Path, tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "pyproject.toml").write_text(
        "\n".join(
            [
                "[tool.bub]",
                "skills = [",
                f'  {{ git = "{skill_repo}", include = ["python*"] }},',
                "]",
            ]
        ),
        encoding="utf-8",
    )

    builder = SimpleNamespace(
        location=project_root,
        target="wheel",
        config_settings={},
        config=SimpleNamespace(),
    )
    context = Context(
        build_dir=tmp_path / "build",
        dist_dir=tmp_path / "dist",
        kwargs={},
        builder=builder,
    )
    files = {"bub_skills/python-alpha/SKILL.md": project_root / "old.txt"}

    hook = BubBuildHook()
    hook.pdm_build_update_files(context, files)

    assert sorted(files) == [
        "bub_skills/python-alpha/SKILL.md",
        "bub_skills/python-gamma/SKILL.md",
    ]
    assert (
        files["bub_skills/python-alpha/SKILL.md"].read_text(encoding="utf-8")
        == "alpha\n"
    )
