import os
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

# Ensure cloud mode for serverless
os.environ.setdefault("CLOUD_MODE", "true")

from app import app as flask_app  # imports the Flask app instance


# Vercel looks for a top-level `handler`
def handler(request, response):
    # This handler signature is not used by @vercel/python; we expose `app` instead.
    pass

# Export as `app` for @vercel/python runtime
app = flask_app


