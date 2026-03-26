from __future__ import annotations

import importlib.util
from pathlib import Path


def main() -> None:
    """Run ACN Agent with python3 acn_agent.py."""
    package_main = Path(__file__).resolve().parent / "acn_agent" / "main.py"
    spec = importlib.util.spec_from_file_location("acn_agent_package_main", package_main)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load acn_agent/main.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()


if __name__ == "__main__":
    main()
