#!/usr/bin/env python3
"""Fail on personal data in the text of a post outside the imported archive years.

The archive years are the ones `.github/prose-gate-excludes` lists, so the two gates
share one boundary. Every other Markdown file under `content/` is read whole, front
matter and code blocks included, because a configuration snippet is where a hardware
address or a station identifier is most likely to be pasted.

Each finding is printed as its file, line, and class, and never with the value. A log
that echoed the value would publish the thing the gate exists to keep out.

A value a post prints on purpose is declared in `checks/text-pii-allow.json`, with the
reason it is intended. An entry nothing matches is itself a failure, so the list only
ever holds values a post still prints.
"""

import argparse
import ipaddress
import json
import pathlib
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass

REPO = pathlib.Path(__file__).resolve().parent.parent
EXCLUDES = pathlib.Path(".github/prose-gate-excludes")
ALLOW = pathlib.Path("checks/text-pii-allow.json")
CONTENT = "content"

CLASSES = (
    "email",
    "hardware address",
    "public ip",
    "coordinates",
    "coordinate url",
    "instance url",
    "street address",
    "phone",
)

EMAIL = re.compile(
    r"(?<![\w.%+-])[\w.%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b"
)

# A retina asset name such as icon@2x.png has the shape of an address.
FILE_SUFFIXES = frozenset(("png", "jpg", "jpeg", "gif", "webp", "svg", "avif"))

# A label such as MAC: may touch the address, and a seventh separated group still reports the first six.
MAC = re.compile(
    r"(?<![0-9A-Za-z])(?:[0-9A-Fa-f]{2}([:-])(?:[0-9A-Fa-f]{2}\1){4}[0-9A-Fa-f]{2}"
    r"|[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4}\.[0-9A-Fa-f]{4})(?![0-9A-Za-z])"
)

IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w]|\.\d)")
# A four-part version number has the shape of an address.
VERSION_WORD = re.compile(
    r"\b(?:version|ver|v|build|driver|firmware|release)[\s:=]*$", re.IGNORECASE
)
IPV6 = re.compile(r"(?<![\w:.])(?:[0-9A-Fa-f]{0,4}:){2,7}[0-9A-Fa-f]{0,4}(?![\w:])")

# Three decimal places is about a hundred meters, which is a block rather than a city.
DECIMAL_PAIR = re.compile(
    r"(?<![\w.])([-+]?\d{1,3}\.\d{3,})\s*°?\s*([NSEW])?\s*([,/]|\s)\s*"
    r"([-+]?\d{1,3}\.\d{3,})\s*°?\s*([NSEW])?(?![\w.])"
)
COORDINATE_KEY = re.compile(
    r"(?<![A-Za-z])(?:lat|latitude|lon|lng|longitude)[\"']?\s*[:=\s]\s*[\"']?[-+]?\d{1,3}\.\d{3,}",
    re.IGNORECASE,
)
DMS = re.compile(
    r"\d{1,3}\s*°\s*\d{1,2}\s*['\u2032]\s*(?:\d{1,2}(?:\.\d+)?\s*[\"\u2033]\s*)?([NSEW])\b"
)

URL = re.compile(r"https?://[^\s)\]>\"'`]+", re.IGNORECASE)
COORDINATE_URL = re.compile(
    r"[?&#](?:lat|latitude|lon|lng|long|longitude|mlat|mlon)=[-+]?\d+\.\d{3,}"
    r"|[?&#](?:ll|sll|center|q|query|destination|daddr)=[-+]?\d+\.\d{3,}(?:,|%2C)[-+]?\d+\.\d{3,}"
    r"|@[-+]?\d+\.\d{3,},[-+]?\d+\.\d{3,}"
    r"|map=\d+/[-+]?\d+\.\d{3,}/[-+]?\d+\.\d{3,}",
    re.IGNORECASE,
)

