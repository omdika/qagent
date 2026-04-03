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

    def discover_page(self):
        """Scan halaman dan return semua elemen yang relevan"""
        
        # Ambil semua interactive elements beserta selector & teksnya
        elements = self.page.evaluate("""() => {
            const result = { inputs: [], buttons: [], links: [], texts: [] };

            // Input fields
            document.querySelectorAll('input, textarea, select').forEach(el => {
                result.inputs.push({
                    tag: el.tagName.toLowerCase(),
                    id: el.id || null,
                    name: el.name || null,
                    type: el.type || null,
                    placeholder: el.placeholder || null,
                    selector: el.id ? '#' + el.id : (el.name ? `[name="${el.name}"]` : el.tagName.toLowerCase())
                });
            });

            // Buttons
            document.querySelectorAll('button, [role="button"], input[type="submit"]').forEach(el => {
                result.buttons.push({
                    text: el.innerText?.trim() || el.value || null,
                    id: el.id || null,
                    selector: el.id ? '#' + el.id : 'button'
                });
            });

            // Links
            document.querySelectorAll('a[href]').forEach(el => {
                result.links.push({
                    text: el.innerText?.trim(),
                    href: el.href,
                    id: el.id || null
                });
            });

            // Visible text (headings & labels)
            document.querySelectorAll('h1,h2,h3,label,p').forEach(el => {
                const text = el.innerText?.trim();
                if (text && text.length < 100) result.texts.push(text);
            });

            return result;
        }""")

        screenshot_path = self.screenshot("discovery")
        return {
            "url": self.get_url(),
            "elements": elements,
            "screenshot": screenshot_path
        }