"""Tests for the free values check-media-metadata.py pins, every value in them constructed."""

import contextlib
import importlib.util
import io
import pathlib
import random
import shutil
import struct
import subprocess
import tempfile
import unittest
import zipfile
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


def span(data: bytes, name: bytes) -> tuple[int, int]:
    return next((s, e) for c, s, e in gate.png_parts(data)[0] if c == name)


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


def ico_of(*images: bytes, bits: int = 8, tail: bytes = b"") -> bytes:
    """An icon holding each image in turn, its directory naming a 1x1 picture."""
    start = 6 + 16 * len(images)
    entries = b""
    for image in images:
        entries += struct.pack("<BBBBHHII", 1, 1, 0, 0, 1, bits, len(image), start)
        start += len(image)
    head = gate.ICO_HEADER + struct.pack("<H", len(images))
    return head + entries + b"".join(images) + tail


def text_chunk() -> bytes:
    return fuzz.png_chunk(b"tEXt", b"Author\x00someone")


def iso_with_title() -> bytes:
    """A file the gate reads as a video, holding a user data box it does not admit."""

    def box(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", 8 + len(body)) + kind + body

    return box(b"ftyp", b"isom\x00\x00\x02\x00isom") + box(b"udta", b"")


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

    def test_png_refused_for_its_structure_is_not_inflated(self) -> None:
        data = fuzz.png_fixture()
        signature, ihdr, end = data[:8], data[8:33], data[-12:]
        idat = data[slice(*span(data, b"IDAT"))]
        palette = fuzz.palette_png_fixture()
        plte = palette[slice(*span(palette, b"PLTE"))]
        twice = palette.replace(plte, plte * 2)
        with mock.patch.object(gate.zlib, "decompressobj") as inflate:
            self.assertEqual(
                gate.scan(signature + idat + ihdr + end),
                {"PNG IHDR not the first chunk"},
            )
            self.assertIsNone(normalizer.normalize_bytes(twice))
        inflate.assert_not_called()
        # A stream fault beside a droppable chunk is still named, since it is why the normalizer refuses.
        start, stop = span(data, b"IDAT")
        cut = fuzz.png_chunk(b"IDAT", data[start + 8 : stop - 8])
        text = fuzz.png_chunk(b"tEXt", b"Comment\x00planted")
        bent = data[:start] + cut + text + data[stop:]
        self.assertEqual(
            gate.scan(bent),
            {"PNG tEXt chunk", "PNG IDAT stream cut off before its end"},
        )
        self.assertIsNone(normalizer.normalize_bytes(bent))

    def test_png_missing_critical_chunk_is_refused(self) -> None:
        data = fuzz.png_fixture()
        signature, ihdr, end = data[:8], data[8:33], data[-12:]
        idat = data[slice(*span(data, b"IDAT"))]
        palette = fuzz.palette_png_fixture()
        first, last = span(palette, b"PLTE")
        for problem, bent in (
            ("PNG without IHDR", signature + idat + end),
            ("PNG IHDR not the first chunk", signature + idat + ihdr + end),
            ("PNG without IDAT", signature + ihdr + end),
            ("PNG palette image without PLTE", palette[:first] + palette[last:]),
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

    def test_png_side_past_libpng_limit_is_refused(self) -> None:
        limit = gate.PNG_SIDE_LIMIT
        for width, height in ((limit + 1, 1), (1, limit + 1)):
            header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
            data = fuzz.png_fixture()
            bent = data[:8] + fuzz.png_chunk(b"IHDR", header) + data[33:]
            self.assertEqual(gate.scan(bent), {"PNG IHDR side past libpng's limit"})
            self.assertIsNone(normalizer.normalize_bytes(bent))
        header = struct.pack(">IIBBBBB", limit, 1, 8, 0, 0, 0, 0)
        rows = fuzz.png_chunk(b"IDAT", zlib.compress(bytes(limit + 1)))
        data = fuzz.png_fixture()
        start, end = span(data, b"IDAT")
        wide = data[:8] + fuzz.png_chunk(b"IHDR", header) + data[33:start] + rows
        self.assertEqual(gate.scan(wide + data[end:]), set())

    def test_png_picture_past_the_size_limit_is_refused_before_inflating(self) -> None:
        side = gate.PNG_SIDE_LIMIT // 10
        header = struct.pack(">IIBBBBB", side, side, 8, 0, 0, 0, 0)
        self.assertGreater(gate.png_picture_size(header), gate.SIZE_LIMIT)
        data = fuzz.png_fixture()
        bent = data[:8] + fuzz.png_chunk(b"IHDR", header) + data[33:]
        with mock.patch.object(gate.zlib, "decompressobj") as inflate:
            self.assertEqual(
                gate.scan(bent), {"PNG IHDR picture larger than the gate inflates"}
            )
        inflate.assert_not_called()
        self.assertIsNone(normalizer.normalize_bytes(bent))

    def test_png_interlaced_size_sums_its_adam7_passes(self) -> None:
        header = struct.pack(">IIBBBBB", 8, 8, 8, 0, 0, 0, 1)
        # Passes of 1x1, 1x1, 2x1, 2x2, 4x2, 4x4 and 8x4 pixels, each row opening with a filter byte.
        self.assertEqual(gate.png_picture_size(header), 2 + 2 + 3 + 6 + 10 + 20 + 36)
        self.assertEqual(gate.png_picture_size(header[:12] + b"\x00"), 8 * 9)
        # A pass with no pixels holds no rows, so a 1x1 picture holds the first pass alone.
        one = struct.pack(">IIBBBBB", 1, 1, 8, 0, 0, 0, 1)
        self.assertEqual(gate.png_picture_size(one), 2)
        # At one bit a sample, 5x3 passes of 1x1, 1x1, 1x1, 3x1, 2x2 and 5x1 pixels each fit a byte a row.
        small = struct.pack(">IIBBBBB", 5, 3, 1, 0, 0, 0, 1)
        self.assertEqual(gate.png_picture_size(small), 2 + 2 + 2 + 2 + 4 + 2)
        self.assertEqual(gate.png_picture_size(small[:12] + b"\x00"), 3 * 2)

    def test_png_picture_data_not_one_whole_stream_is_refused(self) -> None:
        data = fuzz.png_fixture()
        start, end = span(data, b"IDAT")
        stream = data[start + 8 : end - 4]
        rows = zlib.decompress(stream)
        for problem, bodies in (
            ("PNG IDAT stream cut off before its end", [b""]),
            ("PNG IDAT not a valid zlib stream", [b"planted"]),
            ("PNG bytes after the end of the IDAT stream", [stream + b"\x00"]),
            ("PNG bytes after the end of the IDAT stream", [stream, b"\x00"]),
            ("PNG IDAT stream cut off before its end", [stream[:-4]]),
            ("PNG IDAT inflates past what IHDR needs", [zlib.compress(rows + b"\x00")]),
            ("PNG IDAT inflates short of what IHDR needs", [zlib.compress(rows[:-1])]),
            (
                "PNG IDAT row filter type not a defined one",
                [zlib.compress(b"\x05" + rows[1:])],
            ),
        ):
            idat = b"".join(fuzz.png_chunk(b"IDAT", body) for body in bodies)
            bent = data[:start] + idat + data[end:]
            self.assertEqual(gate.scan(bent), {problem})
            self.assertIsNone(normalizer.normalize_bytes(bent))
        # A stream split across chunks at any byte is still one stream.
        split = [stream[:1], stream[1:3], stream[3:]]
        whole = b"".join(fuzz.png_chunk(b"IDAT", body) for body in split)
        self.assertEqual(gate.scan(data[:start] + whole + data[end:]), set())
        text = fuzz.png_chunk(b"tEXt", b"Comment\x00planted")
        parted = fuzz.png_chunk(b"IDAT", split[0]) + text
        parted += fuzz.png_chunk(b"IDAT", b"".join(split[1:]))
        bent = data[:start] + parted + data[end:]
        self.assertIn("PNG IDAT chunks not consecutive", gate.scan(bent))
        self.assertIsNone(normalizer.normalize_bytes(bent))

    def test_png_end_with_a_body_is_emptied(self) -> None:
        data = fuzz.png_fixture()
        self.assert_restated(data[:-12] + fuzz.png_chunk(b"IEND", b"\x00"), data)

    def test_png_chunk_whose_crc_is_not_its_own_is_dropped_or_refused(self) -> None:
        data = fuzz.png_fixture()
        self.assert_restated(data[:-4] + bytes(4), data)
        start, end = span(data, b"gAMA")
        bent = data[: end - 4] + bytes(4) + data[end:]
        self.assert_restated(bent, data[:start] + data[end:])
        end = span(data, b"IHDR")[1]
        bent = data[: end - 4] + bytes(4) + data[end:]
        self.assertIn("PNG IHDR CRC not its chunk's", gate.scan(bent))
        self.assertIsNone(normalizer.normalize_bytes(bent))

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


class Sites(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.root = pathlib.Path(self._dir.name).resolve()
        patch = mock.patch.object(gate, "REPO", self.root)
        patch.start()
        self.addCleanup(patch.stop)

    def key(self, name: str) -> str:
        return str(pathlib.Path("sites", "example.test", name))

    def found(self, name: str, data: bytes) -> dict[str, set[str]]:
        path = self.root / "sites" / "example.test" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return dict(gate.findings())

    def test_site_png_holding_text_is_reported(self) -> None:
        found = self.found("og-image.png", png_with(text_chunk()))
        self.assertIn(self.key("og-image.png"), found)

    def test_site_png_named_otherwise_is_still_read(self) -> None:
        found = self.found("og-image.bin", png_with(text_chunk()))
        self.assertIn(self.key("og-image.bin"), found)

    def test_site_markup_is_left_alone(self) -> None:
        self.assertEqual(self.found("index.html", b"<!doctype html>"), {})

    def test_site_script_reading_as_an_iso_box_is_left_alone(self) -> None:
        self.assertEqual(self.found("site.js", b"let wide = matchMedia('');"), {})

    def test_site_video_by_a_name_outside_the_text_is_read(self) -> None:
        found = self.found("clip.m4a", b"let wide = matchMedia('');")
        self.assertIn(self.key("clip.m4a"), found)

    def test_site_video_under_a_text_name_is_read(self) -> None:
        found = self.found("notes.txt", b"\x00\x00\x00\x08ftyp\xa9")
        self.assertIn(self.key("notes.txt"), found)

    def test_png_named_as_an_icon_is_judged_as_a_png(self) -> None:
        found = self.found("favicon.ico", png_with(text_chunk()))
        self.assertNotIn("unrecognized container", found[self.key("favicon.ico")])

    def test_normalizer_judges_a_site_file_by_the_site_rule(self) -> None:
        page = self.root / "sites" / "example.test" / "index.html"
        loose = self.root / "static" / "media" / "index.html"
        with mock.patch.object(normalizer, "REPO", self.root):
            self.assertEqual(normalizer.judge(page, b"<!doctype html>"), set())
            self.assertTrue(normalizer.judge(loose, b"<!doctype html>"))

    def test_icon_reading_as_an_iso_box_is_read(self) -> None:
        found = self.found("favicon.ico", gate.ICO_HEADER + b"free" + bytes(20))
        self.assertEqual(found[self.key("favicon.ico")], {"ICO directory cut off"})

    def test_binary_opening_like_an_icon_is_left_alone(self) -> None:
        self.assertEqual(self.found("table.bin", gate.ICO_HEADER + bytes(60)), {})

    def test_normalizer_names_an_icon_it_cannot_clean(self) -> None:
        held = self.root / "icons.zip"
        with zipfile.ZipFile(held, "w") as archive:
            archive.writestr("favicon.ico", ico_of(png_with(text_chunk())))
        with contextlib.redirect_stdout(io.StringIO()) as out:
            normalizer.normalize_archive(held, False)
        self.assertIn("icons.zip!favicon.ico: ICO entry 0: ", out.getvalue())

    def test_normalizer_never_sends_an_icon_to_ffmpeg(self) -> None:
        data = gate.ICO_HEADER + b"free" + bytes(20)
        icon = self.root / "favicon.ico"
        icon.write_bytes(data)
        argv = ["normalize-media.py", str(icon)]
        with (
            mock.patch.object(normalizer.shutil, "which", return_value="ffmpeg"),
            mock.patch.object(normalizer.sys, "argv", argv),
            contextlib.redirect_stdout(io.StringIO()) as out,
        ):
            member = normalizer.normalize_member(data, ".ico")
            normalizer.main()
        self.assertIsNone(member)
        self.assertIn("favicon.ico: needs a re-encode", out.getvalue())

    def test_normalizer_skips_a_missing_default_root(self) -> None:
        held = self.root / "static" / "media" / "held.png"
        held.parent.mkdir(parents=True)
        held.write_bytes(png_with(text_chunk()))
        with (
            mock.patch.object(normalizer, "REPO", self.root),
            mock.patch.object(normalizer.sys, "argv", ["normalize-media.py"]),
            contextlib.redirect_stdout(io.StringIO()) as out,
        ):
            self.assertEqual(normalizer.main(), 0)
        self.assertIn("1 file(s) to normalize", out.getvalue())

    def test_normalizer_names_a_dangling_default_root(self) -> None:
        try:
            (self.root / "sites").symlink_to(self.root / "gone")
        except OSError as exc:
            self.skipTest(f"symlinks need a privilege here: {exc}")
        with (
            mock.patch.object(normalizer, "REPO", self.root),
            mock.patch.object(normalizer.sys, "argv", ["normalize-media.py"]),
            contextlib.redirect_stdout(io.StringIO()) as out,
        ):
            self.assertEqual(normalizer.main(), 0)
        self.assertIn("sites: symlink, not followed", out.getvalue())

    def link(self, name: str, target: pathlib.Path) -> pathlib.Path:
        """A symlink under the scratch repository, or a skip where one needs a privilege."""
        link = self.root / name
        link.parent.mkdir(parents=True, exist_ok=True)
        try:
            link.symlink_to(target)
        except OSError as exc:
            self.skipTest(f"symlinks need a privilege here: {exc}")
        return link

    def outside(self) -> pathlib.Path:
        """A directory outside the scratch repository, holding a PNG the gate fails."""
        held = tempfile.TemporaryDirectory()
        self.addCleanup(held.cleanup)
        target = pathlib.Path(held.name).resolve()
        (target / "held.png").write_bytes(png_with(text_chunk()))
        return target

    def normalize(self, *argv: str) -> str:
        args = ["normalize-media.py", *argv]
        with (
            mock.patch.object(normalizer, "REPO", self.root),
            mock.patch.object(normalizer.sys, "argv", args),
            contextlib.redirect_stdout(io.StringIO()) as out,
        ):
            self.assertEqual(normalizer.main(), 0)
        return out.getvalue()

    def test_symlinked_tree_is_named_and_not_read(self) -> None:
        self.link("static/media", self.outside())
        self.assertEqual(dict(gate.findings()), {"static/media": {"symlink, not read"}})

    def test_dangling_symlinked_tree_is_named(self) -> None:
        self.link("sites", self.root / "gone")
        self.assertEqual(gate.findings(), [("sites", {"symlink, not read"})])

    def test_file_at_a_tree_name_is_left_alone_by_both(self) -> None:
        (self.root / "sites").write_bytes(png_with(text_chunk()))
        self.assertEqual(gate.findings(), [])
        self.assertIn("0 file(s) to normalize", self.normalize())

    def test_tree_under_a_symlinked_directory_is_named_and_not_read(self) -> None:
        target = self.outside()
        (target / "media").mkdir()
        (target / "media" / "held.png").write_bytes(png_with(text_chunk()))
        self.link("static", target)
        self.assertEqual(gate.findings(), [("static/media", {"symlink, not read"})])

    def seeds(self) -> list[str]:
        """The carried seeds the fuzzer samples from the scratch repository."""
        with (
            mock.patch.object(fuzz, "REPO", self.root),
            mock.patch.object(fuzz.gate, "REPO", self.root),
        ):
            seeds = fuzz.carried_seeds(random.Random(0), 9, 1 << 20)
        return [name for name, _ in seeds]

    def test_fuzzer_samples_a_real_tree(self) -> None:
        held = self.root / "static" / "media" / "held.png"
        held.parent.mkdir(parents=True)
        held.write_bytes(png_with(text_chunk()))
        self.assertEqual(
            self.seeds(), [str(pathlib.Path("static", "media", "held.png"))]
        )

    def test_fuzzer_does_not_sample_a_symlinked_root(self) -> None:
        self.link("sites", self.outside())
        self.assertEqual(self.seeds(), [])

    def test_fuzzer_does_not_sample_a_root_under_a_symlink(self) -> None:
        target = self.outside()
        (target / "media").mkdir()
        (target / "media" / "held.png").write_bytes(png_with(text_chunk()))
        self.link("static", target)
        self.assertEqual(self.seeds(), [])

    def test_normalizer_does_not_follow_a_symlinked_root(self) -> None:
        target = self.outside()
        before = (target / "held.png").read_bytes()
        self.link("static/media", target)
        out = self.normalize("--apply")
        self.assertIn("static/media: symlink, not followed", out)
        self.assertIn("0 file(s) normalized", out)
        self.assertEqual((target / "held.png").read_bytes(), before)

    def test_normalizer_does_not_follow_a_named_root_under_a_symlink(self) -> None:
        target = self.outside()
        before = (target / "held.png").read_bytes()
        self.link("static", target)
        out = self.normalize("--apply", str(self.root / "static" / "held.png"))
        self.assertIn("held.png: symlink, not followed", out)
        self.assertEqual((target / "held.png").read_bytes(), before)

    def swapped(self, swap: pathlib.Path, target: pathlib.Path) -> str:
        """Apply the normalizer with `swap` turned into a link once the walk has run."""
        judge = normalizer.judge

        def late(path: pathlib.Path, data: bytes) -> set[str]:
            shutil.rmtree(swap) if swap.is_dir() else swap.unlink()
            try:
                swap.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symlinks need a privilege here: {exc}")
            return judge(path, data)

        with mock.patch.object(normalizer, "judge", late):
            return self.normalize("--apply")

    def test_normalizer_refuses_a_file_swapped_for_a_symlink_after_the_walk(
        self,
    ) -> None:
        target = self.outside()
        before = (target / "held.png").read_bytes()
        held = self.root / "static" / "media" / "held.png"
        held.parent.mkdir(parents=True)
        held.write_bytes(png_with(text_chunk()))
        out = self.swapped(held, target / "held.png")
        self.assertIn("held.png: symlink, not followed", out)
        self.assertIn("0 file(s) normalized", out)
        self.assertEqual((target / "held.png").read_bytes(), before)

    def test_normalizer_refuses_a_directory_swapped_for_a_symlink_after_the_walk(
        self,
    ) -> None:
        target = self.outside()
        before = (target / "held.png").read_bytes()
        held = self.root / "static" / "media" / "sub" / "held.png"
        held.parent.mkdir(parents=True)
        held.write_bytes(png_with(text_chunk()))
        out = self.swapped(held.parent, target)
        self.assertIn("held.png: symlink, not followed", out)
        self.assertEqual((target / "held.png").read_bytes(), before)

    def test_replacing_a_symlink_leaves_its_target_alone(self) -> None:
        target = self.outside()
        before = (target / "held.png").read_bytes()
        held = self.link("static/media/held.png", target / "held.png")
        with normalizer.replacing(held) as stream:
            stream.write(b"new")
        self.assertFalse(held.is_symlink())
        self.assertEqual(held.read_bytes(), b"new")
        self.assertEqual((target / "held.png").read_bytes(), before)

    def test_path_through_an_alias_of_the_repository_is_still_checked(self) -> None:
        target = self.outside()
        self.link("static/media/linked", target)
        alias = self.outside() / "alias"
        try:
            alias.symlink_to(self.root)
        except OSError as exc:
            self.skipTest(f"symlinks need a privilege here: {exc}")
        named = alias / "static" / "media" / "linked" / "held.png"
        self.assertTrue(gate.symlinked(named))
        self.assertFalse(gate.symlinked(alias / "static" / "media"))

    def test_normalizer_keeps_the_mode_of_a_file_it_rewrites(self) -> None:
        held = self.root / "static" / "media" / "held.png"
        held.parent.mkdir(parents=True)
        held.write_bytes(png_with(text_chunk()))
        held.chmod(0o640)
        self.normalize("--apply")
        self.assertEqual(gate.scan(held.read_bytes()), set())
        self.assertEqual(held.stat().st_mode & 0o777, 0o640)
        self.assertEqual(list(held.parent.iterdir()), [held])

    def test_normalizer_reports_a_video_ffmpeg_cannot_write_as_a_re_encode(
        self,
    ) -> None:
        held = self.root / "static" / "media" / "clip.txt"
        held.parent.mkdir(parents=True)
        held.write_bytes(iso_with_title())
        with (
            mock.patch.object(normalizer.shutil, "which", return_value="ffmpeg"),
            mock.patch.object(normalizer, "normalize_iso", return_value=False),
        ):
            out = self.normalize()
        self.assertIn("clip.txt: needs a re-encode", out)
        self.assertNotIn("would remove", out)

    @unittest.skipUnless(shutil.which("ffmpeg"), "needs ffmpeg")
    def test_report_and_apply_agree_on_what_ffmpeg_can_write(self) -> None:
        clip = self.root / "clip.mov"
        subprocess.run(
            [
                *("ffmpeg", "-loglevel", "error", "-f", "lavfi"),
                *("-i", "testsrc=duration=0.1:size=16x16:rate=10"),
                *("-c:v", "mpeg4", "-metadata", "title=example", str(clip)),
            ],
            check=True,
            timeout=60,
        )
        media = self.root / "static" / "media"
        media.mkdir(parents=True)
        for name in ("clip.mov", "clip.txt"):
            (media / name).write_bytes(clip.read_bytes())
        with contextlib.redirect_stderr(io.StringIO()):
            report, applied = self.normalize(), self.normalize("--apply")
        for out in (report, applied):
            self.assertIn("clip.txt: needs a re-encode", out)
            self.assertIn("1 file(s) ", out)
        self.assertIn("clip.mov: would remove ISO udta atom", report)
        self.assertIn("clip.mov: removed ISO udta atom", applied)
        self.assertEqual(gate.scan((media / "clip.mov").read_bytes()), set())

    def test_normalizer_reports_a_member_ffmpeg_cannot_write_as_a_re_encode(
        self,
    ) -> None:
        held = self.root / "clips.zip"
        with zipfile.ZipFile(held, "w") as archive:
            archive.writestr("clip.txt", iso_with_title())
        with (
            mock.patch.object(normalizer.shutil, "which", return_value="ffmpeg"),
            mock.patch.object(normalizer, "normalize_iso", return_value=False),
            contextlib.redirect_stdout(io.StringIO()) as out,
        ):
            self.assertEqual(normalizer.normalize_archive(held, False), [])
        self.assertIn(
            "clips.zip!clip.txt: ISO udta atom -> needs a re-encode", out.getvalue()
        )

    def test_icon_inside_an_archive_is_read(self) -> None:
        held = self.root / "held.zip"
        with zipfile.ZipFile(held, "w") as archive:
            archive.writestr("favicon.ico", ico_of(png_with(text_chunk())))
        found = self.found("icons.zip", held.read_bytes())
        self.assertIn(self.key("icons.zip") + "!favicon.ico", found)

    def test_large_icon_entry_states_its_side_as_zero(self) -> None:
        ihdr = fuzz.png_chunk(b"IHDR", struct.pack(">IIBBBBB", 512, 1, 8, 0, 0, 0, 0))
        idat = fuzz.png_chunk(b"IDAT", zlib.compress(bytes(513)))
        image = b"\x89PNG\r\n\x1a\n" + ihdr + idat + fuzz.png_chunk(b"IEND", b"")
        data = ico_of(image)
        wide = data[:6] + b"\x00" + data[7:]
        self.assertEqual(self.found("favicon.ico", wide), {})

    def test_clean_site_png_and_icon_pass(self) -> None:
        self.found("apple-touch-icon.png", fuzz.png_fixture())
        self.assertEqual(
            self.found("favicon.ico", ico_of(*[fuzz.png_fixture()] * 2)), {}
        )

    def test_icon_entry_holding_text_is_reported(self) -> None:
        found = self.found("favicon.ico", ico_of(png_with(text_chunk())))
        tags = found[self.key("favicon.ico")]
        self.assertTrue(all(tag.startswith("ICO entry 0: ") for tag in tags), tags)

    def test_icon_bytes_outside_its_entries_are_reported(self) -> None:
        found = self.found("favicon.ico", ico_of(fuzz.png_fixture(), tail=b"note"))
        self.assertEqual(
            found[self.key("favicon.ico")], {"ICO bytes past the last entry"}
        )

    def test_icon_entry_past_the_end_is_reported(self) -> None:
        data = ico_of(fuzz.png_fixture())
        found = self.found("favicon.ico", data[:-1])
        self.assertEqual(
            found[self.key("favicon.ico")],
            {"ICO entry 0 not where the last one ends"},
        )

    def test_icon_bytes_before_an_entry_are_reported(self) -> None:
        image = fuzz.png_fixture()
        entry = struct.pack("<BBBBHHII", 1, 1, 0, 0, 1, 8, len(image), 26)
        data = gate.ICO_HEADER + b"\x01\x00" + entry + b"note" + image
        found = self.found("favicon.ico", data)
        self.assertEqual(
            found[self.key("favicon.ico")],
            {"ICO entry 0 not where the last one ends"},
        )

    def test_icon_entry_not_a_png_is_reported(self) -> None:
        found = self.found("favicon.ico", ico_of(bytes(40)))
        self.assertEqual(found[self.key("favicon.ico")], {"ICO entry 0 not a PNG"})

    def test_icon_directory_disagreeing_with_its_image_is_reported(self) -> None:
        found = self.found("favicon.ico", ico_of(fuzz.png_fixture(), bits=32))
        self.assertEqual(
            found[self.key("favicon.ico")],
            {"ICO entry 0 directory not its image's own"},
        )

    def test_unrecognized_icon_is_reported(self) -> None:
        found = self.found("favicon.ico", b"not an icon")
        self.assertEqual(found[self.key("favicon.ico")], {"unrecognized container"})


if __name__ == "__main__":
    unittest.main()
