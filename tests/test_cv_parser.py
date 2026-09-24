import unittest

import pymupdf

from cv_parser import (
    CVParserError,
    extract_text_from_pdf_bytes,
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


if __name__ == "__main__":
    unittest.main()
