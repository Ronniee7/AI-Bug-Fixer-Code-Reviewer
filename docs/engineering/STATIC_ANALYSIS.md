# Static Analysis Engine

The orchestration service combines the existing Python AST scanner with Ruff and Bandit.
All results are normalized into the `Finding` schema with separate severity and confidence.

## Safety
- Subprocesses use argument arrays and `shell=False`.
- Target code is parsed/scanned, never imported or executed by these analyzers.
- Each subprocess has a timeout.
- Project paths are resolved and restricted to `WORKSPACE_ROOT`.
- Findings are signals for human review, not proof of exploitability.
- AI-generated patches must require explicit approval before modifying files.

## API
`POST /api/v1/analysis/run?project_path=<path-relative-to-workspace-root>`
