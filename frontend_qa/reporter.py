import json
import os
from datetime import datetime


def load_bugs(path="reports/bug_report.json"):
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


def generate_markdown_report(bugs, total_scenarios):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    passed = total_scenarios - len(bugs)
    pass_rate = int(passed / total_scenarios * 100) if total_scenarios else 0

    lines = []
    lines.append(f"# 🤖 QAgent — Frontend QA Report")
    lines.append(f"**Generated:** {now}\n")

    # Summary
    status_emoji = "✅" if len(bugs) == 0 else "⚠️" if len(bugs) < total_scenarios / 2 else "❌"
    lines.append(f"## {status_emoji} Summary\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Test Cases | {total_scenarios} |")
    lines.append(f"| ✅ Passed | {passed} |")
    lines.append(f"| ❌ Failed | {len(bugs)} |")
    lines.append(f"| Pass Rate | {pass_rate}% |\n")

    if not bugs:
        lines.append("## ✅ All test cases passed!")
        return "\n".join(lines)

    # Bugs by severity
    lines.append(f"## 🐛 Bug Reports\n")
    severity_order = ["critical", "high", "medium", "low"]
    severity_icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}

    for severity in severity_order:
        filtered = [b for b in bugs if b.get("severity") == severity]
        if not filtered:
            continue

        icon = severity_icons[severity]
        lines.append(f"### {icon} {severity.upper()} ({len(filtered)})\n")

        for bug in filtered:
            lines.append(f"#### {bug['bug_id']}: {bug['title']}\n")
            lines.append(f"- **Test Case:** `{bug['test_case']}`")
            lines.append(f"- **Expected:** {bug['expected']}")
            lines.append(f"- **Actual:** {bug['actual']}")
            if bug.get("screenshot"):
                lines.append(f"- **Screenshot:** `{bug['screenshot']}`")
            lines.append(f"\n**Steps to Reproduce:**")
            for i, step in enumerate(bug["steps_to_reproduce"], 1):
                lines.append(f"{i}. `{step}`")
            lines.append("")

    return "\n".join(lines)


def print_summary(bugs, total_scenarios):
    passed = total_scenarios - len(bugs)
    pass_rate = int(passed / total_scenarios * 100) if total_scenarios else 0

    print(f"\n{'='*60}")
    print(f"📊 QAgent FINAL REPORT")
    print(f"{'='*60}")
    print(f"  Total   : {total_scenarios} test cases")
    print(f"  Passed  : {passed} ✅")
    print(f"  Failed  : {len(bugs)} ❌")
    print(f"  Rate    : {pass_rate}%")

    if bugs:
        print(f"\n  🐛 Bugs Found:")
        icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        for bug in bugs:
            icon = icons.get(bug.get("severity", "low"), "⚪")
            print(f"  {icon} [{bug['severity'].upper()}] {bug['bug_id']}: {bug['title']}")

    print(f"{'='*60}")


def run_reporter(total_scenarios: int):
    bugs = load_bugs()
    print_summary(bugs, total_scenarios)

    report = generate_markdown_report(bugs, total_scenarios)
    os.makedirs("reports", exist_ok=True)
    path = "reports/qa_report.md"
    with open(path, "w") as f:
        f.write(report)

    print(f"\n💾 Full report saved to {path}")


if __name__ == "__main__":
    run_reporter(total_scenarios=5)