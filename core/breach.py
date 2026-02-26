import hashlib
import requests

HIBP_RANGE_URL = "https://api.pwnedpasswords.com/range/{}"
# Per HIBP guidance, a short user-agent is polite.
_HEADERS = {"User-Agent": "SafePass-Student-App"}

def sha1_hex(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest().upper()

def check_breach(password: str) -> tuple[int, bool, str]:
    """
    K-anonymity check using HIBP:
      1) Hash password with SHA-1 (uppercase hex).
      2) Send only the first 5 chars (prefix) to HIBP range API.
      3) Search returned suffixes locally.
    Returns: (count, found, message)
      - count: number of times seen in breaches (0 if not found or on error)
      - found: True if password hash appears in results
      - message: short human-readable status
    """
    if not password:
        return 0, False, "No password provided."

    full_hash = sha1_hex(password)
    prefix, suffix = full_hash[:5], full_hash[5:]

    try:
        resp = requests.get(HIBP_RANGE_URL.format(prefix), headers=_HEADERS, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        # Network or service error — fail closed (don’t block the app).
        return 0, False, f"Could not contact breach service ({e.__class__.__name__})."

    # Each line: SUFFIX:COUNT
    for line in resp.text.splitlines():
        parts = line.split(":")
        if len(parts) != 2:
            continue
        returned_suffix, count_str = parts[0].strip(), parts[1].strip()
        if returned_suffix.upper() == suffix:
            try:
                count = int(count_str.replace(",", ""))
            except ValueError:
                count = 1
            return count, True, "Password appears in known breaches."
    return 0, False, "No match found in known breaches."
