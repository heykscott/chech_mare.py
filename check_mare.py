import requests
from bs4 import BeautifulSoup
import json
import os
import re

# Query MARE directly for children ages 0 to 5
url = "https://www.mareinc.org/child-gallery?minAge=0&maxAge=5"
memory_file = "known_children.json"

# Step 1: Load previously seen child IDs
if os.path.exists(memory_file):
    with open(memory_file, "r") as f:
        known_ids = json.load(f)
else:
    known_ids = []

# Step 2: Request the gallery page
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Step 3: Find child profile links/cards
current_children = []
current_ids = []
new_children = []

# Look for profile links or cards on the page
profiles = soup.find_all("a", href=re.compile(r"/child/\d+"))

seen_urls = set()
for p in profiles:
    link = p.get("href")
    if link in seen_urls:
        continue
    seen_urls.add(link)
    
    child_id = link.split("/")[-1]
    
    # Extract text from link or surrounding container
    container = p.find_parent("div") or p
    text = container.get_text(" ", strip=True)
    
    # Parse name and age if present
    match = re.search(r"([A-Za-z\s\'-]+?)\s*,?\s*age\s*(\d+)", text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        age = match.group(2).strip()
        label = f"{name} - {age}"
    else:
        # Fallback to link text
        link_text = p.get_text(strip=True) or f"Child {child_id}"
        label = link_text

    current_ids.append(child_id)
    current_children.append(label)

    if child_id not in known_ids:
        new_children.append(label)

# Step 4: Save current IDs
with open(memory_file, "w") as f:
    json.dump(current_ids, f, indent=2)

# Step 5: Build the notification text
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

# Step 6: Send push notification via ntfy
headers = {
    "Title": "MARE Daily Under 6 Report",
    "Click": "https://www.mareinc.org/child-gallery"
}
requests.post("https://ntfy.sh/katie-mare-alerts-2026", data=report.encode("utf-8"), headers=headers)
