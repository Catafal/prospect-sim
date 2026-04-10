# prospect-sim — Project Rules for Claude

## Git & Pull Requests

**ALWAYS open PRs against `Catafal/prospect-sim`** — never against `aaronjmars/MiroShark` (upstream).

This repo has two remotes:
- `origin` → `https://github.com/Catafal/prospect-sim.git` ← **always use this**
- `upstream` → `https://github.com/aaronjmars/MiroShark.git` ← read-only reference, never push PRs here

When creating PRs, always pass `--repo Catafal/prospect-sim` explicitly:
```bash
gh pr create --repo Catafal/prospect-sim --title "..." --body "..."
```

Sir will explicitly state if a PR should go elsewhere. Default is always `Catafal/prospect-sim`.

---

## Stack

- **Backend**: Python / Flask (`backend/`)
- **Frontend**: Vue 3 (`frontend/src/`)
- **Simulation framework**: OASIS / Wonderwall (`backend/wonderwall/`)
- **Platforms simulated**: Twitter + Reddit (Polymarket removed)

## Key Rules

- Use `.venv` in `backend/` for all Python commands
- Max 200 lines per function, max 1000 lines per file
- All imports at top of file
- Tests go in `tests/` folder
- For config values, always use `app/config.py` — never access `.env` directly
