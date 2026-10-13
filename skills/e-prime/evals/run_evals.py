#!/usr/bin/env python3
"""run_evals — behavioral evals for the e-prime skill on the pi runtime.

Two independent signals per case, both measured from the pi event stream
(`pi -p --mode json`), never from the model's self-report:

  activation   did pi advertise the skill in <available_skills>, and did
               the model open skill resources (SKILL.md, references/,
               scripts/eprime_lint.py) before answering?
  compliance   does the final reply pass the skill's deterministic
               linter with zero counted violations?

Why self-report never enters the picture: published experiments put
first-pass LLM compliance near 50% (references/llm-notes.md), and live
testing on this very repo showed a model denying a skills block that
demonstrably sat in its system prompt. The event stream supplies ground
truth; the model supplies only the text under test.

Modes
-----
auto    plain prompt. Measures description-driven activation: whether
        the model consults the skill on its own. Easy tasks can pass
        compliance from prior knowledge — such a run FAILS here, because
        an unconsulted clean answer proves nothing about the skill.
slash   prompt prefixed with /skill:e-prime, which pi expands into the
        full SKILL.md. Measures the skill's effect when consultation
        happens for certain (skill efficacy).

Verdicts
--------
auto    pass = advertised AND consulted AND lint-clean (when the case
        expects an E-Prime deliverable)
slash   pass = injected AND lint-clean (when expected)

Setup required
--------------
pi on PATH, a reachable model, and — for auto cases — the skill hooked
into the runtime (project .pi/skills/e-prime plus project trust, or a
user-level ~/.pi/agent/skills drop-in) so the system prompt advertises
it. Run from anywhere; the harness always launches pi in the repo root.

Usage
-----
    python3 run_evals.py [--only ID,ID] [--runs N] [--model PATTERN]
                         [--timeout SEC] [--cases FILE] [--verbose]
    python3 run_evals.py --list

Exits 0 when every verdict passes, 1 otherwise. Stdlib only; the same
python3 that runs this script also runs the linter.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
REPO_ROOT = SKILL_DIR.parents[1]
LINTER = SKILL_DIR / "scripts" / "eprime_lint.py"
DEFAULT_CASES = SCRIPT_DIR / "cases.json"
SKILL_NAME = "e-prime"
SLASH_PREFIX = "/skill:e-prime "
ADVERTISED_MARK = f"<name>{SKILL_NAME}</name>"
INJECTED_MARK = f'<skill name="{SKILL_NAME}"'


def text_of(content) -> str:
    """Plain text from a message content, which arrives as str or blocks."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return ""


def system_text(message: dict) -> str:
    """Full system-prompt text: content plus every named section."""
    parts = [message.get("content") or ""]
    sections = message.get("sections")
    if isinstance(sections, dict):
        parts.extend(str(v) for v in sections.values())
    return "\n".join(parts)


def consultation_markers() -> list[str]:
    """Path fragments that identify tool calls touching skill resources.

    Covers the real skill dir, the project symlink dir, and any linter
    invocation regardless of how the model spelled the path.
    """
    symlink_dir = REPO_ROOT / ".pi" / "skills" / SKILL_NAME
    return [str(SKILL_DIR), str(symlink_dir), "eprime_lint"]


def parse_events(events: list[dict], markers: list[str]) -> dict:
    """Reduce one pi json session to the signals under test."""
    out = {
        "advertised": False,
        "injected": False,
        "consulted": False,
        "linter_run": False,
        "reply": "",
    }
    saw_user = False
    for ev in events:
        etype = ev.get("type")
        if etype == "message_start":
            message = ev.get("message") or {}
            role = message.get("role")
            if role == "system":
                if ADVERTISED_MARK in system_text(message):
                    out["advertised"] = True
            elif role == "user" and not saw_user:
                saw_user = True
                if text_of(message.get("content")).lstrip().startswith(
                        INJECTED_MARK):
                    out["injected"] = True
        elif etype == "message_end":
            message = ev.get("message") or {}
            if message.get("role") == "assistant":
                reply = text_of(message.get("content")).strip()
                if reply:
                    out["reply"] = reply
        elif etype == "tool_execution_start":
            blob = json.dumps(
                {"tool": ev.get("toolName"), "args": ev.get("args")},
                default=str)
            if any(marker in blob for marker in markers):
                out["consulted"] = True
                if "eprime_lint" in blob:
                    out["linter_run"] = True
    return out


