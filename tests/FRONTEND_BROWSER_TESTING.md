# Optional real-browser verification

The standard test suite includes frontend contract checks that run without a browser. For an actual browser smoke test, install Playwright in a separate development environment:

```cmd
python -m pip install playwright
python -m playwright install chromium
```

Start the app in another terminal using the repository's documented command:

```cmd
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Then run this one-off browser check from the repository root:

```cmd
python -c "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); b=p.chromium.launch(headless=True); page=b.new_page(); page.goto('http://127.0.0.1:8000'); page.get_by_role('button',name='Support').click(); assert page.get_by_role('heading',name='Support ARLAW AI').is_visible(); link=page.get_by_role('link',name='Contact on Instagram'); assert 'instagram.com/architdutta17' in link.get_attribute('href'); page.get_by_role('button',name='Settings').click(); assert page.get_by_role('dialog').is_visible(); page.locator('#prefTheme').select_option('dark'); assert page.locator('html').get_attribute('data-theme')=='dark'; page.get_by_role('button',name='Done').click(); assert page.locator('html').get_attribute('data-theme')=='dark'; b.close(); p.stop(); print('Browser smoke test passed')"
```

This verifies the Support navigation, Instagram destination, settings dialog and dark-theme selection in Chromium. It does not test AI-provider credentials or certify legal-answer quality.