# The service names a station, so the link locates whoever runs it.
INSTANCE_URL = re.compile(
    r"[?&#](?:sensor|sensors|sensor_id|sensorid|sensor_index|select|show|station|stations"
    r"|station_id|stationid|device|device_id|deviceid|pws|call|callsign)=\w"
    r"|wunderground\.com/(?:dashboard/pws|personal-weather-station)/"
    r"|purpleair\.com/.*\b(?:sensor|select|show)\b"
    r"|sensor\.community/.*\bsensor/\d"
    r"|(?:aqicn\.org|waqi\.info)/station/"
    r"|ambientweather\.net/dashboard/"
    r"|weathercloud\.net/.*\bd\d{6,}"
    r"|pwsweather\.com/station/"
    r"|opensensemap\.org/explore/"
    r"|aprs\.fi/(?:#!call=|info/)"
    r"|findu\.com/cgi-bin/",
    re.IGNORECASE,
)

STREET_SUFFIX = (
    r"(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Way"
    r"|Place|Pl|Terrace|Ter|Circle|Cir|Parkway|Pkwy|Highway|Hwy|Loop|Trail|Trl)"
)
STREET = re.compile(
    r"\b\d{1,6}[A-Za-z]?\s+(?:(?:N|S|E|W|NE|NW|SE|SW)\.?\s+)?"
    r"(?:(?:[A-Z][a-z]+|\d+(?:st|nd|rd|th))\.?\s+){1,4}" + STREET_SUFFIX + r"\b\.?"
    r"|\bP\.?\s?O\.?\s+Box\s+\d+",
)

NANP = re.compile(
    r"(?<![\w.+-])(?:\+?1[\s.-]?)?(?:\(\d{3}\)\s?|\d{3}[\s.-])\d{3}[\s.-]\d{4}(?![\w-])"
)
INTERNATIONAL = re.compile(r"(?<![\w+])\+\d[\d\s().-]{6,18}\d(?![\w-])")


@dataclass(frozen=True)
class Finding:
    """One identifier on one line, with the value kept only for allow-list matching."""

    path: str
    line: int
    kind: str
    value: str


def is_public(text: str) -> bool:
    """Whether an address parses and is globally routable, which the documentation ranges are not."""
    try:
        return ipaddress.ip_address(text).is_global
    except ValueError:
        return False


def is_coordinate(
    first: str, first_hemi: str | None, sep: str, second: str, second_hemi: str | None
) -> bool:
    """Whether two decimals read as a coordinate pair rather than two measurements."""
    if sep.isspace() and not (first_hemi and second_hemi):
        return False
    if (first_hemi and first.startswith(("-", "+"))) or (
        second_hemi and second.startswith(("-", "+"))
    ):
        return False
    a, b = abs(float(first)), abs(float(second))
    if first_hemi and second_hemi:
        if {first_hemi, second_hemi} not in (
            {"N", "E"},
            {"N", "W"},
            {"S", "E"},
            {"S", "W"},
        ):
            return False
        lat, lon = (a, b) if first_hemi in "NS" else (b, a)
        return lat <= 90 and lon <= 180
    if first_hemi or second_hemi:
        first_is_lat = first_hemi in "NS" if first_hemi else second_hemi in "EW"
        lat, lon = (a, b) if first_is_lat else (b, a)
        return lat <= 90 and lon <= 180
    if a <= 90 and b <= 180:
        return True
    # Longitude first is how GeoJSON writes a point, and a measurement rarely carries four places.
    places = min(len(first.split(".")[1]), len(second.split(".")[1]))
    return a <= 180 and b <= 90 and places >= 4


def scan_line(text: str) -> Iterator[tuple[str, str]]:
    """Yield each identifier on a line as its class and matched value."""
    for m in EMAIL.finditer(text):
        if m.group().rsplit(".", 1)[-1].lower() not in FILE_SUFFIXES:
            yield "email", m.group()
    for m in MAC.finditer(text):
        yield "hardware address", m.group()
    for m in IPV4.finditer(text):
        if is_public(m.group()) and not VERSION_WORD.search(text[: m.start()]):
            yield "public ip", m.group()
    for m in IPV6.finditer(text):
        if is_public(m.group()):
            yield "public ip", m.group()
    for m in DECIMAL_PAIR.finditer(text):
        if is_coordinate(*m.groups()):
            yield "coordinates", m.group()
    for m in COORDINATE_KEY.finditer(text):
        yield "coordinates", m.group()
    hemispheres = {m.group(1) for m in DMS.finditer(text)}
    if hemispheres & {"N", "S"} and hemispheres & {"E", "W"}:
        yield "coordinates", " ".join(m.group() for m in DMS.finditer(text))
    for m in URL.finditer(text):
        if COORDINATE_URL.search(m.group()):
            yield "coordinate url", m.group()
        if INSTANCE_URL.search(m.group()):
            yield "instance url", m.group()
    for m in STREET.finditer(text):
        yield "street address", m.group()
    for m in NANP.finditer(text):
        yield "phone", m.group()
    for m in INTERNATIONAL.finditer(text):
        if 8 <= sum(c.isdigit() for c in m.group()) <= 15:
            yield "phone", m.group()