def run_pi(prompt: str, opt) -> tuple[list[dict], str]:
    """Run one pi session; return (events, stderr tail)."""
    cmd = ["pi", "-p", "--no-session", "--mode", "json"]
    if opt.model:
        cmd += ["--model", opt.model]
    cmd += ["--", prompt]
    try:
        proc = subprocess.run(
            cmd, cwd=str(REPO_ROOT), capture_output=True, text=True,
            timeout=opt.timeout)
    except subprocess.TimeoutExpired:
        return [], f"pi timed out after {opt.timeout}s"
    events: list[dict] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue  # startup chatter, not an event
    return events, (proc.stderr or "")[-400:]


def lint_reply(reply: str) -> dict:
    """Run the deterministic linter on a reply; return its verdict."""
    with tempfile.NamedTemporaryFile(
            "w", suffix=".txt", encoding="utf-8", delete=False) as fh:
        fh.write(reply + "\n")
        tmp = fh.name
    try:
        proc = subprocess.run(
            [sys.executable, str(LINTER), tmp, "--json"],
            capture_output=True, text=True, timeout=60)
        try:
            data = json.loads(proc.stdout) if proc.stdout else {}
        except json.JSONDecodeError:
            data = {}
        files = data.get("files") or []
        hits = [h for f in files for h in f.get("hits", [])]
        return {
            "clean": data.get("total_counted_violations", 1) == 0,
            "counted": data.get("total_counted_violations", 1),
            "possible": sum(1 for h in hits
                            if h.get("category") == "possible"),
        }
    finally:
        Path(tmp).unlink(missing_ok=True)


def run_case(case: dict, opt, markers: list[str]) -> dict:
    """One pi session against one case; reduce to a verdict row."""
    prompt = case["prompt"]
    if case.get("mode") == "slash":
        prompt = SLASH_PREFIX + prompt
    row = {
        "id": case["id"],
        "mode": case.get("mode", "auto"),
        "deliverable": case.get("deliverable", "rewrite"),
        "error": "",
        "reasons": [],
    }
    events, stderr = run_pi(prompt, opt)
    if not events:
        row["error"] = f"no events from pi ({stderr or 'see stderr'})"
        row["verdict"] = "FAIL"
        return row
    signals = parse_events(events, markers)
    row.update(signals)

    if row["deliverable"] == "rewrite":
        if not row["reply"]:
            row["reasons"].append("model produced no reply text")
        else:
            row["lint"] = lint_reply(row["reply"])
            if not row["lint"]["clean"]:
                row["reasons"].append(
                    f"{row['lint']['counted']} counted to-be violation(s)")
    else:
        row["lint"] = None

    if row["mode"] == "slash":
        if not row["injected"]:
            row["reasons"].append(
                "/skill:e-prime did not expand (skill not loaded?)")
    else:
        if not row["advertised"]:
            row["reasons"].append(
                "skill not advertised (hook up .pi/skills + project trust)")
        if not row["consulted"]:
            row["reasons"].append(
                "skill never consulted — answered from prior knowledge")
    row["verdict"] = "FAIL" if row["reasons"] else "PASS"
    return row


def yn(flag: bool) -> str:
    return "yes" if flag else "no"


