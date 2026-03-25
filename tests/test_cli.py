"""Tests for the svblock CLI."""

from __future__ import annotations

import tempfile
from pathlib import Path

from svblock.cli import main


def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


class TestCLIVersion:
    def test_version_flag(self, capsys: object) -> None:
        try:
            main(["--version"])
        except SystemExit:
            pass


class TestCLIListModules:
    def test_list_modules(self, capsys: object) -> None:
        result = main([
            str(fixtures_dir() / "multi_module.sv"),
            "--list-modules",
        ])
        assert result == 0
        captured = capsys.readouterr()  # type: ignore[attr-defined]
        assert "mod_a" in captured.out
        assert "mod_b" in captured.out


class TestCLIRender:
    def test_render_svg(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.svg"
            result = main([
                str(fixtures_dir() / "simple_module.sv"),
                "-o", str(out),
            ])
            assert result == 0
            assert out.exists()
            content = out.read_text(encoding="utf-8")
            assert "<svg" in content
            assert "simple" in content

    def test_render_specific_module(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "mod_b.svg"
            result = main([
                str(fixtures_dir() / "multi_module.sv"),
                "-m", "mod_b",
                "-o", str(out),
            ])
            assert result == 0
            content = out.read_text(encoding="utf-8")
            assert "mod_b" in content

    def test_render_with_theme(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "dark.svg"
            result = main([
                str(fixtures_dir() / "simple_module.sv"),
                "--theme", "dark",
                "-o", str(out),
            ])
            assert result == 0
            content = out.read_text(encoding="utf-8")
            assert "#1e1e2e" in content

    def test_render_no_params(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.svg"
            result = main([
                str(fixtures_dir() / "params.sv"),
                "--no-params",
                "-o", str(out),
            ])
            assert result == 0

    def test_render_no_groups(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.svg"
            result = main([
                str(fixtures_dir() / "simple_module.sv"),
                "--no-groups",
                "-o", str(out),
            ])
            assert result == 0

    def test_render_no_decorators(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.svg"
            result = main([
                str(fixtures_dir() / "simple_module.sv"),
                "--no-decorators",
                "-o", str(out),
            ])
            assert result == 0

    def test_custom_width(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.svg"
            result = main([
                str(fixtures_dir() / "simple_module.sv"),
                "--width", "500",
                "-o", str(out),
            ])
            assert result == 0

    def test_sphinx_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "out.svg"
            result = main([
                str(fixtures_dir() / "simple_module.sv"),
                "--sphinx",
                "-o", str(out),
            ])
            assert result == 0
            content = out.read_text(encoding="utf-8")
            assert "xmlns" not in content


class TestCLIErrors:
    def test_file_not_found(self) -> None:
        result = main(["nonexistent.sv"])
        assert result == 1

    def test_module_not_found(self) -> None:
        result = main([
            str(fixtures_dir() / "simple_module.sv"),
            "-m", "nonexistent",
        ])
        assert result == 1

    def test_no_input_files(self) -> None:
        result = main([])
        assert result == 1

    def test_unsupported_format(self) -> None:
        result = main([
            str(fixtures_dir() / "simple_module.sv"),
            "-f", "png",
        ])
        assert result == 1
