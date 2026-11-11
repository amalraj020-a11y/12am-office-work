# Day 1 — Safe Local Cybersecurity Lab

## Status

**PASS** — completed on 2026-10-21.

## Work completed

- Created the `amala-cybersecurity` 30-day portfolio workspace.
- Created the Day 1 lab directory and future project structure.
- Built a Python environment verifier.
- Added a unit test for the verifier.
- Verified Python, Git, Ollama, Qwen3:4B, and curl availability.
- Confirmed that no network scans or third-party testing were performed.
- Fixed an incorrect project-root/evidence path discovered during testing.
- Re-ran the verifier and confirmed the corrected implementation.

## Tests executed

```powershell
python .\src\verify_environment.py
python -m unittest discover -s .\tests -v
```

Result: **1 test passed**.

## Evidence

- `evidence/environment-check.json`
- `src/verify_environment.py`
- `tests/test_environment.py`

## Tools used

- Python 3.13.14
- Git 2.55.0
- Ollama with local `qwen3:4b`
- curl 8.21.0
- PowerShell
- OpenClaw orchestration

## Safety status

- Active scanning: **NOT RUN**
- Third-party testing: **NOT RUN**
- External disclosure: **NOT RUN**
- Private data access: **NOT RUN**

## Next step

Day 2 — Python Security Toolkit.
