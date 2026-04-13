import os
import json


class MCP:
    def __init__(self):
        self.root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.demo_app_dir = os.path.join(self.root, "demo_app")
        self.reports_dir = os.path.join(self.root, "reports")
        os.makedirs(self.reports_dir, exist_ok=True)

    def read_demo_files(self) -> dict:
        files = {}
        if not os.path.isdir(self.demo_app_dir):
            return files

        for filename in os.listdir(self.demo_app_dir):
            if filename.endswith((".html", ".js", ".jsx", ".tsx")):
                filepath = os.path.join(self.demo_app_dir, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        files[filename] = f.read()
                except Exception:
                    pass
        return files

    def discover_pages(self, browser, base_url: str) -> dict:
        """Use existing browser instance to discover pages"""
        pages_info = {}

        pages = [
            ("login", base_url + "/index.html"),
            ("products", base_url + "/products.html"),
            ("cart", base_url + "/cart.html"),
        ]

        for name, url in pages:
            try:
                browser.navigate(url)
                browser.wait(1500)
                pages_info[name] = browser.discover_page()
            except Exception as e:
                print(f"      ⚠️  Failed to scan {name}: {e}")

        return pages_info

    def save_report(self, filename: str, data) -> str:
        path = os.path.join(self.reports_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return path
