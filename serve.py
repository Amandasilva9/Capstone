from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
class NoCache(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()
print("Website running at http://localhost:5500")
ThreadingHTTPServer(("", 5500), NoCache).serve_forever()
