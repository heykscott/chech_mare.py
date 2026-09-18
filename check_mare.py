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
    
    # Wait for child profile links to appear in the DOM
    page.wait_for_selector("a[href*='/child/']", timeout=20000)
    
    # Find all profile links on the page
    links = page.query_selector_all("a[href*='/child/']")
    seen_ids = set()

    for link in links:
        href = link.get_attribute("href") or ""
        child_id = href.split("/")[-1]
        
        if not child_id or child_id in seen_ids:
            continue
        seen_ids.add(child_id)
        
        # Grab the text inside the link's card container
        parent = link.evaluate_handle("el => el.closest('div') || el")
        card_text = parent.inner_text()
        
        # Check for ages 0 through 5
        ages = re.findall(r"\b(\d+)\s*(?:years?|yrs?|yo|\b)", card_text, re.IGNORECASE)
        name_match = re.search(r"([A-Za-z]+)", card_text)
        name = name_match.group(1) if name_match else f"Child {child_id}"

        # Match any age under 6 or baby/infant keywords
        under_6 = any(int(a) < 6 for a in ages) or "baby" in card_text.lower() or "infant" in card_text.lower()
        
        if under_6:
            age_str = ages[0] if ages else "under 6"
            entry = f"{name} - {age_str}"
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
