# 🛡️ VaultGuard -- Password Advisor

**VaultGuard** is a modern and secure password advisor built with
**Python** and **Streamlit**.\
It helps users test the **strength**, **security**, and **exposure
risk** of their passwords --- all locally on their machine.

Developed by **Mina Astafanous (2025)**, this app combines cryptographic
security concepts, local authentication, and interactive password
analytics --- all wrapped in a modern dark-themed dashboard.

------------------------------------------------------------------------

## 🚀 What We Built

### 1. **Password Strength & Analysis**

-   Evaluates password strength (0--100).
-   Explains why a password is weak or strong.
-   Checks against **common words** and **personal words**.
-   Suggests stronger passwords like `SkyMaple_938Z`.

### 2. **Breach Check (Privacy-Safe)**

-   Uses **k-anonymity hashing (SHA-1 prefix)** to check if a password
    appears in known data breaches.
-   Never sends your full password to the web.

### 3. **Report Generation & Management**

-   Save results as `.txt` or `.pdf`.
-   View, Download, or Delete reports directly inside the app.
-   Inline **PDF viewer** and confirmation dialog for delete.

### 4. **User Authentication System**

-   Local **login / signup / forgot password**.
-   Credentials stored securely in `assets/creds.yaml` (bcrypt-hashed).
-   Change password any time from the Account page.

### 5. **Modern UI/UX**

-   Sleek dark theme with sidebar navigation.
-   Pages:
    -   🏠 Home -- Password tools
    -   📄 Reports -- Manage reports
    -   👤 Account -- Update password / logout
-   Animated gradient buttons and layout transitions.

### 6. **Everything Runs Locally**

-   No cloud login or tracking.
-   All logic runs safely on your machine.

------------------------------------------------------------------------

## 🧩 Tools & Libraries

  Category      Tools / Libraries
  ------------- --------------------------------------
  Framework     Streamlit
  Language      Python 3.13
  Security      bcrypt, PyYAML
  PDF Reports   reportlab
  UI            Custom CSS + Streamlit Components
  API           requests (k-anonymity breach lookup)
  Images        Pillow

------------------------------------------------------------------------

## 🗂️ Folder Structure

    VaultGuard/
    ├─ app.py
    ├─ core/
    │  ├─ auth.py
    │  ├─ breach.py
    │  ├─ evaluator.py
    │  ├─ report.py
    │  ├─ suggester.py
    ├─ assets/
    │  ├─ vaultguard_logo.png
    │  ├─ common_words.txt
    │  └─ creds.yaml
    ├─ reports/
    │  └─ (saved reports)
    └─ README.md

------------------------------------------------------------------------

## ⚙️ Installation

### 1️⃣ Open the project folder in VS Code

    File → Open Folder → SafePass or VaultGuard folder

### 2️⃣ Open Terminal and activate environment

``` bash
cd "C:\Users\minaa\OneDrive\Desktop\SafePass"
.venv\Scripts\activate
```

### 3️⃣ Install dependencies

``` bash
pip install -r requirements.txt
```

### 4️⃣ Run the app

``` bash
streamlit run app.py
```

Then open your browser at **http://localhost:8501**

------------------------------------------------------------------------

## 🔐 Authentication

-   All credentials stored in `assets/creds.yaml`
-   Passwords hashed with bcrypt
-   You can **Sign Up**, **Sign In**, and **Reset Password** directly
    inside the app.

------------------------------------------------------------------------

## 🧾 How VaultGuard Is Different

  Regular Password Checkers   VaultGuard
  --------------------------- ----------------------------------
  Sends data online           100% Local
  No account system           Secure local login
  Plain text results          PDF/TXT report system
  Basic design                Modern dark UI
  Unsafe breach checks        Privacy-safe k-anonymity hashing

------------------------------------------------------------------------

## 💡 Educational Value

This project covers: - Streamlit interface design - Authentication
systems - Secure password hashing - File operations and PDF generation -
Local storage management - UI/UX development in Python

------------------------------------------------------------------------

## 👨‍💻 Credits

**Developed by:** Mina Astafanous\
**Year:** 2025\
**Institution:** California State University, Fullerton\
**Project Type:** Cybersecurity & Software Engineering Portfolio Project

------------------------------------------------------------------------

## 🧾 License

This project was created for **portfolio and educational purposes**.\
It is not intended for commercial use or distribution.

© 2025 **VaultGuard** --- Developed by *Mina Astafanous*.