"""Vercel entry point.

Vercel runs this file as a serverless function, and vercel.json sends every
request to it. The app itself is the same Flask app that runs locally with
`python run.py`.
"""
import os
import sys

# Make the project folder importable (this file lives in api/, the app package is one level up)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402

app = create_app()
