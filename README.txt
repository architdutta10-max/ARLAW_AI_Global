ARLAW AI — Chat History update

This patch targets the current public repository layout:
app/main.py, app/static/index.html, app/static/app.js, app/static/style.css.

INSTALL
1. Back up your project first.
2. Extract this ZIP.
3. Run from Command Prompt:
   python install_chat_history.py "C:\path\to\ARLAW_AI_Global"
4. Review the changed files and run:
   python -m compileall app
   python -m pytest -q
5. Start the app with your existing command and test send, history, reopen, refresh and delete.

RENDER STORAGE
SQLite on Render's normal filesystem may be lost on redeploy/restart. Attach a persistent disk mounted at /var/data and set:
ARLAW_CHAT_DB=/var/data/chat_history.sqlite3

PRIVACY WARNING
This first implementation is shared across visitors because the current app has no user login. Do not use it for private or confidential conversations. Per-user authentication and ownership checks are required before public deployment.

This ZIP is a source patch installer, not a prebuilt replacement of the entire repository. It does not push to GitHub or deploy to Render.
