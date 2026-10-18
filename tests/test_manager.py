import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('lazy', Path(__file__).parents[1] / 'lazy.py')
lazy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lazy)

class SafetyTests(unittest.TestCase):
    def test_archive_escape_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            for name in ['../secret','/etc/passwd','a/../../secret']:
                with self.assertRaises(RuntimeError):
                    lazy.safe_destination(Path(d), name)

    def test_checksum_failure_preserves_cache(self):
        with tempfile.TemporaryDirectory() as d:
            a = {'sha256':'0'*64, 'url':'https://github.com/example/asset', 'name':'test'}
            from io import BytesIO
            with patch.object(lazy.urllib.request, 'urlopen', return_value=BytesIO(b'bad')):
                with self.assertRaises(RuntimeError):
                    lazy.fetch(a, Path(d))
            self.assertEqual(list(Path(d).iterdir()), [])

    def test_failed_update_keeps_active_release(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'runtime'; root.mkdir()
            source = Path(d)/'source'; source.mkdir()
            (source/'config').mkdir(); (source/'config/mpv.conf').write_text('vo=gpu-next\n')
            (source/'VERSION').write_text('test'); (source/'lazy.py').write_text('test')
            lock = source/'dependencies.lock.json'
            lock.write_text('{"assets":[]}')
            with patch.object(lazy, 'SOURCE', source):
                lazy.install(root, Path(d)/'cache')
                first = (root/'current').resolve()
                lock.write_text(json.dumps({'assets':[{'kind':'file'}]}))
                with patch.object(lazy, 'fetch', side_effect=RuntimeError('download failed')):
                    with self.assertRaises(RuntimeError):
                        lazy.install(root, Path(d)/'cache')
                self.assertEqual((root/'current').resolve(), first)
                lazy.verify(first)
                self.assertEqual(list(root.glob('.stage-*')), [])

    def test_lifecycle_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'runtime'; root.mkdir()
            source = Path(d)/'source'; source.mkdir()
            (source/'config').mkdir(); (source/'config/mpv.conf').write_text('vo=gpu-next\n')
            (source/'VERSION').write_text('test'); (source/'lazy.py').write_text('test')
            (source/'dependencies.lock.json').write_text('{"assets":[]}')
            with patch.object(lazy, 'SOURCE', source):
                lazy.install(root, Path(d)/'cache')
                first = (root/'current').resolve()
                lazy.install(root, Path(d)/'cache')
                self.assertEqual(len(list((root/'releases').iterdir())), 1)
                (source/'config/mpv.conf').write_text('vo=gpu-next\nosc=no\n')
                lazy.install(root, Path(d)/'cache')
                self.assertEqual((root/'previous').resolve(), first)
                self.assertTrue(list((root/'backups').glob('*.tar.gz')))
                with patch('sys.argv',['lazy','--root',str(root),'rollback']):
                    lazy.main()
                self.assertEqual((root/'current').resolve(),first)
                (first/'mpv.conf').write_text('corrupted')
                with self.assertRaises(RuntimeError):
                    lazy.verify(first)

if __name__ == '__main__': unittest.main()
