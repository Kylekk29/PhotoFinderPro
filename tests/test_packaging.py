"""Packaging helpers: selftest and asset lookup (no window, synthetic data only)."""
import sys

from photofinder import app


def test_selftest_ok(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("TEMP", str(tmp_path))
    assert app.selftest() == 0
    assert "RESULT: OK" in (tmp_path / "photofinderpro_selftest.txt").read_text(encoding="utf-8")


def test_asset_path_exists_from_source():
    assert not getattr(sys, "frozen", False)
    assert app.asset_path("app.ico").is_file() and app.asset_path("app.png").is_file()
