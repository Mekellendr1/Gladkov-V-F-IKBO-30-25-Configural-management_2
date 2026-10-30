#!/usr/bin/env bash
set -u

TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATUS=0

for suite in "${TESTS_DIR}"/test_stage*.sh; do
    echo "== ${suite##*/} =="
    bash "${suite}" || STATUS=1
done

exit "${STATUS}"