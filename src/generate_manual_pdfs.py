import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MANUALS_DIR = os.path.join(REPO_ROOT, "data", "manuals")

def build_pdf_from_txt(txt_path: str, pdf_path: str):
    with open(txt_path, "r", encoding="utf-8") as f:
        content = f.read()

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1e1b4b"),
        spaceAfter=6
    )
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12
    )
    section_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#4338ca"),
        spaceBefore=10,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'SectionBody',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=6
    )
    code_style = ParagraphStyle(
        'ErrorCode',
        parent=styles['Normal'],
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#dc2626"),
        fontName="Helvetica-Bold",
        spaceAfter=2
    )

    story = []

    mach_match = re.search(r"^MACHINE:\s*(.+)$", content, re.MULTILINE)
    machine_name = mach_match.group(1).strip() if mach_match else "Factory Equipment"

    model_match = re.search(r"^MODEL:\s*(.+)$", content, re.MULTILINE)
    model_name = model_match.group(1).strip() if model_match else ""

    story.append(Paragraph(f"{machine_name}", title_style))
    story.append(Paragraph(f"Model: {model_name} • Industrial Technical & Troubleshooting Manual", meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4f46e5"), spaceAfter=14))

    sections = re.split(r"(?=^SECTION:)", content, flags=re.MULTILINE)
    current_page = None

    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        
        page_match = re.search(r"PAGE:\s*(\d+)", sec)
        if page_match:
            p_num = int(page_match.group(1))
            if current_page is not None and p_num > current_page:
                story.append(PageBreak())
            current_page = p_num

        lines = sec.split("\n")
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            if line_str.startswith("SECTION:"):
                sec_title = line_str.replace("SECTION:", "").strip()
                story.append(Paragraph(f"<b>{sec_title}</b>", section_style))
            elif line_str.startswith("ERROR CODE:"):
                story.append(Paragraph(f"⚠️ {line_str}", code_style))
            elif line_str.startswith("PAGE:"):
                continue
            elif line_str.startswith("MEANING:") or line_str.startswith("SYMPTOM:"):
                story.append(Paragraph(f"<b>{line_str[:8]}</b> {line_str[8:].strip()}", body_style))
            elif line_str.startswith("CAUSES:") or line_str.startswith("STEPS:"):
                story.append(Paragraph(f"<b>{line_str}</b>", body_style))
            else:
                escaped = line_str.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(f"&nbsp;&nbsp;{escaped}", body_style))

        story.append(Spacer(1, 8))

    doc.build(story)
    print(f"Generated PDF: {pdf_path}")

def generate_all_manual_pdfs():
    os.makedirs(MANUALS_DIR, exist_ok=True)
    mapping = [
        ("cncmx7.txt", "cncmx7.pdf"),
        ("conveyorcb4400.txt", "conveyorcb4400.pdf"),
        ("presshp2200.txt", "presshp2200.pdf")
    ]
    for txt_name, pdf_name in mapping:
        txt_path = os.path.join(MANUALS_DIR, txt_name)
        pdf_path = os.path.join(MANUALS_DIR, pdf_name)
        if os.path.exists(txt_path):
            build_pdf_from_txt(txt_path, pdf_path)

if __name__ == "__main__":
    generate_all_manual_pdfs()
