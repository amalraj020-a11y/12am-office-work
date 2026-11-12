#!/usr/bin/env python3
"""Passive-only daily research runner for Amala Cyber Guardian."""

from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

IST = __import__("zoneinfo").ZoneInfo("Asia/Kolkata")
ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports" / "cyber-guardian"
PORTFOLIO = ROOT / "amala-cybersecurity"
LOG_CSV = PORTFOLIO / "research-log.csv"
XLSX = ROOT / "12pm_office_work_inventory.xlsx"
GITHUB_REPO = "https://github.com/amalraj020-a11y/12pm-office-work"

# Official organization or official program-platform pages only. The runner rotates
# three entries daily and never treats this list itself as authorization to test.
PROGRAMS = [
    {"organization": "Google", "sector": "Technology", "region": "Global", "url": "https://bughunters.google.com/about/rules/6625378258649088/google-and-alphabet-vulnerability-reward-program-vrp-rules"},
    {"organization": "Microsoft", "sector": "Technology", "region": "Global", "url": "https://www.microsoft.com/en-us/msrc/bounty"},
    {"organization": "Mozilla", "sector": "Open source", "region": "Global", "url": "https://www.mozilla.org/en-US/security/bug-bounty/"},
    {"organization": "GitLab", "sector": "Open source", "region": "Global", "url": "https://hackerone.com/gitlab"},
    {"organization": "Shopify", "sector": "E-commerce", "region": "Global", "url": "https://hackerone.com/shopify"},
    {"organization": "Automattic", "sector": "Publishing", "region": "Global", "url": "https://hackerone.com/automattic"},
    {"organization": "curl", "sector": "Open source", "region": "Global", "url": "https://curl.se/docs/bugbounty.html"},
    {"organization": "GitHub", "sector": "Developer platform", "region": "Global", "url": "https://bounty.github.com/"},
    {"organization": "Meta", "sector": "Social technology", "region": "Global", "url": "https://www.facebook.com/whitehat"},
]

AUTH_WORDS = ("safe harbor", "in scope", "scope", "authorized", "bounty", "eligible")
PROHIBITED_WORDS = ("denial of service", "social engineering", "brute force", "spam", "out of scope")


def fetch(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "AmalaCyberGuardian/1.0 passive-policy-check"})
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            raw = response.read(1_500_000)
            status = response.status
            final_url = response.geturl()
        text = raw.decode("utf-8", "replace")
        text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
        text = html.unescape(re.sub(r"(?s)<[^>]+>", " ", text))
        text = re.sub(r"\s+", " ", text).strip()
        lower = text.lower()
        money = []
        for match in re.finditer(r"(?:US\$|USD|\$|€|£|₹)\s?[0-9][0-9,]*(?:\.[0-9]+)?(?:\s*(?:-|to|–)\s*(?:US\$|USD|\$|€|£|₹)?\s?[0-9][0-9,]*)?", text, re.I):
            snippet = text[max(0, match.start() - 70): min(len(text), match.end() + 100)]
            if snippet not in money:
                money.append(snippet)
            if len(money) == 3:
                break
        return {
            "status": status,
            "final_url": final_url,
            "hash": hashlib.sha256(raw).hexdigest()[:16],
            "authorization_signals": [word for word in AUTH_WORDS if word in lower],
            "prohibited_signals": [word for word in PROHIBITED_WORDS if word in lower],
            "reward_evidence": money,
            "error": "",
        }
    except Exception as exc:
        return {"status": "unavailable", "final_url": url, "hash": "", "authorization_signals": [], "prohibited_signals": [], "reward_evidence": [], "error": f"{type(exc).__name__}: {exc}"[:300]}


def ollama_summary(results: list[dict]) -> tuple[str, str]:
    for model in ("qwen3:4b", "qwen3:0.6b"):
        try:
            tags = json.load(urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=4))
            names = {item.get("name") for item in tags.get("models", [])}
            if model not in names:
                continue
            prompt = (
                "Summarize this passive authorization research in at most 5 bullets. "
                "Do not claim vulnerabilities, do not recommend testing without verified written scope, "
                "and state that earnings are not guaranteed. Data: " + json.dumps(results)
            )
            body = json.dumps({"model": model, "prompt": prompt, "stream": False, "think": False, "options": {"num_predict": 180}}).encode()
            req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as response:
                answer = json.load(response).get("response", "").strip()
            if answer:
                return model, answer
        except Exception:
            continue
    return "none", "Local Qwen was unavailable or timed out; the deterministic passive report was still completed."


