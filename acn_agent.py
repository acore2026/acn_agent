from __future__ import annotations

import importlib


def main() -> None:
    """Run ACN Agent with python3 acn_agent.py."""
    module = importlib.import_module("acn_agent.main")
    module.main()


if __name__ == "__main__":
    main()
