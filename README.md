# PDF Unlocker (Local)

Local Flask app that removes a known password from a PDF using pypdf.

## Run
1. `python -m venv .venv`
2. `.venv\\Scripts\\activate`
3. `pip install -r requirements.txt`
4. `python app.py`
5. Open `http://127.0.0.1:5000`

## Notes
- If the PDF is encrypted, enter the password you know.
- Unlocked copies are written to `output/` and offered as downloads.
- Max upload size is 50 MB (adjust `MAX_MB` in `app.py`).
