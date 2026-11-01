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

SELF_FILE="${WORK_DIR}/self.json"
printf '{"A": [{"id": "A"}]}\n' > "${SELF_FILE}"

DEEP_FILE="${WORK_DIR}/deep.json"
cat > "${DEEP_FILE}" <<EOF
{
  "A": [{"id": "B"}],
  "B": [{"id": "C"}],
  "C": [{"id": "D"}],
  "D": [{"id": "E"}],
  "E": []
}
EOF

MISSING_FILE="${WORK_DIR}/missing.json"
printf '{"A": [{"id": "Z"}]}\n' > "${MISSING_FILE}"

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

check_absent() {
    local title="$1"
    local needle="$2"
    shift 2
    local output
    if ! output="$("$@" 2>&1)"; then
        echo "FAIL: ${title} (command failed)"
        FAILED=1
    elif printf '%s\n' "${output}" | grep -qF -- "${needle}"; then
        echo "FAIL: ${title} (unexpected '${needle}')"
        FAILED=1
    else
        echo "PASS: ${title}"
    fi
}

ARGS=(--test-mode --version 1.0.0)

# Дерево: транзитивность + общий потомок D виден один раз
check_output "tree edge A B" "A -> B" \
    "${RUN_SH}" --package A --source "${TREE_FILE}" "${ARGS[@]}" --max-depth 5
check_output "tree edge B D" "B -> D" \
    "${RUN_SH}" --package A --source "${TREE_FILE}" "${ARGS[@]}" --max-depth 5
check_output "tree edge C D" "C -> D" \
    "${RUN_SH}" --package A --source "${TREE_FILE}" "${ARGS[@]}" --max-depth 5
check_output "tree leaf D" "D -> (none)" \
    "${RUN_SH}" --package A --source "${TREE_FILE}" "${ARGS[@]}" --max-depth 5

# Цикл A->B->C->A
check_output "cycle detected" "C -> (cycle)" \
    "${RUN_SH}" --package A --source "${CYCLE_FILE}" "${ARGS[@]}" --max-depth 5
check_exit "cycle exits 0" 0 \
    "${RUN_SH}" --package A --source "${CYCLE_FILE}" "${ARGS[@]}" --max-depth 5

# Самоссылка
check_output "self cycle" "A -> (cycle)" \
    "${RUN_SH}" --package A --source "${SELF_FILE}" "${ARGS[@]}" --max-depth 5

# Ограничение глубины
check_output "depth1 root" "A -> B" \
    "${RUN_SH}" --package A --source "${DEEP_FILE}" "${ARGS[@]}" --max-depth 1
check_output "depth1 limit marker" "B -> (depth limit)" \
    "${RUN_SH}" --package A --source "${DEEP_FILE}" "${ARGS[@]}" --max-depth 1
check_absent "depth1 no C" "C" \
    "${RUN_SH}" --package A --source "${DEEP_FILE}" "${ARGS[@]}" --max-depth 1
check_output "depth3 reaches D" "C -> D" \
    "${RUN_SH}" --package A --source "${DEEP_FILE}" "${ARGS[@]}" --max-depth 3
check_output "depth3 limit at E" "D -> (depth limit)" \
    "${RUN_SH}" --package A --source "${DEEP_FILE}" "${ARGS[@]}" --max-depth 3

# Несуществующая зависимость в графе
check_exit "missing dep handled" 0 \
    "${RUN_SH}" --package A --source "${MISSING_FILE}" "${ARGS[@]}" --max-depth 5
check_output "missing dep marker" "A -> (error" \
    "${RUN_SH}" --package A --source "${MISSING_FILE}" "${ARGS[@]}" --max-depth 5

rm -rf "${WORK_DIR}"

if [ "${FAILED}" -ne 0 ]; then
    echo "STAGE 3 TESTS: FAILED"
    exit 1
fi
echo "STAGE 3 TESTS: PASSED"