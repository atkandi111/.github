#!/usr/bin/env python3
"""Allow-and-deny fixtures for official skill provenance."""

from __future__ import annotations

import datetime as dt
import json
import pathlib
import subprocess
import sys
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts/check-skill-provenance.py"
MANIFEST = ROOT / "governance/official-skills.json"


def run(path: pathlib.Path, *args: str) -> int:
    return subprocess.run(
        [sys.executable, str(CHECKER), str(path), *args],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    ).returncode


def main() -> None:
    assert run(MANIFEST) == 0
    with tempfile.TemporaryDirectory() as directory:
        fixture = pathlib.Path(directory) / "skills.json"
        runtime = pathlib.Path(directory) / "runtime.json"
        data = json.loads(MANIFEST.read_text())
        skill = {
            "name": "verified-gcp-skill",
            "package_id": "GoogleCloudPlatform/verified-gcp-skill",
            "publisher": "GoogleCloudPlatform",
            "source": "https://github.com/GoogleCloudPlatform/verified-gcp-skill",
            "version": "v1.2.3",
            "digest": "sha256:" + "a" * 64,
            "evidence": "https://cloud.google.com/example",
            "verified_on": dt.date.today().isoformat(),
            "purpose": "Manage GCP",
        }
        data["vendors"]["gcp"]["approved_skills"] = [skill]
        fixture.write_text(json.dumps(data))
        assert run(fixture) == 0, "vendor-controlled immutable identity should pass"

        runtime.write_text(json.dumps({"skills": [{key: skill[key] for key in (
            "name", "package_id", "publisher", "source", "version", "digest"
        )}]}))
        runtime_args = ("--runtime-manifest", str(runtime), "--require-skill", skill["name"])
        assert run(fixture, *runtime_args) == 0, "exact runtime provenance should pass"

        altered = json.loads(json.dumps(data))
        altered["vendors"]["gcp"]["allowed_publishers"] = ["third-party"]
        fixture.write_text(json.dumps(altered))
        assert run(fixture) != 0, "registry must not redefine validator-owned trust roots"

        for bad_url in (
            "https://github.com/GoogleCloudPlatform/../third-party/skill",
            "https://github.com/GoogleCloudPlatform/%2e%2e/third-party/skill",
            "https://user@github.com/GoogleCloudPlatform/skill",
            "https://github.com:443/GoogleCloudPlatform/skill",
        ):
            altered = json.loads(json.dumps(data))
            altered["vendors"]["gcp"]["approved_skills"][0]["source"] = bad_url
            fixture.write_text(json.dumps(altered))
            assert run(fixture) != 0, f"non-canonical URL must be rejected: {bad_url}"

        altered = json.loads(json.dumps(data))
        altered["vendors"]["gcp"]["approved_skills"][0]["verified_on"] = (
            dt.date.today() + dt.timedelta(days=1)
        ).isoformat()
        fixture.write_text(json.dumps(altered))
        assert run(fixture) != 0, "future verification dates must be rejected"

        altered["vendors"]["gcp"]["approved_skills"][0]["verified_on"] = (
            dt.date.today() - dt.timedelta(days=366)
        ).isoformat()
        fixture.write_text(json.dumps(altered))
        assert run(fixture) != 0, "stale verification dates must be rejected"

        altered = json.loads(json.dumps(data))
        altered["vendors"]["gcp"]["approved_skills"][0].update({
            "publisher": "random-user",
            "source": "https://example.com/skill",
        })
        fixture.write_text(json.dumps(altered))
        assert run(fixture) != 0, "unofficial publisher and source must be rejected"

        fixture.write_text(json.dumps(data))
        wrong_runtime = json.loads(runtime.read_text())
        wrong_runtime["skills"][0]["source"] = "https://github.com/GoogleCloudPlatform/same-name-impostor"
        runtime.write_text(json.dumps(wrong_runtime))
        assert run(fixture, *runtime_args) != 0, "same-name, different-source runtime must fail"

        wrong_runtime["skills"][0]["source"] = skill["source"]
        wrong_runtime["skills"][0]["digest"] = "sha256:" + "b" * 64
        runtime.write_text(json.dumps(wrong_runtime))
        assert run(fixture, *runtime_args) != 0, "runtime digest mismatch must fail"

        data["vendors"]["gcp"]["approved_skills"][0]["digest"] = "sha256:not-a-digest"
        fixture.write_text(json.dumps(data))
        assert run(fixture) != 0, "non-immutable digest must be rejected"
    print("ok: official skill provenance")


if __name__ == "__main__":
    main()
