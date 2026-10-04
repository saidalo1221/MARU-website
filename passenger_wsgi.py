"""Entry point for hosts that run Python apps through Passenger (cPanel/DirectAdmin "Setup Python App").

Passenger speaks WSGI; MARU's backend is an ASGI (FastAPI) app, so a2wsgi translates between them.
Settings come from the `.env` file in the application root (Passenger starts the app there).
Not used when the backend runs with uvicorn (local development, a VPS).
"""
from a2wsgi import ASGIMiddleware

from app.main import app

application = ASGIMiddleware(app)
