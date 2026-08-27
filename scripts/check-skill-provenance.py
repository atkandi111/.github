#!/usr/bin/env python3
"""Validate the reviewed vendor-official skill registry."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
from urllib.parse import urlparse


ROOT = pathlib.Path(__file__).resolve().parents[1]
EXPECTED_VENDORS = {"aws", "gcp", "terraform"}
REQUIRED_SKILL_FIELDS = {"name", "publisher", "source", "evidence", "verified_on", "purpose"}


def validate(path: pathlib.Path) -> list[str]:
    errors: list[str] = []
    try:
        data = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return [f"invalid registry: {error}"]
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    vendors = data.get("vendors")
    if not isinstance(vendors, dict) or set(vendors) != EXPECTED_VENDORS:
        return errors + ["vendors must contain exactly aws, gcp, and terraform"]

    seen: set[str] = set()
    for vendor_name, vendor in vendors.items():
        publishers = vendor.get("allowed_publishers")
        sources = vendor.get("allowed_sources")
        skills = vendor.get("approved_skills")
        if not isinstance(publishers, list) or not publishers or not all(isinstance(value, str) and value for value in publishers):
            errors.append(f"{vendor_name}: allowed_publishers must be a non-empty string list")
            continue
        if not isinstance(sources, list) or not sources or not all(isinstance(value, str) and value.startswith("https://") for value in sources):
            errors.append(f"{vendor_name}: allowed_sources must contain HTTPS prefixes")
            continue
        if not isinstance(skills, list):
            errors.append(f"{vendor_name}: approved_skills must be a list")
            continue
        for skill in skills:
            if not isinstance(skill, dict) or set(skill) != REQUIRED_SKILL_FIELDS:
                errors.append(f"{vendor_name}: every skill must contain exactly {sorted(REQUIRED_SKILL_FIELDS)}")
                continue
            name = skill["name"]
            if not isinstance(name, str) or not name or name in seen:
                errors.append(f"{vendor_name}: skill names must be non-empty and globally unique")
            seen.add(name)
            if skill["publisher"] not in publishers:
                errors.append(f"{vendor_name}/{name}: publisher is not vendor-approved")
            for field in ("source", "evidence"):
                value = skill[field]
                if not isinstance(value, str) or not any(value.startswith(prefix) for prefix in sources):
                    errors.append(f"{vendor_name}/{name}: {field} is outside vendor-controlled sources")
                elif urlparse(value).scheme != "https":
                    errors.append(f"{vendor_name}/{name}: {field} must use HTTPS")
            try:
                dt.date.fromisoformat(skill["verified_on"])
            except (TypeError, ValueError):
                errors.append(f"{vendor_name}/{name}: verified_on must be YYYY-MM-DD")
            if not isinstance(skill["purpose"], str) or not skill["purpose"].strip():
                errors.append(f"{vendor_name}/{name}: purpose must be non-empty")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", nargs="?", type=pathlib.Path, default=ROOT / "governance/official-skills.json")
    args = parser.parse_args()
    errors = validate(args.manifest)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print("official skill registry is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
