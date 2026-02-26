import os 
import re
import base64
from datetime import datetime

import bcrypt
import streamlit as st
from streamlit.components.v1 import html as st_html  # kept; not used for preview now

from core.evaluator import evaluate_password
from core.suggester import suggest_password
from core.breach import check_breach
from core.report import save_report_txt, save_report_pdf
from core.auth import add_user, load_yaml, update_password  # password update

# =========================
# PAGE CONFIG & BRANDING
# =========================
st.set_page_config(
    page_title="VaultGuard – Password Advisor",
    page_icon="🛡️",
    layout="centered",
)

LOGO_PATH = "assets/vaultguard_logo.png"

# Built-in SVG logo fallback (teal shield with gold lock)
_BUILTIN_LOGO_SVG = """
<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
  <svg width="44" height="44" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg"
       role="img" aria-label="VaultGuard logo">
    <defs>
      <linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#0f766e"/>
        <stop offset="100%" stop-color="#134e4a"/>
      </linearGradient>
    </defs>
    <path d="M32 4l20 8v16c0 14.5-9.6 25.8-20 32-10.4-6.2-20-17.5-20-32V12l20-8z"
          fill="url(#g1)"/>
    <rect x="20" y="28" width="24" height="18" rx="3" fill="#f4b740"/>
    <path d="M32 22c-4.4 0-8 3.6-8 8h4c0-2.2 1.8-4 4-4s4 1.8 4 4h4c0-4.4-3.6-8-8-8z"
          fill="#f4b740"/>
    <circle cx="32" cy="36" r="2.6" fill="#1f2937"/>
    <rect x="31" y="38" width="2" height="5" rx="1" fill="#1f2937"/>
  </svg>
  <div style="font-weight:700;font-size:22px;letter-spacing:.2px;">
    VaultGuard – Password Advisor
  </div>
</div>
"""

def _render_logo():
    if os.path.exists(LOGO_PATH):
        try:
            st.image(LOGO_PATH, width=140)
            return
        except Exception:
            pass
    st.markdown(_BUILTIN_LOGO_SVG, unsafe_allow_html=True)

_render_logo()
st.write(
    "Check strength (0–100), read short reasons, get a stronger suggestion, "
    "and run a k-anonymity breach check."
)

CREDS_PATH = os.path.join("assets", "creds.yaml")

# =========================
# Helpers
# =========================
@st.cache_data
def load_common_words():
    try:
        with open("assets/common_words.txt", "r", encoding="utf-8") as f:
            return [w.strip() for w in f if w.strip()]
    except FileNotFoundError:
        return ["password", "letmein", "welcome", "football", "baseball", "dragon", "monkey"]

def parse_personal_words(s: str):
    return [w.strip() for w in s.split(",") if w.strip()]

def _init_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "name" not in st.session_state:
        st.session_state.name = None
    if "username" not in st.session_state:
        st.session_state.username = None

    if "score" not in st.session_state:
        st.session_state.score = None
    if "label" not in st.session_state:
        st.session_state.label = None
    if "reasons" not in st.session_state:
        st.session_state.reasons = []
    if "suggestion" not in st.session_state:
        st.session_state.suggestion = None
    if "breach" not in st.session_state:
        st.session_state.breach = {"count": 0, "found": False, "message": "Not checked."}

    if "password_input" not in st.session_state:
        st.session_state.password_input = ""
    if "personal_words_input" not in st.session_state:
        st.session_state.personal_words_input = ""

    # Sign-up field state (stable keys)
    st.session_state.setdefault("su_username", "")
    st.session_state.setdefault("su_name", "")
    st.session_state.setdefault("su_email", "")
    st.session_state.setdefault("su_password", "")

    # Reports UI state
    st.session_state.setdefault("view_report", None)

    # Modal state (for delete confirm)
    st.session_state.setdefault("modal_open", False)
    st.session_state.setdefault("modal_file", None)

_init_state()

