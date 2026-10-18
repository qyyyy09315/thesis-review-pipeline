import delivery


def test_new_ids_ignore_severity(tmp_path):
    path = tmp_path / "delivery.json"
    major = delivery.add_item(
        item_type="defect",
        problem="类别索引用错了",
        mentions=["@qyyyy09315"],
        severity="major",
        path=path,
    )
    minor = delivery.add_item(
        item_type="improvement",
        problem="补一条成功路径测试",
        mentions=["@acme/review-pipeline"],
        severity="minor",
        path=path,
    )
    assert (major["id"], minor["id"]) == ("R-01", "R-02")
    assert major["status"] == "candidate"


def test_add_item_requires_mention(tmp_path):
    path = tmp_path / "delivery.json"
    try:
        delivery.add_item(item_type="defect", problem="没人接", mentions=[], path=path)
    except ValueError as exc:
        assert "@" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_status_stays_specific_and_id_is_stable(tmp_path):
    path = tmp_path / "delivery.json"
    item = delivery.add_item(
        item_type="claim",
        problem="修复后是否仍达到原分数",
        mentions=["@qyyyy09315"],
        track="algorithm",
        path=path,
    )
    moved = delivery.set_status(
        item["id"],
        "impl_pending_experiment",
        note="实现已核对，实验还没跑",
        path=path,
    )
    assert moved is not None
    assert moved["id"] == "R-01"
    assert moved["status"] == "impl_pending_experiment"
    accepted = delivery.add_item(
        item_type="accepted_limit",
        problem="保留随机切片早停并写明范围",
        mentions=["@qyyyy09315"],
        status="accepted",
        path=path,
    )
    counts = delivery.summarize(delivery.load_delivery(path))
    assert counts["by_status"]["impl_pending_experiment"] == 1
    assert counts["by_status"]["accepted"] == 1
    assert accepted["id"] == "R-02"


def test_overview_does_not_treat_a_closed_track_as_ready(tmp_path):
    path = tmp_path / "delivery.json"
    delivery.set_project(
        {
            "decision": "是否开始最小重跑",
            "deliverable_now": "系统缺陷已登记闭环",
            "unverified": "修复后的算法精度",
            "next_action": "冻结修复版，做最小 12k 重跑",
        },
        path=path,
    )
    delivery.add_item(
        item_type="claim",
        problem="新算法精度尚未产生",
        mentions=["@qyyyy09315"],
        track="algorithm",
        status="impl_pending_experiment",
        path=path,
    )
    text = delivery.render_overview(delivery.load_delivery(path))
    assert "本轮只回答：是否开始最小重跑" in text
    assert "不表示毕设可以放行" in text
    assert "@qyyyy09315" in text
    assert "待验证主张" in text
    assert "实现通过待实验" in text
    assert "首轮四条最小证据尚未齐" in text


def test_import_v1_closed_is_not_a_fix(tmp_path):
    path = tmp_path / "delivery.json"
    added = delivery.import_v1(
        {
            "issues": [
                {
                    "id": "M-01",
                    "severity": "major",
                    "status": "closed",
                    "location": "3.2",
                    "problem": "旧记录",
                }
            ]
        },
        mention="@qyyyy09315",
        track="paper",
        path=path,
    )
    assert added[0]["id"] == "M-01"
    assert added[0]["status"] == "superseded"
    assert "不得当成已经修复" in added[0]["note"]
    again = delivery.import_v1(
        {"issues": [{"id": "M-01", "severity": "major", "status": "closed", "problem": "旧记录"}]},
        mention="@qyyyy09315",
        track="paper",
        path=path,
    )
    assert again == []
