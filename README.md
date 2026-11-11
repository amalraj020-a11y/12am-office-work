# Amala Cyber Guardian

Daily autonomous cybersecurity research portfolio.

## Daily 12:00 AM and 12:00 PM IST runs

Amala starts at midnight and noon India Standard Time and performs two authorization-first, low-impact research sessions each day:

1. Selects organizations worldwide across technology, entertainment, media, consumer goods, e-commerce, education, and open source.
2. Checks official vulnerability disclosure or bug bounty rules before any testing.
3. Performs only passive public checks unless explicit authorization is verified.
4. Uses free local tools and Ollama models, with Qwen3:4B preferred.
5. Reviews results for false positives, duplicates, confidence, and severity.
6. Saves a dated Markdown report and supporting evidence.
7. Updates the daily folder and pushes the report to this GitHub repository.
8. Never exploits systems, accesses private data, submits reports, emails security teams, or contacts employees without Raj's approval.

The always-on runner is installed on the `amala-worker` EC2 instance as a
systemd user timer. It searches only official program pages, verifies public
policy evidence, creates a rotating worldwide shortlist, records possible
reward evidence, and may prepare up to three unsent proposals when a genuine
public small-business need can be evidenced. It works while Raj's local PC is
off, provided the EC2 instance remains running and has internet access.

If the local model is slow or unavailable, the runner records the limitation and still saves a safe report instead of claiming a vulnerability.

## Folder structure

- `amala-cybersecurity/Day-01/` - completed lab setup, tests, and safe curl evidence.
- `amala-cybersecurity/Day-02/` - next planned Python security toolkit work.
- `reports/cyber-guardian/` - dated daily run reports.
- `automation/` - the Windows scheduled runner and launcher.
- `automation/amala_cyber_guardian.py` - passive Linux/EC2 research runner.
- `automation/amala-cyber-guardian.timer` - daily 12:00 AM and 12:00 PM IST systemd timer.
- `12pm_office_work_inventory.xlsx` - Excel-compatible daily research ledger.

## Safety status

This project is for responsible security research only. No finding is treated as confirmed without evidence and verified authorization. External disclosure always requires Raj's approval.