def _reset_form():
    st.session_state.score = None
    st.session_state.label = None
    st.session_state.reasons = []
    st.session_state.suggestion = None
    st.session_state.breach = {"count": 0, "found": False, "message": "Not checked."}
    st.session_state.password_input = ""
    st.session_state.personal_words_input = ""

# ---- Sidebar UI helpers ----
def _ensure_page():
    if "page" not in st.session_state:
        st.session_state.page = "Home"

def _nav_button(label: str, key: str, icon: str):
    selected = (st.session_state.page == label)
    return st.button(
        f"{icon}  {label}",
        key=key,
        use_container_width=True,
        type="primary" if selected else "secondary",
    )

# --- Global CSS (includes nicer reports buttons) ---
_SIDEBAR_CSS = """
<style>
section[data-testid="stSidebar"] { padding-top: .5rem !important; }
.vg-card {
  background: linear-gradient(135deg, rgba(34,197,94,.12), rgba(16,185,129,.10));
  border: 1px solid rgba(16,185,129,.35);
  padding: 14px 16px;
  border-radius: 14px;
  margin-bottom: 12px;
}
.vg-user { font-weight: 700; letter-spacing:.2px; }
.vg-sub  { font-size:.85rem; opacity:.75; margin-top:2px; }
.vg-nav-title { margin: 12px 0 6px 2px; font-size:.82rem; letter-spacing:.06em; opacity:.8; }
section[data-testid="stSidebar"] .stButton > button {
  border-radius: 12px;
  padding: .60rem .8rem;
  border: 1px solid rgba(148,163,184,.25);
  background: rgba(30,41,59,.20);
}
section[data-testid="stSidebar"] .stButton > button:hover {
  background: rgba(148,163,184,.15);
}
section[data-testid="stSidebar"] .stButton [data-testid="baseButton-primary"] {
  background: linear-gradient(135deg, #10b981, #0ea5e9);
  border: none;
}

/* Reports buttons */
div[data-testid="stDownloadButton"] > button {
  border-radius: 12px !important;
  background: linear-gradient(135deg,#6366f1,#0ea5e9) !important;
  color: white !important;
  border: none !important;
}
.view-btn [data-testid="baseButton-primary"] {
  background: linear-gradient(135deg,#0ea5e9,#22c55e) !important;
  border: none !important;
}

/* Modern logout button */
.vg-logout .stButton > button {
  width: 100%;
  border: none;
  border-radius: 12px;
  padding: .70rem 1rem;
  font-weight: 700;
  letter-spacing: .01em;
  background: linear-gradient(135deg, #ef4444, #f97316);
  color: #fff;
  box-shadow: 0 8px 18px rgba(239, 68, 68, .28);
  transition: transform .08s ease, box-shadow .12s ease, filter .12s ease;
}
.vg-logout .stButton > button:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 22px rgba(239, 68, 68, .35);
  filter: brightness(1.03);
}
.vg-logout .stButton > button:active {
  transform: translateY(0);
  box-shadow: 0 6px 14px rgba(239, 68, 68, .25);
}
</style>
"""

# ===== Modal overlay CSS (retained, not used by confirm panel) =====
_MODAL_CSS = """
<style>
.vg-modal-mask{
  position: fixed; inset: 0;
  background: rgba(0,0,0,.55);
  z-index: 9999;
  display: flex; align-items: center; justify-content: center;
}
.vg-modal{
  width: min(520px, 92vw);
  background: #111827;
  border: 1px solid rgba(148,163,184,.25);
  border-radius: 16px;
  padding: 20px 22px;
  box-shadow: 0 20px 50px rgba(0,0,0,.35);
}
.vg-modal h4{ margin: 0 0 6px 0; }
.vg-modal p { margin: 6px 0 0 0; color: #cbd5e1; }
.vg-modal .row{ display:flex; gap:12px; justify-content:flex-end; margin-top:16px; }
.vg-modal .stButton > button{
  white-space: nowrap;
  min-width: 120px;
  padding: .62rem 1rem;
  border-radius: 12px;
  font-weight: 700;
}
.vg-btn-ghost{
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(148,163,184,.25);
}
.vg-btn-danger{
  background: linear-gradient(135deg,#ef4444,#dc2626);
  color: #fff; border: none;
}
</style>
"""

