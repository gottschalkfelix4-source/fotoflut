"""Phase-0-Platzhalter für den FotoFlut-ML-Worker.

Später: BullMQ-Consumer mit ONNX Runtime + OpenVINO EP (Intel Arc via /dev/dri,
CPU-Fallback über FF_ML_DEVICE=CPU). Modelle im Mount /model-cache.
"""

import http.server
import json
import os
import socketserver

PORT = int(os.environ.get("FF_ML_PORT", "8081"))
DEVICE = os.environ.get("FF_ML_DEVICE", "GPU")


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path in ("/healthz", "/api/health"):
            body = json.dumps(
                {"status": "ok", "service": "fotoflut-ml", "device": DEVICE}
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        print(f"fotoflut-ml placeholder listening on :{PORT} (device={DEVICE})")
        httpd.serve_forever()
