"""
Minimal HTTP health server for Celery worker on Cloud Run.
Runs alongside celery in the same container, responds on $PORT.
"""
import http.server
import os
import subprocess
import sys
import threading


PORT = int(os.environ.get("PORT", 8080))


class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health", "/healthz"):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status":"ok","service":"lia-worker"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def run_health_server():
    server = http.server.HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()


if __name__ == "__main__":
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()

    celery_cmd = [
        "celery", "-A", "app.core.celery_app", "worker",
        "--loglevel", os.environ.get("CELERY_LOGLEVEL", "info"),
        "--concurrency", os.environ.get("CELERY_CONCURRENCY", "2"),
        "--queues", os.environ.get("CELERY_QUEUES",
            "sourcing_high,evaluation_normal,vagas_normal,onboarding_low"),
        "--without-heartbeat",
        "--without-gossip",
        "--without-mingle",
        "--prefetch-multiplier=1",
    ]
    sys.exit(subprocess.call(celery_cmd))
