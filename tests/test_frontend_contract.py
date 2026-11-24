from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "app/static/index.html").read_text(encoding="utf-8")
JS = (ROOT / "app/static/app.js").read_text(encoding="utf-8")
CSS = (ROOT / "app/static/style.css").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_support_navigation_and_view_are_wired():
    assert 'id="supportTab"' in HTML
    assert 'id="supportView"' in HTML
    assert '$("supportTab").onclick=()=>show("support")' in JS
    assert 'v!=="support"' in JS


def test_support_instagram_link_is_safe_and_correct():
    match = re.search(r'<a class="support-link" href="([^"]+)"[^>]*>(.*?)</a>', HTML)
    assert match, "Support page must expose a clickable Instagram link"
    assert match.group(1).startswith("https://www.instagram.com/architdutta17")
    assert 'target="_blank"' in HTML and 'rel="noopener noreferrer"' in HTML
    assert "@architdutta17" in HTML


def test_creator_credit_and_social_links_are_in_readme():
    assert "Created by <b>Archit Dutta</b>" in HTML
    assert "Archit Dutta" in README
    assert "https://www.linkedin.com/in/archit-dutta-4522693aa/" in README
    assert "https://www.instagram.com/architdutta17" in README


def test_settings_and_theme_controls_exist():
    for element_id in ("settingsOpen", "settingsDialog", "settingsClose", "prefTheme", "prefLanguage", "prefFontSize", "prefContrast", "prefMotion"):
        assert f'id="{element_id}"' in HTML
    assert "function applyTheme" in JS
    assert "localStorage.setItem('arlaw-preferences'" in JS
    assert 'html[data-theme="dark"] .support-card' in CSS


def test_support_styles_include_responsive_theme_support():
    assert ".support-card" in CSS
    assert 'html[data-theme="dark"] .support-card' in CSS


def test_recent_chat_and_request_feedback_controls_exist():
    assert 'id="historyList"' in HTML
    assert 'id="requestStatus"' in HTML
    assert "const HISTORY_KEY='arlaw-chat-history-v1'" in JS
    assert 'function renderHistory()' in JS
    assert 'function saveConversation()' in JS
    assert 'loading-message' in JS


def test_colour_palette_has_at_least_30_persistent_options():
    assert 'id="prefAccent"' in HTML
    palettes = re.findall(r"\['([a-z]+)',\s*'#[0-9a-fA-F]{6}',\s*'#[0-9a-fA-F]{6}'\]", JS)
    assert len(palettes) >= 30
    assert "preferences.accent" in JS
    assert "localStorage.setItem('arlaw-preferences'" in JS


def test_readme_discloses_verification_and_history_limitations():
    assert "does not determine whether that source actually supports" in README
    assert "not synchronized to the server or other devices" in README
    assert "do not constitute a production security audit" in README


def test_chat_request_is_bounded_to_backend_schema_limits():
    assert "history.slice(-30)" in JS
    assert "content:String(m.content||'').slice(0,14000)" in JS
    assert 'maxlength="14000"' in HTML
