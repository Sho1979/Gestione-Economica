"""Launch the Gestione Economica desktop application from any directory."""
from __future__ import annotations

import os
import sys
import textwrap
from pathlib import Path

REQUIRED_PACKAGES = ("pandas", "PySide6")


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
        Impossibile avviare l'applicazione: mancano i seguenti pacchetti
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

    app_entrypoint = project_root / "main.py"
    with app_entrypoint.open("rb") as handle:
        code = compile(handle.read(), str(app_entrypoint), "exec")
    exec_globals = {"__name__": "__main__", "__file__": str(app_entrypoint)}
    exec(code, exec_globals)
    return 0


if __name__ == "__main__":
    sys.exit(main())
