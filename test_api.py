import base64
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


def pdf_base64(pdf):
    return base64.b64encode(pdf.getvalue()).decode("ascii")


def decoded_pdf_from_payload(payload):
    return base64.b64decode(payload["pdf_base64"], validate=True)


def encryption_dict(pdf_bytes):
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return reader.trailer["/Encrypt"].get_object()


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

    def test_api_lock_json_base64_returns_json_aes_pdf(self):
        response = self.client.post(
            "/api/v1/lock",
            json={
                "file_base64": pdf_base64(make_pdf()),
                "filename": "sample.pdf",
                "password": "newsecret",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        payload = response.get_json()
        self.assertEqual(payload["filename"], "sample_protected.pdf")
        self.assertTrue(payload["encrypted"])

        pdf_bytes = decoded_pdf_from_payload(payload)
        self.assertEqual(payload["bytes"], len(pdf_bytes))
        output = PdfReader(io.BytesIO(pdf_bytes))
        self.assertTrue(output.is_encrypted)
        encrypt = encryption_dict(pdf_bytes)
        self.assertEqual(encrypt["/V"], 5)
        self.assertEqual(encrypt["/R"], 6)
        self.assertEqual(encrypt["/Length"], 256)
        self.assertEqual(encrypt["/CF"]["/StdCF"]["/CFM"], "/AESV3")
        self.assertNotEqual(output.decrypt("newsecret"), 0)
        self.assertEqual(len(output.pages), 1)

    def test_api_unlock_json_base64_returns_json_unencrypted_pdf(self):
        lock_response = self.client.post(
            "/api/v1/lock",
            json={
                "file_base64": pdf_base64(make_pdf()),
                "filename": "sample.pdf",
                "password": "newsecret",
            },
        )
        locked_pdf = decoded_pdf_from_payload(lock_response.get_json())

        response = self.client.post(
            "/api/v1/unlock",
            json={
                "file_base64": base64.b64encode(locked_pdf).decode("ascii"),
                "filename": "sample.pdf",
                "password": "newsecret",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        payload = response.get_json()
        self.assertEqual(payload["filename"], "sample_unlocked.pdf")
        self.assertFalse(payload["encrypted"])

        pdf_bytes = decoded_pdf_from_payload(payload)
        self.assertEqual(payload["bytes"], len(pdf_bytes))
        output = PdfReader(io.BytesIO(pdf_bytes))
        self.assertFalse(output.is_encrypted)
        self.assertEqual(len(output.pages), 1)

    def test_api_multipart_lock_can_return_base64_json(self):
        response = post_api_pdf(
            self.client,
            "/api/v1/lock?output=base64",
            make_pdf(),
            password="newsecret",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")
        payload = response.get_json()
        self.assertEqual(payload["filename"], "sample_protected.pdf")
        self.assertTrue(payload["encrypted"])
        output = PdfReader(io.BytesIO(decoded_pdf_from_payload(payload)))
        self.assertTrue(output.is_encrypted)
        self.assertNotEqual(output.decrypt("newsecret"), 0)

    def test_api_json_lock_can_return_binary_pdf(self):
        response = self.client.post(
            "/api/v1/lock?output=binary",
            json={
                "file_base64": pdf_base64(make_pdf()),
                "filename": "sample.pdf",
                "password": "newsecret",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/pdf")
        self.assertIn("sample_protected.pdf", response.headers["Content-Disposition"])
        output = PdfReader(io.BytesIO(response.data))
        self.assertTrue(output.is_encrypted)
        self.assertNotEqual(output.decrypt("newsecret"), 0)

    def test_api_json_unlock_wrong_password_returns_json_error(self):
        locked_pdf = make_pdf(encrypted=True, password="secret")

        response = self.client.post(
            "/api/v1/unlock",
            json={
                "file_base64": pdf_base64(locked_pdf),
                "password": "wrong",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["code"], "wrong_password")

    def test_api_json_missing_file_returns_json_error(self):
        response = self.client.post("/api/v1/unlock", json={"password": "secret"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["code"], "no_file")

    def test_api_json_bad_base64_returns_json_error(self):
        response = self.client.post(
            "/api/v1/unlock",
            json={"file_base64": "not valid base64", "password": "secret"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["code"], "invalid_pdf")

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
