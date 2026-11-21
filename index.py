"""Vercel entry point.

Vercel looks for a Flask object named `app` in index.py at the project root and runs it
as a serverless function. The app itself is the same Flask app that runs locally with
`python run.py`.
"""
from app import create_app

app = create_app()
