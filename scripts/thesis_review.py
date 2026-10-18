"""CLI for the undergraduate thesis review workflow."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import delivery
import ledger
import pr_check
import scope as review_scope
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
    targets = [worklog.PUBLIC_LOG, worklog.GLOBAL_LOG] + [Path(p) for p in args.extra]
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in targets:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    targets = unique
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


_CODE_STATUS_DONE = {"missing", "partial", "checked"}
_CODE_VERDICTS = {"match", "mismatch", "unverifiable"}
# 四维对账：实验数字 / 模型结构 / 超参数 / 实验设计。
_CODE_ASPECTS = ("number", "architecture", "hyperparameter", "design")
_CODE_ABSENCE_MARKERS = (
    "代码", "日志", "配置", "对账", "结果文件", "脚本", "csv", "CSV",
    "实现", "模型", "超参", "参数", "数据集", "划分",
)


def code_audit_problems(run_dir: Path) -> list[str]:
    """Flag a finished deep review that never tied its claims to code.

    Covers the four correspondence aspects: numbers, model architecture,
    hyperparameters and experiment design. Runs written before this field
    existed have no `code_status` and are skipped.
    """
    cons_path = run_dir / "agents" / "consolidator.json"
    agent_path = run_dir / "agents" / "agent_c_experiments.json"
    if not cons_path.is_file() or not agent_path.is_file():
        return []
    cons = json.loads(cons_path.read_text(encoding="utf-8"))
    if str(cons.get("status", "")).lower() != "done":
        return []
    agent_c = json.loads(agent_path.read_text(encoding="utf-8"))
    if "code_status" not in agent_c:
        return []
    run_id = run_dir.name
    status = str(agent_c.get("code_status") or "").strip().lower()
    if status not in _CODE_STATUS_DONE:
        return [
            f"[code] {run_id} 深审已 done，但 code_status={agent_c.get('code_status')!r}"
            "（须为 missing、partial 或 checked）"
        ]
    rows = agent_c.get("code_correspondence")
    if not isinstance(rows, list):
        return [f"[code] {run_id} code_correspondence 不是数组"]
    if status == "missing":
        note = str(agent_c.get("code_note") or "").strip()
        problems = []
        if not note:
            problems.append(f"[code] {run_id} code_status=missing 但 code_note 为空")
        if agent_c.get("quantitative_claims", True) and not _mentions_code_gap(cons, agent_c):
            problems.append(
                f"[code] {run_id} 定量结果无法对账，但 Major 未记录缺失的代码或结果文件"
            )
        return problems
    problems = []
    if not rows:
        problems.append(f"[code] {run_id} code_status={status} 但 code_correspondence 为空")
        return problems
    saw_unverifiable = False
    saw_mismatch = False
    covered_aspects: set[str] = set()
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            problems.append(f"[code] {run_id} 对账第 {index} 行不是对象")
            continue
        for key in ("claim", "aspect", "paper_ref", "paper_value", "code_ref", "verdict"):
            if not str(row.get(key) or "").strip():
                problems.append(f"[code] {run_id} 对账第 {index} 行缺 {key}")
        aspect = str(row.get("aspect") or "").strip().lower()
        if aspect in _CODE_ASPECTS:
            covered_aspects.add(aspect)
        elif aspect:
            problems.append(
                f"[code] {run_id} 对账第 {index} 行 aspect 非法: {row.get('aspect')!r}"
                "（须为 number / architecture / hyperparameter / design）"
            )
        verdict = str(row.get("verdict") or "").strip().lower()
        if verdict and verdict not in _CODE_VERDICTS:
            problems.append(f"[code] {run_id} 对账第 {index} 行 verdict 非法: {row.get('verdict')!r}")
        if verdict == "mismatch":
            saw_mismatch = True
            if "code_value" not in row or not str(row.get("code_value") or "").strip():
                problems.append(f"[code] {run_id} 对账第 {index} 行 mismatch 未给出 code_value")
            if not str(row.get("paper_quote") or "").strip():
                problems.append(
                    f"[code] {run_id} 对账第 {index} 行 mismatch 未给出 paper_quote"
                    "（原文摘引，供 Major 锚定）"
                )
        if verdict == "unverifiable":
            saw_unverifiable = True
    problems.extend(_aspect_coverage_problems(run_id, agent_c, covered_aspects))
    if status == "checked" and saw_unverifiable:
        problems.append(f"[code] {run_id} code_status=checked 仍有 unverifiable 行，应改为 partial")
    if saw_mismatch and not _mentions_code_gap(cons, agent_c):
        problems.append(f"[code] {run_id} 存在 mismatch，但 Major 未记录论文数字与代码不一致")
    return problems


def _aspect_coverage_problems(run_id: str, agent_c: dict, covered: set[str]) -> list[str]:
    """Each aspect needs a row or a written skip reason; theory papers drop `number`."""
    required = set(_CODE_ASPECTS)
    if not agent_c.get("quantitative_claims", True):
        required.discard("number")
    skipped_raw = agent_c.get("aspects_skipped")
    if skipped_raw is None:
        skipped_raw = {}
    if not isinstance(skipped_raw, dict):
        return [f"[code] {run_id} aspects_skipped 不是对象（aspect → 跳过理由）"]
    problems: list[str] = []
    skipped: set[str] = set()
    for key, reason in skipped_raw.items():
        key_norm = str(key).strip().lower()
        if key_norm not in _CODE_ASPECTS:
            problems.append(f"[code] {run_id} aspects_skipped 含未知维度 {key!r}")
            continue
        if not str(reason or "").strip():
            problems.append(f"[code] {run_id} aspects_skipped[{key_norm}] 未写跳过理由")
            continue
        skipped.add(key_norm)
    for aspect in sorted(required - covered - skipped):
        problems.append(
            f"[code] {run_id} 未对账维度 {aspect}"
            "（数字/结构/超参/设计须各有对账行，或在 aspects_skipped 写明理由）"
        )
    return problems


def _mentions_code_gap(cons: dict, agent_c: dict) -> bool:
    texts: list[str] = []
    for item in cons.get("majors") or []:
        if isinstance(item, dict):
            texts.append(str(item.get("problem") or ""))
            texts.append(str(item.get("location") or ""))
    for item in agent_c.get("findings") or []:
        if isinstance(item, dict) and str(item.get("severity", "")).lower() == "major":
            texts.append(str(item.get("problem") or ""))
            texts.append(str(item.get("location") or ""))
    blob = "\n".join(texts)
    return any(marker in blob for marker in _CODE_ABSENCE_MARKERS)


def cmd_doctor(args: argparse.Namespace) -> int:
    del args  # doctor takes no options today; kept for parser symmetry.
    problems: list[str] = []
    runs_root = ROOT / "runs"
    chunks: list[str] = []
    seen_logs: set[Path] = set()
    for path in (worklog.PUBLIC_LOG, worklog.GLOBAL_LOG, ROOT / "docs" / "worklog.local.md"):
        resolved = path.resolve()
        if resolved in seen_logs or not path.exists():
            continue
        seen_logs.add(resolved)
        chunks.append(path.read_text(encoding="utf-8"))
    log_text = "\n".join(chunks)
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
            problems.append(f"[privacy] 工作日志含绝对路径: {leak.group(0)}")
    for cons_path in sorted(runs_root.glob("*/agents/consolidator.json")):
        cons = json.loads(cons_path.read_text(encoding="utf-8"))
        status = str(cons.get("status", "")).lower()
        if status not in {"pending", "done"}:
            run_id = cons_path.parents[1].name
            problems.append(f"[schema] {run_id} consolidator.status 异常: {cons.get('status')!r}")
        problems.extend(code_audit_problems(cons_path.parents[1]))
    if problems:
        print("\n".join(problems))
        print(f"\ndoctor：发现 {len(problems)} 个问题。")
        return 1
    print("doctor：一切正常。")
    return 0


def _delivery_path(args: argparse.Namespace) -> Path | None:
    raw = getattr(args, "delivery", "") or ""
    return Path(raw) if raw else None


def cmd_item(args: argparse.Namespace) -> int:
    path = _delivery_path(args)
    try:
        if args.action == "add":
            item = delivery.add_item(
                item_type=args.type,
                problem=args.problem,
                mentions=list(args.mention or []),
                location=args.location,
                severity=args.severity,
                track=args.track,
                status=args.status or "candidate",
                acceptance=args.acceptance,
                novelty=args.novelty,
                path=path,
            )
            worklog.append_worklog(
                f"item add {item['id']} {item['type']}/{item['status']} {' '.join(item['mentions'])}"
            )
            print(f"{item['id']} {item['type']} {item['status']} {' '.join(item['mentions'])}")
            return 0
        if args.action == "set":
            if not args.id or not args.status:
                print("set 需要 --id 和 --status", file=sys.stderr)
                return 1
            item = delivery.set_status(args.id, args.status, note=args.note, path=path)
            if item is None:
                print(f"未找到 {args.id}", file=sys.stderr)
                return 1
            worklog.append_worklog(f"item set {item['id']} → {item['status']}")
            print(f"{item['id']} {item['status']}")
            return 0
        if args.action == "list":
            for item in delivery.load_delivery(path).get("items") or []:
                mentions = " ".join(item.get("mentions") or [])
                print(f"{item['id']} {item['track']} {item['type']} {item['status']} {mentions}")
            return 0
        if args.action == "import-v1":
            payload = json.loads(Path(args.src).read_text(encoding="utf-8"))
            added = delivery.import_v1(
                payload,
                mention=" ".join(args.mention or []),
                track=args.track,
                path=path,
            )
            worklog.append_worklog(f"item import-v1 {len(added)} 条 → {args.track}")
            print(f"imported {len(added)}")
            return 0
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"未知动作：{args.action}", file=sys.stderr)
    return 1


def cmd_project(args: argparse.Namespace) -> int:
    path = _delivery_path(args)
    if args.action == "show":
        print(json.dumps(delivery.load_delivery(path)["project"], ensure_ascii=False, indent=2))
        return 0
    updates = {
        key: getattr(args, key)
        for key in delivery.PROJECT_FIELDS
        if getattr(args, key) is not None
    }
    delivery.set_project(updates, path=path)
    worklog.append_worklog("project set " + ", ".join(sorted(updates)))
    print("project updated")
    return 0


def cmd_overview(args: argparse.Namespace) -> int:
    text = delivery.render_overview(delivery.load_delivery(_delivery_path(args)))
    if args.out:
        dest = Path(args.out)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        print(dest)
    else:
        print(text, end="")
    return 0


def cmd_scope(args: argparse.Namespace) -> int:
    loaded = review_scope.load_scope(Path(args.scope) if args.scope else None)
    plan = review_scope.select_checks(list(args.changed or []), loaded)
    print(review_scope.render_plan(plan), end="")
    return 0


def cmd_pr_check(args: argparse.Namespace) -> int:
    title = args.title or os.environ.get("PR_TITLE", "")
    body = args.body or ""
    if args.body_file:
        body = Path(args.body_file).read_text(encoding="utf-8")
    if not body:
        body = os.environ.get("PR_BODY", "")
    errors = pr_check.check_pull_request(title, body)
    if errors:
        print("\n".join(errors))
        return 1
    print("pr-check：通过")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    del args
    proc = subprocess.run([sys.executable, "-m", "pytest", "tests", "-q"], cwd=ROOT)
    if proc.returncode != 0:
        return proc.returncode
    return cmd_doctor(argparse.Namespace())


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

    p_doc = sub.add_parser(
        "doctor",
        help="体检：run 日志对账、绝对路径泄漏、consolidator 状态、代码–论文对账（数字/结构/超参/设计）",
    )
    p_doc.set_defaults(func=cmd_doctor)

    p_aud = sub.add_parser("audit", help="可选：调用 paper-audit（仅 tex/typ/pdf）")
    p_aud.add_argument("file", type=Path)
    p_aud.add_argument("--mode", default="quick-audit")
    p_aud.add_argument("--lang", default="zh")
    p_aud.add_argument("--pdf-mode", default="enhanced")
    p_aud.add_argument("--out-dir", default="")
    p_aud.set_defaults(func=cmd_audit)

    p_item = sub.add_parser("item", help="交付条目：类型和状态分开，建议必须 @ 人")
    p_item.add_argument("action", choices=["add", "set", "list", "import-v1"])
    p_item.add_argument("--type", default="defect", choices=list(delivery.TYPES))
    p_item.add_argument("--status", default="")
    p_item.add_argument("--severity", default="major", choices=list(delivery.SEVERITIES))
    p_item.add_argument("--track", default="paper", choices=list(delivery.TRACKS))
    p_item.add_argument("--location", default="")
    p_item.add_argument("--problem", default="")
    p_item.add_argument("--mention", action="append", default=[])
    p_item.add_argument("--id", default="")
    p_item.add_argument("--note", default="")
    p_item.add_argument("--acceptance", default="")
    p_item.add_argument("--novelty", default="new", choices=["new", "carry"])
    p_item.add_argument("--src", default="", help="import-v1 的 v1 台账路径")
    p_item.add_argument("--delivery", default="", help="交付台账路径，默认 docs/delivery.json")
    p_item.set_defaults(func=cmd_item)

    p_proj = sub.add_parser("project", help="填写总览用的版本和本轮决定")
    p_proj.add_argument("action", choices=["set", "show"])
    p_proj.add_argument("--delivery", default="")
    for key in delivery.PROJECT_FIELDS:
        p_proj.add_argument(f"--{key.replace('_', '-')}", default=None)
    p_proj.set_defaults(func=cmd_project)

    p_ov = sub.add_parser("overview", help="渲染一页项目总览")
    p_ov.add_argument("--delivery", default="")
    p_ov.add_argument("--out", default="")
    p_ov.set_defaults(func=cmd_overview)

    p_scope = sub.add_parser("scope", help="按改动路径选择检查，未变依赖沿用证据")
    p_scope.add_argument("--changed", action="append", default=[])
    p_scope.add_argument("--scope", default="", help="自定义 docs/check_scope.json")
    p_scope.set_defaults(func=cmd_scope)

    p_pr = sub.add_parser("pr-check", help="检查 PR 标题、章节和 @ 提及")
    p_pr.add_argument("--title", default="")
    p_pr.add_argument("--body", default="")
    p_pr.add_argument("--body-file", default="")
    p_pr.set_defaults(func=cmd_pr_check)

    p_check = sub.add_parser("check", help="稳定入口：pytest 然后 doctor")
    p_check.set_defaults(func=cmd_check)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
