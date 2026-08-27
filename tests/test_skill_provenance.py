#!/usr/bin/env python3
"""Allow-and-deny fixtures for official skill provenance."""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check-skill-provenance.py"
MANIFEST = ROOT / "governance/official-skills.json"


def run(path: pathlib.Path) -> int:
    return subprocess.run(
        [sys.executable, str(CHECKER), str(path)],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode


def main() -> None:
    assert run(MANIFEST) == 0
    data = json.loads(MANIFEST.read_text())
    with tempfile.TemporaryDirectory() as directory:
        fixture = pathlib.Path(directory) / "skills.json"
        data["vendors"]["gcp"]["approved_skills"] = [{
            "name": "third-party-gcp",
            "publisher": "random-user",
            "source": "https://example.com/skill",
            "evidence": "https://example.com/about",
            "verified_on": "2026-08-27",
            "purpose": "Manage GCP",
        }]
        fixture.write_text(json.dumps(data))
        assert run(fixture) != 0, "unofficial publisher and source must be rejected"

        data["vendors"]["gcp"]["approved_skills"][0].update({
            "name": "verified-gcp-skill",
            "publisher": "GoogleCloudPlatform",
            "source": "https://github.com/GoogleCloudPlatform/example/tree/main/skill",
            "evidence": "https://cloud.google.com/example",
        })
        fixture.write_text(json.dumps(data))
        assert run(fixture) == 0, "vendor-controlled publisher and sources should pass structural validation"
    print("ok: official skill provenance")


if __name__ == "__main__":
    main()
