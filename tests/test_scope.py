from scope import render_plan, select_checks

SCOPE = {
    "areas": [
        {
            "id": "ingest",
            "globs": ["scripts/ingest.py"],
            "checks": ["pytest tests/test_ingest.py"],
        },
        {
            "id": "linter",
            "globs": ["scripts/linter.py"],
            "checks": ["pytest tests/test_linter.py"],
        },
    ],
    "release_checks": ["python scripts/thesis_review.py check"],
}


def test_known_change_skips_unchanged_area():
    plan = select_checks(["scripts/ingest.py"], SCOPE)
    assert plan["run"] == ["pytest tests/test_ingest.py"]
    assert plan["skip"] == [{"id": "linter", "reason": "依赖未变，沿用已有证据"}]
    assert plan["release_checks"] == []
    text = render_plan(plan)
    assert "依赖未变" in text


def test_unknown_path_asks_for_release_checks():
    plan = select_checks(["notes/extra.md"], SCOPE)
    assert plan["unmatched"] == ["notes/extra.md"]
    assert plan["release_checks"] == ["python scripts/thesis_review.py check"]
    assert "未登记路径" in plan["release_reason"]


def test_directory_glob_matches_nested_template():
    scope = {
        "areas": [
            {
                "id": "render",
                "globs": ["templates/**"],
                "checks": ["pytest tests/test_render.py"],
            }
        ],
        "release_checks": [],
    }
    plan = select_checks(["templates/agents/agent_c_experiments.md"], scope)
    assert plan["run"] == ["pytest tests/test_render.py"]
    assert plan["release_checks"] == []
