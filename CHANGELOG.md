# Changelog

## Integrated hybrid milestone

- Added task classification and task-specific provider routing.
- Added independent peer-review mode using additional configured providers.
- Added retrieved-reference label validation for `[S#]` citations.
- Updated health metadata and frontend connection status to show provider/model/task.
- Added a teacher-output distillation data preparation utility with expert approval and source provenance checks.
- Added API evaluation runner and tests for routing, fallback, citation references and peer review.
- Preserved the existing FastAPI application, static teal UI, SQLite/FTS knowledge store, deployment configuration and repository layout.

## User settings build
- Added a visible Settings control in the application header.
- Added persistent light/dark appearance preferences.
- Added English, Hindi, and Bengali interface labels.
- Added text-size, higher-contrast, and reduced-motion controls.
- Preferences remain local to the browser.


## Professional workspace expansion

- Added task routing for lawyer/advocate workflow assistance, accounting support, CA/tax research and neutral judicial research.
- Added `/api/capabilities` to expose supported workflows and professional boundaries.
- Added starter prompts for the four professional workflows.
- Added explicit human-review, source-verification and non-substitution safeguards.
- Updated GitHub Actions to run tests through `python -m pytest` with the repository root on `PYTHONPATH`.

## Release 1.2.0
- Consolidated the integrated professional-workspace release package.
- Added bounded, typed chat-message input validation and rejected unsupported message roles at the API boundary.
- Updated API release metadata and FastAPI startup lifecycle handling.
- Added release notes and a production-readiness checklist that clearly identifies security and evaluation work still required.
