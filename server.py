"""
Frontend Service - Simple HTTP server to serve the HTML interface
"""

import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent), **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()


def serve(port: int = 8003):
    """Start the frontend server"""
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, CustomHandler)
    print(f"Frontend server running on http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down frontend server...")
        httpd.shutdown()


if __name__ == "__main__":
    import sys
    port = int(os.getenv("FRONTEND_SERVICE_PORT", "8003"))
    serve(port)

