import pr_check
from mentions import extract_mentions, require_mentions


def test_extract_user_and_team_mentions():
    text = "请 @qyyyy09315 看，也请 @acme/review-pipeline 看。邮件 dev@example.com 不算。"
    assert extract_mentions(text) == ["@qyyyy09315", "@acme/review-pipeline"]


def test_require_mentions_rejects_empty():
    try:
        require_mentions("这里没有点名")
    except ValueError as exc:
        assert "@" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_pr_body_requires_sections_and_mention():
    body = "\n".join(
        [
            "## 摘要",
            "补上交付总览。",
            "## 动机",
            "关闭数不能代表可交付。",
            "## 改动",
            "新增条目状态。",
            "## 测试",
            "pytest tests/test_pr_check.py",
            "## 决定",
            "本 PR 只回答流水线是否分开记录类型和状态。",
            "## 隐私",
            "不含个人稿件与具体审稿记录",
            "",
            "@qyyyy09315",
        ]
    )
    assert pr_check.check_pull_request("feat(delivery): 分开类型和状态", body) == []


def test_script_entry_reads_environment(monkeypatch):
    monkeypatch.setenv("PR_TITLE", "feat: 示例")
    monkeypatch.setenv(
        "PR_BODY",
        "## 摘要\n\n## 动机\n\n## 改动\n\n## 测试\n\n## 决定\n\n## 隐私\n\n不含个人稿件\n\n@qyyyy09315\n",
    )
    assert pr_check.main() == 0


def test_pr_check_rejects_missing_mention_and_bad_title():
    body = "## 摘要\n\n## 动机\n\n## 改动\n\n## 测试\n\n## 决定\n\n没有点名\n"
    errors = pr_check.check_pull_request("update stuff", body)
    assert any("约定式" in item for item in errors)
    assert any("@name" in item for item in errors)
    assert any("不含个人稿件" in item for item in errors)


def test_redacted_or_authorized_attestation_is_enough():
    common = "## 摘要\n\n## 动机\n\n## 改动\n\n## 测试\n\n## 决定\n\n## 隐私\n\n@qyyyy09315\n"
    assert pr_check.check_pull_request("docs: 说明", common + "已脱敏，范围是样例分数。") == []
    assert pr_check.check_pull_request("docs: 说明", common + "已获授权，只含目录名。") == []
