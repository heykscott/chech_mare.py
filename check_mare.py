from playwright.sync_api import sync_playwright
import json
import os
import re
import requests

url = "https://www.mareinc.org/child-gallery"
memory_file = "known_children.json"

# Load previously seen list
if os.path.exists(memory_file):
    with open(memory_file, "r") as f:
        known_roster = json.load(f)
else:
    known_roster = []

current_children = []

with sync_playwright() as p:
    # Launch with real browser user-agent and stealth args
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled"]
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800}
    )
    page = context.new_page()
    page.goto(url, wait_until="domcontentloaded")

    # Give dynamic content up to 10 seconds to mount
    page.wait_for_timeout(8000)

    # Scrape all visible text on the page to identify child profile entries
    full_text = page.inner_text("body")
    print(f"Page title loaded: {page.title()}")

    # Find profile links or cards
    links = page.query_selector_all("a")
    for link in links:
        href = link.get_attribute("href") or ""
        text = link.inner_text().strip()
        
        # Match gallery profile cards
        if "/child" in href or "/profile" in href:
            match = re.search(r"([A-Za-z]+).*?(\d+)", text)
            if match:
                name = match.group(1).strip()
                age = int(match.group(2))
                if age < 6:
                    entry = f"{name} - {age}"
                    if entry not in current_children:
                        current_children.append(entry)

    # Fallback: scan regex against rendered body text for patterns like 'Paul, age 1' or 'Viridiana, 4'
    if not current_children:
        matches = re.findall(r"([A-Z][a-z]+)\s*(?:,|\s-|\sis)?\s*(?:age\s*)?(\d+)\s*(?:years?|yrs?|yo)", full_text, re.IGNORECASE)
        for name, age_str in matches:
            age = int(age_str)
            if age < 6 and name not in ["MARE", "Boston", "Search", "Filter", "Age"]:
                entry = f"{name} - {age}"
                if entry not in current_children:
                    current_children.append(entry)

    print(f"Discovered children under 6: {current_children}")
    browser.close()

# Identify new children
new_children = [c for c in current_children if c not in known_roster]

# Save current list
with open(memory_file, "w") as f:
    json.dump(current_children, f, indent=2)

# Build daily report
if len(new_children) > 0:
    report = f"*** NEW ADDITIONS TODAY ({len(new_children)}) ***\n"
    for child in new_children:
        report += f"- {child}\n"
    report += "\n"
else:
    report = "No new profiles added today.\n\n"

report += "Under 6 year olds:\n"
if len(current_children) > 0:
    for child in current_children:
        report += f"- {child}\n"
else:
    report += "- None currently listed\n"

print(report)

# Send push notification
headers = {
    "Title": "MARE Daily Under 6 Report",
    "Click": "https://www.mareinc.org/child-gallery"
}
requests.post("https://ntfy.sh/katie-mare-alerts-2026", data=report.encode("utf-8"), headers=headers)
