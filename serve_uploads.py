#!/usr/bin/env python3
"""
Simple HTTP server to serve uploads directory for Ollama access
This runs on port 11435 so Ollama can access files via http://localhost:11435/
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# Get the uploads directory
uploads_dir = Path(__file__).parent / "uploads"
if not uploads_dir.exists():
    uploads_dir.mkdir(exist_ok=True)

# Change to uploads directory
os.chdir(uploads_dir)

# Create server
PORT = 11435
Handler = http.server.SimpleHTTPRequestHandler

# Allow CORS
class CORSHTTPRequestHandler(Handler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    # Allow reuse of the port
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), CORSHTTPRequestHandler) as httpd:
        print(f"📁 Serving uploads directory at http://localhost:{PORT}")
        print(f"📂 Directory: {uploads_dir.absolute()}")
        print("Press Ctrl+C to stop")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")
        except Exception as e:
            print(f"\n❌ Server error: {e}")
            sys.exit(1) 