"""Lightweight install/runtime checks for CI and end-user validation."""

from __future__ import annotations

import importlib
import sys
import unittest


REQUIRED_MODULES = [
    "osgeo",
    "numpy",
    "pandas",
    "geopandas",
    "rasterio",
    "pyproj",
    "cv2",
    "pinginstaller",
    "pingwizard",
    "pingverter",
]


def _missing_required_modules() -> list[str]:
    """Return required modules that fail to import."""
    missing = []
    for mod_name in REQUIRED_MODULES:
        try:
            importlib.import_module(mod_name)
        except Exception:
            missing.append(mod_name)
    return missing


def run_self_check(verbose: bool = True) -> int:
    """Run dependency checks and unit tests. Returns process exit code."""
    print("\nPINGMapper self-check\n")

    missing = _missing_required_modules()
    if missing:
        print("Missing required modules:")
        for name in missing:
            print(f" - {name}")
        print("\nSelf-check failed: install appears incomplete.")
        return 1

    print("Dependency import checks passed.")

    suite = unittest.defaultTestLoader.loadTestsFromName("pingmapper.test_dq_filter")
    runner = unittest.TextTestRunner(verbosity=2 if verbose else 1)
    result = runner.run(suite)

    if not result.wasSuccessful():
        print("\nSelf-check failed: unit tests did not pass.")
        return 1

    print("\nSelf-check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(run_self_check())