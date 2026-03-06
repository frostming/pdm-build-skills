# pdm-build-bub

`pdm-build-bub` is a `pdm-backend` build hook that downloads skill repositories declared in `pyproject.toml` and vendors them into the built wheel under `bub_skills/`.

## Installation

Add the plugin to the project that produces the wheel:

```toml
[build-system]
requires = ["pdm-backend", "pdm-build-bub"]
build-backend = "pdm.backend"
```

## Configuration

Declare sources in `pyproject.toml`:

```toml
[tool.bub]
skills = [
    "PsiACE/skills",
    { git = "https://github.com/PsiACE/skills.git", ref = "v1.0.0", include = ["python*"] },
]
```

Supported source formats:

- Full Git URLs such as `https://github.com/PsiACE/skills.git`
- GitHub shorthand in `OWNER/REPO` form such as `PsiACE/skills`

Each repository must contain a top-level `skills/` directory. Every direct child directory under `skills/` is treated as one skill. `include` filters by skill directory name with standard shell-style globs.

When the wheel already contains files under `bub_skills/`, files coming from the plugin override matching paths.


This downloads the configured skills into `./bub_skills`. Use `--output /path/to/dir` to choose another directory.

## Development

Run tests with:

```bash
python -m pytest
```

Build the package with:

```bash
python -m build
```
