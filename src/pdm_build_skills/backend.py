from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Literal, overload

from .config import load_skill_sources
from .fetcher import materialize_sources

if TYPE_CHECKING:
    from pdm.backend.hooks import BuildHookInterface
    from pdm.backend.hooks.base import Context
else:
    BuildHookInterface = object
    Context = object


class SkillsBuildHook(BuildHookInterface):
    SKILL_DIR = "skills"

    def pdm_build_hook_enabled(self, context: Context) -> bool:
        if context.target not in ("wheel", "editable"):
            return False
        pyproject_path = context.root / "pyproject.toml"
        return pyproject_path.is_file()

    def pdm_build_clean(self, context: Context) -> None:
        build_root = self._build_root(context, create=False)
        if build_root is not None and build_root.exists():
            shutil.rmtree(build_root)

    def pdm_build_update_files(self, context: Context, files: dict[str, Path]) -> None:
        sources = load_skill_sources(context.root / "pyproject.toml")
        if not sources:
            return

        staging_root = self._build_root(context)
        assert staging_root is not None
        if staging_root.exists():
            shutil.rmtree(staging_root)
        materialize_sources(sources, staging_root)

        for path in sorted(staging_root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(staging_root)
            files[(Path(self.SKILL_DIR) / relative).as_posix()] = path

    def pdm_build_finalize(self, context: Context, artifact: Path) -> None:
        build_root = self._build_root(context, create=False)
        if build_root is not None and build_root.exists():
            shutil.rmtree(build_root)

    @staticmethod
    @overload
    def _build_root(context: Context, create: Literal[True] = True) -> Path: ...

    @staticmethod
    @overload
    def _build_root(context: Context, create: Literal[False]) -> Path | None: ...

    @staticmethod
    def _build_root(context: Context, create: bool = True) -> Path | None:
        existing = getattr(context, "_skills_build_root", None)
        if existing is not None:
            return existing
        if not create:
            return None

        build_root = Path(tempfile.mkdtemp(prefix="pdm-build-skills-"))
        setattr(context, "_skills_build_root", build_root)
        return build_root
