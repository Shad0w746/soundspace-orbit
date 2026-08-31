from pathlib import Path

import pytest

from soundspace_orbit.converter import OrbitSettings, _build_filter_graph, _safe_filename, is_url
from soundspace_orbit.version import __version__


def test_version_file_matches_package_version():
    assert Path("VERSION").read_text(encoding="utf-8").strip() == __version__


def test_versioned_settings_normalize_format_and_bounds():
    settings = OrbitSettings(cycle_seconds=0.2, depth=3.0, output_format=".WAV").normalized()

    assert settings.cycle_seconds == 1.0
    assert settings.depth == 0.95
    assert settings.output_format == "wav"


def test_filter_graph_exposes_orbit_output_label():
    graph = _build_filter_graph(OrbitSettings(cycle_seconds=8.0, depth=0.85, spatial_reverb=True))

    assert "[orbit]" in graph
    assert "sin(2*PI*t/8.0000)" in graph
    assert "aecho=" in graph


def test_url_detection():
    assert is_url("https://example.com/audio.mp3")
    assert not is_url(str(Path("track.mp3")))


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("My Song!.mp3", "My Song_.mp3"),
        ("   ...   ", "audio"),
    ],
)
def test_safe_filename(raw, expected):
    assert _safe_filename(raw) == expected
