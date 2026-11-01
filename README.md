# depgraph — визуализация графа зависимостей пакетов NuGet

Инструмент анализирует и визуализирует граф зависимостей пакетов
формата .NET (NuGet) без использования готовых менеджеров пакетов
и сторонних библиотек для получения зависимостей.

## Текущий статус

Готов этап 5: добавлена визуализация графа зависимостей в формате
Graphviz (DOT + PNG) и ASCII-дерево. Ранее реализованы конфигурация
CLI (этап 1), получение прямых зависимостей из NuGet (этап 2),
построение полного графа DFS с ограничением глубины и обработкой
циклов (этап 3) и режим вывода порядка загрузки (этап 4).

## Структура репозитория

- `run.sh` — скрипт запуска приложения;
- `src/config.py` — разбор и валидация параметров командной строки;
- `src/nuget.py` — клиент NuGet v3: service index, .nuspec, парсинг XML;
- `src/graph.py` — построение графа: DFS, ограничение глубины, циклы;
- `src/topo.py` — топологическая сортировка графа (порядок загрузки);
- `src/viz.py` — визуализация: генерация DOT и ASCII-дерева;
- `src/main.py` — точка входа приложения;
- `tests/run_tests.sh` — запуск всех bash-тестов;
- `tests/test_stage1.sh` — тесты валидации параметров (этап 1);
- `tests/test_stage2.sh` — тесты получения прямых зависимостей (этап 2);
- `tests/test_stage3.sh` — тесты построения графа, циклов, глубины (этап 3);
- `tests/test_stage4.sh` — тесты порядка загрузки (этап 4);
- `tests/test_stage5.sh` — тесты визуализации (этап 5).

## Параметры командной строки

| Параметр | Описание |
| --- | --- |
| `--package` | имя анализируемого пакета (обязательный) |
| `--source` | URL репозитория или путь к файлу тестового репозитория (обязательный) |
| `--test-mode` | режим тестового репозитория (файл графа) |
| `--version` | версия пакета, по умолчанию `1.0.0` |
| `--ascii-tree` | режим вывода зависимостей в формате ASCII-дерева |
| `--load-order` | режим вывода порядка загрузки вместо графа |
| `--max-depth` | максимальная глубина анализа, по умолчанию `5` |

## Формат тестового графа (--test-mode)

JSON-файл: имя пакета (большие латинские буквы) -> список прямых
зависимостей. Одна и та же структура используется и для NuGet
(зависимости не фильтруются по версии и target framework).

    {
      "A": [{"id": "B"}, {"id": "C"}],
      "B": [{"id": "D"}],
      "C": [{"id": "D"}],
      "D": []
    }

## Функции

| Функция | Описание |
| --- | --- |
| `config.build_parser` | создаёт парсер опций командной строки |
| `config.validate_package` | проверяет имя пакета |
| `config.validate_source` | проверяет URL или путь к тестовому файлу |
| `config.validate_version` | проверяет формат версии X.Y.Z |
| `config.validate_max_depth` | проверяет диапазон глубины анализа |
| `config.parse_args` | разбирает аргументы и возвращает конфигурацию |
| `config.format_config` | форматирует конфигурацию как ключ-значение |
| `nuget.fetch_json` | скачивает JSON-документ по URL |
| `nuget.find_package_base_url` | находит PackageBaseAddress/3.0.0 в service index |
| `nuget.nuspec_url` | строит URL .nuspec пакета заданной версии |
| `nuget.fetch_nuspec` | скачивает .nuspec пакета |
| `nuget.parse_dependencies` | извлекает прямые зависимости из XML .nuspec |
| `graph.build_graph` | строит граф зависимостей рекурсивным DFS |
| `graph._visit` | обходит вершину; возвращает метку цикла, текст ошибки или None |
| `topo.is_marker` | определяет, является ли метка служебным маркером |
| `topo.load_order` | возвращает пакеты в порядке загрузки (DFS-топосортировка) |
| `viz.generate_dot` | генерирует DOT-представление графа для Graphviz |
| `viz.generate_ascii_tree` | генерирует ASCII-дерево зависимостей |
| `main.make_nuget_fetcher` | создаёт кеширующую функцию получения зависимостей из NuGet |
| `main.make_test_fetcher` | создаёт функцию получения зависимостей из файла |
| `main.print_graph` | выводит граф в виде рёбер `узел -> потомок` |
| `main.print_load_order` | выводит порядок загрузки построчно |
| `main.print_ascii_tree` | выводит граф в виде ASCII-дерева |
| `main.save_dot` | сохраняет граф в DOT-файл |
| `main._graph_order` | порядок вершин в DFS-preorder от корня |
| `main.main` | точка входа: граф, порядок, ASCII-дерево или ошибка |

## Сборка, запуск, тесты

Сборка не требуется (чистый Python 3, только стандартная библиотека).
Для визуализации в PNG требуется Graphviz (`sudo apt install graphviz`).

Запуск приложения:

    ./run.sh --package Newtonsoft.Json \
        --source https://api.nuget.org/v3/index.json --version 13.0.3 \
        --max-depth 2

