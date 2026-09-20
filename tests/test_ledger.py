import ledger


def test_add_and_close_roundtrip(tmp_path):
    path = tmp_path / "ledger.json"
    issue = ledger.add_issue(
        severity="minor",
        location="5.6 第三段",
        problem="表述超出对齐实验支持范围",
        run_id="v20",
        path=path,
    )
    assert issue["id"] == "N-01"
    second = ledger.add_issue(
        severity="major", location="3.5", problem="消融与主流程互斥", path=path
    )
    assert second["id"] == "M-01"
    closed = ledger.close_issue("N-01", run_id="v21", note="已按口径改写", path=path)
    assert closed is not None
    assert closed["status"] == "closed"
    assert closed["closed_in"] == "v21"
    assert [i["id"] for i in ledger.open_issues(path)] == ["M-01"]


def test_severity_prefix_sequence(tmp_path):
    path = tmp_path / "ledger.json"
    a = ledger.add_issue(severity="major", location="x", problem="1", path=path)
    b = ledger.add_issue(severity="major", location="y", problem="2", path=path)
    assert (a["id"], b["id"]) == ("M-01", "M-02")


def test_close_unknown_or_closed_id_returns_none(tmp_path):
    path = tmp_path / "ledger.json"
    assert ledger.close_issue("M-99", path=path) is None
    ledger.add_issue(severity="minor", location="l", problem="p", path=path)
    ledger.close_issue("N-01", path=path)
    assert ledger.close_issue("N-01", path=path) is None


def test_render_surfaces_open_ledger(tmp_path, monkeypatch):
    import json

    from ingest import ingest_file, slugify
    from linter import lint_file
    from workspace import create_run
    import render as render_mod
    from render import render_report

    fixture = tmp_path / "paper.md"
    fixture.write_text("# 测试\n\n正文一句话。", encoding="utf-8")
    ingest_md = ingest_file(fixture, tmp_path / "ingest")
    run_dir = create_run(
        paper_src=fixture,
        ingest_md=ingest_md,
        slug=slugify(fixture.stem),
        title="测试",
        field="计算机",
        runs_dir=tmp_path / "runs",
    )
    lint = lint_file(run_dir / "paper.md")
    (run_dir / "stage1" / "linter.json").write_text(
        json.dumps(lint.to_dict(), ensure_ascii=False), encoding="utf-8"
    )
    ledger_path = tmp_path / "docs" / "ledger.json"
    ledger.add_issue(
        severity="minor", location="5.6", problem="遗留表述", run_id="v20", path=ledger_path
    )
    monkeypatch.setattr(
        render_mod, "open_issues", lambda: ledger.open_issues(ledger_path)
    )
    report = render_report(run_dir)
    text = report.read_text(encoding="utf-8")
    assert "跨轮遗留" in text
    assert "N-01" in text
