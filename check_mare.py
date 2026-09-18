from playwright.sync_api import sync_playwright
import json
import os
import re
import requests

url = "https://www.mareinc.org/child-gallery"
memory_file = "known_children.json"

# Load previously seen names
if os.path.exists(memory_file):
    with open(memory_file, "r") as f:
        known_roster = json.load(f)
else:
    known_roster = []

current_children = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(url, wait_until="networkidle")
    
    # Wait for the profile cards to appear on the screen
    page.wait_for_selector(".card, [class*='child']", timeout=15000)
    
    # Extract all text elements containing age information
    cards = page.query_selector_all(".card, div[class*='profile'], div[class*='child-card']")
    for card in cards:
        text = card.inner_text()
        
        # Match pattern: Name and Age
        match = re.search(r"([A-Za-z]+).*?(\d+)\s*(?:years?|yrs?|\n)", text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            age = int(match.group(2))
            if age < 6:
                entry = f"{name} - {age}"
                if entry not in current_children:
                    current_children.append(entry)

    browser.close()

# Identify any newly added children
new_children = [child for child in current_children if child not in known_roster]

# Save current list back to file
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
