from pathlib import Path

from ingest import ingest_file, slugify

FIXTURE = Path(__file__).parent / "fixtures" / "sample_thesis.md"


def test_slugify_keeps_cjk():
    assert "注意力" in slugify("基于改进注意力机制")


def test_ingest_markdown_roundtrip(tmp_path: Path):
    dest = ingest_file(FIXTURE, tmp_path)
    text = dest.read_text(encoding="utf-8")
    assert "图像分类" in text
    assert dest.suffix == ".md"
