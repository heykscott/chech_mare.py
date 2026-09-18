# Find profile links or cards
    links = page.query_selector_all("a")
    for link in links:
        href = link.get_attribute("href") or ""
        
        # Match gallery profile cards
        if "/child" in href or "/profile" in href:
            # Look at the parent container to get the name and age together
            container = link.evaluate_handle("el => el.closest('.card') || el.closest('article') || el.parentElement || el")
            card_text = container.inner_text().strip()
            
            # Find age in the card text
            age_match = re.search(r"\b(\d+)\s*(?:years?|yrs?|yo|\b)", card_text, re.IGNORECASE)
            if age_match:
                age = int(age_match.group(1))
                if age < 6:
                    # Find first real name (ignore words like Profile, View, Child, Learn)
                    words = re.findall(r"\b[A-Z][a-z]+\b", card_text)
                    ignore_words = {"View", "Profile", "More", "Child", "Learn", "About", "Meet", "Waiting", "Details"}
                    names = [w for w in words if w not in ignore_words]
                    name = names[0] if names else f"Child ({href.split('/')[-1]})"
                    
                    entry = f"{name} - {age}"
                    if entry not in current_children:
                        current_children.append(entry)
