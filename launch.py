"""PyInstaller-friendly entry point.

PyInstaller treats whatever script you point it at as the top-level
module, so the package's own ``__main__.py`` cannot use relative
imports like ``from .app import build_app`` — there's no parent
package anymore. This launcher sits one level above the
``stalcraft_helper`` package and uses an absolute import, which works
both for plain ``python launch.py`` and for the built ``.exe``.

For day-to-day development you can still use ``python -m stalcraft_helper``.
"""

from __future__ import annotations

import sys

from stalcraft_helper.app import build_app


def main() -> int:
    app, window = build_app()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
