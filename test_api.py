import io
import unittest

from pypdf import PdfReader, PdfWriter

from app import app


def make_pdf(encrypted=False, password="secret"):
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    if encrypted:
        writer.encrypt(password)
    data = io.BytesIO()
    writer.write(data)
    data.seek(0)
    return data


def post_api_pdf(client, path, pdf, filename="sample.pdf", password="", field="file"):
    return client.post(
        path,
        data={
            field: (pdf, filename),
            "password": password,
        },
        content_type="multipart/form-data",
    )


class ApiTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_api_unlock_encrypted_pdf_with_correct_password(self):
        response = post_api_pdf(
            self.client,
            "/api/v1/unlock",
            make_pdf(encrypted=True),
            password="secret",
            field="file",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertIn("sample_unlocked.pdf", response.headers["Content-Disposition"])

        output = PdfReader(io.BytesIO(response.data))
        self.assertFalse(output.is_encrypted)
        self.assertEqual(len(output.pages), 1)

    def test_api_unlock_with_wrong_password_returns_json_error(self):
        response = post_api_pdf(
            self.client,
            "/api/v1/unlock",
            make_pdf(encrypted=True),
            password="wrong",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["code"], "wrong_password")

    def test_api_lock_plain_pdf_adds_password(self):
        response = post_api_pdf(
            self.client,
            "/api/v1/lock",
            make_pdf(),
            password="newsecret",
            field="pdf",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertIn("sample_protected.pdf", response.headers["Content-Disposition"])

        output = PdfReader(io.BytesIO(response.data))
        self.assertTrue(output.is_encrypted)
        self.assertNotEqual(output.decrypt("newsecret"), 0)
        self.assertEqual(len(output.pages), 1)

    def test_api_lock_with_empty_password_returns_json_error(self):
        response = post_api_pdf(self.client, "/api/v1/lock", make_pdf(), password="")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["code"], "password_required")

    def test_api_lock_already_encrypted_pdf_returns_json_error(self):
        response = post_api_pdf(
            self.client,
            "/api/v1/lock",
            make_pdf(encrypted=True),
            password="newsecret",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["code"], "already_encrypted")

    def test_api_missing_file_returns_json_error(self):
        response = self.client.post(
            "/api/v1/unlock",
            data={"password": "secret"},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["code"], "no_file")

    def test_api_index_documents_endpoint_names(self):
        response = self.client.get("/api")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("/api/v1/unlock", payload["endpoints"])
        self.assertIn("/api/v1/lock", payload["endpoints"])

    def test_api_options_preflight_includes_cors_headers(self):
        response = self.client.options("/api/v1/lock")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], "*")


if __name__ == "__main__":
    unittest.main()