def render_modal():
    """
    Retained function (no-op UI wrapper using native Streamlit).
    We don't call this globally; the confirmation renders inline
    at the top of the Reports page for reliability.
    """
    if not st.session_state.get("modal_open"):
        return
    fname = st.session_state.get("modal_file")
    with st.container(border=True):
        st.markdown("### Delete report?")
        st.write(f"`{fname}` will be permanently removed. This cannot be undone.")
        colA, colB = st.columns(2)
        with colA:
            if st.button("Cancel", key="modal_cancel"):
                st.session_state.modal_open = False
                st.session_state.modal_file = None
                st.rerun()
        with colB:
            if st.button("Delete", key="modal_delete"):
                try:
                    os.remove(_safe_path(fname))
                    if st.session_state.view_report == fname:
                        st.session_state.view_report = None
                    st.success(f"Deleted {fname}")
                except Exception as e:
                    st.error(f"Could not delete: {e}")
                finally:
                    st.session_state.modal_open = False
                    st.session_state.modal_file = None
                    st.rerun()

# =========================
# AUTH (manual login system)
# =========================
def render_login():
    st.markdown("""
    <style>
      .vg-form .stTextInput>div>div>input { padding: 0.75rem 0.9rem; font-size: 1rem; }
      .vg-form .stButton>button { width: 100%; padding: 0.8rem 1rem; font-weight: 600; border-radius: 10px; }
      .vg-muted { color: var(--text-color-secondary,#94a3b8); font-size: 0.92rem; }
    </style>
    """, unsafe_allow_html=True)

    st.subheader("Sign In")

    with st.container():
        with st.form("login_form", clear_on_submit=False):
            st.text_input("Username", key="login_user", placeholder="Enter your username", help="Your VaultGuard username.")
            st.text_input("Password", key="login_pass", type="password", placeholder="Enter your password")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

    # Forgot password
    with st.expander("Forgot password?"):
        st.markdown('<div class="vg-muted">Reset your password for an existing username.</div>', unsafe_allow_html=True)
        fp_user = st.text_input("Username (existing)")
        fp_new = st.text_input("New password", type="password")
        fp_conf = st.text_input("Confirm new password", type="password")
        if st.button("Update Password", use_container_width=True):
            if not (fp_user and fp_new and fp_conf):
                st.warning("Please fill in all fields.")
            elif fp_new != fp_conf:
                st.error("Passwords do not match.")
            elif len(fp_new) < 6:
                st.warning("New password should be at least 6 characters.")
            else:
                try:
                    if update_password(fp_user.strip(), fp_new.strip()):
                        st.success("✅ Password updated. You can sign in with the new password now.")
                    else:
                        st.error("Username not found. Check the spelling or create a new account below.")
                except FileNotFoundError:
                    st.error("⚠️ Credentials file not found (assets/creds.yaml).")

    # Sign Up
    with st.expander("New here? Create an account"):
        st.text_input("New username", key="su_username")
        st.text_input("Full name", key="su_name")
        st.text_input("Email", key="su_email", placeholder="name@example.com")
        st.text_input("New password", type="password", key="su_password")
        if st.button("Sign Up", use_container_width=True):
            new_username = st.session_state.su_username.strip()
            new_name = st.session_state.su_name.strip()
            new_email = st.session_state.su_email.strip()
            new_password = st.session_state.su_password.strip()

            if not all([new_username, new_name, new_email, new_password]):
                st.warning("Please fill in all fields.")
            elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", new_email):
                st.warning("Please enter a valid email address.")
            elif len(new_password) < 6:
                st.warning("Password should be at least 6 characters.")
            else:
                try:
                    ok = add_user(new_username, new_name, new_email, new_password)
                    if ok:
                        st.success("✅ Account created. You can sign in now.")
                    else:
                        st.error("Username already exists. Choose another.")
                except FileNotFoundError:
                    st.error("⚠️ Credentials file not found (assets/creds.yaml).")

    if submitted:
        cfg = {}
        try:
            cfg = load_yaml(CREDS_PATH) or {}
        except FileNotFoundError:
            st.error("⚠️ Credentials file not found (assets/creds.yaml).")
            return
        except Exception as e:
            st.error(f"⚠️ Failed to load credentials: {e}")
            return

        users = (cfg.get("credentials", {}) or {}).get("usernames", {}) or {}
        username = st.session_state.get("login_user", "")
        password = st.session_state.get("login_pass", "")

        user = users.get(username)
        if not user:
            st.error("Invalid username or password.")
            return

        hashed = user.get("password", "")
        try:
            ok = bcrypt.checkpw((password or "").encode("utf-8"), (hashed or "").encode("utf-8"))
        except Exception:
            ok = False

        if ok:
            st.session_state.authenticated = True
            st.session_state.name = user.get("name", username)
            st.session_state.username = username
            st.rerun()
        else:
            st.error("Invalid username or password.")

