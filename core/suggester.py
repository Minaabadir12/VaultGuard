import re
import secrets
import string

# A small built-in word bank for suggestions (capitalized later)
_WORDS = [
    "sky", "maple", "river", "ember", "storm", "nova", "orbit", "quartz", "arbor", "polar",
    "cobalt", "neon", "apex", "vertex", "zenith", "glacier", "cedar", "sage", "ember", "onyx",
    "raven", "falcon", "aster", "echo", "vortex", "solace", "cinder", "willow", "harbor", "prairie",
    "blizzard", "citron", "topaz", "coral", "granite", "comet", "aurora", "meteor", "silk", "gale",
    "meadow", "spruce", "dune", "breeze", "lotus", "panda", "tundra", "zephyr", "lagoon", "fjord",
    "pebble", "emberly", "marble", "saffron", "sable", "walnut", "pearl", "garnet", "jasper", "basil",
    "canyon", "summit", "sagebrush", "fable", "lilac", "hazel", "bramble", "thistle", "poppy", "indigo",
    "amber", "cinder", "kestrel", "juniper", "olive", "flint", "cascade", "drift", "emberline", "reef",
    "solstice", "equinox", "plume", "quiver", "emberstone", "sprout", "harvest", "voyage", "cinderfox",
    "midnight", "daybreak", "starlit", "seaborn", "seastar", "pine", "aspen", "alpine", "wisteria", "opal"
]

_SYMBOLS = list("!@#$%^&*_-?")

_SEQ_PATTERNS = ["012345", "12345", "abcdef", "qwerty", "asdf", "zxcv"]

def _pick_word(exclude_lower: set):
    # Pick a word not in the exclude set
    for _ in range(200):
        w = secrets.choice(_WORDS)
        if w.lower() not in exclude_lower:
            return w.capitalize()
    # Fallback
    return secrets.choice(_WORDS).capitalize()

def _has_all_classes(s: str) -> bool:
    return (re.search(r'[a-z]', s) and
            re.search(r'[A-Z]', s) and
            re.search(r'\d', s) and
            re.search(r'[^a-zA-Z0-9]', s) is not None)

def _contains_weak_bits(s: str, personal_words, common_words) -> bool:
    low = s.lower()
    if any(w.strip() and w.strip().lower() in low for w in personal_words):
        return True
    if any(w and w.lower() in low for w in common_words):
        return True
    if any(seq in low for seq in _SEQ_PATTERNS):
        return True
    if re.search(r'(.)\1\1', s):  # triple repeat
        return True
    return False

def suggest_password(current_password: str, personal_words: list, common_words: list) -> str:
    """
    Build a suggestion in the format:
      Two Capitalized Words + 1 symbol + 3 digits + 1 uppercase tail
    Ensure:
      - length >= 12
      - contains lowercase, uppercase, digit, symbol
      - avoids common/personal words and sequences
    Example: SkyMaple_938Z
    """
    # Exclude anything already in the current password to "remove weak bits"
    exclude_lower = set()
    for token in re.findall(r'[a-zA-Z]+', current_password or ""):
        if len(token) >= 3:
            exclude_lower.add(token.lower())
    for w in personal_words:
        if w.strip():
            exclude_lower.add(w.strip().lower())
    for w in common_words:
        exclude_lower.add(w.lower())

    for _ in range(500):  # Try up to 500 times to satisfy constraints
        w1 = _pick_word(exclude_lower)
        w2 = _pick_word(exclude_lower)

        sym = secrets.choice(_SYMBOLS)
        digits = "".join(secrets.choice(string.digits) for _ in range(3))
        tail = secrets.choice(string.ascii_uppercase)

        candidate = f"{w1}{w2}{sym}{digits}{tail}"

        # Ensure minimum length and class coverage
        if len(candidate) < 12:
            # pad with an extra digit and uppercase if needed
            candidate += secrets.choice(string.digits) + secrets.choice(string.ascii_uppercase)

        if not _has_all_classes(candidate):
            continue
        if _contains_weak_bits(candidate, personal_words, common_words):
            continue
        # Final sanity: avoid embedding the original password verbatim
        if current_password and current_password.lower() in candidate.lower():
            continue

        return candidate

    # Worst-case fallback (should rarely happen)
    return "SkyMaple_938Z"
