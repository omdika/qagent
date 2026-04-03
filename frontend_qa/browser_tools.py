from playwright.sync_api import sync_playwright
import os

class BrowserTools:
    def __init__(self, headless=False):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=headless,
            channel="chrome"
        )
        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = self.context.new_page()
        self.console_errors = []

        # tangkap console errors otomatis
        self.page.on("console", lambda msg: self.console_errors.append(msg.text) if msg.type == "error" else None)

        os.makedirs("reports/screenshots", exist_ok=True)

    def navigate(self, url):
        try:
            self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
            return f"OK: navigated to {url}"
        except Exception as e:
            return f"ERROR: {e}"

    def click(self, selector):
        try:
            self.page.click(selector, timeout=5000)
            return f"OK: clicked {selector}"
        except Exception as e:
            return f"ERROR click {selector}: {e}"

    def type_text(self, selector, text):
        try:
            self.page.fill(selector, text)
            return f"OK: typed '{text}' into {selector}"
        except Exception as e:
            return f"ERROR type {selector}: {e}"

    def get_text(self, selector):
        try:
            return self.page.inner_text(selector, timeout=5000)
        except Exception as e:
            return f"ERROR get_text {selector}: {e}"

    def is_visible(self, selector):
        try:
            return self.page.is_visible(selector, timeout=3000)
        except:
            return False

    def get_url(self):
        return self.page.url

    def clear_local_storage(self):
        self.page.evaluate("localStorage.clear()")
        return "OK: localStorage cleared"

    def screenshot(self, name="screenshot"):
        path = f"reports/screenshots/{name}.png"
        self.page.screenshot(path=path, full_page=False)
        return path

    def get_console_errors(self):
        errors = self.console_errors.copy()
        self.console_errors.clear()
        return errors

    def wait(self, ms=1000):
        self.page.wait_for_timeout(ms)
        return f"OK: waited {ms}ms"

    def close(self):
        self.browser.close()
        self.playwright.stop()