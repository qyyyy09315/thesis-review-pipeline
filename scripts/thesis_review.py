"""CLI for the undergraduate thesis review workflow."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from ingest import ingest_file, slugify
from linter import lint_file, render_markdown
from render import render_report
from worklog import append_worklog
from workspace import create_run, load_meta, relpath, save_meta

ROOT = Path(__file__).resolve().parents[1]
PAPER_AUDIT = Path.home() / ".agents" / "skills" / "paper-audit" / "scripts" / "audit.py"


def cmd_ingest(args: argparse.Namespace) -> int:
    dest = ingest_file(args.file, Path(args.out_dir))
    append_worklog(f"ingest `{relpath(args.file)}` → `{relpath(dest)}`")
    print(dest)
    return 0


def cmd_lint(args: argparse.Namespace) -> int:
    result = lint_file(args.file)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(render_markdown(result))
    append_worklog(
        f"lint `{relpath(args.file)}`：未定义符号 {len(result.undefined_symbols)}，"
        f"过强断言 {len(result.overclaims)}，结构缺口 {len(result.structure_gaps)}"
    )
    return 0


def cmd_init_run(args: argparse.Namespace) -> int:
    src = Path(args.file)
    ingest_dir = Path(args.ingest_dir) if args.ingest_dir else ROOT / "ingest"
    ingest_md = ingest_file(src, ingest_dir)
    slug = slugify(src.stem)
    title = args.title or ingest_md.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
    run_dir = create_run(
        paper_src=src,
        ingest_md=ingest_md,
        slug=slug,
        title=title,
        field=args.field,
        runs_dir=Path(args.runs_dir) if args.runs_dir else None,
    )
    paper_md = run_dir / "paper.md"
    lint = lint_file(paper_md)
    (run_dir / "stage1" / "linter.json").write_text(
        json.dumps(lint.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (run_dir / "stage1" / "linter.md").write_text(render_markdown(lint), encoding="utf-8")
    report = render_report(run_dir)
    meta = load_meta(run_dir)
    meta["stage"] = "stage1-complete"
    meta["grade"] = json.loads((run_dir / "stage3" / "render_context.json").read_text(encoding="utf-8")).get(
        "grade"
    )
    save_meta(run_dir, meta)
    append_worklog(
        f"init-run `{src.name}` → `{run_dir.name}`，定级 {meta.get('grade')}，报告 `{report.name}`",
        run_dir=run_dir,
        extra=(
            f"- ingest: `{relpath(ingest_md)}`\n"
            f"- linter: `{relpath(run_dir / 'stage1' / 'linter.json')}`"
        ),
    )
    print(run_dir)
    print(report)
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir)
    dest = render_report(run_dir)
    append_worklog(f"render `{run_dir.name}` → `{relpath(dest)}`", run_dir=run_dir)
    print(dest)
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    src = Path(args.file)
    if src.suffix.lower() not in {".tex", ".typ", ".pdf"}:
        print("paper-audit 仅支持 .tex / .typ / .pdf。docx/md 请用 init-run。", file=sys.stderr)
        return 2
    if not PAPER_AUDIT.exists():
        print(f"未找到 paper-audit：{PAPER_AUDIT}", file=sys.stderr)
        return 2
    out_dir = Path(args.out_dir) if args.out_dir else ROOT / "runs" / f"paper-audit-{slugify(src.stem)}"
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-B",
        str(PAPER_AUDIT),
        str(src),
        "--mode",
        args.mode,
        "--lang",
        args.lang,
    ]
    if src.suffix.lower() == ".pdf":
        cmd.extend(["--pdf-mode", args.pdf_mode])
    proc = subprocess.run(cmd, cwd=str(PAPER_AUDIT.parent), capture_output=True, text=True)
    (out_dir / "audit_stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (out_dir / "audit_stderr.txt").write_text(proc.stderr, encoding="utf-8")
    append_worklog(
        f"paper-audit {args.mode} `{src.name}` rc={proc.returncode} → `{relpath(out_dir)}`",
        extra="默认离线。未传 --online。日志只记文件名，不写本机绝对路径。",
    )
    print(proc.stdout)
    if proc.returncode:
        print(proc.stderr, file=sys.stderr)
    return proc.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="本科毕业设计审稿工作流")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ing = sub.add_parser("ingest", help="把论文归一成 Markdown")
    p_ing.add_argument("file", type=Path)
    p_ing.add_argument("--out-dir", default=str(ROOT / "ingest"))
    p_ing.set_defaults(func=cmd_ingest)

    p_lint = sub.add_parser("lint", help="Stage 1 机械预检")
    p_lint.add_argument("file", type=Path)
    p_lint.add_argument("--json", action="store_true")
    p_lint.set_defaults(func=cmd_lint)

    p_init = sub.add_parser("init-run", help="创建一次审稿 run：ingest+lint+骨架+初稿报告")
    p_init.add_argument("file", type=Path)
    p_init.add_argument("--title", default="")
    p_init.add_argument("--field", default="未标注")
    p_init.add_argument("--runs-dir", default="")
    p_init.add_argument("--ingest-dir", default="")
    p_init.set_defaults(func=cmd_init_run)

    p_ren = sub.add_parser("render", help="根据 agents/*.json 渲染四段式报告")
    p_ren.add_argument("run_dir", type=Path)
    p_ren.set_defaults(func=cmd_render)

    p_aud = sub.add_parser("audit", help="可选：调用 paper-audit（仅 tex/typ/pdf）")
    p_aud.add_argument("file", type=Path)
    p_aud.add_argument("--mode", default="quick-audit")
    p_aud.add_argument("--lang", default="zh")
    p_aud.add_argument("--pdf-mode", default="enhanced")
    p_aud.add_argument("--out-dir", default="")
    p_aud.set_defaults(func=cmd_audit)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