# If not authenticated, show login
if not st.session_state.authenticated:
    render_login()
    st.stop()

# =========================
# Utility for Reports
# =========================
def _reports_dir():
    return os.path.join(".", "reports")

def _safe_path(fname: str) -> str:
    fname = os.path.basename(fname)
    full = os.path.realpath(os.path.join(_reports_dir(), fname))
    root = os.path.realpath(_reports_dir())
    if not full.startswith(root):
        raise ValueError("Unsafe path.")
    return full

# =========================
# PAGES
# =========================
def page_home():
    password = st.text_input("Enter your password:", type="password", key="password_input")
    personal_words_raw = st.text_input("Enter personal words (comma-separated):", key="personal_words_input")

    col1, col2, col3 = st.columns(3)
    check_strength_clicked = col1.button("Check Strength")
    check_breach_clicked = col2.button("Check Breach")
    col3.button("Reset", on_click=_reset_form)

    scol1, scol2 = st.columns(2)
    save_txt_clicked = scol1.button("Save Report (TXT)")
    save_pdf_clicked = scol2.button("Save Report (PDF)")

    if check_strength_clicked:
        common_words = load_common_words()
        personal_words = parse_personal_words(personal_words_raw)

        score, label, reasons = evaluate_password(password, personal_words, common_words)
        suggestion = suggest_password(password, personal_words, common_words)

        st.session_state.score = score
        st.session_state.label = label
        st.session_state.reasons = reasons
        st.session_state.suggestion = suggestion

        st.subheader("Strength")
        st.progress(score)
        if label == "Strong":
            st.success(f"Label: {label} — {score}/100")
        elif label == "Good":
            st.info(f"Label: {label} — {score}/100")
        elif label == "Fair":
            st.warning(f"Label: {label} — {score}/100")
        else:
            st.error(f"Label: {label} — {score}/100")

        st.subheader("Reasons")
        if reasons:
            for r in reasons:
                st.write(f"• {r}")
        else:
            st.write("• Looks solid. Nice work!")

        st.subheader("Suggested Password")
        st.info("Format: Two capitalized words + 1 symbol + 3 digits + 1 uppercase tail (e.g., SkyMaple_938Z).")
        st.code(suggestion, language="text")

    if check_breach_clicked:
        st.subheader("Breach Check")
        with st.spinner("Contacting breach service…"):
            count, found, message = check_breach(password)

        st.session_state.breach = {"count": count, "found": found, "message": message}

        if found:
            st.error(f"⚠️ Password appears in known breaches — seen {count} time(s).")
        else:
            if "Could not contact" in message:
                st.warning(message)
            else:
                st.success("✅ Not found in the breach database (k-anonymity range search).")

    if save_txt_clicked:
        if st.session_state.score is None:
            st.warning("Run **Check Strength** first (and optionally **Check Breach**) before saving.")
        else:
            report_dict = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "score": st.session_state.score,
                "label": st.session_state.label,
                "reasons": st.session_state.reasons,
                "suggestion": st.session_state.suggestion or "(not generated)",
                "breach": st.session_state.breach or {"count": 0, "found": False, "message": "Not checked."},
            }
            path = save_report_txt(report_dict, base_dir=".")
            st.success(f"Saved TXT report: {path}")
            with open(path, "rb") as f:
                st.download_button("Download TXT Report", f, file_name=os.path.split(path)[-1], mime="text/plain")

    if save_pdf_clicked:
        if st.session_state.score is None:
            st.warning("Run **Check Strength** first (and optionally **Check Breach**) before saving.")
        else:
            report_dict = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "score": st.session_state.score,
                "label": st.session_state.label,
                "reasons": st.session_state.reasons,
                "suggestion": st.session_state.suggestion or "(not generated)",
                "breach": st.session_state.breach or {"count": 0, "found": False, "message": "Not checked."},
            }
            path = save_report_pdf(report_dict, base_dir=".")
            st.success(f"Saved PDF report: {path}")
            with open(path, "rb") as f:
                st.download_button("Download PDF Report", f, file_name=os.path.split(path)[-1], mime="application/pdf")

