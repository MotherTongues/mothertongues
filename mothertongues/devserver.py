"""Local development servers used by the `run`, `build-and-run` and `dev` commands.

These are for previewing a dictionary locally and are not secure for production.
"""

import json
import signal
import time
import uuid
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urlsplit

import watchfiles
from loguru import logger

PACKAGE_DIR = Path(__file__).parent
DATA_ROUTE = "/assets/dictionary_data.json"
RELOAD_ROUTE = "/__mtd_reload"

# Kept in sync with mothertongues-UI/packages/mtd-mobile-ui/dev/mtd-reload.js.
# Every server process sends a fresh id, and EventSource reconnects on its own
# after a restart, so a new id means the dictionary was rebuilt.
RELOAD_SCRIPT = """<script>
(function () {
  var first = null;
  new EventSource('/__mtd_reload').onmessage = function (e) {
    if (first === null) first = e.data;
    else if (e.data !== first) location.reload();
  };
})();
</script>"""


class _Server(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


class NoCacheHandler(SimpleHTTPRequestHandler):
    """Serves files without letting the browser cache them, so rebuilds always show up.

    Optionally serves the dictionary data from memory and a live-reload event stream.
    """

    data: Optional[bytes] = None
    live_reload = False
    build_id = ""

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-transform")
        super().end_headers()

    def do_GET(self):
        if not self._handle_special(head_only=False):
            super().do_GET()

    def do_HEAD(self):
        if not self._handle_special(head_only=True):
            super().do_HEAD()

    def _handle_special(self, head_only: bool) -> bool:
        path = urlsplit(self.path).path
        if self.live_reload and path == RELOAD_ROUTE:
            self._send_events(head_only)
        elif self.data is not None and path == DATA_ROUTE:
            self._send_body(self.data, "application/json", head_only)
        elif self.live_reload and path in ("/", "/index.html"):
            index = Path(self.directory) / "index.html"  # type: ignore[attr-defined]
            if not index.exists():
                return False
            html = index.read_text(encoding="utf8")
            html = html.replace("</body>", RELOAD_SCRIPT + "\n</body>", 1)
            self._send_body(html.encode("utf8"), "text/html; charset=utf-8", head_only)
        else:
            return False
        return True

    def _send_body(self, body: bytes, content_type: str, head_only: bool):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def _send_events(self, head_only: bool):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.end_headers()
        if head_only:
            return
        try:
            self.wfile.write(f"data: {self.build_id}\n\n".encode())
            self.wfile.flush()
            # Hold the connection open; it drops when this server restarts.
            while True:
                time.sleep(15)
                self.wfile.write(b": ping\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass


def serve(
    directory: Optional[Path],
    port: int,
    data: Optional[bytes] = None,
    live_reload: bool = False,
    announce: bool = True,
):
    """Serve the UI in `directory` (or only the data and reload routes if None) until ctrl+c."""
    handler_class = type(
        "Handler",
        (NoCacheHandler,),
        {"data": data, "live_reload": live_reload, "build_id": uuid.uuid4().hex},
    )
    if directory is None:
        handler_class.do_GET = handler_class.do_HEAD = _not_found  # type: ignore
    handler = partial(handler_class, directory=str(directory or PACKAGE_DIR))
    logger.warning(
        "WARNING: This is a Development server and is not secure for production"
    )
    httpd = _Server(("", port), handler)
    if announce:
        logger.info(
            "Open http://localhost:{port} in your browser to see your dictionary",
            port=port,
        )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


def _not_found(self: NoCacheHandler):
    if not self._handle_special(head_only=self.command == "HEAD"):
        self.send_error(404)


class _WatchFilter(watchfiles.DefaultFilter):
    """Watch dictionary files, plus Python source in the mothertongues package."""

    def __init__(self, ignore: Iterable[Path]):
        super().__init__()
        self.ignore = [p.resolve() for p in ignore]

    def __call__(self, change: watchfiles.Change, path: str) -> bool:
        if not super().__call__(change, path):
            return False
        resolved = Path(path).resolve()
        if any(resolved.is_relative_to(p) for p in self.ignore):
            return False
        if resolved.is_relative_to(PACKAGE_DIR):
            return resolved.suffix == ".py"
        return True


def _export_and_serve(
    config_path: Path, port: int, ui_dir: Optional[Path], announce: bool
):
    # watchfiles stops this process with SIGINT on every change, so make sure it isn't
    # ignored (e.g. when launched in the background), or each restart waits for a SIGKILL.
    signal.signal(signal.SIGINT, signal.default_int_handler)
    # Imported here so that each restart picks up edits to the mothertongues code.
    from mothertongues.config.models import MTDConfiguration
    from mothertongues.dictionary import MTDictionary
    from mothertongues.utils import load_mtd_configuration

    try:
        config = MTDConfiguration(**load_mtd_configuration(config_path))
        output = MTDictionary(config).export()
    except Exception as e:
        logger.error(f"Could not build your dictionary: {e}")
        logger.info("Waiting for changes...")
        return
    data = json.dumps(output.model_dump(mode="json")).encode("utf8")
    serve(ui_dir, port, data=data, live_reload=True, announce=announce)


def watch_and_serve(
    config_path: Path,
    port: int,
    ui_dir: Optional[Path],
    ignore: Iterable[Path] = (),
    announce: bool = True,
):
    """Rebuild and re-serve the dictionary whenever its files or the mothertongues code change.

    Watches the directory containing the configuration (so data files, alphabets etc. are
    picked up) and the mothertongues package. Open pages reload themselves after each rebuild.
    """
    config_path = config_path.resolve()
    ignore = [PACKAGE_DIR / "ui", PACKAGE_DIR.parent / "mothertongues-UI", *ignore]
    logger.info(f"Watching {config_path.parent} for changes")
    watchfiles.run_process(
        config_path.parent,
        PACKAGE_DIR,
        target=_export_and_serve,
        args=(config_path, port, ui_dir, announce),
        watch_filter=_WatchFilter(ignore),
        callback=lambda changes: logger.info(
            f"Change detected in {', '.join(sorted({Path(p).name for _, p in changes}))}, rebuilding..."
        ),
    )
