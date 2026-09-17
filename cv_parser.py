from pathlib import Path

import pymupdf


class CVParserError(Exception):
    """Raised when a CV PDF cannot be processed correctly."""


def extract_text_from_pdf(pdf_path):
    path = Path(pdf_path)

    if not path.exists():
        raise CVParserError(f"CV file not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise CVParserError("The CV file must be a PDF.")

    try:
        document = pymupdf.open(path)
    except Exception as error:
        raise CVParserError("The PDF file could not be opened.") from error

    try:
        if document.page_count == 0:
            raise CVParserError("The PDF contains no pages.")

        text_parts = []

        for page in document:
            page_text = page.get_text("text")

            if page_text:
                cleaned_text = page_text.strip()

                if cleaned_text:
                    text_parts.append(cleaned_text)

        extracted_text = "\n\n".join(text_parts).strip()

        if not extracted_text:
            raise CVParserError(
                "No readable text was found in the PDF. "
                "The CV may be a scanned or image-only PDF."
            )

        return extracted_text

    finally:
        document.close()