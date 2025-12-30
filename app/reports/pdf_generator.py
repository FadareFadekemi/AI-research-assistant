from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def generate_pdf(sections: dict, output_path: str):
    doc = SimpleDocTemplate(output_path)
    styles = getSampleStyleSheet()
    story = []

    for title, content in sections.items():
        story.append(Paragraph(f"<b>{title.upper()}</b>", styles["Heading2"]))
        story.append(Paragraph(content, styles["BodyText"]))

    doc.build(story)
