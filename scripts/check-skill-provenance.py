#!/usr/bin/env python3
"""Validate vendor trust roots and exact runtime skill provenance."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys
from urllib.parse import urlsplit


ROOT = pathlib.Path(__file__).resolve().parents[1]
MAX_VERIFICATION_AGE_DAYS = 365
TRUST_ROOTS = {
    "aws": {
        "display_name": "AWS",
        "publishers": ["aws", "awslabs"],
        "sources": ["https://github.com/aws/", "https://github.com/awslabs/"],
        "evidence": ["https://github.com/aws/", "https://github.com/awslabs/", "https://docs.aws.amazon.com/"],
    },
    "gcp": {
        "display_name": "Google Cloud",
        "publishers": ["GoogleCloudPlatform"],
        "sources": ["https://github.com/GoogleCloudPlatform/"],
        "evidence": ["https://github.com/GoogleCloudPlatform/", "https://cloud.google.com/"],
    },
    "terraform": {
        "display_name": "HashiCorp Terraform",
        "publishers": ["hashicorp"],
        "sources": ["https://github.com/hashicorp/"],
        "evidence": ["https://github.com/hashicorp/", "https://developer.hashicorp.com/terraform/"],
    },
}
REQUIRED_SKILL_FIELDS = {
    "name", "package_id", "publisher", "source", "version", "digest",
    "evidence", "verified_on", "purpose",
}
RUNTIME_IDENTITY_FIELDS = {"name", "package_id", "publisher", "source", "version", "digest"}


def load_json(path: pathlib.Path) -> tuple[dict[str, object] | None, list[str]]:
    try:
        value = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return None, [f"invalid JSON in {path}: {error}"]
    if not isinstance(value, dict):
        return None, [f"{path} must contain a JSON object"]
    return value, []


def canonical_vendor_url(value: object, prefixes: list[str]) -> bool:
    if not isinstance(value, str) or "%" in value:
        return False
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return False
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or port is not None:
        return False
    if parsed.query or parsed.fragment or "//" in parsed.path or any(part in {".", ".."} for part in parsed.path.split("/")):
        return False
    for prefix in prefixes:
        trusted = urlsplit(prefix)
        if parsed.hostname.lower() == trusted.hostname.lower() and parsed.path.startswith(trusted.path):
            return True
    return False


def validate_registry(path: pathlib.Path, today: dt.date | None = None) -> tuple[dict[str, object] | None, list[str]]:
    data, errors = load_json(path)
    if data is None:
        return None, errors
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    vendors = data.get("vendors")
    if not isinstance(vendors, dict) or set(vendors) != set(TRUST_ROOTS):
        return data, errors + ["vendors must contain exactly aws, gcp, and terraform"]

    seen: set[str] = set()
    current = today or dt.date.today()
    for vendor_name, root in TRUST_ROOTS.items():
        vendor = vendors[vendor_name]
        if not isinstance(vendor, dict):
            errors.append(f"{vendor_name}: vendor entry must be an object")
            continue
        if vendor.get("display_name") != root["display_name"]:
            errors.append(f"{vendor_name}: display_name trust anchor drifted")
        if vendor.get("allowed_publishers") != root["publishers"]:
            errors.append(f"{vendor_name}: allowed_publishers trust anchor drifted")
        if vendor.get("allowed_sources") != root["sources"]:
            errors.append(f"{vendor_name}: allowed_sources trust anchor drifted")
        if vendor.get("allowed_evidence") != root["evidence"]:
            errors.append(f"{vendor_name}: allowed_evidence trust anchor drifted")
        skills = vendor.get("approved_skills")
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
            seen.add(str(name))
            if skill["publisher"] not in root["publishers"]:
                errors.append(f"{vendor_name}/{name}: publisher is not vendor-approved")
            if not isinstance(skill["package_id"], str) or not skill["package_id"].startswith(f"{skill['publisher']}/"):
                errors.append(f"{vendor_name}/{name}: package_id must be namespaced by the approved publisher")
            if not canonical_vendor_url(skill["source"], root["sources"]):
                errors.append(f"{vendor_name}/{name}: source is not a canonical vendor repository URL")
            if not canonical_vendor_url(skill["evidence"], root["evidence"]):
                errors.append(f"{vendor_name}/{name}: evidence is outside canonical vendor sources")
            if not isinstance(skill["version"], str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", skill["version"]):
                errors.append(f"{vendor_name}/{name}: version must be an exact immutable release identifier")
            if not isinstance(skill["digest"], str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", skill["digest"]):
                errors.append(f"{vendor_name}/{name}: digest must be sha256 followed by 64 lowercase hex characters")
            try:
                verified = dt.date.fromisoformat(skill["verified_on"])
                age = (current - verified).days
                if age < 0:
                    errors.append(f"{vendor_name}/{name}: verified_on cannot be in the future")
                elif age > MAX_VERIFICATION_AGE_DAYS:
                    errors.append(f"{vendor_name}/{name}: provenance verification is older than {MAX_VERIFICATION_AGE_DAYS} days")
            except (TypeError, ValueError):
                errors.append(f"{vendor_name}/{name}: verified_on must be YYYY-MM-DD")
            if not isinstance(skill["purpose"], str) or not skill["purpose"].strip():
                errors.append(f"{vendor_name}/{name}: purpose must be non-empty")
    return data, errors


def validate_runtime(registry: dict[str, object], runtime_path: pathlib.Path, required: list[str]) -> list[str]:
    runtime, errors = load_json(runtime_path)
    if runtime is None:
        return errors
    installed = runtime.get("skills")
    if not isinstance(installed, list):
        return ["runtime manifest must contain a skills list"]
    by_name: dict[str, dict[str, object]] = {}
    for skill in installed:
        if not isinstance(skill, dict) or set(skill) != RUNTIME_IDENTITY_FIELDS:
            errors.append(f"runtime skills must contain exactly {sorted(RUNTIME_IDENTITY_FIELDS)}")
            continue
        name = skill.get("name")
        if not isinstance(name, str) or name in by_name:
            errors.append("runtime skill names must be non-empty and unique")
            continue
        by_name[name] = skill

    approved: dict[str, dict[str, object]] = {}
    vendors = registry.get("vendors", {})
    if isinstance(vendors, dict):
        for vendor in vendors.values():
            if isinstance(vendor, dict):
                for skill in vendor.get("approved_skills", []):
                    if isinstance(skill, dict) and isinstance(skill.get("name"), str):
                        approved[skill["name"]] = skill
    for name in required:
        expected = approved.get(name)
        actual = by_name.get(name)
        if expected is None:
            errors.append(f"required skill {name!r} is not approved")
        elif actual is None:
            errors.append(f"required skill {name!r} is not installed")
        else:
            mismatch = [field for field in RUNTIME_IDENTITY_FIELDS if actual.get(field) != expected.get(field)]
            if mismatch:
                errors.append(f"required skill {name!r} runtime provenance mismatch: {', '.join(sorted(mismatch))}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", nargs="?", type=pathlib.Path, default=ROOT / "governance/official-skills.json")
    parser.add_argument("--runtime-manifest", type=pathlib.Path)
    parser.add_argument("--require-skill", action="append", default=[])
    args = parser.parse_args()
    registry, errors = validate_registry(args.manifest)
    if args.require_skill and not args.runtime_manifest:
        errors.append("--require-skill needs --runtime-manifest")
    if registry is not None and args.runtime_manifest:
        errors.extend(validate_runtime(registry, args.runtime_manifest, args.require_skill))
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print("official skill provenance is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
