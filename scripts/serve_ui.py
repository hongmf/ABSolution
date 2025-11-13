#!/usr/bin/env python3
"""
Simple HTTP server for ABSolution Dialogue Panel UI
Serves the frontend with proper CORS headers for local development
"""

import http.server
import socketserver
import os
import sys
from urllib.parse import urlparse, parse_qs

PORT = 8080
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), '..', 'src', 'frontend')

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    """
    HTTP Request Handler with CORS support
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def end_headers(self):
        """Add CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        """Handle preflight requests"""
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        """Custom log format"""
        sys.stdout.write("%s - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format % args))


def main():
    """Start the HTTP server"""

    # Check if frontend directory exists
    if not os.path.exists(FRONTEND_DIR):
        print(f"Error: Frontend directory not found at {FRONTEND_DIR}")
        sys.exit(1)

    # Check if index.html exists
    index_path = os.path.join(FRONTEND_DIR, 'index.html')
    if not os.path.exists(index_path):
        print(f"Error: index.html not found at {index_path}")
        sys.exit(1)

    print("=" * 60)
    print("ABSolution Dialogue Panel - Local Server")
    print("=" * 60)
    print()
    print(f"Serving from: {FRONTEND_DIR}")
    print(f"Port: {PORT}")
    print()
    print(f"🌐 Open in browser: http://localhost:{PORT}")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    print()

    # Create server
    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n" + "=" * 60)
            print("Server stopped")
            print("=" * 60)
            sys.exit(0)


if __name__ == "__main__":
    main()
