#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_SH="${ROOT_DIR}/run.sh"
WORK_DIR="$(mktemp -d)"
GRAPH_FILE="${WORK_DIR}/graph.json"
FAILED=0

cat > "${GRAPH_FILE}" <<EOF
{
  "A": [{"id": "B"}, {"id": "C"}],
  "B": [{"id": "D"}],
  "C": [],
  "D": []
}
EOF

BAD_DEPS="${WORK_DIR}/baddeps.json"
printf '{"A": [{"version": "1.0.0"}]}\n' > "${BAD_DEPS}"
BAD_LIST="${WORK_DIR}/badlist.json"
printf '{"A": "oops"}\n' > "${BAD_LIST}"
BAD_JSON="${WORK_DIR}/badjson.json"
printf 'not json\n' > "${BAD_JSON}"

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

check_output() {
    local title="$1"
    local needle="$2"
    shift 2
    local output
    if ! output="$("$@" 2>&1)"; then
        echo "FAIL: ${title} (command failed)"
        FAILED=1
    elif printf '%s\n' "${output}" | grep -qF -- "${needle}"; then
        echo "PASS: ${title}"
    else
        echo "FAIL: ${title} (missing '${needle}')"
        FAILED=1
    fi
}

check_exit "test mode builds graph" 0 "${RUN_SH}" --package A \
    --source "${GRAPH_FILE}" --test-mode --max-depth 5
check_output "test mode edge A B" "A -> B" "${RUN_SH}" --package A \
    --source "${GRAPH_FILE}" --test-mode --max-depth 5
check_output "test mode edge A C" "A -> C" "${RUN_SH}" --package A \
    --source "${GRAPH_FILE}" --test-mode --max-depth 5
check_output "test mode edge B D" "B -> D" "${RUN_SH}" --package A \
    --source "${GRAPH_FILE}" --test-mode --max-depth 5
check_output "test mode leaf C" "C -> (none)" "${RUN_SH}" --package A \
    --source "${GRAPH_FILE}" --test-mode --max-depth 5

check_exit "test mode missing package" 2 "${RUN_SH}" --package Z \
    --source "${GRAPH_FILE}" --test-mode --max-depth 5
check_exit "test mode dep without id" 2 "${RUN_SH}" --package A \
    --source "${BAD_DEPS}" --test-mode --max-depth 5
check_exit "test mode deps not a list" 2 "${RUN_SH}" --package A \
    --source "${BAD_LIST}" --test-mode --max-depth 5
check_exit "test mode bad json" 2 "${RUN_SH}" --package A \
    --source "${BAD_JSON}" --test-mode --max-depth 5

if command -v curl >/dev/null 2>&1 \
    && curl -fsSI https://api.nuget.org/ >/dev/null 2>&1; then
    GOOD_URL="https://api.nuget.org/v3/index.json"
    check_exit "nuget newtonsoft exits 0" 0 "${RUN_SH}" \
        --package Newtonsoft.Json --source "${GOOD_URL}" \
        --version 13.0.3 --max-depth 2
    check_output "nuget has Microsoft.CSharp" "Microsoft.CSharp" \
        "${RUN_SH}" --package Newtonsoft.Json \
        --source "${GOOD_URL}" --version 13.0.3 --max-depth 2
else
    echo "SKIP: nuget live tests (no internet)"
fi

rm -rf "${WORK_DIR}"

if [ "${FAILED}" -ne 0 ]; then
    echo "STAGE 2 TESTS: FAILED"
    exit 1
fi
echo "STAGE 2 TESTS: PASSED"