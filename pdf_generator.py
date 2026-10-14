"""Create a polished, exactly-five-page PDF storybook."""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph


def _validate_image(path: Path) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Illustration not found: {path}")
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            if image.width < 1 or image.height < 1:
                raise ValueError("Image dimensions are invalid.")
    except Exception as exc:
        raise ValueError(f"Invalid illustration: {path}") from exc


def create_storybook_pdf(
    story_plan,
    image_paths: list[str | Path],
    output_path: str | Path = "outputs/storybook.pdf",
) -> Path:
    """Write each of the five story pages with its illustration and text."""
    if len(story_plan.pages) != 5:
        raise ValueError("The story must contain exactly five pages.")
    if [page.page_number for page in story_plan.pages] != [1, 2, 3, 4, 5]:
        raise ValueError("Story pages must be numbered from 1 to 5 in order.")
    if len(image_paths) != 5:
        raise ValueError("Exactly five page illustrations are required.")

    paths = [Path(path) for path in image_paths]
    for path in paths:
        _validate_image(path)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    pdf = canvas.Canvas(str(output_path), pagesize=A4, pageCompression=1)
    pdf.setTitle(str(story_plan.title))
    pdf.setAuthor("Storybook Agent")
    page_width, page_height = A4

    title_style = ParagraphStyle(
        "BookTitle",
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=27,
        alignment=1,
        textColor=HexColor("#263b2f"),
        spaceAfter=0,
    )
    running_title_style = ParagraphStyle(
        "RunningTitle",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        alignment=1,
        textColor=HexColor("#53665a"),
    )
    page_label_style = ParagraphStyle(
        "PageLabel",
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        alignment=0,
        textColor=HexColor("#263b2f"),
    )

    background = HexColor("#fff8e8")
    ink = HexColor("#333333")
    left_margin = 48
    text_width = page_width - 2 * left_margin
    image_width = 330
    image_height = 390
    image_x = (page_width - image_width) / 2

    for index, page in enumerate(story_plan.pages):
        pdf.setFillColor(background)
        pdf.rect(0, 0, page_width, page_height, fill=1, stroke=0)

        safe_title = escape(str(story_plan.title))
        if index == 0:
            title = Paragraph(safe_title, title_style)
            _, title_height = title.wrap(page_width - 80, 58)
            title.drawOn(pdf, 40, page_height - 36 - title_height)
            image_top = page_height - 36 - title_height - 23
        else:
            title = Paragraph(safe_title, running_title_style)
            _, title_height = title.wrap(text_width, 20)
            title.drawOn(pdf, left_margin, page_height - 28 - title_height)
            image_top = page_height - 48 - title_height

        image_y = image_top - image_height
        pdf.drawImage(
            ImageReader(str(paths[index])),
            image_x,
            image_y,
            width=image_width,
            height=image_height,
            preserveAspectRatio=True,
            anchor="c",
            mask="auto",
        )

        label = Paragraph(f"Page {page.page_number}", page_label_style)
        _, label_height = label.wrap(text_width, 22)
        label_y = image_y - 25 - label_height
        label.drawOn(pdf, left_margin, label_y)

        # Escape story text so symbols like '&' or '<' are printed as text,
        # not interpreted as ReportLab paragraph markup.
        narrative = escape(str(page.narrative_text)).replace("\n", "<br/>")
        body_top = label_y - 8
        available_height = body_top - 52
        fitted_paragraph = None
        fitted_height = None
        for font_size, leading in ((12, 16), (11, 14.5), (10, 13), (9, 11.5)):
            body_style = ParagraphStyle(
                f"StoryBody{index}_{font_size}",
                fontName="Helvetica",
                fontSize=font_size,
                leading=leading,
                textColor=ink,
                alignment=0,
                splitLongWords=1,
            )
            paragraph = Paragraph(narrative, body_style)
            _, paragraph_height = paragraph.wrap(text_width, available_height)
            if paragraph_height <= available_height:
                fitted_paragraph = paragraph
                fitted_height = paragraph_height
                break

        if fitted_paragraph is None or fitted_height is None:
            raise ValueError(
                f"Narrative text on page {page.page_number} is too long for the PDF layout. "
                "Shorten the page's narrative_text and rerun the pipeline."
            )

        fitted_paragraph.drawOn(pdf, left_margin, body_top - fitted_height)

        pdf.setStrokeColor(HexColor("#d9d2c2"))
        pdf.setLineWidth(0.6)
        pdf.line(left_margin, 38, page_width - left_margin, 38)
        pdf.setFillColor(HexColor("#6b705c"))
        pdf.setFont("Helvetica", 9)
        pdf.drawCentredString(page_width / 2, 22, f"{index + 1} / 5")
        pdf.showPage()

    pdf.save()
    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError("PDF generation did not produce a valid output file.")
    return output_path
