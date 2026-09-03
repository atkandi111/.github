#!/usr/bin/env python3
"""Pure status decisions for the Atkandi Portfolio Project reconciler."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


def desired_status(item: dict[str, Any]) -> str | None:
    kind = item.get("kind")
    state = item.get("state")

    if kind == "PullRequest":
        if state == "MERGED" or item.get("merged_at"):
            return "Done"
        if state == "OPEN":
            if item.get("is_draft") or item.get("review_decision") == "CHANGES_REQUESTED":
                return "In Progress"
            return "For Review"
        if state == "CLOSED":
            return None
        raise ValueError(f"unexpected pull-request state for {item.get('url')}: {state}")

    if kind != "Issue":
        return None

    if state == "CLOSED":
        return "Done" if item.get("state_reason") == "COMPLETED" else None
    if state != "OPEN":
        raise ValueError(f"unexpected Issue state for {item.get('url')}: {state}")

    linked = item.get("linked_pull_requests") or []
    if item.get("state_reason") != "REOPENED" and any(
        pr.get("state") == "MERGED" or pr.get("merged_at") for pr in linked
    ):
        return "Done"

    open_prs = [pr for pr in linked if pr.get("state") == "OPEN"]
    if open_prs:
        if any(pr.get("is_draft") or pr.get("review_decision") == "CHANGES_REQUESTED" for pr in open_prs):
            return "In Progress"
        return "For Review"

    if item.get("execution_started") is True:
        return "In Progress"
    return "Todo"


def plan_updates(items: Iterable[dict[str, Any]]) -> list[dict[str, str | None]]:
    unique: dict[str, dict[str, Any]] = {}
    for item in items:
        item_id = item.get("item_id")
        if not isinstance(item_id, str) or not item_id:
            raise ValueError("Project item is missing item_id")
        if item_id in unique and unique[item_id] != item:
            raise ValueError(f"conflicting duplicate Project item: {item_id}")
        unique[item_id] = item

    updates: list[dict[str, str | None]] = []
    for item in unique.values():
        desired = desired_status(item)
        current = item.get("current_status")
        if desired is None or current == desired:
            continue
        updates.append(
            {
                "item_id": item["item_id"],
                "url": item.get("url"),
                "current": current,
                "desired": desired,
            }
        )
    return sorted(updates, key=lambda update: (str(update.get("url")), str(update["item_id"])))


def _read_json_lines(stream: Any) -> list[dict[str, Any]]:
    values: list[dict[str, Any]] = []
    for line in stream:
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError("expected one JSON object per line")
            values.append(value)
    return values


def verify_updates(plan: Iterable[dict[str, Any]], items: Iterable[dict[str, Any]]) -> list[str]:
    current = {item.get("item_id"): item.get("current_status") for item in items}
    return [
        str(update.get("url") or update["item_id"])
        for update in plan
        if current.get(update["item_id"]) != update.get("desired")
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("plan")
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--plan", required=True, type=Path)
    args = parser.parse_args()

    try:
        if args.command == "plan":
            for update in plan_updates(_read_json_lines(sys.stdin)):
                print(json.dumps(update, separators=(",", ":"), sort_keys=True))
            return 0
        if args.command == "verify":
            with args.plan.open() as plan_file:
                missing = verify_updates(_read_json_lines(plan_file), _read_json_lines(sys.stdin))
            for url in missing:
                print(url, file=sys.stderr)
            return 1 if missing else 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"portfolio status input error: {error}", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
