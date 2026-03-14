from __future__ import annotations

from pdm_build_skills.config import normalize_git_url, parse_skill_sources


def test_parse_skill_sources() -> None:
    data = {
        "tool": {
            "pdm": {
                "build": {
                    "skills": [
                        "PsiACE/skills",
                        {
                            "git": "https://example.com/repo.git",
                            "ref": "v1.0.0",
                            "include": ["python*"],
                        },
                    ]
                }
            }
        }
    }

    sources = parse_skill_sources(data)

    assert len(sources) == 2
    assert sources[0].normalized_git == "https://github.com/PsiACE/skills.git"
    assert sources[1].ref == "v1.0.0"
    assert sources[1].include == ("python*",)


def test_normalize_git_url_keeps_local_paths(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    assert normalize_git_url(str(repo)) == str(repo)


def test_parse_skill_sources_supports_explicit_subpath() -> None:
    data = {
        "tool": {
            "pdm": {
                "build": {
                    "skills": [
                        {
                            "git": "vercel-labs/agent-skills",
                            "subpath": "skills/review",
                        }
                    ]
                }
            }
        }
    }

    sources = parse_skill_sources(data)

    assert [source.git for source in sources] == [
        "https://github.com/vercel-labs/agent-skills.git"
    ]
    assert sources[0].subpath == "skills/review"
