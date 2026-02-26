import os
from datetime import datetime
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

APP_NAME = "VaultGuard"
REPORT_DIR = "reports"

def _ensure_dir(base_dir: str):
    out_dir = os.path.join(base_dir, REPORT_DIR)
    os.makedirs(out_dir, exist_ok=True)
    return out_dir

def _label_line(k, v):
    return f"{k}: {v}"

def save_report_txt(report: dict, base_dir: str = ".") -> str:
    out_dir = _ensure_dir(base_dir)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{APP_NAME}_Report_{ts}.txt"
    path = os.path.join(out_dir, fname)

    lines = []
    lines.append(f"{APP_NAME} – Password Advisor (TXT Report)")
    lines.append("=" * 48)
    lines.append(_label_line("Generated", report.get("timestamp", "")))
    lines.append(_label_line("Score", report.get("score", "")))
    lines.append(_label_line("Label", report.get("label", "")))
    lines.append("")
    lines.append("Reasons:")
    reasons = report.get("reasons", []) or []
    if reasons:
        for r in reasons:
            lines.append(f"  • {r}")
    else:
        lines.append("  • Looks solid.")
    lines.append("")
    lines.append(_label_line("Suggestion", report.get("suggestion", "")))
    lines.append("")
    breach = report.get("breach", {}) or {}
    lines.append("Breach Check:")
    if breach.get("found"):
        lines.append(f"  ⚠ Found {breach.get('count', 0)} times in known breaches.")
    else:
        msg = breach.get("message", "Not found.")
        lines.append(f"  {msg}")
    lines.append("")
    lines.append("Footer: All checks are local. Breach uses k-anonymity (first 5 hex of SHA-1 only).")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path

def save_report_pdf(report: dict, base_dir: str = ".") -> str:
    out_dir = _ensure_dir(base_dir)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"{APP_NAME}_Report_{ts}.pdf"
    path = os.path.join(out_dir, fname)

    doc = SimpleDocTemplate(path, pagesize=LETTER, title=f"{APP_NAME} – Password Advisor")
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    h_style = styles["Heading2"]
    body = styles["BodyText"]

    story = []
    story.append(Paragraph(f"{APP_NAME} – Password Advisor", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Generated: {report.get('timestamp','')}", body))
    story.append(Spacer(1, 8))

    story.append(Paragraph(f"Score: {report.get('score','')} / 100", h_style))
    story.append(Paragraph(f"Label: {report.get('label','')}", body))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Reasons:", h_style))
    reasons = report.get("reasons", []) or []
    if reasons:
        for r in reasons:
            story.append(Paragraph(f"• {r}", body))
    else:
        story.append(Paragraph("• Looks solid.", body))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Suggested Password:", h_style))
    story.append(Paragraph(report.get("suggestion", "(not generated)"), body))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Breach Check:", h_style))
    breach = report.get("breach", {}) or {}
    if breach.get("found"):
        story.append(Paragraph(f"⚠ Found {breach.get('count',0)} times in known breaches.", body))
    else:
        msg = breach.get("message", "Not found.")
        story.append(Paragraph(msg, body))
    story.append(Spacer(1, 12))

    footer = "All checks are local. Breach uses k-anonymity (first 5 hex of SHA-1 only)."
    story.append(Paragraph(footer, body))

    doc.build(story)
    return path


