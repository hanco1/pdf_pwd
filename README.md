# PDF Unlocker (Local)

Local web app that removes a known password from a PDF so you can edit it.
Built with Flask and pypdf. Files never leave your machine.

## Problem solved
- Many PDFs are protected with an owner password that blocks editing.
- This tool unlocks a PDF using the password you already know.
- No uploads to third party services.

## Features
- Local only processing
- Upload and process UI
- Download unlocked PDF
- Works with encrypted and unencrypted PDFs

## Screenshot (Safari on Windows)
![UI on Safari Windows](screenshots/ui-safari-windows.png)

Place a real screenshot at `screenshots/ui-safari-windows.png`.

## Quick start
1. `python -m venv .venv`
2. `.venv\\Scripts\\activate`
3. `pip install -r requirements.txt`
4. `python app.py`
5. Open `http://127.0.0.1:5000`

## Usage
1. Click "Upload PDF" and choose a file.
2. Enter the password if the PDF is encrypted.
3. Press "Process".
4. Download the unlocked copy.

## Notes
- You must know the password. This does not break encryption.
- Unlocked copies are written to `output/` and offered as downloads.
- Max upload size is 50 MB (adjust `MAX_MB` in `app.py`).
