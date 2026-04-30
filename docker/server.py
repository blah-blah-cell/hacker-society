from http.server import BaseHTTPRequestHandler, HTTPServer
import os

class SimpleServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"Welcome to the Defender Server!")

    def do_POST(self):
        # Extremely vulnerable: allow reading files if 'path' is in headers
        # A simple hook to let the attacker find the flag
        if 'path' in self.headers:
            path = self.headers['path']
            try:
                with open(path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Missing 'path' header")

def run(server_class=HTTPServer, handler_class=SimpleServer, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
