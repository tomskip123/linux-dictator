"""Allow running as python -m dictation."""

from .main import main

if __name__ == "__main__":
    raise SystemExit(main())
