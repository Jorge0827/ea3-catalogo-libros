"""Arranque de producción. Lee PORT, que inyecta el servicio de alojamiento."""

from __future__ import annotations

import os
import subprocess
import sys


def main() -> int:
    puerto = os.environ.get("PORT", "5000")
    if os.name == "nt":
        from app import app

        app.run(host="127.0.0.1", port=int(puerto), debug=False)
        return 0
    comando = [
        sys.executable,
        "-m",
        "gunicorn",
        "app:app",
        "--bind",
        f"0.0.0.0:{puerto}",
        "--workers",
        "1",
        "--timeout",
        "60",
    ]
    return subprocess.call(comando)


if __name__ == "__main__":
    raise SystemExit(main())
