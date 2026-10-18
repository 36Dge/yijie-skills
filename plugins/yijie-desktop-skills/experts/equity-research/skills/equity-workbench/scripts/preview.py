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

import hashlib


def server_for(project, port):
    root = project.resolve()
    receipt_path = root / 'receipt.json'
    if receipt_path.is_symlink() or not receipt_path.is_file() or receipt_path.stat().st_size > 100000:
        raise ValueError('Ordinary receipt required')
    receipt = json.loads(receipt_path.read_text())
    allowed = {}
    for name in ('index.html', 'data.js', 'report.js', 'report.css'):
        p = root / name
        if p.is_symlink() or not p.is_file() or p.stat().st_size > 10000000:
            raise ValueError('Report file unavailable: ' + name)
        content = p.read_bytes()
        if hashlib.sha256(content).hexdigest() != receipt['files'].get(name):
            raise ValueError('Report changed; regenerate rather than alter receipt')
        allowed[name] = content
    entry = 'index.html'

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.serve(True)

        def do_HEAD(self):
            self.serve(False)

        def serve(self, body):
            if self.headers.get('Host') != f'127.0.0.1:{self.server.server_port}':
                self.send_error(403, 'Use the declared loopback URL')
                return
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
