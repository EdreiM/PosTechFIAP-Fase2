"""Configuração pytest — registra subpastas de src/ no sys.path."""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]
for _pasta in ("config", "ui", "llm", "genetic_algorithm_tsp"):
    _caminho = str(_SRC / _pasta)
    if _caminho not in sys.path:
        sys.path.insert(0, _caminho)
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
