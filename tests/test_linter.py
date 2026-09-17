from pathlib import Path

from linter import lint_file, lint_text

FIXTURE = Path(__file__).parent / "fixtures" / "sample_thesis.md"


def test_sample_flags_undefined_lambda_and_alpha():
    result = lint_file(FIXTURE)
    symbols = {item.symbol for item in result.undefined_symbols}
    joined = " ".join(symbols)
    assert "lambda" in joined
    assert "alpha" in joined or any(item.symbol in {"R", "mathcalR"} for item in result.undefined_symbols)


def test_sample_flags_overclaims_without_numbers():
    result = lint_file(FIXTURE)
    codes = {item.code for item in result.overclaims}
    assert "OC1" in codes
    assert "OC3" in codes
    assert all(not item.has_number for item in result.overclaims if item.code in {"OC1", "OC3"})


def test_sample_flags_missing_ablation_and_related_work():
    result = lint_file(FIXTURE)
    keys = {g.key for g in result.structure_gaps}
    assert "ablation" in keys
    assert "related_work" in keys
    assert "variance" in keys
    assert "failure_case" in keys


def test_negated_ablation_still_counts_as_gap():
    text = "第四章 实验\n与 ResNet-18 对比。未做消融，未报告方差。"
    result = lint_text(text)
    keys = {g.key for g in result.structure_gaps}
    assert "ablation" in keys
    assert "variance" in keys


def test_positive_ablation_is_not_a_gap():
    text = "第四章 实验\n进行消融实验，报告均值±标准差，并分析失效案例。相关工作见第二章。"
    result = lint_text(text)
    keys = {g.key for g in result.structure_gaps}
    assert "ablation" not in keys
    assert "variance" not in keys
    assert "related_work" not in keys


def test_defined_symbol_is_not_flagged():
    text = "令 $L_{ce}$ 表示交叉熵。公式 $L_{ce}$ 再出现一次。"
    result = lint_text(text)
    symbols = {item.symbol for item in result.undefined_symbols}
    assert "L_ce" not in symbols
    assert "Lce" not in symbols
