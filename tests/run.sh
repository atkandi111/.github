#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

ruby -e 'require "yaml"; ARGV.each { |file| YAML.parse_file(file); puts "yaml ok: #{file}" }' \
  .github/workflows/agent.yml \
  .github/workflows/ci.yml \
  templates/client/.github/workflows/agent.yml \
  templates/client/.github/workflows/ci.yml \
  templates/client/.github/ISSUE_TEMPLATE/agent-task.yml

python3 tests/test_pipeline.py
python3 tests/test_skill_provenance.py
git diff --check
echo "all local checks passed"
