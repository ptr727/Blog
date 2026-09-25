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


def truecolor_png(chunks: bytes) -> bytes:
    ihdr = fuzz.png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = fuzz.png_chunk(b"IDAT", zlib.compress(bytes(4)))
    end = fuzz.png_chunk(b"IEND", b"")
    return b"\x89PNG\r\n\x1a\n" + ihdr + chunks + idat + end


def iccp(name: bytes, stream: bytes) -> bytes:
    return fuzz.png_chunk(b"iCCP", name + b"\x00\x00" + stream)


def webp_with_profile(flags: int, profile: bytes) -> bytes:
    body = fuzz.riff_chunk(b"VP8X", bytes((flags,)) + bytes(9))
    body += fuzz.riff_chunk(b"ICCP", profile)
    body += fuzz.riff_chunk(b"VP8L", b"\x2f\x00\x00\x00\x00")
    return b"RIFF" + struct.pack("<I", len(body) + 4) + b"WEBP" + body


class Profiles(unittest.TestCase):
    def test_known_jpeg_profile_passes_as_one_chunk(self) -> None:
        segment = fuzz.jpeg_segment(0xE2, fuzz.ICC + PROFILE)
        with known():
            self.assertEqual(gate.scan(jpeg_with(segment)), set())

    def test_known_jpeg_profile_in_other_chunks_is_recut(self) -> None:
        with known():
            for order in ((1, 2), (2, 1)):
                data = jpeg_with(*icc_chunks(PROFILE, order))
                self.assertEqual(
                    gate.scan(data), {"JPEG ICC profile not in its canonical chunks"}
                )
                new = normalizer.normalize_bytes(data)
                self.assertIsNotNone(new)
                self.assertEqual(gate.scan(new), set())
                self.assertIn(fuzz.ICC + PROFILE, new)

    def test_jpeg_profile_after_the_scan_is_refused(self) -> None:
        first, second = icc_chunks(PROFILE, (1, 2))
        whole = fuzz.jpeg_segment(0xE2, fuzz.ICC + PROFILE)
        with known():
            for before, after in (([first], second), ([], whole)):
                data = jpeg_with(*before)
                data = data[:-2] + after + data[-2:]
                self.assertIn("JPEG ICC chunk after the first scan", gate.scan(data))
                self.assertIsNone(normalizer.normalize_bytes(data))

    def test_unknown_jpeg_profile_is_refused(self) -> None:
        data = jpeg_with(*icc_chunks(PROFILE, (1, 2)))
        self.assertIn("JPEG ICC profile not a known profile", gate.scan(data))
        self.assertIsNone(normalizer.normalize_bytes(data))

    def test_known_png_profile_in_its_canonical_body_passes(self) -> None:
        data = png_with(fuzz.png_chunk(b"iCCP", gate.png_icc_body(PROFILE)))
        with known():
            self.assertEqual(gate.scan(data), set())

    def test_known_png_profile_in_another_body_is_restated(self) -> None:
        for name, level in ((b"planted", 6), (b"icc", 9), (b"icc", 1)):
            data = png_with(iccp(name, zlib.compress(PROFILE, level)))
            with known():
                self.assertEqual(
                    gate.scan(data), {"PNG iCCP not in its canonical form"}
                )
                new = normalizer.normalize_bytes(data)
                self.assertIsNotNone(new)
                self.assertEqual(gate.scan(new), set())
                self.assertNotIn(b"planted", new)

    def test_png_bytes_past_the_stream_are_refused(self) -> None:
        data = png_with(iccp(b"icc", zlib.compress(PROFILE) + b"planted"))
        with known():
            self.assertIn("PNG ICC profile not a known profile", gate.scan(data))
            self.assertIsNone(normalizer.normalize_bytes(data))

    def test_webp_profile_flag_disagreeing_is_refused(self) -> None:
        with known():
            self.assertEqual(gate.scan(webp_with_profile(0x20, PROFILE)), set())
            data = webp_with_profile(0x00, PROFILE)
            self.assertEqual(
                gate.scan(data), {"WebP VP8X flags disagree with its chunks"}
            )
            self.assertIsNone(normalizer.normalize_bytes(data))

    def test_webp_reserved_bits_are_cleared(self) -> None:
        with known():
            data = webp_with_profile(0x20 | 0x01, PROFILE)
            self.assertEqual(gate.scan(data), {"WebP VP8X reserved bits not zero"})
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


