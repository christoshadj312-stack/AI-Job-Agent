import unittest

import pymupdf

from cv_parser import (
    CVParserError,
    extract_text_from_pdf_bytes,
    render_pdf_pages_as_png,
)


class CVParserBytesTests(unittest.TestCase):
    def test_extracts_text_from_uploaded_pdf_bytes(self):
        document = pymupdf.open()
        page = document.new_page()
        page.insert_text(
            (72, 72),
            "Python Machine Learning",
        )
        pdf_bytes = document.tobytes()
        document.close()

        text = extract_text_from_pdf_bytes(
            pdf_bytes
        )

        self.assertIn("Python", text)

    def test_rejects_empty_upload(self):
        with self.assertRaises(CVParserError):
            extract_text_from_pdf_bytes(b"")

    def test_renders_scanned_pdf_page_as_png(self):
        document = pymupdf.open()
        document.new_page()
        pdf_bytes = document.tobytes()
        document.close()

        page_images = render_pdf_pages_as_png(
            pdf_bytes
        )

        self.assertEqual(len(page_images), 1)
        self.assertTrue(
            page_images[0].startswith(b"\x89PNG")
        )


if __name__ == "__main__":
    unittest.main()
