"""Normalize thesis drafts into UTF-8 Markdown."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


SUPPORTED = {".md", ".markdown", ".txt", ".tex", ".typ", ".pdf", ".docx"}


def slugify(value: str) -> str:
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", value, flags=re.UNICODE).strip("-").lower()
    return slug or "paper"


def ingest_file(src: Path, dest_dir: Path) -> Path:
    src = src.resolve()
    if not src.is_file():
        raise FileNotFoundError(src)
    suffix = src.suffix.lower()
    if suffix not in SUPPORTED:
        raise ValueError(f"不支持的格式: {suffix}. 支持 {sorted(SUPPORTED)}")
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{slugify(src.stem)}.md"
    if suffix in {".md", ".markdown", ".txt", ".tex", ".typ"}:
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        return dest
    if suffix == ".docx":
        dest.write_text(_from_docx(src), encoding="utf-8")
        return dest
    if suffix == ".pdf":
        dest.write_text(_from_pdf(src), encoding="utf-8")
        return dest
    raise ValueError(suffix)


def _from_docx(path: Path) -> str:
    try:
        import mammoth
        from markdownify import markdownify as to_md
    except ImportError as exc:
        raise RuntimeError("DOCX 解析需要 mammoth 与 markdownify，请 pip install -r requirements.txt") from exc
    with path.open("rb") as handle:
        html = mammoth.convert_to_html(handle).value
    return to_md(html, heading_style="ATX")


def _from_pdf(path: Path) -> str:
    try:
        import pymupdf4llm
    except ImportError:
        pymupdf4llm = None
    if pymupdf4llm is not None:
        return pymupdf4llm.to_markdown(str(path))
    try:
        import pymupdf
    except ImportError as exc:
        raise RuntimeError("PDF 解析需要 pymupdf 或 pymupdf4llm") from exc
    doc = pymupdf.open(path)
    parts = [page.get_text("text") for page in doc]
    doc.close()
    return "\n\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest a thesis into Markdown")
    parser.add_argument("file", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("ingest"))
    args = parser.parse_args(argv)
    dest = ingest_file(args.file, args.out_dir)
    print(dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
