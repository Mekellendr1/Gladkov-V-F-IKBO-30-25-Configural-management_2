#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_SH="${ROOT_DIR}/run.sh"
WORK_DIR="$(mktemp -d)"
GRAPH_FILE="${WORK_DIR}/graph.json"
FAILED=0

printf '{"A": {"1.0.0": []}}\n' > "${GRAPH_FILE}"

check_exit() {
    local title="$1"
    local expected="$2"
    shift 2
    local status=0
    "$@" > /dev/null 2>&1 || status=$?
    if [ "${status}" -ne "${expected}" ]; then
        echo "FAIL: ${title} (exit ${status}, want ${expected})"
        FAILED=1
    else
        echo "PASS: ${title}"
    fi
}

BASE=("${RUN_SH}" --package A --source "${GRAPH_FILE}" --test-mode)

check_exit "valid config exits 0" 0 "${BASE[@]}"
check_exit "missing package" 2 "${RUN_SH}" --source "${GRAPH_FILE}" \
    --test-mode
check_exit "empty package" 2 "${RUN_SH}" --package "" \
    --source "${GRAPH_FILE}" --test-mode
check_exit "bad package chars" 2 "${RUN_SH}" --package "bad name" \
    --source "${GRAPH_FILE}" --test-mode
check_exit "missing source" 2 "${RUN_SH}" --package A
check_exit "missing test file" 2 "${RUN_SH}" --package A \
    --source "${WORK_DIR}/nope.json" --test-mode
check_exit "bad url" 2 "${RUN_SH}" --package A --source "notaurl"
check_exit "bad version" 2 "${BASE[@]}" --version 1.2
check_exit "bad depth zero" 2 "${BASE[@]}" --max-depth 0
check_exit "bad depth big" 2 "${BASE[@]}" --max-depth 100
check_exit "bad depth text" 2 "${BASE[@]}" --max-depth abc

rm -rf "${WORK_DIR}"

if [ "${FAILED}" -ne 0 ]; then
    echo "STAGE 1 TESTS: FAILED"
    exit 1
fi
echo "STAGE 1 TESTS: PASSED"