# ARLAW AI Global 2.0.2

- Consolidated the Groq-only provider configuration and direct Python startup workflow.
- Removed Windows batch launch/installer scripts; start with `python run.py`.
- Updated Windows setup, repository integration and QA documentation to match the package.
- Preserved the existing teal UI, legal workflows, settings, multilingual prompting, retrieval and evaluation utilities.
- No claim of production security certification or legal-accuracy certification.

# Release 2.0.1

- Removed Gemini and Ollama provider adapters and routing.
- Groq is the only active cloud AI provider.
- Added automatic `.env` loading.
- Added `python run.py` direct startup; no Windows batch file is needed to launch the application.
- Updated health reporting, configuration examples, documentation and tests.
- Existing UI, retrieval, specialist prompts and project structure are retained.

# ARLAW AI Global 2.0.0 — Final Stable Package

## Release purpose

A consolidated, feature-complete package for the current ARLAW AI Global implementation. The release preserves the existing FastAPI backend and teal frontend rather than replacing the application.

## Included project capabilities

- FastAPI application and existing teal web interface.
- Groq-only cloud provider adapters with configured fallback.
- Task-specific provider routing and optional independent multi-model review.
- Retrieval from the existing SQLite/FTS5 knowledge library.
- English, Hindi, Bengali and mixed-language prompting.
- Settings for appearance, interface language, text size, contrast and reduced motion.
- Support page, creator attribution and social links.
- Training/evaluation utilities, automated tests, deployment files and documentation.
- Guarded Windows integration script with backup and local-data preservation.

## Verification boundary

The release package includes automated backend and frontend-contract tests. See `RELEASE_QA.md` for commands and limitations. Packaging is not evidence of browser testing, legal correctness certification, production security certification, or a completed GitHub deployment.

## Maintenance policy

No planned feature upgrade is required to use this release within its current scope. Necessary security patches, dependency updates, model-provider compatibility fixes and legal-source maintenance remain important.
