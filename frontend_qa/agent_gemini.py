"""
QAgent — Frontend QA Agent for SwiftShop (Gemini version)
Reads user story → generates test cases → executes → reports
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import google.generativeai as genai
from browser_tools import BrowserTools
from mcp import MCP
from reporter import run_reporter
import json
import time

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ============================================================
# CONFIG
# Ganti BASE_URL dengan URL Vercel kamu setelah deploy
# ============================================================
BASE_URL = os.getenv("APP_URL", "http://localhost:3000")

bugs = []
all_results = []

# ============================================================
# STEP 0: EXTRACT SELECTORS FROM SOURCE CODE
# ============================================================

def extract_selectors_from_source() -> dict:
    """Read demo_app source files and let AI extract selectors"""
    demo_app_path = os.path.join(os.path.dirname(__file__), "../demo_app")
    source_content = {}
    
    for filename in os.listdir(demo_app_path):
        if filename.endswith((".html", ".js", ".jsx", ".tsx")):
            filepath = os.path.join(demo_app_path, filename)
            try:
                with open(filepath, "r") as f:
                    source_content[filename] = f.read()
            except:
                pass
    
    if not source_content:
        print("   ⚠️  No source files found in demo_app")
        return {}
    
    # AI analyze source → extract selectors
    prompt = f"""Analyze these source files and extract ALL clickable/input elements with their selectors.
Return JSON: {{"page_name": {{"element_name": "selector"}}}}

SOURCE FILES:
{json.dumps(source_content, indent=1)}

JSON only:
{{"login": {{"username": "#username", "password": "#password"}}, "products": {{"filter": ".filter-btn"}}}}
"""
    
    model = genai.GenerativeModel('gemini-3-flash-preview')
    response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.1))
    text = response.text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    
    try:
        selectors = json.loads(text)
        print(f"   ✓ Extracted selectors from {len(source_content)} files")
        return selectors
    except:
        print(f"   ✗ Failed to parse selectors from AI response")
        return {}


# ============================================================
# STEP 1: GENERATE TEST SCENARIOS
# ============================================================

def discover_all_pages(browser: BrowserTools, base_url: str) -> dict:
    """Kunjungi semua halaman utama dan scan elemennya"""
    pages_info = {}

    pages = [
        ("login", base_url + "/index.html"),
        ("products", base_url + "/products.html"),
        ("cart", base_url + "/cart.html"),
    ]

    for name, url in pages:
        print(f"   🔍 Scanning {name}: {url}")
        browser.navigate(url)
        browser.wait(1500)
        info = browser.discover_page()
        pages_info[name] = info
        print(f"      → {len(info['elements']['inputs'])} inputs, "
              f"{len(info['elements']['buttons'])} buttons")

    return pages_info


def generate_test_scenarios(user_story: str, pages_info: dict, source_selectors: dict) -> list:
    # Merge discovered + source selectors
    all_selectors = {"discovered": pages_info}
    if source_selectors:
        all_selectors["from_source"] = source_selectors
    
    prompt = f"""QA: Generate 4-6 test scenarios.

STORY: {user_story}

AVAILABLE SELECTORS:
{json.dumps(all_selectors, indent=1)}

Generate using ONLY real selectors above. Actions: navigate, click, type, assert_visible, assert_text, assert_url_contains.

JSON only:
[{{"id":"TC001","name":"...","priority":"high/medium/low","steps":["navigate: ..."],"expected":"..."}}]
"""
    model = genai.GenerativeModel('gemini-3-flash-preview')
    response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.2))
    text = response.text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


# ============================================================
# STEP 2: EXECUTE EACH STEP
# ============================================================

def execute_step(step: str, browser: BrowserTools) -> dict:
    step = step.strip()
    result = {"step": step, "status": "ok", "output": ""}

    try:
        if step.startswith("navigate:"):
            url = step.replace("navigate:", "").strip()
            output = browser.navigate(url)

        elif step.startswith("click:"):
            selector = step.replace("click:", "").strip()
            output = browser.click(selector)

        elif step.startswith("type:"):
            parts = step.replace("type:", "").strip().split("|")
            selector, text = parts[0].strip(), parts[1].strip()
            output = browser.type_text(selector, text)

        elif step.startswith("assert_visible:"):
            selector = step.replace("assert_visible:", "").strip()
            visible = browser.is_visible(selector)
            output = f"visible={visible} for {selector}"
            if not visible:
                result["status"] = "fail"

        elif step.startswith("assert_text:"):
            parts = step.replace("assert_text:", "").strip().split("|")
            selector, expected = parts[0].strip(), parts[1].strip()
            actual = browser.get_text(selector)
            match = expected.lower() in actual.lower()
            output = f"expected='{expected}' actual='{actual}' match={match}"
            if not match:
                result["status"] = "fail"

        elif step.startswith("assert_url_contains:"):
            path = step.replace("assert_url_contains:", "").strip()
            current_url = browser.get_url()
            match = path in current_url
            output = f"expected url contains '{path}', current='{current_url}' match={match}"
            if not match:
                result["status"] = "fail"

        elif step.startswith("clear_storage"):
            output = browser.clear_local_storage()

        elif step.startswith("wait:"):
            ms = int(step.replace("wait:", "").strip())
            output = browser.wait(ms)

        elif step.startswith("screenshot:"):
            name = step.replace("screenshot:", "").strip()
            path = browser.screenshot(name)
            output = f"screenshot saved: {path}"

        else:
            output = f"unknown step: {step}"
            result["status"] = "skip"

    except Exception as e:
        output = f"exception: {e}"
        result["status"] = "fail"

    result["output"] = output
    return result


# ============================================================
# STEP 3: VERDICT FROM LLM
# ============================================================

def get_verdict(scenario: dict, step_results: list, console_errors: list) -> dict:
    prompt = f"""QA: PASS or FAIL?
