"""CLI for the undergraduate thesis review workflow."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import ledger
import worklog
from ingest import ingest_file, slugify
from linter import lint_file, render_markdown
from render import render_report
from workspace import create_run, load_meta, relpath, save_meta

ROOT = Path(__file__).resolve().parents[1]
PAPER_AUDIT = Path.home() / ".agents" / "skills" / "paper-audit" / "scripts" / "audit.py"


def cmd_ingest(args: argparse.Namespace) -> int:
    dest = ingest_file(args.file, Path(args.out_dir), versioned=args.versioned)
    worklog.append_worklog(f"ingest `{relpath(args.file)}` → `{relpath(dest)}`")
    print(dest)
    return 0


def cmd_lint(args: argparse.Namespace) -> int:
    result = lint_file(args.file)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(render_markdown(result))
    worklog.append_worklog(
        f"lint `{relpath(args.file)}`：未定义符号 {len(result.undefined_symbols)}，"
        f"过强断言 {len(result.overclaims)}，结构缺口 {len(result.structure_gaps)}"
    )
    return 0


def cmd_init_run(args: argparse.Namespace) -> int:
    src = Path(args.file)
    ingest_dir = Path(args.ingest_dir) if args.ingest_dir else ROOT / "ingest"
    ingest_md = ingest_file(src, ingest_dir, versioned=args.versioned)
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
    suggested = json.loads((run_dir / "stage3" / "render_context.json").read_text(encoding="utf-8")).get(
        "grade"
    )
    meta["stage"] = "stage1-complete"
    meta["grade"] = "待深审"
    meta["grade_suggested"] = suggested
    save_meta(run_dir, meta)
    worklog.append_worklog(
        f"init-run `{src.name}` → `{run_dir.name}`，待深审（机械预检建议定级 {suggested}），报告 `{report.name}`",
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
    worklog.append_worklog(f"render `{run_dir.name}` → `{relpath(dest)}`", run_dir=run_dir)
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
    worklog.append_worklog(
        f"paper-audit {args.mode} `{src.name}` rc={proc.returncode} → `{relpath(out_dir)}`",
        extra="默认离线。未传 --online。日志只记文件名，不写本机绝对路径。",
    )
    print(proc.stdout)
    if proc.returncode:
        print(proc.stderr, file=sys.stderr)
    return proc.returncode


def cmd_sanitize(args: argparse.Namespace) -> int:
    targets = [worklog.GLOBAL_LOG] + [Path(p) for p in args.extra]
    total = 0
    for path in targets:
        if not path.exists():
            print(f"跳过（不存在）：{relpath(path)}")
            continue
        text = path.read_text(encoding="utf-8")
        cleaned = worklog.scrub_local_paths(text)
        if cleaned != text:
            path.write_text(cleaned, encoding="utf-8")
            n = sum(
                1 for _ in worklog.ABS_PATH_RE.finditer(text)
            )
            total += n
            print(f"清洗 {relpath(path)}：{n} 处绝对路径")
        else:
            print(f"已是干净状态：{relpath(path)}")
    if total:
        worklog.append_worklog(f"sanitize 清洗绝对路径 {total} 处（docs/worklog.md 等）")
    return 0


def cmd_ledger(args: argparse.Namespace) -> int:
    path = Path(args.ledger) if args.ledger else None
    if args.action == "add":
        issue = ledger.add_issue(
            severity=args.severity,
            location=args.location,
            problem=args.problem,
            run_id=args.run,
            path=path,
        )
        worklog.append_worklog(f"ledger add {issue['id']}：{issue['location']} — {issue['problem'][:80]}")
        print(f"{issue['id']} ({issue['status']}) {issue['location']}")
    elif args.action == "close":
        issue = ledger.close_issue(args.id, run_id=args.run, note=args.note, path=path)
        if issue is None:
            print(f"未找到 open 状态的 {args.id}", file=sys.stderr)
            return 1
        worklog.append_worklog(f"ledger close {issue['id']}（{issue['closed_in']}）{('：' + issue['close_note']) if issue['close_note'] else ''}")
        print(f"{issue['id']} closed in {issue['closed_in']}")
    else:
        data = ledger.load_ledger(path)
        issues = data.get("issues", [])
        rows = issues if args.all else [i for i in issues if i.get("status") == "open"]
        if not rows:
            print("（无匹配 issue）")
        for issue in rows:
            print(
                f"{issue['id']}  {issue['status']:<6}  {issue['severity']:<5}  "
                f"{issue['location']}  {issue['problem'][:60]}"
            )
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    del args  # doctor takes no options today; kept for parser symmetry.
    problems: list[str] = []
    runs_root = ROOT / "runs"
    log_text = (
        worklog.GLOBAL_LOG.read_text(encoding="utf-8")
        if worklog.GLOBAL_LOG.exists()
        else ""
    )
    for meta_path in sorted(runs_root.glob("*/metadata.json")):
        run_id = meta_path.parent.name
        if run_id not in log_text:
            problems.append(f"[worklog] run 无日志记录: {run_id}")
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        for key in ("source", "ingest"):
            value = str(meta.get(key) or "")
            if worklog.ABS_PATH_RE.fullmatch(value) or value.startswith(("F:/", "F:\\", "C:/", "C:\\")):
                problems.append(f"[privacy] {run_id} metadata.{key} 含绝对路径: {value}")
    if log_text:
        for leak in worklog.ABS_PATH_RE.finditer(log_text):
            problems.append(f"[privacy] docs/worklog.md 含绝对路径: {leak.group(0)}")
    for cons_path in sorted(runs_root.glob("*/agents/consolidator.json")):
        cons = json.loads(cons_path.read_text(encoding="utf-8"))
        status = str(cons.get("status", "")).lower()
        if status not in {"pending", "done"}:
            run_id = cons_path.parents[1].name
            problems.append(f"[schema] {run_id} consolidator.status 异常: {cons.get('status')!r}")
    if problems:
        print("\n".join(problems))
        print(f"\ndoctor：发现 {len(problems)} 个问题。")
        return 1
    print("doctor：一切正常。")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="本科毕业设计审稿工作流")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ing = sub.add_parser("ingest", help="把论文归一成 Markdown")
    p_ing.add_argument("file", type=Path)
    p_ing.add_argument("--out-dir", default=str(ROOT / "ingest"))
    p_ing.add_argument(
        "--versioned",
        action="store_true",
        help="输出文件名追加时间戳后缀，避免同名覆盖丢失历史版本",
    )
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
    p_init.add_argument("--versioned", action="store_true")
    p_init.set_defaults(func=cmd_init_run)

    p_ren = sub.add_parser("render", help="根据 agents/*.json 渲染四段式报告")
    p_ren.add_argument("run_dir", type=Path)
    p_ren.set_defaults(func=cmd_render)

    p_san = sub.add_parser("sanitize", help="清洗 docs/worklog.md 等文件中的本机绝对路径")
    p_san.add_argument("extra", nargs="*", help="可选：额外要清洗的文件路径")
    p_san.set_defaults(func=cmd_sanitize)

    p_led = sub.add_parser("ledger", help="跨轮问题台账：add / close / list")
    p_led.add_argument("action", choices=["add", "close", "list"])
    p_led.add_argument("--severity", choices=["major", "minor"], default="major")
    p_led.add_argument("--location", default="")
    p_led.add_argument("--problem", default="")
    p_led.add_argument("--id", default="")
    p_led.add_argument("--run", default="", help="关联的 run id（可省略）")
    p_led.add_argument("--note", default="", help="close 时的闭环说明")
    p_led.add_argument("--all", action="store_true", help="list 时包含已 closed")
    p_led.add_argument("--ledger", default="", help="自定义台账路径（默认 docs/ledger.json）")
    p_led.set_defaults(func=cmd_ledger)

    p_doc = sub.add_parser("doctor", help="体检：run 日志对账、绝对路径泄漏、consolidator 状态")
    p_doc.set_defaults(func=cmd_doctor)

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
