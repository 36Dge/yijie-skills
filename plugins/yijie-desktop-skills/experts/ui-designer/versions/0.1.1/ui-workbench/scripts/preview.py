"""Foreground read-only loopback preview of a declared project. Stop via Ctrl-C or stdin 'stop'."""
import argparse
import json
import mimetypes
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

# Managed expert resources are immutable, including undeclared bytecode caches.
sys.dont_write_bytecode = True

from validate_project import local_file, validate


def server_for(project, port):
    root = project.resolve()
    validated = validate(root)
    # Freeze the file bytes reviewed at startup; no directory listing or live path re-resolution.
    allowed = {name: local_file(root, name).read_bytes() for name in validated['files']}
    import hashlib
    if any(hashlib.sha256(content).hexdigest() != validated['files'][name] for name, content in allowed.items()):
        raise ValueError('Project changed during preview startup; validate again')
    entry = validated['entry']

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.serve(True)

        def do_HEAD(self):
            self.serve(False)

        def serve(self, body):
            name = unquote(urlsplit(self.path).path).lstrip('/') or entry
            if name not in allowed:
                self.send_error(404, 'File not declared in project')
                return
            content = allowed[name]
            mime = 'application/javascript' if name.endswith(('.js', '.cjs')) else (mimetypes.guess_type(name)[0] or 'application/octet-stream')
            self.send_response(200)
            self.send_header('Content-Type', mime + ('; charset=utf-8' if mime.startswith('text/') or mime in ('application/javascript', 'application/json') else ''))
            self.send_header('Content-Length', str(len(content)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self'; font-src 'self'; connect-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'")
            self.end_headers()
            if body:
                self.wfile.write(content)

        def log_message(self, fmt, *args):
            # Avoid echoing query strings or page text into logs.
            pass

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)


def run(project, port):
    server = server_for(project, port)
    worker = threading.Thread(target=server.serve_forever, daemon=False)
    worker.start()
    print(json.dumps({'url': f'http://127.0.0.1:{server.server_port}/', 'stop': 'Type stop or press Ctrl-C', 'reload': 'Restart normally after changing files; snapshot is immutable'}, ensure_ascii=False), flush=True)
    try:
        for line in sys.stdin:
            if line.strip().lower() == 'stop':
                break
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()
        worker.join()
        print('Preview stopped normally.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--port', type=int, default=0)
    args = parser.parse_args()
    try:
        run(args.project, args.port)
    except (ValueError, OSError, KeyError, TypeError) as e:
        parser.exit(2, 'Preview unavailable: ' + str(e) + '\n')
