"""Tests for the free values check-media-metadata.py pins, every value in them constructed."""

import importlib.util
import pathlib
import struct
import unittest
import zlib
from unittest import mock

REPO = pathlib.Path(__file__).resolve().parent.parent.parent


def load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


normalizer = load("normalizer", REPO / "scripts" / "normalize-media.py")
fuzz = load("fuzz", REPO / "checks" / "fuzz-media-parsers.py")
gate = normalizer.gate

# A stand-in profile, admitted by patching its digest into the set for the test that needs it.
PROFILE = b"acsp" * 64


def known():
    digest = gate.hashlib.sha256(PROFILE).hexdigest()
    return mock.patch.object(gate, "ICC_PROFILES", gate.ICC_PROFILES | {digest})


def jpeg_with(*segments: bytes) -> bytes:
    data = fuzz.jpeg_fixture(False)
    bare = data.replace(fuzz.jpeg_segment(0xE0, fuzz.JFIF), b"")
    bare = bare.replace(fuzz.exif_segment(), b"")
    return bare[:2] + b"".join(segments) + bare[2:]


def icc_chunks(profile: bytes, order: tuple[int, ...]) -> list[bytes]:
    half = len(profile) // 2
    pieces = (profile[:half], profile[half:])
    return [
        fuzz.jpeg_segment(0xE2, fuzz.ICC[:12] + bytes((n, 2)) + pieces[n - 1])
        for n in order
    ]


def png_with(chunk: bytes) -> bytes:
    data = fuzz.png_fixture()
    return data[:33] + chunk + data[33:]


def iccp(name: bytes, stream: bytes) -> bytes:
    return fuzz.png_chunk(b"iCCP", name + b"\x00\x00" + stream)


def webp_with_profile(flags: int, profile: bytes) -> bytes:
    body = fuzz.riff_chunk(b"VP8X", bytes((flags,)) + bytes(9))
    body += fuzz.riff_chunk(b"ICCP", profile)
    body += fuzz.riff_chunk(b"VP8L", b"\x2f\x00\x00\x00\x00")
    return b"RIFF" + struct.pack("<I", len(body) + 4) + b"WEBP" + body


class Profiles(unittest.TestCase):
    def test_known_jpeg_profile_passes_in_either_chunk_order(self) -> None:
        with known():
            for order in ((1, 2), (2, 1)):
                self.assertEqual(
                    gate.scan(jpeg_with(*icc_chunks(PROFILE, order))), set()
                )

    def test_unknown_jpeg_profile_is_refused(self) -> None:
        data = jpeg_with(*icc_chunks(PROFILE, (1, 2)))
        self.assertIn("JPEG ICC profile not a known profile", gate.scan(data))
        self.assertIsNone(normalizer.normalize_bytes(data))

    def test_png_profile_under_another_name_is_renamed(self) -> None:
        data = png_with(iccp(b"planted", zlib.compress(PROFILE)))
        with known():
            self.assertEqual(gate.scan(data), {"PNG iCCP name not a known name"})
            new = normalizer.normalize_bytes(data)
            self.assertIsNotNone(new)
            self.assertEqual(gate.scan(new), set())
            self.assertNotIn(b"planted", new)

    def test_png_stream_longer_than_its_profile_is_recompressed(self) -> None:
        # A stored stream is the profile's own bytes plus its framing, so it is longer.
        data = png_with(iccp(b"icc", zlib.compress(PROFILE, 0)))
        with known():
            self.assertIn("PNG iCCP stream longer than its profile", gate.scan(data))
            new = normalizer.normalize_bytes(data)
            self.assertIsNotNone(new)
            self.assertEqual(gate.scan(new), set())

    def test_png_bytes_past_the_stream_are_refused(self) -> None:
        data = png_with(iccp(b"icc", zlib.compress(PROFILE) + b"planted"))
        with known():
            self.assertIn("PNG ICC profile not a known profile", gate.scan(data))
            self.assertIsNone(normalizer.normalize_bytes(data))

    def test_webp_profile_flag_is_restated(self) -> None:
        with known():
            self.assertEqual(gate.scan(webp_with_profile(0x20, PROFILE)), set())
            data = webp_with_profile(0x00, PROFILE)
            self.assertEqual(
                gate.scan(data), {"WebP VP8X flags disagree with its chunks"}
            )
            new = normalizer.normalize_bytes(data)
            self.assertIsNotNone(new)
            self.assertEqual(gate.scan(new), set())

    def test_unknown_webp_profile_is_refused(self) -> None:
        data = webp_with_profile(0x20, PROFILE)
        self.assertIn("WebP ICC profile not a known profile", gate.scan(data))
        self.assertIsNone(normalizer.normalize_bytes(data))


class Fields(unittest.TestCase):
    def test_jfif_out_of_its_values_is_restated(self) -> None:
        data = jpeg_with(fuzz.jpeg_segment(0xE0, fuzz.bend(fuzz.JFIF, 8, b"\x00\x48")))
        self.assertTrue(gate.scan(data))
        new = normalizer.normalize_bytes(data)
        self.assertIsNotNone(new)
        self.assertEqual(gate.scan(new), set())
        self.assertIn(gate.JFIF_FIELDS, new)

    def test_real_jfif_values_pass(self) -> None:
        for version, units, density in (
            (b"\x01\x02", 1, b"\x00\x48"),
            (b"\x01\x00", 2, b"\x00\x00"),
        ):
            fields = (
                fuzz.JFIF[:5] + version + bytes((units,)) + density * 2 + b"\x00\x00"
            )
            self.assertEqual(
                gate.scan(jpeg_with(fuzz.jpeg_segment(0xE0, fields))), set()
            )

    def test_adobe_flags_are_cleared_and_transform_kept(self) -> None:
        data = jpeg_with(fuzz.jpeg_segment(0xEE, fuzz.bend(fuzz.ADOBE, 7, b"\x40\x00")))
        new = normalizer.normalize_bytes(data)
        self.assertIsNotNone(new)
        self.assertEqual(gate.scan(new), set())
        self.assertIn(fuzz.ADOBE, new)

    def test_adobe_transform_out_of_its_values_is_refused(self) -> None:
        data = jpeg_with(fuzz.jpeg_segment(0xEE, fuzz.bend(fuzz.ADOBE, 11, b"\x09")))
        self.assertTrue(gate.scan(data))
        self.assertIsNone(normalizer.normalize_bytes(data))

    def test_exif_values_in_range_pass(self) -> None:
        for value in range(1, 9):
            entry = (0x0112, 3, 1, struct.pack("<H", value))
            self.assertEqual(
                gate.scan(jpeg_with(fuzz.exif_ifd_segment([entry]))), set()
            )
        versions = [(0x9000, 7, 4, b"0232"), (0xA000, 7, 4, b"0100")]
        self.assertEqual(gate.scan(jpeg_with(fuzz.exif_ifd_segment(versions))), set())

    def test_zero_exif_pad_byte_passes(self) -> None:
        entries = [fuzz.ORIENTATION, (0x0132, 2, 20, fuzz.DATE)]
        segment = fuzz.exif_ifd_segment(entries, b"\x00")
        self.assertEqual(gate.scan(jpeg_with(segment)), set())

    def test_zero_webp_pad_byte_passes(self) -> None:
        self.assertEqual(gate.scan(fuzz.webp_fixture()), set())


if __name__ == "__main__":
    unittest.main()