def print_row(row: dict, verbose: bool) -> None:
    lint = row.get("lint")
    lint_s = "n/a"
    if isinstance(lint, dict):
        lint_s = "clean" if lint["clean"] else f"{lint['counted']} hits"
        if lint["possible"]:
            lint_s += f" (+{lint['possible']} possible)"
    line = (f"[{row['verdict']}] {row['id']:<28} {row['mode']:<5} "
            f"adv={yn(row.get('advertised', False))} "
            f"inj={yn(row.get('injected', False))} "
            f"cons={yn(row.get('consulted', False))} "
            f"lint={lint_s}")
    if row.get("linter_run"):
        line += "  [ran linter]"
    print(line)
    if row.get("error"):
        print(f"       error: {row['error']}")
    for reason in row["reasons"]:
        print(f"       reason: {reason}")
    reply = row.get("reply", "")
    if reply and (verbose or row["verdict"] == "FAIL"):
        shown = reply if len(reply) <= 220 else reply[:217] + "..."
        print(f"       reply: {shown}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Run behavioral evals for the e-prime skill on pi.")
    parser.add_argument("--cases", default=str(DEFAULT_CASES),
                        help="cases JSON file")
    parser.add_argument("--only", default="",
                        help="comma-separated case ids to run")
    parser.add_argument("--runs", type=int, default=1,
                        help="sessions per case (default 1)")
    parser.add_argument("--model", default="",
                        help="model pattern passed through to pi")
    parser.add_argument("--timeout", type=int, default=240,
                        help="seconds per pi session (default 240)")
    parser.add_argument("--verbose", action="store_true",
                        help="print replies for passing runs too")
    parser.add_argument("--list", action="store_true",
                        help="list case ids and exit")
    args = parser.parse_args(argv)

    try:
        cases = json.loads(Path(args.cases).read_text(encoding="utf-8"))
        cases = cases.get("cases", cases)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot load cases: {exc}", file=sys.stderr)
        return 1
    if args.only:
        wanted = {c.strip() for c in args.only.split(",") if c.strip()}
        cases = [c for c in cases if c.get("id") in wanted]

    if args.list:
        for case in cases:
            print(f"{case['id']:<28} {case.get('mode', 'auto'):<5} "
                  f"{case.get('deliverable', 'rewrite')}")
        return 0
    if not cases:
        print("error: no cases selected", file=sys.stderr)
        return 1
    if shutil.which("pi") is None:
        print("error: pi not found on PATH", file=sys.stderr)
        return 1

    markers = consultation_markers()
    rows: list[dict] = []
    for case in cases:
        for run in range(1, args.runs + 1):
            suffix = f" (run {run}/{args.runs})" if args.runs > 1 else ""
            print(f"--- {case['id']}{suffix} ...", flush=True)
            row = run_case(case, args, markers)
            row["id"] = row["id"] + (f"#{run}" if args.runs > 1 else "")
            rows.append(row)
            print_row(row, args.verbose)

    print()
    total = len(rows)
    passed = sum(1 for r in rows if r["verdict"] == "PASS")
    auto_rows = [r for r in rows if r["mode"] == "auto"]
    slash_rows = [r for r in rows if r["mode"] == "slash"]
    rewrite_rows = [r for r in rows
                    if isinstance(r.get("lint"), dict)]
    print(f"runs:      {total} "
          f"(auto {len(auto_rows)}, slash {len(slash_rows)})")
    print(f"verdicts:  {passed}/{total} pass")
    if auto_rows:
        adv = sum(1 for r in auto_rows if r.get("advertised"))
        cons = sum(1 for r in auto_rows if r.get("consulted"))
        print(f"activation (auto): advertised {adv}/{len(auto_rows)}, "
              f"consulted {cons}/{len(auto_rows)}")
    if slash_rows:
        inj = sum(1 for r in slash_rows if r.get("injected"))
        print(f"injection (slash): {inj}/{len(slash_rows)}")
    if rewrite_rows:
        clean = sum(1 for r in rewrite_rows if r["lint"]["clean"])
        print(f"compliance (rewrite deliverables): {clean}/{len(rewrite_rows)} "
              f"lint-clean")
    verified = sum(1 for r in rows if r.get("linter_run"))
    print(f"self-verify: linter invoked in {verified}/{total} runs")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
