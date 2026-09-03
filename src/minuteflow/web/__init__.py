"""Local web app: FastAPI backend plus SPA serving for ``minuteflow web``."""

from minuteflow.web.app import create_app
from minuteflow.web.server import resolve_frontend_dist, serve

__all__ = ["create_app", "resolve_frontend_dist", "serve"]
