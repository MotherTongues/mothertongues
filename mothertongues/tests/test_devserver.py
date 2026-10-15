import threading
import urllib.error
import urllib.request
from functools import partial
from unittest import main
from unittest.mock import patch

import watchfiles

from mothertongues.devserver import (
    PACKAGE_DIR,
    RELOAD_SCRIPT,
    NoCacheHandler,
    _export_and_serve,
    _Server,
    _WatchFilter,
    serve,
    watch_and_serve,
)
from mothertongues.tests.base_test_case import BasicTestCase
from mothertongues.tests.utils import capture_logs


class DevServerTest(BasicTestCase):
    """Test the local development server"""

    def setUp(self):
        super().setUp()
        (self.tempdir / "assets").mkdir()
        (self.tempdir / "index.html").write_text(
            "<html><body></body></html>", encoding="utf8"
        )
        (self.tempdir / "main.js").write_text("console.log(1)", encoding="utf8")

    def start(self, handler=None, **handler_attrs):
        if handler is None:
            handler_class = type("Handler", (NoCacheHandler,), handler_attrs)
            handler = partial(handler_class, directory=str(self.tempdir))
        httpd = _Server(("localhost", 0), handler)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        self.addCleanup(httpd.server_close)
        self.addCleanup(httpd.shutdown)
        return f"http://localhost:{httpd.server_address[1]}"

    def get(self, url, method="GET"):
        request = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(request) as response:
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

    def test_head_requests(self):
        url = self.start(data=b'{"data": []}', live_reload=True)
        headers, body = self.get(url + "/assets/dictionary_data.json", method="HEAD")
        self.assertEqual(headers["Content-Length"], "12")
        self.assertEqual(body, "")
        headers, body = self.get(url + "/main.js", method="HEAD")
        self.assertIn("no-store", headers["Cache-Control"])
        self.assertEqual(body, "")
        headers, body = self.get(url + "/__mtd_reload", method="HEAD")
        self.assertEqual(headers["Content-Type"], "text/event-stream")
        self.assertEqual(body, "")

    def test_reload_script_only_with_live_reload(self):
        _, body = self.get(self.start() + "/")
        self.assertNotIn(RELOAD_SCRIPT, body)
        _, body = self.get(self.start(live_reload=True) + "/")
        self.assertIn(RELOAD_SCRIPT, body)

    def test_live_reload_without_index(self):
        (self.tempdir / "index.html").unlink()
        url = self.start(live_reload=True)
        _, body = self.get(url + "/")
        self.assertNotIn(RELOAD_SCRIPT, body)

    def test_reload_events(self):
        url = self.start(live_reload=True, build_id="abc123")
        with urllib.request.urlopen(url + "/__mtd_reload", timeout=5) as response:
            self.assertEqual(response.headers["Content-Type"], "text/event-stream")
            self.assertEqual(response.readline(), b"data: abc123\n")

    def test_reload_events_keepalive(self):
        url = self.start(live_reload=True, build_id="abc123")
        with patch("mothertongues.devserver.time") as mock_time:
            mock_time.sleep = lambda seconds: None
            with urllib.request.urlopen(url + "/__mtd_reload", timeout=5) as response:
                self.assertEqual(response.readline(), b"data: abc123\n")
                self.assertEqual(response.readline(), b"\n")
                self.assertEqual(response.readline(), b": ping\n")

    def test_serve(self):
        with patch("mothertongues.devserver._Server") as mock_server:
            mock_server.return_value.serve_forever.side_effect = KeyboardInterrupt
            with capture_logs() as logs:
                serve(self.tempdir, 4321, data=b"{}", live_reload=True)
        (address, handler), _ = mock_server.call_args
        self.assertEqual(address, ("", 4321))
        self.assertEqual(handler.keywords["directory"], str(self.tempdir))
        self.assertEqual(handler.func.data, b"{}")
        self.assertTrue(handler.func.live_reload)
        mock_server.return_value.server_close.assert_called_once()
        self.assertIn("http://localhost:4321", logs[-1])

    def test_serve_without_ui(self):
        # Used by the `dev` command: only the data and reload routes are served
        with patch("mothertongues.devserver._Server") as mock_server:
            mock_server.return_value.serve_forever.side_effect = KeyboardInterrupt
            with capture_logs() as logs:
                serve(None, 4321, data=b"{}", live_reload=True, announce=False)
        self.assertNotIn("http://localhost:4321", "".join(logs))
        _, handler = mock_server.call_args.args
        url = self.start(handler)
        _, body = self.get(url + "/assets/dictionary_data.json")
        self.assertEqual(body, "{}")
        headers, _ = self.get(url + "/assets/dictionary_data.json", method="HEAD")
        self.assertEqual(headers["Content-Length"], "2")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.get(url + "/devserver.py")
        self.assertEqual(cm.exception.code, 404)

    def test_watch_filter(self):
        ignored = self.tempdir / "mothertongues-UI"
        watch_filter = _WatchFilter([ignored])
        added = watchfiles.Change.added
        self.assertTrue(watch_filter(added, str(self.tempdir / "data.csv")))
        self.assertTrue(watch_filter(added, str(PACKAGE_DIR / "cli.py")))
        self.assertFalse(watch_filter(added, str(PACKAGE_DIR / "ui" / "main.js")))
        self.assertFalse(watch_filter(added, str(PACKAGE_DIR / "schemas" / "x.json")))
        self.assertFalse(watch_filter(added, str(ignored / "src" / "app.ts")))
        self.assertFalse(watch_filter(added, str(self.tempdir / ".git" / "HEAD")))

    def test_export_and_serve(self):
        with patch("mothertongues.devserver.serve") as mock_serve:
            _export_and_serve(
                self.data_dir / "config_data_check.json", 4321, self.tempdir, False
            )
        (directory, port), kwargs = mock_serve.call_args
        self.assertEqual((directory, port), (self.tempdir, 4321))
        self.assertIn(b'"data"', kwargs["data"])
        self.assertTrue(kwargs["live_reload"])
        self.assertFalse(kwargs["announce"])

    def test_export_and_serve_bad_config(self):
        bad_config = self.tempdir / "config.mtd.json"
        bad_config.write_text("{broken", encoding="utf8")
        with patch("mothertongues.devserver.serve") as mock_serve:
            with capture_logs() as logs:
                _export_and_serve(bad_config, 4321, self.tempdir, True)
        mock_serve.assert_not_called()
        self.assertIn("Could not build your dictionary", logs[0])
        self.assertIn("Waiting for changes", logs[1])

    def test_watch_and_serve(self):
        config_path = self.data_dir / "config_data_check.json"
        with patch("mothertongues.devserver.watchfiles.run_process") as run_process:
            watch_and_serve(config_path, 4321, self.tempdir, ignore=[self.tempdir])
            paths = run_process.call_args.args
            kwargs = run_process.call_args.kwargs
            self.assertEqual(paths, (config_path.resolve().parent, PACKAGE_DIR))
            self.assertIs(kwargs["target"], _export_and_serve)
            self.assertEqual(
                kwargs["args"], (config_path.resolve(), 4321, self.tempdir, True)
            )
            self.assertIn(self.tempdir.resolve(), kwargs["watch_filter"].ignore)
            with capture_logs() as logs:
                kwargs["callback"]({(watchfiles.Change.modified, "/x/data.csv")})
            self.assertIn("Change detected in data.csv", logs[0])


if __name__ == "__main__":
    main()
