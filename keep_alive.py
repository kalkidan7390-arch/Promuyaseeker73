import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get("PORT", 8080))

class WebEngineHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"System Instance Alive and Listening")
        
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()
        
    def log_message(self, *args):
        pass  

def start():
    server = HTTPServer(("0.0.0.0", PORT), WebEngineHandler)
    Thread(target=server.serve_forever, daemon=True).start()
    print(f"✅ Web engine microservice online on network routing port {PORT}")
