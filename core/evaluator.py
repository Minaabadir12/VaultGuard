import re

def evaluate_password(password: str, personal_words: list, common_words: list):
    score = 0
    reasons = []

    # --- Length rule (0–30 points) ---
    if len(password) >= 10:
        score += 30
    else:
        score += max(0, (len(password) - 6) * 3)
        reasons.append("Too short (aim 10+).")

    # --- Character variety (15 each) ---
    if re.search(r'[a-z]', password):
        score += 15
    else:
        reasons.append("No lowercase letters.")

    if re.search(r'[A-Z]', password):
        score += 15
    else:
        reasons.append("No uppercase letters.")

    if re.search(r'\d', password):
        score += 15
    else:
        reasons.append("No digits.")

    if re.search(r'[^a-zA-Z0-9]', password):
        score += 15
    else:
        reasons.append("No symbols.")

    # --- Penalties ---
    if re.search(r'(.)\1\1', password):  # triple repeats like aaa or 111
        score -= 10
        reasons.append("Triple repeats (e.g., aaa, 111).")

    if any(word.lower() in password.lower() for word in common_words):
        score -= 15
        reasons.append("Contains common word.")

    if any(word.strip().lower() in password.lower() for word in personal_words if word.strip()):
        score -= 15
        reasons.append("Contains personal word.")

    # Detect common sequences
    sequences = ["12345", "abcdef", "qwerty", "asdf", "zxcv"]
    if any(seq in password.lower() for seq in sequences):
        score -= 10
        reasons.append("Sequential pattern (e.g., 12345, qwerty).")

    # --- Clamp score to 0–100 ---
    score = max(0, min(100, score))

    # --- Label ---
    if score >= 80:
        label = "Strong"
    elif score >= 60:
        label = "Good"
    elif score >= 40:
        label = "Fair"
    else:
        label = "Weak"

    return score, label, reasons
