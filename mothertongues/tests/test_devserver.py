import threading
import urllib.request
from functools import partial
from unittest import main

from mothertongues.devserver import RELOAD_SCRIPT, NoCacheHandler, _Server
from mothertongues.tests.base_test_case import BasicTestCase


class DevServerTest(BasicTestCase):
    """Test the local development server"""

    def setUp(self):
        super().setUp()
        (self.tempdir / "assets").mkdir()
        (self.tempdir / "index.html").write_text(
            "<html><body></body></html>", encoding="utf8"
        )
        (self.tempdir / "main.js").write_text("console.log(1)", encoding="utf8")

    def start(self, **handler_attrs):
        handler_class = type("Handler", (NoCacheHandler,), handler_attrs)
        httpd = _Server(
            ("localhost", 0), partial(handler_class, directory=str(self.tempdir))
        )
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)
        return f"http://localhost:{httpd.server_address[1]}"

    def get(self, url):
        with urllib.request.urlopen(url) as response:
            return response.headers, response.read().decode("utf8")

    def test_no_cache_headers(self):
        url = self.start()
        headers, body = self.get(url + "/main.js")
        self.assertIn("no-store", headers["Cache-Control"])
        self.assertEqual(body, "console.log(1)")

    def test_serves_data_from_memory(self):
        url = self.start(data=b'{"data": []}')
        headers, body = self.get(url + "/assets/dictionary_data.json")
        self.assertEqual(body, '{"data": []}')
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertFalse((self.tempdir / "assets" / "dictionary_data.json").exists())

    def test_reload_script_only_with_live_reload(self):
        _, body = self.get(self.start() + "/")
        self.assertNotIn(RELOAD_SCRIPT, body)
        _, body = self.get(self.start(live_reload=True) + "/")
        self.assertIn(RELOAD_SCRIPT, body)

    def test_reload_events(self):
        url = self.start(live_reload=True, build_id="abc123")
        with urllib.request.urlopen(url + "/__mtd_reload", timeout=5) as response:
            self.assertEqual(response.headers["Content-Type"], "text/event-stream")
            self.assertEqual(response.readline(), b"data: abc123\n")


if __name__ == "__main__":
    main()
