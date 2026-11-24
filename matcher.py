import re
from datetime import datetime

def tokenize(text):
    if not text:
        return set()
    # Lowercase and split into alphanumeric tokens
    tokens = re.findall(r'\b[a-zA-Z0-9]{3,}\b', text.lower())
    # Exclude common stopwords
    stopwords = {
        'the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'were', 'been',
        'near', 'next', 'lost', 'found', 'item', 'please', 'help', 'some', 'about',
        'into', 'after', 'before', 'color', 'black', 'white', 'blue', 'grey', 'gray'
    }
    return set(t for t in tokens if t not in stopwords)


def calculate_similarity(item_a, item_b):
    """
    Computes a smart match percentage score (0 to 100) between two items.
    item_a and item_b can be Item model instances.
    """
    # Items must be of opposite types (one lost, one found)
    if item_a.report_type == item_b.report_type:
        return 0.0

    score = 0.0

    # 1. Category Match (40 points)
    if item_a.category_id == item_b.category_id:
        score += 40.0

    # 2. Location Match (25 points)
    loc_a = tokenize(item_a.location)
    loc_b = tokenize(item_b.location)
    if loc_a and loc_b:
        loc_overlap = loc_a.intersection(loc_b)
        if loc_overlap:
            # Overlap ratio relative to smallest set
            loc_ratio = len(loc_overlap) / min(len(loc_a), len(loc_b))
            score += min(25.0, loc_ratio * 25.0)
    elif item_a.location.strip().lower() == item_b.location.strip().lower():
        score += 25.0

    # 3. Title & Description Keyword Overlap (35 points)
    text_a = f"{item_a.item_name} {item_a.description}"
    text_b = f"{item_b.item_name} {item_b.description}"
    words_a = tokenize(text_a)
    words_b = tokenize(text_b)
    
    if words_a and words_b:
        intersection = words_a.intersection(words_b)
        union = words_a.union(words_b)
        jaccard = len(intersection) / len(union) if union else 0
        # Boost if name tokens specifically match
        name_a = tokenize(item_a.item_name)
        name_b = tokenize(item_b.item_name)
        name_match = len(name_a.intersection(name_b)) > 0

        text_score = (jaccard * 25.0) + (10.0 if name_match else 0.0)
        score += min(35.0, text_score)

    # 4. Date Proximity bonus (up to 5 points)
    if item_a.event_date and item_b.event_date:
        delta_days = abs((item_a.event_date - item_b.event_date).days)
        if delta_days <= 3:
            score += 5.0
        elif delta_days <= 7:
            score += 2.0

    return min(100.0, round(score, 1))


def find_matches_for_item(target_item, candidate_items, threshold=35.0):
    """
    Finds and ranks candidate items that potentially match the target item.
    """
    matches = []
    for cand in candidate_items:
        if cand.id == target_item.id:
            continue
        sim = calculate_similarity(target_item, cand)
        if sim >= threshold:
            matches.append({
                'item': cand.to_dict(safe_mode=True),
                'match_score': sim,
                'confidence': 'High' if sim >= 70 else ('Moderate' if sim >= 50 else 'Possible')
            })

    # Sort descending by match score
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    return matches
