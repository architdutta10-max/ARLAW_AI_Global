# ARLAW AI Global 3.1.2

## Changes

- Added individual conversation deletion to the recent-chat list. Each deletion requires confirmation and is persisted to this browser's local storage.
- Deleting the active conversation clears the current view without silently recreating the deleted conversation.
- Added accessible labels and keyboard-focus styling for the delete controls.
- Corrected task routing so explicit legal provisions and legal intent are considered before broad finance keywords.
- Applied the no-retrieved-sources instruction and high-risk numeric warning to document-review tasks as well as other legal tasks.
- Updated bundled knowledge seeding so managed records refresh their metadata and FTS chunks when the JSON manifest changes, while user-uploaded records with different managed file names are left untouched.
- Updated static asset cache versions and release metadata.

## Verification

- `node --check app/static/app.js`
- `python -m pytest -q`
- Automated suite: 129 passed.

## Limitations

- Chat history remains browser-local; deletion is not synchronized across devices or server accounts.
- Citation-label checks do not prove that a source supports a legal proposition.
- The bundled legal digests and software tests do not certify legal accuracy, source currency, production security or professional suitability.
