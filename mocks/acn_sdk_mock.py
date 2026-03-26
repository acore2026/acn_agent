from __future__ import annotations

import argparse
import json
from typing import Any

import httpx

from mocks.common import (
    PORTS,
    build_url,
    sample_agent_cards_request,
    sample_agent_deletion,
    sample_identity_application,
    sample_task_execution,
    sample_task_termination,
)


def send(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Send one request to ACN Agent and return the response."""
    with httpx.Client(timeout=10.0, trust_env=False) as client:
        response = client.post(build_url(PORTS.agent, path), json=payload)
    return {
        "status_code": response.status_code,
        "path": path,
        "request": payload,
        "response": response.json() if response.text else {},
    }


def execute_action(action: str) -> dict[str, Any]:
    """Run one ACN SDK mock action."""
    if action == "identity":
        return send("/idm/v1/identity-applications", sample_identity_application())
    if action == "cards":
        return send("/arf/v1/agent-cards", sample_agent_cards_request())
    if action == "execute":
        return send("/acn-agent/v1/task-executions", sample_task_execution())
    if action == "delete":
        return send("/acn-agent/v1/agent-deletions", sample_agent_deletion())
    if action == "terminate":
        return send("/acn-agent/v1/task-execution-terminations", sample_task_termination())
    if action == "clear":
        return send("/clear", {})
    raise ValueError(f"Unsupported action: {action}")


def run_demo() -> list[dict[str, Any]]:
    """Run the full demo flow."""
    return [
        execute_action("identity"),
        execute_action("cards"),
        execute_action("execute"),
        execute_action("terminate"),
        execute_action("delete"),
    ]


def main() -> None:
    """CLI entrypoint for the ACN SDK mock."""
    parser = argparse.ArgumentParser(description="ACN SDK mock client")
    parser.add_argument(
        "action",
        choices=["identity", "cards", "execute", "delete", "terminate", "clear", "demo"],
        help="Mock action to execute against ACN Agent",
    )
    args = parser.parse_args()
    result: Any = run_demo() if args.action == "demo" else execute_action(args.action)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
