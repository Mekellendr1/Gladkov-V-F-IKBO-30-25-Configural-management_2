#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_SH="${ROOT_DIR}/run.sh"
WORK_DIR="$(mktemp -d)"
FAILED=0

TREE_FILE="${WORK_DIR}/tree.json"
cat > "${TREE_FILE}" <<EOF
{
  "A": [{"id": "B"}, {"id": "C"}],
  "B": [{"id": "D"}],
  "C": [{"id": "D"}],
  "D": []
}
EOF

CYCLE_FILE="${WORK_DIR}/cycle.json"
cat > "${CYCLE_FILE}" <<EOF
{
  "A": [{"id": "B"}],
  "B": [{"id": "C"}],
  "C": [{"id": "A"}]
}
EOF

DEEP_FILE="${WORK_DIR}/deep.json"
cat > "${DEEP_FILE}" <<EOF
{
  "A": [{"id": "B"}],
  "B": [{"id": "C"}],
  "C": []
}
EOF

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

check_order() {
    local title="$1"
    local before="$2"
    local after="$3"
    shift 3
    local output
    if ! output="$("$@" 2>&1)"; then
        echo "FAIL: ${title} (command failed)"
        FAILED=1
        return
    fi
    local before_line after_line
    before_line=$(printf '%s\n' "${output}" | grep -n "^${before}\$" | head -1 | cut -d: -f1)
    after_line=$(printf '%s\n' "${output}" | grep -n "^${after}\$" | head -1 | cut -d: -f1)
    if [ -z "${before_line}" ] || [ -z "${after_line}" ]; then
        echo "FAIL: ${title} (package not found)"
        FAILED=1
    elif [ "${before_line}" -lt "${after_line}" ]; then
        echo "PASS: ${title}"
    else
        echo "FAIL: ${title} (${before} should come before ${after})"
        FAILED=1
    fi
}

ARGS=(--test-mode --version 1.0.0)

check_exit "load order exits 0" 0 "${RUN_SH}" --package A \
    --source "${TREE_FILE}" "${ARGS[@]}" --load-order --max-depth 5

check_output "load order has D" "D" "${RUN_SH}" --package A \
    --source "${TREE_FILE}" "${ARGS[@]}" --load-order --max-depth 5
check_output "load order has A" "A" "${RUN_SH}" --package A \
    --source "${TREE_FILE}" "${ARGS[@]}" --load-order --max-depth 5

check_order "D before A" "D" "A" "${RUN_SH}" --package A \
    --source "${TREE_FILE}" "${ARGS[@]}" --load-order --max-depth 5
check_order "B before A" "B" "A" "${RUN_SH}" --package A \
    --source "${TREE_FILE}" "${ARGS[@]}" --load-order --max-depth 5
check_order "C before A" "C" "A" "${RUN_SH}" --package A \
    --source "${TREE_FILE}" "${ARGS[@]}" --load-order --max-depth 5

check_output "cycle order has A" "A" "${RUN_SH}" --package A \
    --source "${CYCLE_FILE}" "${ARGS[@]}" --load-order --max-depth 5
check_output "cycle order has B" "B" "${RUN_SH}" --package A \
    --source "${CYCLE_FILE}" "${ARGS[@]}" --load-order --max-depth 5
check_output "cycle order has C" "C" "${RUN_SH}" --package A \
    --source "${CYCLE_FILE}" "${ARGS[@]}" --load-order --max-depth 5
check_exit "cycle order exits 0" 0 "${RUN_SH}" --package A \
    --source "${CYCLE_FILE}" "${ARGS[@]}" --load-order --max-depth 5

check_order "depth order C before A" "C" "A" "${RUN_SH}" --package A \
    --source "${DEEP_FILE}" "${ARGS[@]}" --load-order --max-depth 3
check_output "depth order no marker" "(depth limit)" "${RUN_SH}" --package A \
    --source "${DEEP_FILE}" "${ARGS[@]}" --load-order --max-depth 1
check_exit "depth order exits 0" 0 "${RUN_SH}" --package A \
    --source "${DEEP_FILE}" "${ARGS[@]}" --load-order --max-depth 1

rm -rf "${WORK_DIR}"

if [ "${FAILED}" -ne 0 ]; then
    echo "STAGE 4 TESTS: FAILED"
    exit 1
fi
echo "STAGE 4 TESTS: PASSED"