def excluded_prefixes(root: pathlib.Path) -> tuple[str, ...]:
    """The archive boundary, read the way the prose gate reads it."""
    path = root / EXCLUDES
    if not path.is_file():
        return ()
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return tuple(line for line in lines if line and not line.startswith("#"))


def posts(root: pathlib.Path) -> list[pathlib.Path]:
    """Every Markdown file under content/ that the archive boundary leaves in scope."""
    excludes = excluded_prefixes(root)
    return sorted(
        p
        for p in (root / CONTENT).rglob("*.md")
        if p.is_file() and not p.relative_to(root).as_posix().startswith(excludes)
    )


def findings(root: pathlib.Path) -> list[Finding]:
    """Every identifier in scope, before the allow list is applied."""
    out = []
    for path in posts(root):
        name = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8").split("\n")
        for number, text in enumerate((line.rstrip("\r") for line in lines), 1):
            seen = set()
            for kind, value in scan_line(text):
                if (kind, value) not in seen:
                    seen.add((kind, value))
                    out.append(Finding(name, number, kind, value))
    return out


def load_allow(path: pathlib.Path) -> list[dict]:
    """The declared values, each checked for a known class, one matcher, and a reason."""
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("allow") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise SystemExit(f"{path}: needs an object with an allow list")
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise SystemExit(f"{path}: entry {index}: must be an object")
        if entry.get("class") not in CLASSES:
            raise SystemExit(
                f"{path}: entry {index}: class must be one of {', '.join(CLASSES)}"
            )
        if ("value" in entry) == ("pattern" in entry):
            raise SystemExit(
                f"{path}: entry {index}: needs exactly one of value or pattern"
            )
        if not all(
            isinstance(entry[k], str) for k in ("value", "pattern") if k in entry
        ):
            raise SystemExit(
                f"{path}: entry {index}: value and pattern must be strings"
            )
        if "pattern" in entry:
            try:
                re.compile(entry["pattern"])
            except re.error:
                raise SystemExit(
                    f"{path}: entry {index}: pattern does not compile"
                ) from None
        reason = entry.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            raise SystemExit(f"{path}: entry {index}: needs a reason")
    return entries


def allows(entry: dict, finding: Finding) -> bool:
    """Whether one declared entry covers one finding."""
    if entry["class"] != finding.kind:
        return False
    if "value" in entry:
        return entry["value"] == finding.value
    return re.fullmatch(entry["pattern"], finding.value) is not None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--root", type=pathlib.Path, default=REPO, help="repository root"
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()

    entries = load_allow(root / ALLOW)
    used = [False] * len(entries)
    reported = []
    for finding in findings(root):
        hits = [i for i, entry in enumerate(entries) if allows(entry, finding)]
        for i in hits:
            used[i] = True
        if not hits:
            reported.append(finding)

    for finding in reported:
        print(f"{finding.path}:{finding.line}: {finding.kind}")
    stale = [i for i, was_used in enumerate(used) if not was_used]
    for i in stale:
        print(
            f"{ALLOW.as_posix()}: entry {i} ({entries[i]['class']}) matches nothing in scope"
        )
    if reported or stale:
        advice = []
        if reported:
            advice.append("remove each value or declare it")
        if stale:
            advice.append("drop each unused entry")
        print(
            f"\nfindings: {len(reported)}, unused allow list entries: {len(stale)}."
            f" To fix, {' and '.join(advice)}, see CONTENT.md."
        )
        return 1
    print(f"text pii: {len(posts(root))} file(s) in scope, nothing undeclared")
    return 0


if __name__ == "__main__":
    sys.exit(main())
