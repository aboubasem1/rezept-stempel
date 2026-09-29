# Rezept-Stempel.pyw — Doppelklick ohne Konsolenfenster (pythonw).
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from rezept_stempel.app import main

if __name__ == "__main__":
    raise SystemExit(main())
