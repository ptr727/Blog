"""Tests for `scripts/redact-media.py`, on images built here rather than taken from the archive.

Run with `uv run --with pillow==11.3.0 python -m unittest discover -s scripts/tests`.
"""

import contextlib
import hashlib
import importlib.util
import io
import json
import pathlib
import tempfile
import unittest
from unittest import mock

from PIL import Image

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("redact", SCRIPTS / "redact-media.py")
redact = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(redact)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def jpeg(color: tuple[int, int, int] = (40, 120, 200)) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (64, 48), color).save(out, "JPEG", quality=90)
    return out.getvalue()


def png(**params: object) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", (64, 48), (10, 200, 60)).save(out, "PNG", **params)
    return out.getvalue()


class RedactMediaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = pathlib.Path(self.tmp.name)
        (self.repo / "checks").mkdir()
        (self.repo / "static").mkdir()
        self.manifest_path = self.repo / "checks" / "media-redactions.json"
        self.saved = redact.REPO, redact.MANIFEST
        redact.REPO, redact.MANIFEST = self.repo, self.manifest_path
        self.addCleanup(self.restore)

    def restore(self) -> None:
        redact.REPO, redact.MANIFEST = self.saved

    def add(self, name: str, data: bytes, entry: dict) -> pathlib.Path:
        path = self.repo / "static" / name
        path.write_bytes(data)
        files = self.manifest()["files"] if self.manifest_path.exists() else {}
        files[f"static/{name}"] = entry
        self.manifest_path.write_text(json.dumps({"files": files}, indent=2) + "\n")
        return path

    def manifest(self) -> dict:
        return json.loads(self.manifest_path.read_text())

    def run_script(self, *argv: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), mock.patch("sys.argv", ["redact", *argv]):
            code = redact.main()
        return code, out.getvalue()

    def test_record_then_rerun_converges(self) -> None:
        path = self.add("a.jpg", jpeg(), {"fill": [[8, 8, 24, 24]], "crop": None})
        code, out = self.run_script("--record")
        self.assertEqual(code, 0, out)
        entry = self.manifest()["files"]["static/a.jpg"]
        self.assertEqual(sha256(path.read_bytes()), entry["result"])
        self.assertEqual(entry["declared"], redact.check.declared(entry))
        code, out = self.run_script("--record")
        self.assertEqual(code, 0, out)
        self.assertIn("1 already redacted", out)

    def test_failed_redaction_records_nothing(self) -> None:
        path = self.add("a.jpg", jpeg(), {"fill": [[8, 8, 900, 24]]})
        before = self.manifest_path.read_bytes()
        code, out = self.run_script("--record")
        self.assertEqual(code, 1)
        self.assertIn("outside", out)
        self.assertEqual(self.manifest_path.read_bytes(), before)
        self.assertEqual(path.read_bytes(), jpeg())

    def test_one_failure_leaves_every_entry_unwritten(self) -> None:
        good = self.add("good.jpg", jpeg(), {"fill": [[8, 8, 24, 24]]})
        self.add("bad.jpg", jpeg((1, 2, 3)), {"fill": [[8.0, 8, 24, 24]]})
        before = self.manifest_path.read_bytes()
        code, out = self.run_script("--record")
        self.assertEqual(code, 1)
        self.assertIn("not four integers", out)
        self.assertEqual(self.manifest_path.read_bytes(), before)
        self.assertEqual(good.read_bytes(), jpeg())

    def test_unchanged_entry_is_compared_under_record(self) -> None:
        data = jpeg()
        entry = {"fill": [[8, 8, 24, 24]], "source": sha256(data), "result": "0" * 64}
        entry["declared"] = redact.check.declared(entry)
        self.add("a.jpg", data, entry)
        before = self.manifest_path.read_bytes()
        code, out = self.run_script("--record")
        self.assertEqual(code, 1)
        self.assertIn("does not match its result hash", out)
        self.assertEqual(self.manifest_path.read_bytes(), before)

    def test_changed_entry_needs_a_normalized_source(self) -> None:
        self.add("a.png", png(pnginfo=text_chunk()), {"fill": [[8, 8, 24, 24]]})
        code, out = self.run_script("--record")
        self.assertEqual(code, 1)
        self.assertIn("not normalized", out)
        self.assertNotIn("result", self.manifest()["files"]["static/a.png"])

    def test_malformed_boxes_are_errors_not_crashes(self) -> None:
        for box in ([8, 8, 24, True], [8, 8, 24], "8,8,24,24", None):
            with self.subTest(box=box):
                self.add("a.jpg", jpeg(), {"fill": [box]})
                code, out = self.run_script("--record")
                self.assertEqual(code, 1)
                self.assertIn("not four integers", out)
        self.add("a.jpg", jpeg(), {"fill": None})
        code, out = self.run_script("--record")
        self.assertEqual(code, 1)
        self.assertIn("not a list", out)

    def test_entry_that_is_not_an_object_is_an_error(self) -> None:
        self.add("a.jpg", jpeg(), None)
        code, out = self.run_script()
        self.assertEqual(code, 1)
        self.assertIn("not an object", out)

    def test_apply_writes_good_entries_beside_a_failure(self) -> None:
        data = jpeg()
        entry = {"fill": [[8, 8, 24, 24]]}
        self.add("good.jpg", data, entry)
        self.run_script("--record")
        recorded = self.manifest()["files"]["static/good.jpg"]
        good = self.add("good.jpg", data, recorded)
        self.add("bad.jpg", jpeg((1, 2, 3)), {"fill": [[8, 8, 900, 24]]})
        code, _ = self.run_script("--apply")
        self.assertEqual(code, 1)
        self.assertEqual(sha256(good.read_bytes()), recorded["result"])

    def test_failed_replace_after_record_converges(self) -> None:
        path = self.add("a.jpg", jpeg(), {"fill": [[8, 8, 24, 24]]})
        real = redact.replace

        def fail_on_media(target: pathlib.Path, data: bytes) -> None:
            if target == path:
                raise PermissionError("in use")
            real(target, data)

        with mock.patch.object(redact, "replace", fail_on_media):
            code, out = self.run_script("--record")
        self.assertEqual(code, 1)
        self.assertEqual(path.read_bytes(), jpeg())
        code, out = self.run_script("--apply")
        self.assertEqual(code, 0, out)
        entry = self.manifest()["files"]["static/a.jpg"]
        self.assertEqual(sha256(path.read_bytes()), entry["result"])

    def test_missing_file_is_an_error(self) -> None:
        self.add("a.jpg", jpeg(), {"fill": [[8, 8, 24, 24]]}).unlink()
        code, out = self.run_script()
        self.assertEqual(code, 1)
        self.assertIn("static/a.jpg:", out)

    def test_animated_png_is_refused(self) -> None:
        frames = [
            Image.new("RGB", (32, 32), color) for color in ((255, 0, 0), (0, 0, 255))
        ]
        out = io.BytesIO()
        frames[0].save(out, "PNG", save_all=True, append_images=frames[1:])
        with self.assertRaisesRegex(ValueError, "animated"):
            redact.redact(out.getvalue(), {"fill": [[1, 1, 4, 4]]})

    def test_unwritable_subsampling_is_refused(self) -> None:
        data = bytearray(jpeg())
        sof = data.index(b"\xff\xc0")
        # Forge 4:4:0 by giving the luma component two vertical samples per block.
        data[sof + 11] = 0x12
        with self.assertRaisesRegex(ValueError, "subsampling"):
            redact.redact(bytes(data), {"fill": [[1, 1, 4, 4]]})


def text_chunk() -> object:
    from PIL import PngImagePlugin

    info = PngImagePlugin.PngInfo()
    info.add_text("Comment", "constructed")
    return info


if __name__ == "__main__":
    unittest.main()
