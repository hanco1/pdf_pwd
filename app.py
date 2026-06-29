import io
import os

from flask import Flask, render_template_string, request, send_file
from pypdf import PdfReader, PdfWriter
from pypdf.errors import EmptyFileError, PdfReadError, PdfStreamError
from werkzeug.exceptions import RequestEntityTooLarge
from werkzeug.utils import secure_filename

MAX_MB = int(os.environ.get("MAX_MB", "4"))

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024

TEMPLATE = """\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>PDF Unlocker</title>
    <style>
      :root {
        --bg-1: #f8f1e8;
        --bg-2: #ead4c1;
        --bg-3: #d8e6ec;
        --ink: #1e1b18;
        --muted: #5f554c;
        --accent: #1f7a8c;
        --accent-2: #c8653a;
        --card: #fff7ef;
        --stroke: rgba(31, 122, 140, 0.2);
        --shadow: rgba(31, 60, 75, 0.18);
        --font-display: "Constantia", "Palatino Linotype", "Book Antiqua", serif;
        --font-body: "Candara", "Trebuchet MS", "Geneva", sans-serif;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        min-height: 100vh;
        font-family: var(--font-body);
        color: var(--ink);
        background: radial-gradient(circle at 15% 20%, rgba(200, 101, 58, 0.15), transparent 45%),
          radial-gradient(circle at 85% 15%, rgba(31, 122, 140, 0.18), transparent 50%),
          linear-gradient(135deg, var(--bg-1), var(--bg-2) 45%, var(--bg-3));
      }

      .page {
        max-width: 980px;
        margin: 0 auto;
        padding: 40px 24px 64px;
        position: relative;
      }

      .page::before,
      .page::after {
        content: "";
        position: absolute;
        border-radius: 999px;
        filter: blur(0);
        opacity: 0.6;
        z-index: 0;
        animation: float 18s ease-in-out infinite;
      }

      .page::before {
        width: 260px;
        height: 260px;
        background: rgba(31, 122, 140, 0.18);
        top: 20px;
        right: 40px;
      }

      .page::after {
        width: 200px;
        height: 200px;
        background: rgba(200, 101, 58, 0.18);
        bottom: 40px;
        left: 20px;
        animation-delay: -6s;
      }

      header {
        position: relative;
        z-index: 1;
        display: grid;
        gap: 12px;
        margin-bottom: 24px;
        animation: rise 0.7s ease-out both;
      }

      .badge {
        align-self: flex-start;
        background: rgba(31, 122, 140, 0.15);
        color: var(--accent);
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-size: 12px;
        padding: 6px 12px;
        border-radius: 999px;
      }

      h1 {
        margin: 0;
        font-family: var(--font-display);
        font-size: clamp(32px, 6vw, 56px);
        letter-spacing: 0.02em;
      }

      header p {
        margin: 0;
        color: var(--muted);
        font-size: 17px;
        max-width: 680px;
      }

      .panel {
        position: relative;
        z-index: 1;
        background: var(--card);
        border-radius: 28px;
        padding: 28px;
        box-shadow: 0 24px 60px var(--shadow);
        border: 1px solid rgba(255, 255, 255, 0.6);
        display: grid;
        gap: 24px;
        animation: rise 0.9s ease-out both;
        animation-delay: 0.1s;
      }

      .panel-grid {
        display: grid;
        gap: 24px;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      }

      .step-list {
        margin: 0;
        padding-left: 18px;
        color: var(--muted);
        line-height: 1.6;
      }

      .form-card {
        background: white;
        border-radius: 20px;
        padding: 20px;
        border: 1px solid rgba(31, 122, 140, 0.18);
        display: grid;
        gap: 16px;
      }

      label {
        font-weight: 700;
        font-size: 14px;
        letter-spacing: 0.02em;
        color: var(--muted);
      }

      .file-row {
        display: flex;
        align-items: center;
        gap: 12px;
        flex-wrap: wrap;
      }

      input[type="file"] {
        position: absolute;
        left: -9999px;
      }

      .file-button {
        border: 2px dashed var(--accent);
        padding: 12px 18px;
        border-radius: 14px;
        cursor: pointer;
        font-weight: 700;
        color: var(--accent);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
      }

      .file-button:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 20px rgba(31, 122, 140, 0.18);
      }

      .file-name {
        font-size: 14px;
        color: var(--muted);
      }

      input[type="password"] {
        width: 100%;
        padding: 12px 14px;
        border-radius: 12px;
        border: 1px solid rgba(31, 122, 140, 0.3);
        font-family: var(--font-body);
        font-size: 15px;
      }

      .actions {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
      }

      .btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 12px 20px;
        border-radius: 999px;
        border: none;
        font-weight: 700;
        text-decoration: none;
        cursor: pointer;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        font-family: var(--font-body);
      }

      .btn.primary {
        background: var(--accent);
        color: white;
        box-shadow: 0 14px 26px rgba(31, 122, 140, 0.28);
      }

      .btn.secondary {
        background: rgba(31, 122, 140, 0.1);
        color: var(--accent);
      }

      .btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
        box-shadow: none;
      }

      .btn:hover:not(:disabled) {
        transform: translateY(-1px);
      }

      .status {
        border-radius: 16px;
        padding: 16px;
        border: 1px solid transparent;
        display: grid;
        gap: 8px;
      }

      .status.success {
        background: rgba(31, 122, 140, 0.12);
        border-color: rgba(31, 122, 140, 0.3);
      }

      .status.error {
        background: rgba(200, 101, 58, 0.16);
        border-color: rgba(200, 101, 58, 0.4);
      }

      .status.info {
        background: rgba(52, 67, 88, 0.12);
        border-color: rgba(52, 67, 88, 0.3);
      }

      .status-title {
        font-weight: 800;
        letter-spacing: 0.02em;
      }

      .note {
        font-size: 13px;
        color: var(--muted);
        margin: 0;
      }

      footer {
        margin-top: 20px;
        color: var(--muted);
        font-size: 13px;
      }

      .loading .btn.primary {
        opacity: 0.7;
      }

      .loading .btn.primary::after {
        content: "  ";
      }

      .loading .btn.primary span::after {
        content: " (processing...)";
        font-weight: 600;
      }

      @keyframes rise {
        from {
          opacity: 0;
          transform: translateY(18px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      @keyframes float {
        0%,
        100% {
          transform: translateY(0) translateX(0);
        }
        50% {
          transform: translateY(-14px) translateX(6px);
        }
      }

      @media (max-width: 600px) {
        .panel {
          padding: 20px;
        }

        .file-row {
          flex-direction: column;
          align-items: flex-start;
        }
      }

      @media (prefers-reduced-motion: reduce) {
        * {
          animation: none !important;
          transition: none !important;
        }
      }
    </style>
  </head>
  <body>
    <div class="page">
      <header>
        <div class="badge">Local or hosted</div>
        <h1>PDF Unlocker</h1>
        <p>Upload a password-protected PDF, unlock it with the known password, and download an editable copy.</p>
      </header>

      <section class="panel">
        <div class="panel-grid">
          <div>
            <h2>How it works</h2>
            <ol class="step-list">
              <li>Select your PDF.</li>
              <li>Enter the password if one is required.</li>
              <li>Press process and grab the unlocked file.</li>
            </ol>
          </div>
          <div class="form-card">
            <form id="unlock-form" method="post" action="/process" enctype="multipart/form-data">
              <div>
                <label for="pdf">PDF file</label>
                <div class="file-row">
                  <input id="pdf" name="pdf" type="file" accept="application/pdf" required />
                  <label class="file-button" for="pdf">Upload PDF</label>
                  <span class="file-name" id="file-name">No file selected</span>
                </div>
              </div>
              <div>
                <label for="password">Password (if required)</label>
                <input id="password" name="password" type="password" placeholder="Enter PDF password" />
              </div>
              <div class="actions">
                <button class="btn primary" id="process-btn" type="submit" disabled><span>Process</span></button>
                <button class="btn secondary" type="reset" id="reset-btn">Clear</button>
              </div>
              <p class="note">Hosted uploads are limited to {{ max_mb }} MB. Run it locally for bigger files. Unlock only PDFs you own or have rights to edit.</p>
            </form>
          </div>
        </div>

        {% if message %}
        <div class="status {{ status }}">
          <div class="status-title">{{ status_title }}</div>
          <div>{{ message }}</div>
        </div>
        {% endif %}
      </section>

      <footer>Built with pypdf, runs entirely on your computer.</footer>
    </div>
    <script>
      const fileInput = document.getElementById("pdf");
      const fileName = document.getElementById("file-name");
      const processButton = document.getElementById("process-btn");
      const resetButton = document.getElementById("reset-btn");
      const form = document.getElementById("unlock-form");

      function updateState() {
        if (fileInput.files.length > 0) {
          fileName.textContent = fileInput.files[0].name;
          processButton.disabled = false;
        } else {
          fileName.textContent = "No file selected";
          processButton.disabled = true;
        }
      }

      fileInput.addEventListener("change", updateState);
      resetButton.addEventListener("click", () => {
        setTimeout(updateState, 0);
      });
      form.addEventListener("submit", () => {
        form.classList.add("loading");
        processButton.disabled = true;
        setTimeout(() => {
          form.classList.remove("loading");
          updateState();
        }, 2500);
      });
      window.addEventListener("pageshow", () => {
        form.classList.remove("loading");
        updateState();
      });
      updateState();
    </script>
  </body>
</html>
"""


