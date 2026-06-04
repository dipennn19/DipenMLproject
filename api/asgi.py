from asgiref.wsgi import WsgiToAsgi
from app import app as flask_app

# Wrap the Flask WSGI app into an ASGI app. Vercel's Python runtime can invoke this
# as an HTTP handler when routed to this file.
app = WsgiToAsgi(flask_app)
