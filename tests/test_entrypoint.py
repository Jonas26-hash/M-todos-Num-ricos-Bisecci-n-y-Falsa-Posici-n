"""Regresión del contrato ASGI usado por Vercel, con un servidor real aislado."""

import re
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from websockets.sync.client import connect

ROOT = Path(__file__).resolve().parents[1]


class EntrypointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Puerto efímero para no interferir con la aplicación abierta del usuario.
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            cls.port = sock.getsockname()[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.log = tempfile.TemporaryFile(mode="w+b")
        cls.addClassCleanup(cls.log.close)
        cls.server = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app:app", "--host", "127.0.0.1",
             "--port", str(cls.port)],
            cwd=ROOT, stdout=cls.log, stderr=subprocess.STDOUT,
        )
        cls.addClassCleanup(cls.stop_server)
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            if cls.server.poll() is not None:
                break
            try:
                with urlopen(cls.base + "/_stcore/health", timeout=1) as response:
                    if response.status == 200:
                        return
            except (OSError, URLError):
                time.sleep(0.1)
        cls.log.seek(0)
        raise AssertionError(cls.log.read().decode("utf-8", errors="replace"))

    @classmethod
    def stop_server(cls):
        if cls.server.poll() is None:
            cls.server.terminate()
            try:
                cls.server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                cls.server.kill()
                cls.server.wait(timeout=5)

    def test_import_exports_asgi_without_running_ui(self):
        code = (
            "import inspect, sys; "
            f"sys.path.insert(0, {str(ROOT)!r}); "
            "from app import app; "
            "assert inspect.iscoroutinefunction(app.__call__); "
            "assert app.script_path.name == 'streamlit_app.py'; "
            "assert 'streamlit_app' not in sys.modules; "
            "from streamlit.runtime import Runtime; "
            "assert not Runtime.exists()"
        )
        result = subprocess.run(
            [sys.executable, "-c", code], cwd=ROOT.parent,
            capture_output=True, text=True, timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_http_health_and_frontend_assets(self):
        with urlopen(self.base + "/_stcore/health", timeout=5) as response:
            self.assertEqual(response.read(), b"ok")
        with urlopen(self.base, timeout=5) as response:
            html = response.read().decode("utf-8")
        self.assertIn('id="root"', html)
        script = re.search(r'<script[^>]+src="([^"]+)"', html)
        self.assertIsNotNone(script)
        with urlopen(self.base + "/" + script.group(1).lstrip("./"), timeout=5) as response:
            self.assertEqual(response.status, 200)
            self.assertIn("javascript", response.headers["Content-Type"])

    def test_websocket_connection_and_ping(self):
        with connect(
            f"ws://127.0.0.1:{self.port}/_stcore/stream",
            origin=self.base, subprotocols=["streamlit"], open_timeout=10,
        ) as websocket:
            self.assertEqual(websocket.subprotocol, "streamlit")
            self.assertTrue(websocket.ping().wait(timeout=5))


if __name__ == "__main__":
    unittest.main()
