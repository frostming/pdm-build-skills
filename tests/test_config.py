from __future__ import annotations

from pdm_build_bub.config import normalize_git_url, parse_skill_sources


def test_parse_skill_sources() -> None:
    data = {
        "tool": {
            "bub": {
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

    sources = parse_skill_sources(data)

    assert len(sources) == 2
    assert sources[0].normalized_git == "https://github.com/PsiACE/skills.git"
    assert sources[1].ref == "v1.0.0"
    assert sources[1].include == ("python*",)


def test_normalize_git_url_keeps_local_paths(tmp_path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    assert normalize_git_url(str(repo)) == str(repo)
