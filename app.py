import os
from http.server import BaseHTTPRequestHandler, HTTPServer
MESSAGE = os.environ.get("APP_MESSAGE", "hello from myapp GOOD")
VERSION = os.environ.get("APP_VERSION", "dev")
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body, code = "ok\n", 200
        elif self.path == "/":
            body, code = f"{MESSAGE} (version {VERSION})\n", 200
        else:
            body, code = "not found\n", 404
        self.send_response(code)
        self.end_headers()
        self.wfile.write(body.encode())
print("starting on port 8000", flush=True)
HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()