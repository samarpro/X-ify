import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from service.server import build_parser  # noqa: E402


def test_loopback_only_host_rejected():
    parser = build_parser()
    args = parser.parse_args(["--host", "0.0.0.0"])

    with pytest.raises(ValueError):
        if args.host != "127.0.0.1":
            raise ValueError("Only loopback host 127.0.0.1 is allowed")
