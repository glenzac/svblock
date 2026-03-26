"""Tests for the Sphinx extension directive."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

# We test the directive logic without requiring Sphinx to be installed.
# The directive module imports from sphinx/docutils, so we mock those
# at the module level when needed.


def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


class TestSetup:
    def test_setup_returns_metadata(self) -> None:
        """setup() returns version and parallel-safety flags."""
        try:
            from svblock.sphinx_ext import setup
        except ImportError:
            pytest.skip("sphinx not installed")

        app = MagicMock()
        result = setup(app)
        assert "version" in result
        assert result["parallel_read_safe"] is True
        assert result["parallel_write_safe"] is True
        app.add_directive.assert_called_once()

    def test_setup_registers_directive(self) -> None:
        """setup() registers the 'svblock' directive."""
        try:
            from svblock.sphinx_ext.directive import SvblockDirective, setup
        except ImportError:
            pytest.skip("sphinx not installed")

        app = MagicMock()
        setup(app)
        app.add_directive.assert_called_once_with("svblock", SvblockDirective)


class TestDirectiveOptions:
    def test_option_spec_keys(self) -> None:
        """Directive declares expected option keys."""
        try:
            from svblock.sphinx_ext.directive import SvblockDirective
        except ImportError:
            pytest.skip("sphinx not installed")

        expected = {
            "module", "theme", "no-params",
            "no-groups", "no-decorators", "width",
        }
        assert set(SvblockDirective.option_spec.keys()) == expected

    def test_requires_one_argument(self) -> None:
        """Directive requires exactly 1 argument (file path)."""
        try:
            from svblock.sphinx_ext.directive import SvblockDirective
        except ImportError:
            pytest.skip("sphinx not installed")

        assert SvblockDirective.required_arguments == 1
