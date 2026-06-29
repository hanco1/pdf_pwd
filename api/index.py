import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app  # noqa: E402

# Vercel's @vercel/python serves a module-level WSGI `app`
