import json
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from pathlib import Path
from render_start import ensure_demo_store
from web_app import create_server


class RenderTests(unittest.TestCase):
    def test_seed_copy_keeps_runtime_changes_and_seed_unchanged(self):
        with tempfile.TemporaryDirectory() as root:
            seed, dest = Path(root)/'seed', Path(root)/'demo'
            seed.mkdir(); (seed/'chroma.sqlite3').write_text('seed')
            ensure_demo_store(seed,dest)
            (dest/'chroma.sqlite3').write_text('user addition')
            ensure_demo_store(seed,dest)
            self.assertEqual((dest/'chroma.sqlite3').read_text(),'user addition')
            self.assertEqual((seed/'chroma.sqlite3').read_text(),'seed')

    def test_https_origin_and_demo_config(self):
        with tempfile.TemporaryDirectory() as root:
            server=create_server(0,Path(root)/'db',public_origin='https://pantry.example',demo=True)
            thread=threading.Thread(target=server.serve_forever);thread.start()
            url=f'http://127.0.0.1:{server.server_port}'
            try:
                for endpoint,key in [('/healthz','status'),('/api/config','temporary_demo')]:
                    with urllib.request.urlopen(url+endpoint) as response:
                        self.assertTrue(json.load(response)[key])
                for origin,status in [('https://pantry.example',400),('https://evil.example',403)]:
                    req=urllib.request.Request(url+'/api/search',data=b'{}',headers={'Content-Type':'application/json','Origin':origin})
                    with self.assertRaises(urllib.error.HTTPError) as err:
                        urllib.request.urlopen(req)
                    self.assertEqual(err.exception.code,status)
            finally:
                server.shutdown();server.server_close();thread.join()