def next_day(today: str) -> Path:
    for path in sorted(PORTFOLIO.glob("Day-*")):
        for marker in [path / "run.json", *path.glob("run-*.json")]:
            if marker.exists() and json.loads(marker.read_text()).get("date") == today:
                return path
    numbers = [int(m.group(1)) for p in PORTFOLIO.glob("Day-*") if (m := re.fullmatch(r"Day-(\d+)", p.name))]
    path = PORTFOLIO / f"Day-{max(numbers, default=0) + 1:02d}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_xlsx(rows: list[list[str]]) -> None:
    def cell(value: str, row: int, col: int) -> str:
        letters, n = "", col
        while n:
            n, rem = divmod(n - 1, 26)
            letters = chr(65 + rem) + letters
        return f'<c r="{letters}{row}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'
    sheet_rows = "".join(f'<row r="{r}">' + "".join(cell(v, r, c) for c, v in enumerate(values, 1)) + "</row>" for r, values in enumerate(rows, 1))
    files = {
        "[Content_Types].xml": '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
        "_rels/.rels": '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
        "xl/workbook.xml": '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Daily Research" sheetId="1" r:id="rId1"/></sheets></workbook>',
        "xl/_rels/workbook.xml.rels": '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
        "xl/worksheets/sheet1.xml": f'<?xml version="1.0"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{sheet_rows}</sheetData></worksheet>',
    }
    with zipfile.ZipFile(XLSX, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)


def git_publish(today: str, session: str) -> str:
    try:
        subprocess.run(["git", "add", "README.md", "automation", "amala-cybersecurity", "reports", XSLX_NAME := XLSX.name], cwd=ROOT, check=True)
        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0:
            return "No repository changes"
        subprocess.run(["git", "commit", "-m", f"Amala Cyber Guardian {today} {session}"], cwd=ROOT, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=ROOT, check=True, timeout=120)
        return "Committed and pushed to GitHub"
    except Exception as exc:
        return f"GitHub push failed: {type(exc).__name__}: {exc}"