def page_reports():
    st.subheader("Saved Reports")

    # ---- TOP-OF-PAGE DELETE CONFIRM PANEL (visible immediately after click) ----
    if st.session_state.get("modal_open") and st.session_state.get("modal_file"):
        with st.container(border=True):
            fname = st.session_state.modal_file
            st.markdown("### Delete report?")
            st.write(f"`{fname}` will be permanently removed. This cannot be undone.")
            colA, colB = st.columns(2)
            with colA:
                if st.button("Cancel", key="confirm_cancel"):
                    st.session_state.modal_open = False
                    st.session_state.modal_file = None
                    st.rerun()
            with colB:
                if st.button("Delete", key="confirm_delete"):
                    try:
                        os.remove(_safe_path(fname))
                        if st.session_state.view_report == fname:
                            st.session_state.view_report = None
                        st.success(f"Deleted {fname}")
                    except Exception as e:
                        st.error(f"Could not delete: {e}")
                    finally:
                        st.session_state.modal_open = False
                        st.session_state.modal_file = None
                    st.rerun()
        st.markdown("---")

    reports_dir = _reports_dir()
    if not os.path.isdir(reports_dir):
        st.info("No reports folder yet. Save a TXT or PDF from the Home page first.")
        return

    files = sorted(
        [f for f in os.listdir(reports_dir) if f.lower().endswith((".txt", ".pdf"))],
        reverse=True,
    )
    if not files:
        st.info("No reports found.")
        return

    for fname in files:
        fpath = _safe_path(fname)

        c1, c2, c3, c4 = st.columns([0.46, 0.18, 0.16, 0.20])
        c1.write(f"**{fname}**")

        with open(fpath, "rb") as f:
            mime = "application/pdf" if fname.lower().endswith(".pdf") else "text/plain"
            c2.download_button("Download", f, file_name=fname, mime=mime, key=f"dl_{fname}")

        with c3:
            st.markdown('<div class="view-btn">', unsafe_allow_html=True)
            if st.button("View", key=f"view_{fname}", type="primary", use_container_width=True):
                st.session_state.view_report = fname
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        # Modal trigger for delete
        if c4.button("Delete", key=f"del_{fname}", use_container_width=True):
            st.session_state.modal_open = True
            st.session_state.modal_file = fname
            st.rerun()

        # Inline preview (below row)
        if st.session_state.view_report == fname:
            st.markdown("")
            with st.container(border=True):
                st.markdown(f"**Preview: `{fname}`**")
                try:
                    if fname.lower().endswith(".txt"):
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as tf:
                            content = tf.read()
                        st.code(content, language="text")
                    else:
                        # --- PDF preview WITHOUT extra sandbox; no links section ---
                        with open(fpath, "rb") as pf:
                            data = pf.read()
                        b64 = base64.b64encode(data).decode("utf-8")

                        html_block = f"""
                        <div style="border:1px solid rgba(148,163,184,.35); border-radius:10px; overflow:hidden">
                          <!-- Try <object> first -->
                          <object data="data:application/pdf;base64,{b64}#zoom=page-width"
                                  type="application/pdf" width="100%" height="820">
                            <!-- Fallback to <embed> -->
                            <embed src="data:application/pdf;base64,{b64}#zoom=page-width"
                                   type="application/pdf" width="100%" height="820" />
                            <!-- Final fallback: simple notice -->
                            <div style="padding:14px; color:#cbd5e1; font-family:system-ui,Segoe UI,Roboto,Arial;">
                              PDF preview isn’t supported in this browser.
                            </div>
                          </object>
                        </div>
                        """
                        # IMPORTANT: no st_html here (avoids sandbox); render inline
                        st.markdown(html_block, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Could not preview file: {e}")
                st.button(
                    "Close Preview",
                    key=f"close_{fname}",
                    on_click=lambda: st.session_state.update(view_report=None)
                )

def page_account():
    st.subheader("Account")
    st.write(f"Signed in as **{st.session_state.name}**  \nUsername: `{st.session_state.username}`")

    st.markdown("---")
    st.markdown("**Change password**")
    new1 = st.text_input("New password", type="password", key="acct_new1")
    new2 = st.text_input("Confirm new password", type="password", key="acct_new2")
    if st.button("Update Password", use_container_width=True):
        if not new1 or not new2:
            st.warning("Please fill in both fields.")
        elif new1 != new2:
            st.error("Passwords do not match.")
        elif len(new1) < 6:
            st.warning("Password should be at least 6 characters.")
        else:
            if update_password(st.session_state.username, new1):
                st.success("Password updated.")
            else:
                st.error("Could not update password.")

    st.markdown("---")
    # Keep account page logout (optional; sidebar has one too)
    if st.button("Logout", use_container_width=True, type="primary"):
        st.session_state.authenticated = False
        st.session_state.name = None
        st.session_state.username = None
        st.session_state.view_report = None
        st.session_state.modal_open = False
        st.session_state.modal_file = None
        st.rerun()

# =========================
# SIDEBAR NAV + ROUTER
# =========================
def _render_sidebar():
    st.markdown(_SIDEBAR_CSS, unsafe_allow_html=True)
    if os.path.exists(LOGO_PATH):
        try:
            st.image(LOGO_PATH, width=110)
        except Exception:
            pass
    st.markdown(
        f'<div class="vg-card"><div class="vg-user">Hi, {st.session_state.name}</div>'
        f'<div class="vg-sub">Signed in to VaultGuard</div></div>',
        unsafe_allow_html=True
    )
    st.markdown('<div class="vg-nav-title">NAVIGATE</div>', unsafe_allow_html=True)
    if _nav_button("Home", "nav_home", "🏠"):
        st.session_state.page = "Home"; st.rerun()
    if _nav_button("Reports", "nav_reports", "📄"):
        st.session_state.page = "Reports"; st.rerun()
    if _nav_button("Account", "nav_account", "👤"):
        st.session_state.page = "Account"; st.rerun()

    # --- Divider + modern Logout button in sidebar ---
    st.markdown("---")
    st.markdown('<div class="vg-logout">', unsafe_allow_html=True)
    if st.button("🚪 Logout", key="sb_logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.name = None
        st.session_state.username = None
        st.session_state.view_report = None
        st.session_state.modal_open = False
        st.session_state.modal_file = None
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

_ensure_page()
with st.sidebar:
    _render_sidebar()

# Route
page = st.session_state.page
if page == "Home":
    page_home()
elif page == "Reports":
    page_reports()
else:
    page_account()

# NOTE: we intentionally do NOT call render_modal() globally anymore.
# The inline confirm panel at the top of the Reports page is clearer and reliable.

# Footer
st.caption("© 2025 VaultGuard | Developed by Mina Astafanous. All checks are local. Breach uses k-anonymity (first 5 hex of SHA-1 only).")




























