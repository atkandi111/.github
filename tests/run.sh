#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

ruby -e 'require "yaml"; ARGV.each { |file| YAML.parse_file(file); puts "yaml ok: #{file}" }' \
  .github/workflows/agent.yml \
  .github/workflows/ci.yml \
  .github/workflows/governance.yml \
  templates/client/.github/workflows/agent.yml \
  templates/client/.github/workflows/ci.yml \
  templates/client/.github/workflows/governance.yml \
  .github/ISSUE_TEMPLATE/change-request.yml \
  .github/ISSUE_TEMPLATE/agent-task.yml \
  .github/ISSUE_TEMPLATE/config.yml \
  templates/client/.github/ISSUE_TEMPLATE/change-request.yml \
  templates/client/.github/ISSUE_TEMPLATE/agent-task.yml

python3 scripts/sync-naming-workflow.py --check
python3 tests/test_pipeline.py
python3 tests/test_skill_provenance.py
git diff --check
echo "all local checks passed"
