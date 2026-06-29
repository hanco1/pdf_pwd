import io
import unittest

from pypdf import PdfReader, PdfWriter

from app import app


def make_pdf(encrypted=False, password="secret123"):
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    if encrypted:
        writer.encrypt(password)
    data = io.BytesIO()
    writer.write(data)
    data.seek(0)
    return data


def post_pdf(client, pdf, filename="sample.pdf", password="", mode=None):
    data = {
        "pdf": (pdf, filename),
        "password": password,
    }
    if mode is not None:
        data["mode"] = mode
    return client.post("/process", data=data, content_type="multipart/form-data")


class ProcessModeTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_process_unlock_default_removes_password(self):
        response = post_pdf(self.client, make_pdf(encrypted=True), password="secret123")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertIn("sample_unlocked.pdf", response.headers["Content-Disposition"])

        output = PdfReader(io.BytesIO(response.data))
        self.assertFalse(output.is_encrypted)
        self.assertEqual(len(output.pages), 1)

    def test_process_unknown_mode_uses_unlock(self):
        response = post_pdf(
            self.client,
            make_pdf(encrypted=True),
            mode="unexpected",
            password="secret123",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("sample_unlocked.pdf", response.headers["Content-Disposition"])

        output = PdfReader(io.BytesIO(response.data))
        self.assertFalse(output.is_encrypted)

    def test_process_lock_adds_password(self):
        response = post_pdf(self.client, make_pdf(), mode="lock", password="newpass")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertIn("sample_protected.pdf", response.headers["Content-Disposition"])

        output = PdfReader(io.BytesIO(response.data))
        self.assertTrue(output.is_encrypted)
        self.assertNotEqual(output.decrypt("newpass"), 0)
        self.assertEqual(len(output.pages), 1)

    def test_process_lock_allows_pdf_encrypted_with_empty_password(self):
        response = post_pdf(
            self.client,
            make_pdf(encrypted=True, password=""),
            mode="lock",
            password="newpass",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("sample_protected.pdf", response.headers["Content-Disposition"])

        output = PdfReader(io.BytesIO(response.data))
        self.assertTrue(output.is_encrypted)
        self.assertNotEqual(output.decrypt("newpass"), 0)

    def test_process_lock_requires_password(self):
        response = post_pdf(self.client, make_pdf(), mode="lock", password="")

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Enter a password to protect the PDF.", response.data)

    def test_process_lock_rejects_encrypted_pdf_that_needs_password(self):
        response = post_pdf(
            self.client,
            make_pdf(encrypted=True),
            mode="lock",
            password="newpass",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"This PDF is already password-protected.", response.data)


if __name__ == "__main__":
    unittest.main()
