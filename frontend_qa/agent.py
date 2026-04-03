"""
QAgent — Frontend QA Agent for SwiftShop
Reads user story → generates test cases → executes → reports
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from groq import Groq
from browser_tools import BrowserTools
from reporter import run_reporter
import json
import time

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ============================================================
# CONFIG
# Ganti BASE_URL dengan URL Vercel kamu setelah deploy
# ============================================================
BASE_URL = os.getenv("APP_URL", "http://localhost:3000")

bugs = []
all_results = []

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


def generate_test_scenarios(user_story: str, pages_info: dict) -> list:
    prompt = f"""
You are a senior QA Engineer. You have already scanned the app pages.

USER STORY:
{user_story}

DISCOVERED PAGE ELEMENTS:
{json.dumps(pages_info, indent=2)}

Generate 4-6 test scenarios using ONLY the real selectors found above.
Do not invent selectors — use exactly what was discovered.

Available actions:
- navigate: <url>
- click: <css_selector>
- type: <css_selector> | <text>
- assert_visible: <css_selector>
- assert_text: <css_selector> | <expected_text>
- assert_url_contains: <path>
- clear_storage
- wait: <ms>
- screenshot: <filename>

Respond ONLY with JSON array, no markdown:
[
  {{
    "id": "TC001",
    "name": "...",
    "priority": "high/medium/low",
    "steps": ["navigate: ...", "type: #real-selector | value", ...],
    "expected": "..."
  }}
]
"""
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    text = response.choices[0].message.content.strip()
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
    prompt = f"""
You are a QA Engineer. Evaluate the test case execution below.

TEST CASE: {scenario['name']}
EXPECTED: {scenario['expected']}

STEP RESULTS:
{json.dumps(step_results, indent=2)}

CONSOLE ERRORS: {console_errors if console_errors else "none"}

Based on the results, did this test PASS or FAIL?

Respond ONLY with JSON, no markdown:
{{
  "verdict": "pass" or "fail",
  "reason": "one sentence explanation",
  "bug_title": "short bug title if fail, empty if pass",
  "severity": "critical/high/medium/low if fail, empty if pass"
}}
"""
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    return json.loads(text)


# ============================================================
# MAIN RUNNER
# ============================================================

def run_frontend_qa(user_story: str):
    global bugs, all_results
    bugs = []
    all_results = []

    print(f"\n{'='*60}")
    print(f"🤖 QAgent — Frontend QA")
    print(f"📋 User Story: {user_story[:80]}...")
    print(f"🌐 App URL: {BASE_URL}")
    print(f"{'='*60}\n")

    browser = BrowserTools(headless=False)

    # ✅ TAMBAH INI: discover dulu sebelum generate
    print("🔍 Discovering pages...")
    pages_info = discover_all_pages(browser, BASE_URL)
    print(f"   → {len(pages_info)} pages scanned\n")

    # Generate pakai info halaman yang nyata
    print("📝 Generating test scenarios...")
    scenarios = generate_test_scenarios(user_story, pages_info)
    print(f"   → {len(scenarios)} scenarios generated\n")


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

        result_entry = {
            "id": scenario['id'],
            "name": scenario['name'],
            "priority": scenario['priority'],
            "verdict": verdict['verdict'],
            "reason": verdict['reason'],
            "steps": step_results,
            "screenshot": f"reports/screenshots/{scenario['id'].lower()}_result.png"
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
                "screenshot": result_entry['screenshot']
            }
            bugs.append(bug)
            print(f"   🐛 [{bug['severity'].upper()}] {bug['title']}")

        all_results.append(result_entry)
        time.sleep(2)

    browser.close()

    # Save bugs
    os.makedirs("reports", exist_ok=True)
    with open("reports/bug_report.json", "w") as f:
        json.dump(bugs, f, indent=2, ensure_ascii=False)

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
As a user, I want to be able to login to SwiftShop using
valid credentials so I can browse and purchase products.
If login fails, I should see a clear error message.

After login, I want to:
- Browse products and filter by category 
- Add products to cart
- View cart and see correct total
- Complete checkout and see order confirmation

App URL: {BASE_URL}
Valid credentials: username=standard_user, password=secret_sauce
Invalid credentials: username=wrong_user, password=wrong_pass
Locked user: username=locked_user, password=secret_sauce
""".format(BASE_URL=BASE_URL)

    run_frontend_qa(get_user_story_from_pr())
    # run_frontend_qa(user_story)