class FreeValues(unittest.TestCase):
    def assert_restated(self, data: bytes, expected: bytes) -> None:
        self.assertTrue(gate.scan(data))
        new = normalizer.normalize_bytes(data)
        self.assertEqual(new, expected)
        self.assertEqual(gate.scan(new), set())

    def test_png_values_writers_use_pass(self) -> None:
        for chunk, body in (
            *((b"sRGB", bytes((intent,))) for intent in range(4)),
            *((b"cHRM", primaries) for primaries in gate.PNG_PRIMARIES),
            (b"pHYs", struct.pack(">IIB", 2835, 2835, 0)),
            (b"sBIT", b"\x08"),
            (b"bKGD", bytes(2)),
            (b"tRNS", struct.pack(">H", 255)),
        ):
            self.assertEqual(gate.scan(png_with(fuzz.png_chunk(chunk, body))), set())

    def test_png_undrawn_chunk_out_of_its_value_is_dropped(self) -> None:
        for chunk, body in ((b"sBIT", b"\x05"), (b"bKGD", b"\x00\x07")):
            self.assert_restated(
                png_with(fuzz.png_chunk(chunk, body)), fuzz.png_fixture()
            )

    def test_png_misplaced_chunk_is_dropped_or_refused(self) -> None:
        data = fuzz.png_fixture()
        late = fuzz.png_chunk(b"sBIT", b"\x08")
        self.assert_restated(data[:-12] + late + data[-12:], data)
        late = fuzz.png_chunk(b"pHYs", fuzz.SQUARE)
        data = data[:-12] + late + data[-12:]
        self.assertIn("PNG pHYs chunk out of place", gate.scan(data))
        self.assertIsNone(normalizer.normalize_bytes(data))

    def test_png_repeated_gamma_is_refused(self) -> None:
        data = png_with(fuzz.png_chunk(b"gAMA", struct.pack(">I", 45455)))
        self.assertIn("PNG repeated gAMA chunk", gate.scan(data))
        self.assertIsNone(normalizer.normalize_bytes(data))

    def test_png_repeated_palette_is_refused(self) -> None:
        palette = fuzz.png_chunk(b"PLTE", bytes(6))
        data = truecolor_png(palette * 2)
        self.assertIn("PNG repeated PLTE chunk", gate.scan(data))
        self.assertIsNone(normalizer.normalize_bytes(data))

    def test_png_animation_is_refused(self) -> None:
        data = fuzz.png_fixture()
        control = fuzz.png_chunk(b"acTL", struct.pack(">II", 1, 0))
        frame = fuzz.png_chunk(b"fdAT", bytes(4))
        header = struct.pack(">IIIIIHHBB", 0, 1, 1, 0, 0, 1, 1, 0, 0)
        region = fuzz.png_chunk(b"fcTL", header)
        for chunk, bent in (
            (b"acTL", png_with(control)),
            (b"fcTL", png_with(region)),
            (b"fdAT", data[:-12] + frame + data[-12:]),
        ):
            self.assertIn(f"PNG {chunk.decode()} chunk", gate.scan(bent))
            self.assertIsNone(normalizer.normalize_bytes(bent))

    def test_png_suggested_palette_goes_after_its_transparency(self) -> None:
        color_key = fuzz.png_chunk(b"tRNS", bytes(6))
        data = truecolor_png(color_key + fuzz.png_chunk(b"PLTE", bytes(6)))
        self.assertEqual(
            gate.scan(data), {"PNG PLTE fields not values its format defines"}
        )
        self.assert_restated(data, truecolor_png(color_key))

    def test_png_missing_critical_chunk_is_refused(self) -> None:
        data = fuzz.png_fixture()
        signature, ihdr, end = data[:8], data[8:33], data[-12:]
        idat = next(data[s:e] for c, s, e in gate.png_parts(data)[0] if c == b"IDAT")
        palette = fuzz.palette_png_fixture()
        for problem, bent in (
            ("PNG IHDR not the first chunk", signature + idat + end),
            ("PNG IHDR not the first chunk", signature + idat + ihdr + end),
            ("PNG without IDAT", signature + ihdr + end),
            ("PNG palette image without PLTE", palette[:33] + palette[51:]),
        ):
            self.assertIn(problem, gate.scan(bent))
            self.assertIsNone(normalizer.normalize_bytes(bent))

    def test_png_header_out_of_its_values_is_refused(self) -> None:
        good = struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 0)
        interlaced = good[:12] + b"\x01"
        for header in (
            good[:8] + b"\x10\x03" + good[10:],
            good[:8] + b"\x08\x05" + good[10:],
            good[:10] + b"\x01" + good[11:],
            good[:11] + b"\x01" + good[12:],
            good[:12] + b"\x02",
            bytes(4) + good[4:],
            good + b"\x00",
        ):
            data = fuzz.png_fixture()
            bent = data[:8] + fuzz.png_chunk(b"IHDR", header) + data[33:]
            self.assertIn(
                "PNG IHDR fields not values its format defines", gate.scan(bent)
            )
            self.assertIsNone(normalizer.normalize_bytes(bent))
        data = fuzz.png_fixture()
        self.assertEqual(
            gate.scan(data[:8] + fuzz.png_chunk(b"IHDR", interlaced) + data[33:]), set()
        )

    def test_png_end_with_a_body_is_emptied(self) -> None:
        data = fuzz.png_fixture()
        self.assert_restated(data[:-12] + fuzz.png_chunk(b"IEND", b"\x00"), data)

    def test_gif_unused_control_fields_are_zeroed(self) -> None:
        data = fuzz.gif_fixture()
        at = data.index(b"\x21\xf9") + 3
        bent = data[:at] + b"\xe0" + data[at + 1 : at + 3] + b"\x05" + data[at + 4 :]
        self.assert_restated(bent, data)

    def test_gif_aspect_ratio_is_zeroed(self) -> None:
        data = fuzz.gif_fixture()
        bent = data[:12] + b"\x31" + data[13:]
        self.assertIn("GIF aspect ratio not zero", gate.scan(bent))
        self.assert_restated(bent, data)

    def test_gif_unused_descriptor_fields_are_zeroed(self) -> None:
        data = fuzz.gif_fixture()
        at = data.index(b"\x2c") + 9
        for bent in (
            b"GIF87a" + data[6:],
            data[:10] + b"\xf8" + data[11:],
            data[:at] + b"\x3f" + data[at + 1 :],
        ):
            self.assert_restated(bent, data)

    def test_gif_unread_global_table_is_dropped(self) -> None:
        data = fuzz.gif_fixture()
        at = data.index(b"\x2c") + 9
        local = data[:at] + b"\x80" + bytes(6) + data[at + 1 :]
        self.assert_restated(local, data[:10] + bytes(3) + local[19:])

    def test_webp_background_is_zeroed_and_loop_count_kept(self) -> None:
        data = fuzz.animated_webp_fixture()
        at = data.index(b"ANIM") + 8
        looped = data[:at] + bytes(4) + b"\x03\x00" + data[at + 6 :]
        self.assertEqual(gate.scan(looped), set())
        bent = looped[:at] + b"\xff" * 4 + looped[at + 4 :]
        self.assert_restated(bent, looped)

    def test_jpeg_fill_before_a_marker_is_dropped(self) -> None:
        data = fuzz.jpeg_fixture(False)
        for at in (2, len(data) - 2):
            self.assert_restated(data[:at] + b"\xff" * 3 + data[at:], data)

    def test_jpeg_fill_inside_a_scan_is_refused(self) -> None:
        data = fuzz.jpeg_fixture(False).replace(b"\xff\xd0", b"\xff\xff\xd0")
        self.assertIn("JPEG fill bytes inside a scan", gate.scan(data))
        self.assertIsNone(normalizer.normalize_bytes(data))


if __name__ == "__main__":
    unittest.main()