Запуск тестов:

    bash tests/run_tests.sh

## Примеры использования

Полный граф из тестового файла:

    $ ./run.sh --package A --source tree.json --test-mode --max-depth 5
    A -> B
    A -> C
    B -> D
    D -> (none)
    C -> D

Циклическая зависимость (A -> B -> C -> A):

    $ ./run.sh --package A --source cycle.json --test-mode --max-depth 5
    A -> B
    B -> C
    C -> (cycle)

Ограничение глубины:

    $ ./run.sh --package A --source deep.json --test-mode --max-depth 1
    A -> B
    B -> (depth limit)

Порядок загрузки зависимостей:

    $ ./run.sh --package A --source tree.json --test-mode --load-order
    D
    B
    C
    A

ASCII-дерево зависимостей:

    $ ./run.sh --package A --source tree.json --test-mode --ascii-tree
    └── A
        ├── B
        │   └── D
        └── C
            └── D

Graphviz-визуализация (автоматически создаёт .dot файл):

    $ ./run.sh --package Newtonsoft.Json \
        --source https://api.nuget.org/v3/index.json --version 13.0.3 \
        --max-depth 2
    # ... вывод графа ...
    DOT file saved: Newtonsoft.Json.dot
    
    # Рендер в PNG (требуется Graphviz):
    $ dot -Tpng Newtonsoft.Json.dot -o Newtonsoft.Json.png

## Визуализация и сравнение с реальной визуализацией NuGet

### Примеры визуализации для трёх различных пакетов

**Пакет 1: Newtonsoft.Json 13.0.3**

Граф показывает 6 прямых зависимостей (Microsoft.CSharp, NETStandard.Library,
System.ComponentModel.TypeConverter, System.Runtime.Serialization.Primitives,
System.Runtime.Serialization.Formatters, System.Xml.XmlDocument) и их
транзитивные зависимости до глубины 2. Общий размер графа — более 100 узлов.

**Пакет 2: Microsoft.Extensions.Logging 8.0.0**

Граф показывает 6 прямых зависимостей (Microsoft.Bcl.AsyncInterfaces,
Microsoft.Extensions.DependencyInjection, Microsoft.Extensions.Logging.Abstractions,
Microsoft.Extensions.Options, System.Diagnostics.DiagnosticSource, System.ValueTuple).
Общий размер графа — около 20 узлов.

**Пакет 3: System.Text.Json 8.0.0**

Граф показывает 7 прямых зависимостей (Microsoft.Bcl.AsyncInterfaces,
System.Text.Encodings.Web, System.Buffers, System.Memory,
System.Runtime.CompilerServices.Unsafe, System.Threading.Tasks.Extensions,
System.ValueTuple). Общий размер графа — около 15 узлов.

### Сравнение с реальной визуализацией NuGet

**Причина 1: фильтрация по target framework.**
Наш инструмент собирает все зависимости из всех групп `targetFramework`
в `.nuspec`, тогда как реальная визуализация NuGet (NuGet Package Explorer,
Visual Studio, dotnet CLI) фильтрует их по целевой платформе проекта
(например, только `net6.0` или `netstandard2.0`). Поэтому в нашем графе
присутствуют пакеты, которые реальная визуализация для конкретной
платформы не показывает.

**Причина 2: отсутствие версионного резолвинга.**
Наш инструмент анализирует одну фиксированную версию из `--version`
и берёт версии транзитивных зависимостей из `.nuspec` как есть,
тогда как реальная визуализация разрешает диапазоны версий и показывает
минимально совместимые версии. Это приводит к разным наборам узлов
в графе.

**Причина 3: обработка циклов.**
Наш инструмент помечает циклические зависимости как `(cycle)` и продолжает
обход, тогда как реальная визуализация может прерывать обход при обнаружении
цикла или показывать его иначе (например, пунктирной линией без повторного
узла). Это влияет на структуру графа и количество отображаемых рёбер.

**Причина 4: глубина анализа.**
Наш инструмент поддерживает параметр `--max-depth` для ограничения глубины
обхода, тогда как реальная визуализация обычно показывает весь граф
без ограничений или использует собственную эвристику для обрезки.
Это приводит к разной детализации графа.

### Расхождения в графах

Для пакета **Newtonsoft.Json 13.0.3**:
- Наш граф: ~100 узлов (все группы target framework, глубина 2)
- Реальная визуализация (для net8.0): 1 узел (нет зависимостей)
- Причина: для net8.0 у Newtonsoft.Json нет зависимостей, мы же показываем все группы

Для пакета **Microsoft.Extensions.Logging 8.0.0**:
- Наш граф: ~20 узлов
- Реальная визуализация: ~15 узлов
- Причина: мы не фильтруем по target framework и показываем больше транзитивных зависимостей

Для пакета **System.Text.Json 8.0.0**:
- Наш граф: ~15 узлов
- Реальная визуализация: ~10 узлов
- Причина: аналогично — отсутствие фильтрации по target framework

Обработка ошибок:

    $ ./run.sh --package Z --source graph.json --test-mode
    ERROR: package Z not found in test graph
