# pdm-build-skills

`pdm-build-skills` is a `pdm-backend` build hook that downloads skill repositories declared in `pyproject.toml` and vendors them into built wheel and editable artifacts under `skills/`.

## Installation

Add the plugin to the project that produces the wheel:

```toml
[build-system]
requires = ["pdm-backend", "pdm-build-skills"]
build-backend = "pdm.backend"
```

## Configuration

Declare sources in `pyproject.toml`:

```toml
[tool.pdm.build]
skills = [
    "PsiACE/skills",
    { git = "https://github.com/PsiACE/skills.git", ref = "v1.0.0", include = ["python*"] },
    { git = "vercel-labs/agent-skills", subpath = "skills/find-skills" },
]
```

Supported source formats:

- Full Git URLs such as `https://github.com/PsiACE/skills.git`
- GitHub shorthand in `OWNER/REPO` form such as `PsiACE/skills`

Discovery roughly follows the `npm skills` package:

- If the selected path itself contains `SKILL.md`, it is treated as one skill.
- Otherwise it searches common skill roots such as `skills/`, `skills/.curated/`, `.codex/skills/`, `.claude/skills/`, `.agents/skills/` and similar agent-specific locations.
- If nothing is found in standard locations, it falls back to a bounded recursive search.

`include` filters by discovered skill directory name with standard shell-style globs.

If you need to point at a specific directory inside a repository, use the table form with `subpath`.

When the wheel already contains files under `skills/`, files coming from the plugin override matching paths.


This downloads the configured skills into `./skills`. Use `--output /path/to/dir` to choose another directory.

## Development

Run tests with:

```bash
python -m pytest
```

Build the package with:

```bash
python -m build
```
