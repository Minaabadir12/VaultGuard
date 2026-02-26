import os
import yaml
import bcrypt

CREDS_PATH = os.path.join("assets", "creds.yaml")

def load_yaml(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def _save_yaml(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

def add_user(username: str, name: str, email: str, password_plain: str, path: str = CREDS_PATH) -> bool:
    cfg = load_yaml(path)
    creds = cfg.setdefault("credentials", {}).setdefault("usernames", {})
    if username in creds:
        return False
    hashed = bcrypt.hashpw(password_plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    creds[username] = {"name": name, "email": email, "password": hashed}
    _save_yaml(path, cfg)
    return True

def update_password(username: str, new_password: str, path: str = CREDS_PATH) -> bool:
    cfg = load_yaml(path)
    creds = cfg.setdefault("credentials", {}).setdefault("usernames", {})
    user = creds.get(username)
    if not user:
        return False
    hashed = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user["password"] = hashed
    _save_yaml(path, cfg)
    return True