def render_page(status=None, message=None):
    status_title = None
    if status == "success":
        status_title = "Unlocked"
    elif status == "error":
        status_title = "Could not unlock"
    elif status == "info":
        status_title = "Note"
    return render_template_string(
        TEMPLATE,
        status=status,
        status_title=status_title,
        message=message,
        max_mb=MAX_MB,
    )


def unlocked_pdf_buffer(reader):
    writer = PdfWriter()
    try:
        writer.append(reader)
    except Exception:
        app.logger.warning("Falling back to page-by-page PDF copy.", exc_info=True)
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output


@app.route("/", methods=["GET"])
def index():
    return render_page()


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(error):
    return (
        render_page(
            "error",
            f"That PDF is larger than the {MAX_MB} MB limit for the hosted version. Run it locally for bigger files.",
        ),
        413,
    )


@app.route("/process", methods=["POST"])
def process():
    upload = request.files.get("pdf")
    if not upload or upload.filename == "":
        return render_page("error", "Please choose a PDF file to unlock."), 400

    password = request.form.get("password", "")
    original_name = secure_filename(upload.filename)
    base_name = os.path.splitext(original_name)[0] if original_name else ""
    base_name = secure_filename(base_name) or "document"

    try:
        data = upload.read()
        reader = PdfReader(io.BytesIO(data))
    except (EmptyFileError, PdfReadError, PdfStreamError):
        return render_page("error", "That file does not appear to be a valid PDF."), 400
    except Exception:
        return render_page("error", "That file does not appear to be a valid PDF."), 400

    try:
        if reader.is_encrypted:
            result = reader.decrypt(password or "")
            if result == 0:
                return render_page("error", "That password did not unlock this PDF."), 400

        output = unlocked_pdf_buffer(reader)
        return send_file(
            output,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{base_name}_unlocked.pdf",
        )
    except PdfReadError:
        return render_page("error", "That file does not appear to be a valid PDF."), 400
    except Exception:
        app.logger.exception("Something went wrong while unlocking the PDF.")
        return render_page("error", "Something went wrong while unlocking the PDF."), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))
