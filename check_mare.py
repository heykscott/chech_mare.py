import requests
from bs4 import BeautifulSoup
import json
import os
import re

url = "https://www.mareinc.org/child-gallery"
memory_file = "known_children.json"

# Step 1: Load previously seen child IDs from file
if os.path.exists(memory_file):
    with open(memory_file, "r") as f:
        known_ids = json.load(f)
else:
    known_ids = []

# Step 2: Download the web page
headers = {"User-Agent": "Mozilla/5.0"}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Step 3: Find all cards on the page
cards = soup.find_all("div", class_="card")

current_children = []
current_ids = []
new_children = []

for card in cards:
    # Get ID, Name, and Age
    child_id = card.get("data-childid")
    
    name_tag = card.find("div", class_="name")
    name = name_tag.text.strip() if name_tag else "No Name"

    age_tag = card.find("div", class_="age")
    age_text = age_tag.text.strip() if age_tag else ""

    # Pull numbers from age text (e.g., "1 years old" -> 1)
    numbers = re.findall(r"\d+", age_text)
    
    # Check if child is under age 6 (0 through 5)
    under_6 = False
    for num in numbers:
        if int(num) < 6:
            under_6 = True
    if "baby" in age_text.lower():
        under_6 = True

    if under_6 and child_id:
        current_ids.append(child_id)
        current_children.append(f"{name} ({age_text})")
        
        # Check if we have seen this ID before
        if child_id not in known_ids:
            new_children.append(f"{name} ({age_text})")

# Step 4: Save the current IDs back to the file
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
for child in current_children:
    report += f"- {child}\n"

print(report)

# Step 6: Send push notification to phone via ntfy
requests.post("https://ntfy.sh/katie-mare-alerts-2026", data=report.encode("utf-8"))
