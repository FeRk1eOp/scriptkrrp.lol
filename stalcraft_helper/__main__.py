"""Entry point — ``python -m stalcraft_helper`` opens the helper window."""

import sys

from .app import build_app


def main() -> int:
    app, window = build_app()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
