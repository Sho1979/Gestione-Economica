"""Convenience entry point to execute the project's unit test suite.

This runner ensures the working directory is the project root so it can be
invoked from terminals that start elsewhere (e.g., Windows cmd or PowerShell).
It also performs a light dependency check so newcomers immediately understand
which packages must be installed before the tests can succeed."""
from __future__ import annotations

import os
import sys
import textwrap
import unittest
from pathlib import Path


REQUIRED_PACKAGES = ("pandas",)


def _check_dependencies() -> None:
    missing: list[str] = []
    for package in REQUIRED_PACKAGES:
        try:
            __import__(package)
        except ModuleNotFoundError:
            missing.append(package)

    if not missing:
        return

    command = "pip install " + " ".join(missing)
    message = textwrap.dedent(
        f"""
        Impossibile eseguire i test: non sono installati i seguenti pacchetti
        obbligatori: {', '.join(missing)}

        Installa le dipendenze richieste con:
            {command}

        Poi riesegui questo script.
        """
    ).strip()

    print(message)
    raise SystemExit(1)


def main() -> int:
    project_root = Path(__file__).resolve().parent
    os.chdir(project_root)

    _check_dependencies()

    loader = unittest.defaultTestLoader
    suite = loader.discover(start_dir=str(project_root / "Tests"))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
