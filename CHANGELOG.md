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
