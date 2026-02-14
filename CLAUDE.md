# Cerebro - Enterprise Knowledge Extraction Platform

## Identity

- **Product name**: Cerebro
- **What it is**: Enterprise Knowledge Extraction Platform — code analysis, RAG, and GCP integration
- **What it is NOT**: A "credit burn" tool. GCP credit management is ONE feature, not the identity

## Naming Convention

| Scope | Name |
|-------|------|
| Product / CLI | **Cerebro** (`cerebro` command) |
| Python package dir | `src/phantom/` (kept for backward compat — do NOT rename) |
| CLI entrypoints | Both `cerebro` and `phantom` work (backward compat) |
| Imports in code | `from phantom.core...` (internal, not user-facing) |

## Language Rules

- All user-facing strings (CLI output, TUI labels, docstrings) MUST be in **English**
- Internal code comments: English preferred
- No Portuguese in any user-facing surface

## GCP Configuration

- **Never hardcode** GCP project IDs — use `os.getenv("GCP_PROJECT_ID")`
- **Never hardcode** Data Store IDs — use `os.getenv("DATA_STORE_ID")`
- Placeholder in docs/help: `<your-gcp-project-id>`

## Project Structure

```
src/phantom/           # Python package (internal name)
  cli.py               # CLI entrypoint (Typer)
  tui/                 # Terminal UI (Textual)
  core/                # Business logic
  commands/            # CLI command groups
dashboard/             # React web dashboard
docs/
  architecture/        # Architecture docs, ADR summary
  guides/              # Setup guides, cheatsheets
  features/            # Feature-specific docs (gcp-credits, intelligence, strategy)
  project/             # Project status, plans, audits
  phases/              # Historical phase implementation docs
  i18n/                # Portuguese translations
  commands/            # CLI command docs
```

## Key ADRs

- **ADR-0027**: Phantom Phase 1 API (accepted)
- **ADR-0030**: Enterprise Repositioning & Identity Resolution (accepted)