def whatsapp_notify(today: str, session: str, results: list[dict], model: str, publish: str) -> str:
    """Send Raj a concise run summary only when WhatsApp was explicitly configured."""
    target = os.environ.get("AMALA_WHATSAPP_TARGET", "").strip()
    if not target:
        return "Not configured: set AMALA_WHATSAPP_TARGET after linking WhatsApp"
    openclaw = os.environ.get("OPENCLAW_BIN", "").strip() or shutil.which("openclaw")
    if not openclaw:
        return "Failed: OpenClaw CLI was not found; set OPENCLAW_BIN"
    if publish not in ("Committed and pushed to GitHub", "No repository changes"):
        return "Skipped because the GitHub publication failed"

    verified = sum(1 for item in results if item["status"] == 200)
    report_url = f"{GITHUB_REPO}/blob/main/reports/cyber-guardian/{today}-{session}.md"
    workbook_url = f"{GITHUB_REPO}/blob/main/{XLSX.name}"
    message = (
        f"Amala Cyber Guardian {today} {session} completed.\n"
        f"Official programme pages reviewed: {len(results)} ({verified} reachable).\n"
        "Active testing: none. Confirmed vulnerabilities: none. External submissions: none.\n"
        f"Local model: {model}.\n"
        f"Report: {report_url}\n"
        f"Excel ledger: {workbook_url}\n"
        "Any testing, proposal, or disclosure still requires Raj's approval."
    )
    try:
        completed = subprocess.run(
            [openclaw, "message", "send", "--channel", "whatsapp", "--target", target, "--message", message, "--json"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return "Sent" if completed.returncode == 0 else "Failed without an OpenClaw error message"
    except Exception as exc:
        return f"Failed: {type(exc).__name__}: {exc}"[:300]


def main() -> int:
    start = datetime.now(IST)
    today = start.date().isoformat()
    session = "12AM" if start.hour < 6 else "12PM"
    REPORTS.mkdir(parents=True, exist_ok=True)
    day_dir = next_day(today)
    offset = start.toordinal() % len(PROGRAMS)
    selected = [PROGRAMS[(offset + i) % len(PROGRAMS)] for i in range(3)]
    results = []
    for program in selected:
        item = dict(program)
        item.update(fetch(program["url"]))
        item["decision"] = "Policy page observed; scope must be read and verified before any testing" if item["status"] == 200 else "Passive lead only; page unavailable"
        results.append(item)
    model, summary = ollama_summary(results)
    end = datetime.now(IST)

    lines = [
        f"# Amala Cyber Guardian — {today} {session}", "", "## Session", "",
        f"- Started: {start.isoformat(timespec='seconds')}", f"- Finished: {end.isoformat(timespec='seconds')}",
        f"- Duration: {int((end-start).total_seconds())} seconds", "- Mode: passive policy research only; no scanning, exploitation, login, submission, or outreach", "",
        "## Paid-program shortlist", "",
    ]
    for item in results:
        rewards = " | ".join(item["reward_evidence"]) if item["reward_evidence"] else "No reliable reward amount extracted; consult the linked current rules"
        lines += [
            f"### {item['organization']} — {item['sector']} ({item['region']})", "",
            f"- Official/program link: {item['url']}", f"- HTTP verification: {item['status']} (content hash `{item['hash'] or 'n/a'}`)",
            f"- Written-authorization signals found: {', '.join(item['authorization_signals']) or 'not confirmed'}",
            f"- Prohibited-test signals found: {', '.join(item['prohibited_signals']) or 'not extracted'}",
            f"- Published reward evidence: {rewards}", f"- Decision: {item['decision']}",
            "- Eligibility/scope action: open the current linked rules and confirm asset, method, account, rate-limit, residency, tax, duplicate, and disclosure requirements before any test.", "",
        ]
    lines += [
        "## Small-business help leads and proposals", "",
        "- Passive discovery produced no evidence-backed small-business candidate today. No business was labeled insecure from appearance alone.",
        "- Proposal drafts prepared: 0 of 3. A proposal is created only when a public, legitimate need and a suitable contact channel can be evidenced.",
        "- Nothing was sent. Any future proposal will be marked `AWAITING RAJ APPROVAL`.", "",
        "## Findings and possible earnings", "",
        "- Confirmed vulnerabilities: none.", "- Unverified suspicions: none.",
        "- Possible earnings: only the official reward evidence above; actual earnings are not guaranteed and require a valid, original, in-scope report accepted by the program.", "",
        "## Local-model review", "", f"- Model: `{model}`", summary, "",
        "## Recommended next actions", "",
        "1. Raj may choose one shortlisted program for a manual scope review.",
        "2. Only after its current written authorization is confirmed should Amala prepare a bounded, low-impact test plan.",
        "3. Keep all submissions and outreach awaiting Raj's explicit approval.", "",
        "## Tools and limitations", "",
        "- Python standard library HTTP client, HTML text extraction, SHA-256, systemd, Git, GitHub CLI credentials, and optional local Ollama Qwen.",
        "- Dynamic JavaScript pages may not expose full rules to the passive fetcher. Extracted currency text is evidence to review, not a guaranteed payout range.",
        "- Qwen3:4B is used only when installed and healthy; a smaller local Qwen fallback is recorded explicitly.", "",
        "## Awaiting approval", "", "- No external action is queued. Raj's approval is required before testing, reporting, emailing, or submitting anything.", "",
    ]
    report = "\n".join(lines)
    report_path = REPORTS / f"{today}-{session}.md"
    report_path.write_text(report, encoding="utf-8")
    (day_dir / f"{session}.md").write_text(report, encoding="utf-8")
    (day_dir / f"run-{session}.json").write_text(json.dumps({"date": today, "session": session, "started": start.isoformat(), "finished": end.isoformat(), "model": model, "programs": results}, indent=2), encoding="utf-8")
    (day_dir / "README.md").write_text(
        f"# {day_dir.name} — {today}\n\n"
        "Amala runs at **12:00 AM** and **12:00 PM IST**.\n\n"
        "- [Midnight report](12AM.md)\n"
        "- [Noon report](12PM.md)\n\n"
        "A link may be unavailable until that session has completed.\n",
        encoding="utf-8",
    )

    header = ["date", "session", "organization", "sector", "region", "official_url", "http_status", "authorization_signals", "reward_evidence", "decision", "model"]
    existing = []
    if LOG_CSV.exists():
        with LOG_CSV.open(newline="", encoding="utf-8") as handle:
            existing = list(csv.reader(handle))[1:]
    existing = [([row[0], "legacy"] + row[1:]) if len(row) == 10 else row for row in existing]
    existing = [row for row in existing if row and not (row[0] == today and len(row) > 1 and row[1] == session)]
    for item in results:
        existing.append([today, session, item["organization"], item["sector"], item["region"], item["url"], str(item["status"]), "; ".join(item["authorization_signals"]), " | ".join(item["reward_evidence"]), item["decision"], model])
    with LOG_CSV.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle).writerows([header] + existing)
    write_xlsx([header] + existing)
    publish = git_publish(today, session)
    whatsapp = whatsapp_notify(today, session, results, model, publish)
    print(json.dumps({"status": "complete", "report": str(report_path), "workbook": str(XLSX), "day": day_dir.name, "session": session, "model": model, "publish": publish, "whatsapp": whatsapp}))
    return 0 if publish == "Committed and pushed to GitHub" or publish == "No repository changes" else 1


if __name__ == "__main__":
    raise SystemExit(main())
