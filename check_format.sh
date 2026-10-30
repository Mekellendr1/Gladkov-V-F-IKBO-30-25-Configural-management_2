#!/bin/bash
echo "=== 1. flake8: длина строк, PEP8, пробелы (Р2, И1) ==="
.venv/bin/flake8 src/ --max-line-length=80

echo "=== 2. radon: цикломатическая сложность >10 (Ц1) ==="
.venv/bin/radon cc src/ -a -nc

echo "=== 3. AST: функции >40 строк, аргументы >7, магические числа (Ф1, А1, М1) ==="
.venv/bin/python - <<'EOF'
import ast
import glob

for path in glob.glob('src/**/*.py', recursive=True):
    with open(path, encoding='utf-8') as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            size = node.end_lineno - node.lineno + 1
            if size > 40:
                print(f"Ф1: {path}:{node.lineno} {node.name}() = {size} строк")
            if len(node.args.args) > 7:
                print(f"А1: {path}:{node.lineno} {node.name}() = {len(node.args.args)} аргументов")
        if isinstance(node, ast.Compare):
            for side in [node.left] + node.comparators:
                if isinstance(side, ast.Constant) and type(side.value) in (int, float):
                    print(f"М1: {path}:{node.lineno} число в сравнении")
                    break
EOF

echo "=== 4. Комментарии вместо docstring (К1) ==="
grep -rnE '^\s+#' src/ --include='*.py'

echo "=== 5. Файлы >1000 строк (Р1) ==="
find src -name '*.py' | xargs wc -l | awk '$1 > 1000'

echo "=== Готово. Пустой вывод выше = чисто ==="