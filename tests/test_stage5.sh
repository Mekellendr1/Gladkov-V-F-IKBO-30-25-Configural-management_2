#!/usr/bin/env bash
set -u

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_SH="${ROOT_DIR}/run.sh"
WORK_DIR="$(mktemp -d)"
FAILED=0

TREE_FILE="${WORK_DIR}/tree.json"
cat > "${TREE_FILE}" <<GRAPH
{
  "A": [{"id": "B"}, {"id": "C"}],
  "B": [{"id": "D"}],
  "C": [{"id": "D"}],
  "D": []
}
GRAPH

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

check_file() {
    local title="$1"
    local filename="$2"
    local needle="$3"
    if [ ! -f "${filename}" ]; then
        echo "FAIL: ${title} (file not found: ${filename})"
        FAILED=1
    elif grep -qF -- "${needle}" "${filename}"; then
        echo "PASS: ${title}"
    else
        echo "FAIL: ${title} (missing '${needle}' in ${filename})"
        FAILED=1
    fi
}

ARGS=(--test-mode --version 1.0.0 --max-depth 5)

# ASCII tree mode
check_exit "ascii tree exits 0" 0 "${RUN_SH}" --package A \
    --source "${TREE_FILE}" "${ARGS[@]}" --ascii-tree
check_output "ascii tree has A" "A" "${RUN_SH}" --package A \
    --source "${TREE_FILE}" "${ARGS[@]}" --ascii-tree
check_output "ascii tree has B" "B" "${RUN_SH}" --package A \
    --source "${TREE_FILE}" "${ARGS[@]}" --ascii-tree
check_output "ascii tree has box drawing" "├──" "${RUN_SH}" --package A \
    --source "${TREE_FILE}" "${ARGS[@]}" --ascii-tree

# DOT file generation
cd "${WORK_DIR}"
check_exit "dot file generated" 0 "${RUN_SH}" --package A \
    --source "${TREE_FILE}" "${ARGS[@]}"
check_file "dot file exists" "A.dot" "digraph"
check_file "dot file has edges" "A.dot" '"A" -> "B"'
check_file "dot file has leaf" "A.dot" 'fillcolor=lightgreen'
cd "${ROOT_DIR}"

rm -rf "${WORK_DIR}"

if [ "${FAILED}" -ne 0 ]; then
    echo "STAGE 5 TESTS: FAILED"
    exit 1
fi
echo "STAGE 5 TESTS: PASSED"
