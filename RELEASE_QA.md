# Release 1.2.1 — integration and QA notes

## Automated checks

Run `python -m pytest -q`. The suite includes backend tests and frontend contract checks for Support navigation, Instagram link safety, creator attribution, README social links, theme styles and settings controls.

## Browser check

Follow `tests/FRONTEND_BROWSER_TESTING.md` for an optional Playwright Chromium smoke test. This is a real-browser interaction check; it is not part of the default dependency set.

## Safe local integration

Extract the release ZIP, then run `scripts\\install_release_1_2_1.bat` from the extracted project folder. Optionally pass the target repository path as the first argument. The script requires a clean Git working tree, displays the current branch and remotes, asks for confirmation, creates a backup, preserves `.git`, `.env`, virtual environments and local `data`, installs project requirements, and runs tests. It never commits or pushes.

After successful verification, review `git diff` and decide whether to commit and push. Never use force-push for this release workflow.