Test: {scenario['name']}
Expected: {scenario['expected']}
Results: {json.dumps([{"step":s['step'],"status":s['status']} for s in step_results])}
Errors: {console_errors or "none"}

JSON: {{"verdict":"pass/fail","reason":"...","bug_title":"...","severity":"..."}}
"""
    model = genai.GenerativeModel('gemini-3-flash-preview')
    response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.1))
    text = response.text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        if text == "":
            raise ValueError("empty AI response")
        return json.loads(text)
    except Exception as e:
        print(f"   ⚠️  get_verdict JSON parse failed: {e}")
        print(f"   raw response: {text}")
        return {
            "verdict": "fail",
            "reason": "Unable to parse AI verdict; fallback fail",
            "bug_title": "Invalid AI verdict response",
            "severity": "low"
        }


# ============================================================
# MAIN RUNNER
# ============================================================

def run_frontend_qa(user_story: str):
    global bugs, all_results
    bugs = []
    all_results = []

    print(f"\n{'='*60}")
    print(f"🤖 QAgent — Frontend QA (Gemini)")
    print(f"📋 User Story: {user_story[:80]}...")
    print(f"🌐 App URL: {BASE_URL}")
    print(f"{'='*60}\n")

    mcp = MCP()

    print("📖 Analyzing demo_app source code...")
    source_selectors = extract_selectors_from_source()

    print("🔍 Discovering pages...")
    pages_info = mcp.discover_pages(BASE_URL)
    print(f"   → {len(pages_info)} pages scanned\n")

    # Generate pakai semua selector
    print("📝 Generating test scenarios...")
    scenarios = generate_test_scenarios(user_story, pages_info, source_selectors)
    print(f"   → {len(scenarios)} scenarios generated\n")

    # Simpan test script / scenario ke reports (buat analisis & rerun manual)
    mcp.save_report("test_scenarios.json", scenarios)
    print("📄 Saved generated test scenarios to reports/test_scenarios.json")


    for scenario in scenarios:
        print(f"{'─'*60}")
        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(scenario['priority'], "⚪")
        print(f"🧪 {scenario['id']}: {scenario['name']} {priority_icon}")

        # Step 2: execute
        step_results = []
        for step in scenario['steps']:
            result = execute_step(step, browser)
            step_results.append(result)
            status_icon = "✓" if result['status'] == 'ok' else "✗" if result['status'] == 'fail' else "→"
            print(f"   {status_icon} {step[:55]}")

        console_errors = browser.get_console_errors()

        # Step 3: verdict
        verdict = get_verdict(scenario, step_results, console_errors)
        icon = "✅" if verdict['verdict'] == 'pass' else "❌"
        print(f"\n   {icon} {verdict['verdict'].upper()} — {verdict['reason']}")

        # Ambil screenshot setelah test case selesai
        screenshot_path = browser.screenshot(f"{scenario['id'].lower()}_result")

        result_entry = {
            "id": scenario['id'],
            "name": scenario['name'],
            "priority": scenario['priority'],
            "verdict": verdict['verdict'],
            "reason": verdict['reason'],
            "steps": step_results,
            "console_errors": console_errors,
            "screenshot": screenshot_path
        }

        if verdict['verdict'] == 'fail':
            bug = {
                "bug_id": f"BUG-{len(bugs)+1:03d}",
                "title": verdict.get('bug_title', scenario['name']),
                "severity": verdict.get('severity', 'medium'),
                "test_case": scenario['id'],
                "steps_to_reproduce": scenario['steps'],
                "expected": scenario['expected'],
                "actual": verdict['reason'],
                "console_errors": console_errors,
                "screenshot": result_entry['screenshot']
            }
            bugs.append(bug)
            print(f"   🐛 [{bug['severity'].upper()}] {bug['title']}")

        all_results.append(result_entry)
        time.sleep(2)

    browser.close()

    # Save bugs
    mcp.save_report("bug_report.json", bugs)

    # Report
    run_reporter(total_scenarios=len(scenarios))



def get_user_story_from_pr():
    pr_title = os.getenv("PR_TITLE", "")
    pr_body = os.getenv("PR_BODY", "")
    
    # Gabungkan title + body sebagai user story
    user_story = f"""
    JUDUL PR: {pr_title}
    
    DESKRIPSI:
    {pr_body}
    """
    return user_story

# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    user_story = """
## 🧪 QA User Story

As a user, I want to filter products by category (Electronics, Clothing, Accessories)
so I can find relevant products faster.


## ✅ Expected Behavior
- Clicking "Electronics" filter shows only electronics products
- Clicking "All" resets to show all products
- Multiple filters can be clicked sequentially
- Product count updates after filter applied

## ❌ Should Fail Gracefully
- Clicking filter with no matching products shows empty state message

## 🔑 Credentials
username: standard_user
password: secret_sauce

App URL: {BASE_URL}
Valid credentials: username=standard_user, password=secret_sauce
Invalid credentials: username=wrong_user, password=wrong_pass
Locked user: username=locked_user, password=secret_sauce
""".format(BASE_URL=BASE_URL)

    # run_frontend_qa(get_user_story_from_pr())
    run_frontend_qa(user_story)